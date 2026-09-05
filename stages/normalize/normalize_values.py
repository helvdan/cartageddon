import logging
from pathlib import Path
from typing import Tuple, Dict

from artifacts import PickleArtifact, ParquetArtifact
from schema import SCHEMAS
from stages.base import Stage
from stages.normalize.rules import get_callback


class NormalizeValuesStage(Stage):
    artifact_cls = ParquetArtifact
    name = "NORMALIZE"
    postfix = "normalized"
    logger = logging.getLogger(name)

    def transform(self, artifact: PickleArtifact) -> Tuple:
        transformed_data = []

        for row in artifact.data:
            transformed_row = []
            for i, cell in enumerate(row):
                callback = get_callback(artifact.oc_table_name, i)
                cell = callback(cell) if callback else cell
                transformed_row.append(cell)
            transformed_data.append(tuple(transformed_row))
        return tuple(transformed_data)

    def run(self, artifacts: Dict[str, PickleArtifact]) -> Dict[str, ParquetArtifact]:
        new_artifacts = {}
        for oc_table_name, artifact in artifacts.items():
            self.logger.debug(f"Запуск трансформаций для {oc_table_name}")
            table_data = self.transform(artifact)
            columns_data = [list(col) for col in zip(*table_data)]

            new_artifact = self._create_artifact(oc_table_name)
            new_artifact.save(columns_data, schema=SCHEMAS[oc_table_name])
            new_artifacts[oc_table_name] = new_artifact
        return new_artifacts


if __name__ == '__main__':
    from pipeline import RunTimeContext
    from artifacts import PickleArtifact, ParquetArtifact

    ctx = RunTimeContext(
        work_dir="/tmp"
    )

    norm_stage = NormalizeValuesStage(ctx)
    o = norm_stage.run(
        {
            "oc_product": PickleArtifact(Path("/tmp/oc_product.extracted.pkl")),
            "oc_product_description": PickleArtifact(Path("/tmp/oc_product_description.extracted.pkl")),
            "oc_review": PickleArtifact(Path("/tmp/oc_review.extracted.pkl")),
            "oc_manufacturer": PickleArtifact(Path("/tmp/oc_manufacturer.extracted.pkl")),
            "oc_stock_status": PickleArtifact(Path("/tmp/oc_stock_status.extracted.pkl")),
            "oc_tax_class": PickleArtifact(Path("/tmp/oc_tax_class.extracted.pkl")),
            "oc_length_class": PickleArtifact(Path("/tmp/oc_length_class.extracted.pkl")),
            "oc_weight_class": PickleArtifact(Path("/tmp/oc_weight_class.extracted.pkl")),
        }
    )
    print(o)
