"""nmpa-drug-registry-lookup · 中国药品权威 Registry。

公开 API:
- DrugRecord: frozen dataclass
- UnverifiedDrugError: lookup 失败时调用方应 raise
- lookup_drug(name) -> DrugRecord | None
- lookup_drugs_batch(names) -> dict
- cross_check_drug_mentions(text) -> dict
"""
from __future__ import annotations

from .registry import (
    DrugRecord,
    UnverifiedDrugError,
    cross_check_drug_mentions,
    lookup_drug,
    lookup_drugs_batch,
)

__all__ = [
    "DrugRecord",
    "UnverifiedDrugError",
    "cross_check_drug_mentions",
    "lookup_drug",
    "lookup_drugs_batch",
]
