from dataclasses import dataclass
from typing import Dict, List, Literal

DedupStrategy = Literal["first", "last", "any", "none"]


@dataclass(frozen=True)
class DedupRule:
    subset: List[str]
    comment: str
    keep: DedupStrategy = "first"


DEDUP_RULES: Dict[str, DedupRule] = {
    "oc_review": DedupRule(
        subset=["text"],
        comment="Убираем дубли отзывов по тексту",
    ),
}
