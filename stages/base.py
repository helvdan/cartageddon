import logging
from abc import ABC, abstractmethod
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from typing import Dict, List, Type, Any, Tuple
import shutil

from artifacts import Artifact
from common import RunTimeContext

logger = logging.getLogger("PIPELINE")


class Stage(ABC):
    """Абстрактный класс для стадии ETL-трансформации."""
    is_mandatory: bool = True

    @property
    def logger(self) -> logging.Logger:
        # оставляем как динамическое свойство для форка параллельных стадий
        return logging.getLogger(self.name)

    @property
    @abstractmethod
    def artifact_cls(self) -> Type[Artifact]:
        """Каждый наследник обязан вернуть конкретный класс артефакта."""
        pass

    def __init__(self, context: RunTimeContext) -> None:
        self.global_context = context

    def _get_path(self, oc_table_name) -> Path:
        return Path(f"{self.global_context.work_dir}/{oc_table_name}.{self.postfix}.{self.artifact_cls.extension}")

    def create_artifact(self, oc_table_name: str) -> Artifact:
        path = self._get_path(oc_table_name)
        return self.artifact_cls(path=path)

    def copy_artifact(self, artifact: Artifact) -> Artifact:
        path = self._get_path(artifact.oc_table_name)
        new_artifact = self.artifact_cls(path=path)
        shutil.copyfile(artifact.path, new_artifact.path)
        return new_artifact

    @property
    def postfix(self) -> str:
        """Постфикс для файла"""
        return ""

    @property
    @abstractmethod
    def name(self) -> str:
        """Имя стадии для сопоставления с аргументами CLI."""
        pass

    def clean_previous_data(self) -> Any:
        """Очистить данные предыдущего запуска."""
        d = Path(self.global_context.work_dir)
        for p in d.glob(f"*.{self.postfix}.pkl"):
            p.unlink()

    def transform(self, artifact: Artifact) -> Tuple:
        pass

    def run(self, artifacts: Dict[str, Artifact]) -> Dict[str, Artifact]:
        """Основная логика трансформации."""
        return self._run_stage(artifacts)


def _process_worker_bridge(stage_instance: Stage, shared_artifacts: dict) -> str:
    """
    Глобальная функция-мостик (на уровне модуля).
    Принимает изолированную копию стадии и запускает её метод run.
    Возвращает имя стадии для логов родительского процесса.
    """

    stage_instance.run(shared_artifacts)
    return stage_instance.name


class ParallelStages(Stage):
    """Компоновщик для параллельного запуска стадий LOAD в изолированных ПРОЦЕССАХ."""

    @property
    def artifact_cls(self) -> Type[Artifact]:
        return Artifact  # Заглушка, так как стадия ничего не порождает

    @property
    def postfix(self) -> str:
        return "parallel_load"

    def __init__(self, context: RunTimeContext, *stage_classes: Type[Stage]) -> None:
        super().__init__(context)
        # Создаем экземпляры стадий (например, LoadDBStage и LoadS3Stage)
        self._stages: List[Stage] = [cls(context) for cls in stage_classes]

    @property
    def name(self) -> str:
        return "_and_".join(stage.name for stage in self._stages)

    def run(self, artifacts: Dict[str, Artifact]) -> Dict[str, Artifact]:
        """Запускает стадии параллельно. Ничего не меняет в словаре артефактов."""
        workers = len(self._stages)
        if workers == 0:
            return artifacts

        # Запускаем пул процессов
        with ProcessPoolExecutor(max_workers=workers) as executor:
            # Отправляем каждую стадию на выполнение в свой процесс
            future_to_stage = {
                executor.submit(_process_worker_bridge, stage, artifacts): stage
                for stage in self._stages
            }

            for future in as_completed(future_to_stage):
                stage = future_to_stage[future]
                try:
                    # Если метод run внутри процесса упал,
                    # future.result() выбросит это исключение прямо здесь
                    stage_name = future.result()
                    logger.info(f"[Успех] Параллельный процесс '{stage_name}' успешно завершен.")
                except Exception as exc:
                    logger.critical(f"[Критическая ошибка] Стадия '{stage.name}' в параллельном процессе упала: {exc}")
                    # Прерываем весь пайплайн, чтобы не продолжать работу при падении LOAD
                    raise exc

        # Возвращаем исходный словарь артефактов без изменений (так как это финальный этап)
        return artifacts
