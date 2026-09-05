import logging
from typing import Dict, Generator

import pymysql
from pymysql.cursors import SSCursor

from artifacts import PickleArtifact
from schema import SCHEMAS
from stages.base import Stage


class ExtractTableStage(Stage):
    artifact_cls = PickleArtifact
    postfix = "extracted"
    name = "EXTRACT"
    logger = logging.getLogger(name)

    def _db_chunk_generator(self, cursor, sql: str) -> Generator[list, None, None]:
        """Вспомогательный генератор, который тянет данные из SSCursor пачками"""
        cursor.execute(sql)
        while True:
            rows = cursor.fetchmany(self.global_context.chunk_size)
            if not rows:
                break
            # Возвращаем чанк (list из tuple строк)
            yield rows

    def _extract_tables_data(self, artifacts: Dict[str, None], conn) -> Dict[str, PickleArtifact]:
        new_artifacts = {}

        oc_table_map = {
            oc_table_name: SCHEMAS[oc_table_name] for oc_table_name in artifacts.keys()
        }

        for oc_table_name, schema in oc_table_map.items():
            columns = schema.names
            oc_columns = ", ".join(columns)
            sql = f"SELECT {oc_columns} FROM {oc_table_name}"
            self.logger.debug(f"SQL: {sql}")

            artifact = self.create_artifact(oc_table_name)
            with conn.cursor(SSCursor) as ss_cursor:
                chunks = self._db_chunk_generator(ss_cursor, sql)

                artifact.save(chunks, None)

            new_artifacts[oc_table_name] = artifact

        return new_artifacts

    def run(self, artifacts: Dict[str, None]) -> Dict[str, PickleArtifact]:
        db_config = self.global_context.get_oc_db_config()
        self.logger.debug(f"connecting to {db_config['host']}:{db_config['port']}")
        with pymysql.connect(**db_config) as conn:
            with conn.cursor() as cursor:
                cursor.execute("SET SESSION TRANSACTION READ ONLY;")

            return self._extract_tables_data(artifacts, conn)


if __name__ == '__main__':
    from pipeline import RunTimeContext
    from artifacts import PickleArtifact

    context = RunTimeContext(
        work_dir="/tmp",
        chunk_size=5000,
        oc_user="root",
        oc_password="root_password",
        oc_host="mysql_replica",
        oc_port=3306,
        oc_database="temp_import_db",
    )
    extract_stage = ExtractTableStage(context)
    artifacts = extract_stage.run(
        {
            'oc_product': None,
            'oc_product_description': None,
            'oc_review': None,

            'oc_manufacturer': None,
            'oc_stock_status': None,
            'oc_tax_class': None,
            'oc_length_class': None,
            'oc_weight_class': None
        }
    )
    print(artifacts)
