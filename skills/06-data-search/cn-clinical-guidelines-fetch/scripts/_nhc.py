"""NHC（国家卫健委）诊疗规范 fetcher（占位 stub）。

P2 task：nhc.gov.cn 部分病种诊疗规范（如恶性肿瘤诊疗规范）。
"""

from __future__ import annotations

from pathlib import Path
from typing import Any


def fetch_nhc(
    disease: str,
    year_max: int | None = None,
    cache_dir: Path | None = None,
    sources_dir: Path | None = None,
) -> dict[str, Any] | None:
    """NHC 抓取，stub。sources_dir 参数预留兼容（A1' v2）。"""
    return None
