"""R3a Phase-2-Quality-Fix · T9: 把 composer 输出 list[dict] 落盘成 page_<slug>.html.

返回 list[tuple[str, Path]] 与 build_standalone_html.py:124 签名兼容
(architect 修订 1, 盲点 E - R3a→R3b 数据流类型不兼容修复).

数据流:
    composer.ComposedReport.sub_pages: list[dict {slug, html}]   # 内存字符串
        ↓ persist_sub_pages
    list[tuple[str, Path]]                                         # 落盘后 (slug, file_path)
        ↓ build_standalone_html.py:124
    最终 standalone HTML 合并主页 + 子页
"""
from __future__ import annotations

from pathlib import Path
from typing import List, Tuple


_HTML_WRAPPER = (
    '<!DOCTYPE html><html><head><meta charset="utf-8">'
    '<title>{title}</title></head>'
    "<body>{body}</body></html>"
)


def persist_sub_pages(
    sub_pages: List[dict],
    output_dir: Path,
) -> List[Tuple[str, Path]]:
    """落盘 list[dict {slug, html}] 到 output_dir/page_<slug>.html.

    Args:
        sub_pages: composer ComposedReport.sub_pages 输出 list[dict].
            每 dict 必含 ``slug`` (str) 和 ``html`` (str).
        output_dir: 落盘目标目录 (typically builder 的 ``project_root / 'output'``).

    Returns:
        list[tuple[str, Path]] 与 ``build_standalone_html(sub_pages=...)`` 签名兼容.
    """
    if not sub_pages:
        return []

    output_dir.mkdir(parents=True, exist_ok=True)

    result: List[Tuple[str, Path]] = []
    for entry in sub_pages:
        slug = entry["slug"]
        html_body = entry["html"]
        wrapped = _HTML_WRAPPER.format(title=slug, body=html_body)
        out_path = output_dir / f"page_{slug}.html"
        out_path.write_text(wrapped, encoding="utf-8")
        result.append((slug, out_path))

    return result
