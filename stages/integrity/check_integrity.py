import logging
from pathlib import Path
from typing import Dict

from artifacts import ParquetArtifact
from schema import get_foreign_keys
from stages.base import Stage


class CheckIntegrityStage(Stage):
    artifact_cls = ParquetArtifact
    is_mandatory: bool = False
    name = "INTEGRITY"
    postfix = "checked"
    logger = logging.getLogger(name)

    def _get_path_deleted(self, oc_table_name) -> Path:
        return Path(f"{self.global_context.work_dir}/{oc_table_name}.{self.postfix}.deleted.{self.artifact_cls.extension}")

    def run(self, artifacts: Dict[str, ParquetArtifact]) -> Dict[str, ParquetArtifact]:
        result_artifacts = artifacts.copy()

        for table_name, artifact in artifacts.items():
            # 1. Запрашиваем у артефакта список его внешних ключей по метаданным
            foreign_keys = get_foreign_keys(artifact.oc_table_name)
            if not foreign_keys:
                continue

            for fk_column, target_table, on_delete_action in foreign_keys:
                target_artifact = artifacts.get(target_table)
                if not target_artifact:
                    continue

                # 2. Просим артефакт найти битые строки встроенным методом
                broken_rows = artifact.get_broken_fks(fk_column, target_artifact)

                if not broken_rows.is_empty():
                    self.logger.debug(f"❌ Найдено {len(broken_rows)} битых связей в '{table_name}' по ключу '{fk_column}'")

                    # 3. Сохраняем битые строки в бэкап (вызов вспомогательного пути)
                    deleted_path = self._get_path_deleted(artifact.oc_table_name)
                    # Создаем такой же класс артефакта, какой передан в стадию (ParquetArtifact)
                    deleted_artifact = self.artifact_cls(path=deleted_path)
                    deleted_artifact.save(broken_rows)

                    # 4. Просим применить каскадное правило очистки
                    clean_lazy_data = artifact.apply_cascading_cleanup(fk_column, broken_rows, on_delete_action)

                    # 5. Создаем целевой очищенный артефакт и сохраняем данные
                    changed_artifact = self._create_artifact(artifact.oc_table_name)
                    changed_artifact.save(clean_lazy_data, None)

                    # Обновляем результат в конвейере
                    result_artifacts[table_name] = changed_artifact

        return result_artifacts


if __name__ == '__main__':
    from common import RunTimeContext

    ctx = RunTimeContext(
        work_dir="/tmp"
    )

    integrity_stage = CheckIntegrityStage(ctx)
    d = integrity_stage.run(
        {
            'oc_review': ParquetArtifact(Path("/tmp/oc_review.normalized.parquet")),
            'oc_product': ParquetArtifact(Path("/tmp/oc_product.normalized.parquet"))
        }
    )
    print(d)
