import logging
from typing import Dict, List

import psycopg

from artifacts import ParquetArtifact
from common import PipelineContext
from schema import get_pg_table_name, get_pg_columns, SCHEMAS
from stages.base import Stage


class LoadStage(Stage):
    artifact_cls = ParquetArtifact
    postfix = "loaded"
    name = "LOAD"
    logger = logging.getLogger(name)

    def __init__(self, context: PipelineContext):
        self.context = context
        # Формируем строку подключения (psycopg3 принимает как URI, так и keyword-строку)
        self.conn_info = (
            f"user={self.context.pg_user} password={self.context.pg_password} "
            f"host={self.context.pg_host} port={self.context.pg_port} dbname={self.context.pg_database}"
        )
        super().__init__(context)

    def _get_joined_tables(self, artifact: ParquetArtifact) -> List:
        from stages import JoinTablesStage

        parts = artifact.path.name.split('.')
        return parts[1:parts.index(JoinTablesStage.postfix)] if JoinTablesStage.postfix in parts else []

    def run(self, artifacts: Dict[str, ParquetArtifact]) -> None:
        with psycopg.connect(self.conn_info) as conn:

            for oc_table_name in SCHEMAS.keys():
                if oc_table_name not in artifacts:
                    # Некоторые таблицы могут быть выброшены на предыдущих стадиях, например oc_product_description
                    continue

                artifact = artifacts[oc_table_name]
                joined_tables = self._get_joined_tables(artifact)
                pg_table_name = get_pg_table_name(oc_table_name)
                pg_cols = get_pg_columns(oc_table_name, *joined_tables)

                self.logger.info(f"Начинается загрузка таблицы: {pg_table_name}")
                chunk_counter = 0

                pg_columns_str = ", ".join(pg_cols)
                copy_query = f"COPY {pg_table_name} ({pg_columns_str}) FROM STDIN WITH (FORMAT CSV, NULL '')"

                for binary_buffer in artifact.get_data_chunks(chunk_size=self.context.chunk_size):
                    try:
                        # Открываем курсор для конкретной операции COPY
                        with conn.cursor() as cur:
                            # Используем BINARY режим для максимальной скорости (без парсинга строк)
                            with cur.copy(copy_query) as copy:
                                copy.write(binary_buffer.read())

                        chunk_counter += 1
                    except Exception as e:
                        self.logger.error(f"Ошибка на чанке #{chunk_counter} для таблицы {pg_table_name}: {e}")
                        conn.rollback()  # Откатываем транзакцию этой таблицы при сбое
                        raise e

                conn.commit()


if __name__ == '__main__':
    from pipeline import PipelineContext
    from pathlib import Path

    context = PipelineContext(
        work_dir="/tmp",
        chunk_size=5000,
        pg_user="django_user",
        pg_password="django_password",
        pg_host="postgres",
        pg_port=5432,
        pg_database="django_project_db",
    )
    extract_stage = LoadStage(context)
    extract_stage.run(
        {
            # 'oc_product': ParquetArtifact(Path("/tmp/oc_product.oc_product_description.joined.parquet")),

            # Стандартные нормализованные таблицы и справочники
            'oc_review': ParquetArtifact(Path("/tmp/oc_review.checked.parquet")),
            # 'oc_manufacturer': ParquetArtifact(Path("/tmp/oc_manufacturer.normalized.parquet")),
            # 'oc_stock_status': ParquetArtifact(Path("/tmp/oc_stock_status.normalized.parquet")),
            # 'oc_tax_class': ParquetArtifact(Path("/tmp/oc_tax_class.normalized.parquet")),
            # 'oc_length_class': ParquetArtifact(Path("/tmp/oc_length_class.normalized.parquet")),
            # 'oc_weight_class': ParquetArtifact(Path("/tmp/oc_weight_class.normalized.parquet")),
        }
    )
