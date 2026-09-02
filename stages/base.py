from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Any, Tuple, Type

from artifacts import Artifact


class Stage(ABC):
    """Абстрактный класс для стадии ETL-трансформации."""
    is_mandatory: bool = True

    @property
    @abstractmethod
    def artifact_cls(self) -> Type[Artifact]:
        """Каждый наследник обязан вернуть конкретный класс артефакта."""
        pass

    def __init__(self, context: 'PipelineContext') -> None:
        self.context = context

    def _create_artifact(self, oc_table_name: str) -> Artifact:
        path = self._get_path(oc_table_name)
        return self.artifact_cls(path=path)

    @property
    @abstractmethod
    def postfix(self) -> str:
        """Постфикс для файла"""
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """Имя стадии для сопоставления с аргументами CLI."""
        pass

    def clean_previous_data(self) -> Any:
        """Очистить данные предыдущего запуска."""
        d = Path(self.context.work_dir)
        for p in d.glob(f"*.{self.postfix}.pkl"):
            p.unlink()

    def _get_path(self, oc_table_name) -> Path:
        return Path(f"{self.context.work_dir}/{oc_table_name}.{self.postfix}.{self.artifact_cls.extension}")

    def transform(self, artifact: Artifact) -> Tuple:
        pass

    def run(self, artifacts: Dict[str, Artifact]) -> Dict[str, Artifact]:
        """Основная логика трансформации."""
        return self._run_stage(artifacts)
