"""cn-clinical-guidelines-fetch — 中国权威医学指南抓取与 cross-check。"""

from .fetcher import (
    cross_check_treatment_recommendations,
    fetch_chinese_guidelines,
)

__all__ = [
    "fetch_chinese_guidelines",
    "cross_check_treatment_recommendations",
]
