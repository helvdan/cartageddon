import logging
import os
import sys
import time
from typing import Dict, Set, List, Type

from artifacts import Artifact
from cartageddon.hooks.base import BaseHook, MeasureRunTime, CleanArtifacts, CheckArtifactOverwrite
from common import RunTimeContext
from schema import OC_TABLES
from stages import (
    ExtractTableStage,
    NormalizeValuesStage,
    DeduplicateStage,
    CheckIntegrityStage,
    JoinTablesStage,
    LoadStage,
    S3ImageUploadStage,
)
from stages.base import Stage, ParallelStages

logger = logging.getLogger("PIPELINE")


class Pipeline:
    """Оркестратор, управляет стадиями и хуками"""

    # Стадии спроектированы и оптимизированы под запуск в этом порядке,
    # но могут быть пропущены при определенных условиях
    STAGES_ORDER = (
        ExtractTableStage,
        NormalizeValuesStage,
        DeduplicateStage,
        CheckIntegrityStage,
        JoinTablesStage,
        (
            LoadStage,
            S3ImageUploadStage
        )
    )

    def __init__(self, context: RunTimeContext, run_default_hooks: bool = True) -> None:
        self._context = context
        self.stages = []
        self._hooks = {}

        if not self.STAGES_ORDER[0].is_mandatory:
            raise AssertionError("Первая стадия должна быть обязательна!")

        for stage_cls in self.STAGES_ORDER:
            if isinstance(stage_cls, tuple):
                stage_obj = ParallelStages(context, *stage_cls)
            else:
                stage_obj = stage_cls(context)

            self.stages.append(stage_obj)
            if run_default_hooks:
                self._hooks[stage_obj.name] = [
                    MeasureRunTime(), CheckArtifactOverwrite(), CleanArtifacts()
                ]
            else:
                self._hooks[stage_obj.name] = []

    def add_hook(self, hook: BaseHook, stage_cls: Type[Stage]) -> None:
        self._hooks[stage_cls.name].append(hook)

    def _run_before_hooks(self, stage: Stage, artifacts: List[Artifact]) -> None:
        for hook in self._hooks[stage.name]:
            hook.run_before(stage, artifacts)

    def _run_after_hooks(self, stage: Stage, artifacts: List[Artifact], exc: Exception = None) -> None:
        hooks = reversed(self._hooks[stage.name])
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

    def _create_tmp_dir(self):
        os.makedirs(self._context.work_dir, exist_ok=True)

    def execute(self, oc_table_names: set = None, active_stage_names: set = None) -> None:
        """

        :param oc_table_names:
        :param active_stage_names: Список стадий, которые будут запущены
        :return:
        """
        self._create_tmp_dir()
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
