import logging
import time
from abc import ABC
from typing import List, Any

from artifacts import Artifact
from common import RunTimeContext

logger = logging.getLogger("HOOK")


class BaseHook(ABC):
    run_anyway: bool = False

    def run_before(self, stage: Any, artifacts: List[Artifact]) -> None:
        """Запускается ДО стадии. Принимает только исходные артефакты."""
        pass

    def run_after(self, stage: Any, artifacts: List[Artifact]) -> None:
        """Запускается ДО стадии. Принимает только исходные артефакты."""
        pass


class BasePipelineHook(ABC):

    def run_before(self, ctx: RunTimeContext) -> None:
        pass

    def run_after(self, ctx: RunTimeContext) -> None:
        pass


# default hooks
class MeasureRunTime(BaseHook):

    def __init__(self):
        self.start_time = None

    def run_before(self, stage, artifacts):
        self.start_time = time.perf_counter()

    def run_after(self, stage, artifacts):
        finish_time = time.perf_counter()
        stage_duration = finish_time - self.start_time
        logger.debug(f"Время выполнения стадии '{stage.name}': {stage_duration:.2f} сек.")


class CleanArtifacts(BaseHook):

    def __init__(self):
        self.start_artifacts = None

    def run_before(self, stage, artifacts):
        self.start_artifacts = artifacts

    def run_after(self, stage, artifacts):
        if not artifacts:
            artifacts_to_delete = self.start_artifacts.keys()
        else:
            k_diff = self.start_artifacts.keys() - artifacts.keys()
            artifacts_to_delete = [k for k in artifacts if self.start_artifacts.get(k) and self.start_artifacts[k] != artifacts[k]]
            artifacts_to_delete.extend(k_diff)

        for artifact_key in artifacts_to_delete:
            artifact = self.start_artifacts[artifact_key]
            if artifact is not None:
                artifact.delete()


class CheckArtifactOverwrite(BaseHook):

    def run(self, stage, artifacts):
        pass
