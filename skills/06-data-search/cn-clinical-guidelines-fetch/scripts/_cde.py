"""CDE（药品审评中心）fetcher（占位 stub）。

P2 task：cde.org.cn 临床试验审评信息。
"""

from __future__ import annotations

from pathlib import Path
from typing import Any


def fetch_cde(
    disease: str,
    year_max: int | None = None,
    cache_dir: Path | None = None,
    sources_dir: Path | None = None,
) -> dict[str, Any] | None:
    """CDE 抓取，stub。sources_dir 参数预留兼容（A1' v2）。"""
    return None
