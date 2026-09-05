import logging
import sys
import time
from typing import Dict, Set, List

from artifacts import Artifact
from cartageddon.hooks.base import BaseHook, MeasureRunTime, CleanArtifacts, CheckArtifactOverwrite
from common import RunTimeContext, AppendOnlyDict
from schema import OC_TABLES
from stages import (
    ExtractTableStage,
    NormalizeValuesStage,
    DeduplicateStage,
    CheckIntegrityStage,
    JoinTablesStage,
    LoadStage
)
from stages.base import Stage

logger = logging.getLogger("PIPELINE")


class Pipeline:
    """Оркестратор, управляет стадиями"""

    # Стадии спроектированы и оптимизированы под запуск в этом порядке,
    # но могут быть пропущены при определенных условиях
    STAGES_ORDER = (
        ExtractTableStage,
        NormalizeValuesStage,
        DeduplicateStage,
        CheckIntegrityStage,
        JoinTablesStage,
        LoadStage
    )

    def __init__(self, context: RunTimeContext, run_default_hooks: bool = True) -> None:
        self.stages = [stage_cls(context) for stage_cls in self.STAGES_ORDER]

        if not self.STAGES_ORDER[0].is_mandatory:
            raise AssertionError("Первая стадия должна быть обязательна!")

        self._hooks: List[BaseHook] = [
            MeasureRunTime(), CheckArtifactOverwrite(), CleanArtifacts()
        ] if run_default_hooks else []

    def add_hook(self, hook: BaseHook) -> None:
        self._hooks.append(hook)

    def _run_before_hooks(self, stage: Stage, artifacts: List[Artifact]) -> None:
        for hook in self._hooks:
            hook.run_before(stage, artifacts)

    def _run_after_hooks(self, stage: Stage, artifacts: List[Artifact], exc: Exception = None) -> None:
        hooks = reversed(self._hooks)
        for hook in hooks:
            try:
                if exc is not None:
                    if hook.run_anyway:
                        hook.run_after(stage, artifacts)
                else:
                    hook.run_after(stage, artifacts)
            except Exception as hook_error:
                logger.error(f"Hook {hook.__class__.__name__} failed: {hook_error}")

    def _get_previous_stages(self, idx) -> List[Stage]:
        stages = []
        for stage in self.stages[idx-1::-1]:
            stages.append(stage)
            if stage.is_mandatory:
                break

        return stages

    def _get_first_stage_index(self, active_stage_names: set) -> int | None:
        for stage_idx, stage_cls in enumerate(self.STAGES_ORDER):
            if stage_cls.name in active_stage_names:
                return stage_idx

    def _get_stage_artifacts(self, stage: Stage, oc_table_names) -> Dict[str, Artifact]:
        logger.debug('restoring artifacts')
        artifacts = {}
        tables_to_delete = set()
        for oc_table_name in oc_table_names:
            artifact = stage.create_artifact(oc_table_name)
            if artifact.exists:
                artifacts[oc_table_name] = artifact
                tables_to_delete.add(oc_table_name)

        oc_table_names -= tables_to_delete
        return artifacts

    def _restore_artifacts(self, first_stage_index: int, oc_table_names: Set[str]) -> Dict[str, Artifact]:
        logger.debug('restoring artifacts')
        table_names = oc_table_names.copy()
        artifacts = {}
        prev_stages = self._get_previous_stages(first_stage_index)
        logger.debug(f'Previous stages: {prev_stages}')
        for prev_stage in prev_stages:
            stage_artifacts = self._get_stage_artifacts(prev_stage, table_names)
            artifacts.update(stage_artifacts)
            if not table_names:
                break

        if table_names:
            for oc_table_name in table_names:
                missing_artifact_path = prev_stage._get_path(oc_table_name)
                logger.error(f"Не найден артефакт {missing_artifact_path}")
            raise RuntimeError(f"Не найдены артефакты для таблиц {', '.join(table_names)}")

        return artifacts

    # def _check_artifacts(self, artifacts: Dict[str, Artifact], table_names: Set[str], prev_stages: List[Stage]) -> None:
    #     mandatory_stage = prev_stages[0]
    #     missing = table_names - artifacts.keys()
    #     for oc_table_name in missing:
    #         missing_artifact_path = mandatory_stage._get_path(oc_table_name)
    #         logger.error(f"Не найден артефакт {missing_artifact_path}")
    #
    #     if missing:
    #         raise RuntimeError(f"Не найдены артефакты для таблиц {', '.join(missing)}")

    def execute(self, oc_table_names: set = None, active_stage_names: set = None) -> None:
        """

        :param oc_table_names:
        :param active_stage_names: Список стадий, которые будут запущены
        :return:
        """
        total_stages = len(self.STAGES_ORDER)

        if not oc_table_names:
            oc_table_names = OC_TABLES.copy()

        if active_stage_names:
            total_stages = len(active_stage_names)
            artifacts = self._get_first_stage_artifacts(oc_table_names, active_stage_names)
        else:
            artifacts = dict.fromkeys(oc_table_names)

        pipeline_start = time.perf_counter()
        for stage_num, stage in enumerate(self.stages, 1):

            if active_stage_names and stage.name not in active_stage_names:
                logger.info(f"Стадия '{stage.name}' пропущена.")
                continue

            logger.info(f"==> Запуск стадии [{stage_num}/{total_stages}]: '{stage.name}'")
            try:
                stage_exception = None
                self._run_before_hooks(stage, artifacts)
                try:
                    artifacts = stage.run(artifacts)
                except Exception as e:
                    stage_exception = e
                    raise e
                finally:
                    self._run_after_hooks(stage, artifacts, exc=stage_exception)

                logger.info(f"Стадия '{stage.name}' успешно завершена.")
            except Exception as e:
                logger.error(
                    f"!!! Пайплайн прерван! Ошибка на стадии '{stage.name}': {e}",
                    exc_info=True,
                )
                sys.exit(1)

        total_elapsed = time.perf_counter() - pipeline_start
        logger.info(f"=== Пайплайн завершен. Общее время: {total_elapsed:.2f} сек. ===")

    def _get_first_stage_artifacts(self, oc_table_names, active_stage_names):
        first_stage_index = self._get_first_stage_index(active_stage_names)
        logger.debug(f"first stage index is {first_stage_index}")

        if first_stage_index is None:
            raise AssertionError("Стадия не найдена, pipline не будет запущен")

        if first_stage_index > 0:
            return self._restore_artifacts(first_stage_index, oc_table_names)

        return dict.fromkeys(oc_table_names)


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.DEBUG, format="%(asctime)s [%(name)s] [%(levelname)s] %(message)s"
    )

    ctx = RunTimeContext(
        stages=AppendOnlyDict(),

        work_dir="/tmp",
        single_language=True,

        # mysql
        chunk_size=5000,
        oc_user="opencart_user",
        oc_password="opencart_password",
        oc_host="localhost",
        oc_port=3307,
        oc_database="opencart_db",

        # postgres
        pg_user="django_user",
        pg_password="django_password",
        pg_host="postgres",
        pg_port=5432,
        pg_database="django_project_db",
    )

    pipeline = Pipeline(ctx)
    pipeline.execute(
        oc_table_names={
            'oc_product',
            'oc_product_description',
            'oc_review',
            'oc_manufacturer',
            'oc_stock_status',
            'oc_tax_class',
            'oc_length_class',
            'oc_weight_class'
        },
        active_stage_names={
            # "EXTRACT",
            "NORMALIZE",
            # "deduplicate",
            # "check_integrity",
            # "join_tables",
            # "load"
        }
    )
