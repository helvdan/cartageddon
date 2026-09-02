import logging
import sys
import time
from contextlib import contextmanager
from typing import Dict, Set, List

from artifacts import Artifact
from common import PipelineContext
from stages.base import Stage
from schema import OC_TABLES

logger = logging.getLogger("PIPELINE")


@contextmanager
def measure_time(stage_name: str):
    start_time = time.perf_counter()
    yield
    elapsed_time = time.perf_counter() - start_time
    logger.info(f"Время выполнения стадии '{stage_name}': {elapsed_time:.2f} сек.")


class Pipeline:
    """Оркестратор, управляет стадиями"""

    def __init__(self, context: PipelineContext) -> None:
        from stages import (
            ExtractTableStage,
            NormalizeValuesStage,
            DeduplicateStage,
            CheckIntegrityStage,
            JoinTablesStage,
            LoadStage
        )

        self.STAGES = (
            ExtractTableStage(context),
            NormalizeValuesStage(context),
            DeduplicateStage(context),
            CheckIntegrityStage(context),
            JoinTablesStage(context),
            LoadStage(context)
        )
        if not self.STAGES[0].is_mandatory:
            raise AssertionError("Первая стадия должна быть обязательна!")

    def _get_previous_stages(self, idx) -> List[Stage]:
        stages = []
        for stage in self.STAGES[idx-1::-1]:
            stages.append(stage)
            if stage.is_mandatory:
                break

        return stages

    def _get_first_stage_index(self, active_stage_names: set) -> int | None:
        for stage_idx, stage in enumerate(self.STAGES):
            if stage.name in active_stage_names:
                return stage_idx

    def _get_stage_artifacts(self, stage: Stage, oc_table_names) -> Dict[str, Artifact]:
        artifacts = {}
        tables_to_delete = set()
        for oc_table_name in oc_table_names:
            artifact = stage._create_artifact(oc_table_name)
            if artifact.exists:
                artifacts[oc_table_name] = artifact
                tables_to_delete.add(oc_table_name)

        oc_table_names -= tables_to_delete
        return artifacts

    def _restore_artifacts(self, first_stage_index: int, oc_table_names: Set[str]) -> Dict[str, Artifact]:
        table_names = oc_table_names.copy()
        artifacts = {}
        prev_stages = self._get_previous_stages(first_stage_index)
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

    def _check_artifacts(self, artifacts: Dict[str, Artifact], table_names: Set[str], prev_stages: List[Stage]) -> None:
        mandatory_stage = prev_stages[0]
        missing = table_names - artifacts.keys()
        for oc_table_name in missing:
            missing_artifact_path = mandatory_stage._get_path(oc_table_name)
            logger.error(f"Не найден артефакт {missing_artifact_path}")

        if missing:
            raise RuntimeError(f"Не найдены артефакты для таблиц {', '.join(missing)}")

    def execute(self, oc_table_names: set = None, active_stage_names: set = None, clean_run: bool = False) -> None:
        """

        :param oc_table_names:
        :param active_stage_names: Список стадий, которые будут запущены
        :param clean_run: Удалять артефакты, которые не понадобятся на последующих стадиях
        :return:
        """

        if not oc_table_names:
            oc_table_names = OC_TABLES.copy()

        if active_stage_names:
            first_stage_index = self._get_first_stage_index(active_stage_names)

            if first_stage_index is None:
                logger.info("Стадия не найдена, pipline не будет запущен")
                return

            if first_stage_index > 0:
                artifacts = self._restore_artifacts(first_stage_index, oc_table_names)
            else:
                artifacts = dict.fromkeys(oc_table_names)
        else:
            artifacts = dict.fromkeys(oc_table_names)

        total_stages = len(self.STAGES)
        used_stages = []

        pipeline_start = time.perf_counter()
        for stage_num, stage in enumerate(self.STAGES, 1):
            if active_stage_names and stage.name not in active_stage_names:
                logger.info(f"Стадия '{stage.name}' пропущена.")
                continue

            logger.info(f"==> Запуск стадии [{stage_num}/{total_stages}]: '{stage.name}'")
            try:
                # if used_stages:
                #     prev_stages = self._get_previous_stages(stage_num - 1)
                #     self._check_artifacts(artifacts, oc_table_names, prev_stages)

                # Передаем данные из предыдущей стадии в следующую
                with measure_time(stage.name):
                    new_artifacts = stage.run(artifacts)

                if clean_run:
                    self._clean_artifacts(new_artifacts, artifacts)

                artifacts = new_artifacts

                used_stages.append(stage)
                logger.info(f"Стадия '{stage.name}' успешно завершена.")
            except Exception as e:
                logger.error(
                    f"!!! Пайплайн прерван! Ошибка на стадии '{stage.name}': {e}",
                    exc_info=True,
                )
                sys.exit(1)

        total_elapsed = time.perf_counter() - pipeline_start
        logger.info(f"=== Пайплайн завершен. Общее время: {total_elapsed:.2f} сек. ===")

    def _clean_artifacts(self, new_artifacts, artifacts):
        if not new_artifacts:
            artifacts_to_delete = artifacts.keys()
        else:
            k_diff = artifacts.keys() - new_artifacts.keys()
            artifacts_to_delete = [k for k in artifacts if new_artifacts.get(k) and artifacts[k] != new_artifacts[k]]
            artifacts_to_delete.extend(k_diff)

        for artifact_key in artifacts_to_delete:
            artifact = artifacts[artifact_key]
            if artifact is not None:
                artifact.delete()
                logger.info(f"Артефакт удалён: {artifact.path}")


if __name__ == '__main__':
    ctx = PipelineContext(
        work_dir="/tmp",
        single_language=True,

        # mysql
        chunk_size=5000,
        oc_user="root",
        oc_password="root_password",
        oc_host="mysql_replica",
        oc_port=3306,
        oc_database="temp_import_db",

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
            "extract_tables",
            "normalize_values",
            "deduplicate",
            "check_integrity",
            "join_tables",
            "load"
        },
        clean_run=True
    )
