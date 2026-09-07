from .extract.extract import ExtractTableStage
from .normalize.normalize_values import NormalizeValuesStage
from .join.join_tables import JoinTablesStage
from .integrity.check_integrity import CheckIntegrityStage
from .deduplicate.deduplicate import DeduplicateStage
from .load.load import LoadStage
from .s3_upload.s3_upload import S3ImageUploadStage

# Экспортируем классы для внешнего использования
__all__ = [
    "ExtractTableStage",
    "NormalizeValuesStage",
    "DeduplicateStage",
    "JoinTablesStage",
    "CheckIntegrityStage",
    "LoadStage",
    "S3ImageUploadStage",
]
