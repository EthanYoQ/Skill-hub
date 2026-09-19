"""DrugBank 数据抓取(免费学术用法)。

DrugBank 提供:
- 英文通用名(INN)
- ATC code
- 机制 / 靶点
- 商品名(全球)

注意:
- DrugBank 完整 API 需付费,免费层只支持 search + drug page scrape
- 学术免费用法允许个人查询,但不允许批量爬取
- 本 skill 默认不联网,所有数据走 fallback dict
"""
from __future__ import annotations

from typing import Any

DRUGBANK_SEARCH_URL = "https://go.drugbank.com/drugs/search"


def fetch_from_drugbank(
    name: str,
    timeout: float = 10.0,
    force_online: bool = False,
) -> dict[str, Any] | None:
    """从 DrugBank 抓取英文 / ATC / 靶点。

    返回 None 表示未抓到。
    """
    if not force_online:
        return None

    try:
        import httpx
    except ImportError:
        return None

    try:
        with httpx.Client(timeout=timeout) as client:
            r = client.get(DRUGBANK_SEARCH_URL, params={"query": name})
            r.raise_for_status()
    except (httpx.HTTPError, OSError):
        return None

    # 实际解析略,占位
    return None
