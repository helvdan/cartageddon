import logging
from pathlib import Path
from typing import Dict, List

from artifacts import ParquetArtifact
from common import PipelineContext
from stages.base import Stage


class JoinTablesStage(Stage):
    artifact_cls = ParquetArtifact
    is_mandatory: bool = False
    name = "JOIN"
    postfix = "joined"
    logger = logging.getLogger(name)

    def __init__(self, context: PipelineContext) -> None:
        self.tables_to_join = {}
        if context.single_language:
            self.tables_to_join["oc_product"] = ("oc_product_description",)

        super(JoinTablesStage, self).__init__(context)

    def run(self, artifacts: Dict[str, ParquetArtifact]) -> Dict[str, ParquetArtifact]:
        output: Dict[str, ParquetArtifact] = artifacts.copy()

        if not self.tables_to_join:
            self.logger.info(f"Не переданы флаги для стадии {self.name}, стадия будет пропущена!")
            return output

        for main_table, dependent_tables in self.tables_to_join.items():

            if main_table not in artifacts:
                continue

            main_artifact = artifacts[main_table]
            for dependent_table in dependent_tables:
                if dependent_table not in artifacts:
                    raise KeyError(f"Зависимая таблица {dependent_table} не найдена во входных артефактах.")

                self.logger.info(f"Joining {dependent_table} into {main_table}")
                dependent_artifact = artifacts[dependent_table]
                main_artifact = main_artifact.join(dependent_artifact)

            joined_artifact = self._create_joined_artifact(main_table, dependent_tables)
            joined_artifact.save(main_artifact.data)

            output[main_table] = joined_artifact
            for dependent_table in dependent_tables:
                output.pop(dependent_table, None)

        return output

    def _create_joined_artifact(self, oc_table_name: str, dependent_tables: List[str]) -> ParquetArtifact:
        joined_part = ".".join(dependent_tables)
        filename = f"{oc_table_name}.{joined_part}.{self.postfix}.{self.artifact_cls.extension}"
        path = Path(self.context.work_dir) / filename
        return ParquetArtifact(path=path)


if __name__ == '__main__':
    from artifacts import ParquetArtifact

    ctx = PipelineContext(
        work_dir="/tmp",
        single_language=True
    )
    join_stage = JoinTablesStage(ctx)
    join_stage.run(
        {
            'oc_product': ParquetArtifact(Path("/tmp/oc_product.normalized.parquet")),
            'oc_product_description': ParquetArtifact(Path("/tmp/oc_product_description.normalized.parquet")),
        }
    )
