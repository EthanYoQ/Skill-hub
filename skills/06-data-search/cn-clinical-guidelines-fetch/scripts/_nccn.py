"""NCCN 中文版 fetcher（占位 stub）。

P2 task：抓取 NCCN 中文版指南。当前只返回 None，让流水线降级到 CSCO。
"""

from __future__ import annotations

from pathlib import Path
from typing import Any


def fetch_nccn_zh(
    disease: str,
    year_max: int | None = None,
    cache_dir: Path | None = None,
    sources_dir: Path | None = None,
) -> dict[str, Any] | None:
    """NCCN 中文版抓取。当前为 stub，返回 None。

    sources_dir 参数预留兼容（A1' v2），P2 实现时与 _csco._archive_raw_text 对齐。
    """
    # TODO P2: 实现 NCCN 中文版抓取（公开 HTML）+ 调 _archive_raw_text
    return None
