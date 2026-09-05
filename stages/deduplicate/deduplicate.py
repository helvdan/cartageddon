import logging
from pathlib import Path
from typing import Dict

from artifacts import ParquetArtifact
from stages.base import Stage
from stages.deduplicate.rules import DEDUP_RULES


class DeduplicateStage(Stage):
    artifact_cls = ParquetArtifact
    is_mandatory: bool = False
    name = "DEDUP"
    postfix = "deduplicated"
    logger = logging.getLogger(name)

    def run(self, artifacts: Dict[str, ParquetArtifact]) -> Dict[str, ParquetArtifact]:
        output: Dict[str, ParquetArtifact] = artifacts.copy()

        for oc_table_name, rule in DEDUP_RULES.items():
            if oc_table_name not in artifacts:
                continue

            self.logger.info(f"Deduplicating table '{oc_table_name}' with rules: {rule.comment}")

            artifact = artifacts[oc_table_name]
            cleaned_artifact = artifact.deduplicate(rule.subset, rule.keep)

            deduped_artifact = self._create_artifact(oc_table_name)
            deduped_artifact.save(cleaned_artifact.data)

            output[oc_table_name] = deduped_artifact

        return output


if __name__ == '__main__':
    from common import RunTimeContext

    ctx = RunTimeContext(
        work_dir="/tmp",
    )
    dedup_stage = DeduplicateStage(ctx)
    dedup_stage.run(
        {
            'oc_review': ParquetArtifact(Path("/tmp/oc_review.normalized.parquet")),
        }
    )
