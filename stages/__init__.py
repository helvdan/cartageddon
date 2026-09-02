from .extract.extract import ExtractTableStage
from .normalize.normalize_values import NormalizeValuesStage
from .join.join_tables import JoinTablesStage
from .integrity.check_integrity import CheckIntegrityStage
from .deduplicate.deduplicate import DeduplicateStage
from .load.load import LoadStage

# Экспортируем классы для внешнего использования
__all__ = [
    "ExtractTableStage",
    "NormalizeValuesStage",
    "DeduplicateStage",
    "JoinTablesStage",
    "CheckIntegrityStage",
    "LoadStage",
]
