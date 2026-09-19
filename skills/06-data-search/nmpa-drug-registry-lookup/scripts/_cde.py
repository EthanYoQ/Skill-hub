"""CDE(药品审评中心)数据抓取器。

CDE 提供:
- 临床试验阶段
- 适应症详情
- 审评意见(部分公开)

入口: https://www.cde.org.cn

⚠ 同 _nmpa.py: 默认不联网,留给 fallback dict / cache。
"""
from __future__ import annotations

from typing import Any

CDE_SEARCH_URL = "https://www.cde.org.cn/main/xxgk/listpage/"


def fetch_from_cde(
    name: str,
    timeout: float = 10.0,
    force_online: bool = False,
) -> dict[str, Any] | None:
    """从 CDE 抓取额外字段(适应症 / 临床试验阶段)。

    返回 None 表示未抓到 — 调用方 fallback。
    """
    if not force_online:
        return None

    try:
        import httpx
    except ImportError:
        return None

    try:
        with httpx.Client(timeout=timeout) as client:
            r = client.get(CDE_SEARCH_URL, params={"keyword": name})
            r.raise_for_status()
    except (httpx.HTTPError, OSError):
        return None

    # CDE 实际网站为 SPA,静态 HTML 解析有限
    # 真实实现需要更深入的网站结构分析,此处占位
    return None
