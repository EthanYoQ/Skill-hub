"""NMPA(国家药监局)数据抓取器。

NMPA 网站结构:
- 入口: https://www.nmpa.gov.cn/datasearch/search-result.html
- 表单: searchValue=<药品通用名> + 国产药品/进口药品 tab
- 返回: HTML 列表页 + 每个药品的详情页

策略:
1. 优先用搜索 API(若可用)
2. fallback 到 HTML 抓取 + bs4 解析
3. 网站不可达时返回 None,调用方降级到 _known_drugs_fallback

⚠ 警告: NMPA 网站存在反爬(频次限制 + JS 渲染),
本模块在测试中不主动联网;CI 不允许直连 NMPA。
真实抓取请在调用方显式指定 force_online=True 时启用。
"""
from __future__ import annotations

from typing import Any

# 真实抓取入口(测试中 mock 此函数)
NMPA_SEARCH_URL = "https://www.nmpa.gov.cn/datasearch/search-result.html"
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
)


def fetch_from_nmpa(
    name: str,
    timeout: float = 10.0,
    force_online: bool = False,
) -> dict[str, Any] | None:
    """从 NMPA 抓取药品记录。

    Args:
        name: 药品通用名/商品名
        timeout: HTTP 超时(秒)
        force_online: True 才真正发出 HTTP 请求(默认 False,避免测试和 CI 中误用)

    Returns:
        dict with keys matching DrugRecord, or None if not found / fetch failed
    """
    if not force_online:
        # 默认不走真实网络,留给 fallback dict
        return None

    try:
        import httpx  # local import — 防止环境无 httpx 时整个 skill 也加载失败
        from bs4 import BeautifulSoup
    except ImportError:
        return None

    headers = {"User-Agent": USER_AGENT}
    params = {"searchValue": name}

    try:
        with httpx.Client(timeout=timeout, headers=headers) as client:
            r = client.get(NMPA_SEARCH_URL, params=params)
            r.raise_for_status()
            html = r.text
    except (httpx.HTTPError, OSError):
        return None

    return _parse_nmpa_search_page(html, name)


def _parse_nmpa_search_page(html: str, query_name: str) -> dict[str, Any] | None:
    """解析 NMPA 搜索结果 HTML。

    实际网站会用 JS 异步加载,静态 HTML 解析可能为空。
    返回 None 表示需要 fallback 到 _known_drugs_fallback。

    保留此函数为了未来网站结构稳定后能 plug-in 真正抓取,
    并允许测试 fixture 注入预录制 HTML。
    """
    try:
        from bs4 import BeautifulSoup
    except ImportError:
        return None

    soup = BeautifulSoup(html, "html.parser")

    # NMPA 搜索结果常用结构: 表格 .tableRowList > 每行包含通用名/批准文号/上市日期
    # 实际实现时根据真实页面调整
    rows = soup.select("table tr")
    for row in rows:
        cells = [c.get_text(strip=True) for c in row.find_all("td")]
        if not cells:
            continue
        if any(query_name in c for c in cells):
            # 极简提取:第 1 列假设为通用名,第 2 列批文号,第 3 列上市日期
            return {
                "generic_name_zh": cells[0] if len(cells) > 0 else query_name,
                "nmpa_approval_no": cells[1] if len(cells) > 1 else "",
                "first_approval_date_cn": cells[2] if len(cells) > 2 else "",
                "raw_html_source": "nmpa_search_page",
            }
    return None
