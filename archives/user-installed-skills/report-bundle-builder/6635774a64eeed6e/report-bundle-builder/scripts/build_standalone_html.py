# -*- coding: utf-8 -*-
"""通用化报告 standalone HTML 合并脚本(领域无关).

功能:
- 主页 + N 子页合并到单文件 HTML
- 全部 PNG base64 内嵌
- 跨文件 page_*.html 链接改写为 #page-* 锚点
- 子页 H1 加 page-{slug}- 前缀
- 注入悬浮 TOC + standalone banner

来源:从 output/build_standalone.py 通用化而来,移除疾病硬编码常量。
"""
from __future__ import annotations
import base64
import re
from dataclasses import dataclass
from pathlib import Path


MIN_BUNDLE_BYTES = 1 * 1024 * 1024  # 1 MB · build_standalone_html size_ok 阈值


@dataclass(frozen=True)
class SubPage:
    slug: str
    title: str
    body_html: str
    head_style: str


def _extract_subpage(path: Path, slug: str) -> SubPage:
    text = path.read_text(encoding="utf-8")
    style_match = re.search(r"<style>(.*?)</style>", text, re.DOTALL)
    head_style = style_match.group(1) if style_match else ""
    title_match = re.search(r"<title>(.*?)</title>", text)
    title = title_match.group(1) if title_match else slug
    body_match = re.search(r"<body[^>]*>(.*?)</body>", text, re.DOTALL)
    body = body_match.group(1) if body_match else text
    body = re.sub(r'href="report[^"]*\.html"', 'href="#top"', body)
    body = re.sub(r'href="report[^"]*\.html#([^"]+)"', r'href="#\1"', body)
    return SubPage(slug=slug, title=title, body_html=body.strip(), head_style=head_style.strip())


def _png_to_base64(path: Path) -> str:
    if not path.exists():
        raise FileNotFoundError(f"PNG missing: {path}")
    data = path.read_bytes()
    b64 = base64.b64encode(data).decode("ascii")
    return f"data:image/png;base64,{b64}"


def _inline_all_png(html: str, png_dir: Path) -> tuple[str, int, int, list[str]]:
    pattern = re.compile(r'<img\s+([^>]*?)src="([^"]+\.png)"([^>]*)>', re.IGNORECASE)
    count = 0
    total_bytes = 0
    missing: list[str] = []

    def replace(match: re.Match[str]) -> str:
        nonlocal count, total_bytes
        pre, src, post = match.group(1), match.group(2), match.group(3)
        png_path = (png_dir / src).resolve()
        if not png_path.exists():
            missing.append(src)
            return match.group(0)
        data_uri = _png_to_base64(png_path)
        count += 1
        total_bytes += png_path.stat().st_size
        return f'<img {pre}src="{data_uri}"{post}>'

    new_html = pattern.sub(replace, html)
    return new_html, count, total_bytes, missing


def _rewrite_subpage_links(html: str, sub_pages: list[tuple[str, Path]]) -> str:
    for slug, _ in sub_pages:
        html = re.sub(
            rf'href="page_{re.escape(slug)}\.html(#[^"]*)?"',
            f'href="#page-{slug}"',
            html,
        )
    return html


def _build_section_for_subpage(sub: SubPage, intra_page_anchors: list[str] | None = None) -> str:
    body = sub.body_html
    body = re.sub(r'<h1\s+id="([^"]+)"', rf'<h1 id="page-{sub.slug}-\1"', body)
    if intra_page_anchors:
        # 用 | 拼接 escaped 锚点名,改写跨页内 anchor 为 page-{slug}- 前缀
        anchor_re = "|".join(re.escape(a) for a in intra_page_anchors)
        body = re.sub(rf'href="#({anchor_re})"', rf'href="#page-{sub.slug}-\1"', body)
    return (
        f'\n<section class="standalone-subpage" id="page-{sub.slug}">\n'
        f'  <div class="standalone-divider">'
        f'<span class="standalone-divider-label">子页 · {sub.slug}</span>'
        f'<a href="#top" class="standalone-back">↑ 回到主页顶部</a></div>\n'
        f'  {body}\n</section>\n'
    )


def _validate_output(html: str, out_size: int, sub_pages: list[tuple[str, Path]]) -> dict:
    anchor_count = sum(1 for slug, _ in sub_pages if f'id="page-{slug}"' in html)
    base64_imgs = html.count("data:image/png;base64,")

    # A3 修复:统计悬浮 TOC body 内的 <li> 数量(代理"目录条目数")
    # 子页缺 H1/H2 id 时 extract_headings 返回空 → ftoc-body 内无 <li>
    # → 视觉上 TOC 为空,用户体感"浮动目录消失"。
    toc_body_match = re.search(r'<div class="ftoc-body">(.*?)</div>', html, re.DOTALL)
    toc_li_count = 0
    if toc_body_match:
        toc_li_count = toc_body_match.group(1).count('<li')

    return {
        "size_ok": out_size > MIN_BUNDLE_BYTES,
        "size_bytes": out_size,
        "anchor_count": anchor_count,
        "anchor_target": len(sub_pages),
        "base64_png_count": base64_imgs,
        "toc_li_count": toc_li_count,
        "toc_ok": toc_li_count >= 5,  # < 5 条 = 无效 TOC
    }


def build_standalone_html(
    main_html: Path,
    sub_pages: list[tuple[str, Path]],
    png_dir: Path,
    out_path: Path,
    *,
    auto_validate: bool = True,
    intra_page_anchors: list[str] | None = None,
) -> dict:
    """合并主页 + N 子页 + 全部 PNG base64 内嵌为单文件 HTML.

    Args:
        main_html: 主页 HTML 路径(必须含 <body><main></main></body>)
        sub_pages: [(slug, path), ...] 子页列表;slug 用作 anchor id
        png_dir: PNG 资产目录(<img src="X.png"> 相对此目录解析)
        out_path: 输出 HTML 路径
        auto_validate: 是否自动验证(默认开)。auto_validate=True 时检查
            ``size_ok = (out_size > MIN_BUNDLE_BYTES)``(默认 1 MB,常量
            ``MIN_BUNDLE_BYTES``)。小于阈值的合法输出请用 ``auto_validate=False``
            跳过此检查。
        intra_page_anchors: 子页内部锚点名列表(如 ``["decision", "calc", "lp"]``),
            用于把子页内 ``href="#decision"`` 改写为 ``href="#page-{slug}-decision"``。
            None 或空列表时不做改写。血液 IFI 项目可传
            ``["decision", "calc", "lp", "evidence"]``;通用场景留 None。

    Returns:
        {
            "ok": bool,
            "out_path": str,
            "size_mb": float,
            "png_count": int,
            "missing_pngs": list[str],
            "validation": {"size_ok": bool, "anchor_count": int, ...}
        }

    Raises:
        FileNotFoundError: main_html 或必需 PNG 不存在
        ValueError: main_html 不含 <body>
    """
    if not main_html.exists():
        raise FileNotFoundError(f"Main HTML missing: {main_html}")

    main = main_html.read_text(encoding="utf-8")
    if "<body" not in main:
        raise ValueError("Main HTML missing <body>")

    subs = [_extract_subpage(path, slug) for slug, path in sub_pages]

    # 注入 standalone CSS(子页分隔 + banner + 悬浮 TOC,与原 build_standalone.py 同款)
    extra_css = """
.standalone-subpage { margin-top: 60pt; padding-top: 30pt; border-top: 4pt double var(--navy); page-break-before: always; }
.standalone-divider { display: flex; justify-content: space-between; align-items: center; background: linear-gradient(90deg, var(--navy) 0%, var(--blue) 100%); color: #fff; padding: 12pt 18pt; border-radius: 6pt; margin-bottom: 16pt; font-size: 12pt; font-weight: 700; }
.standalone-divider-label { font-size: 13pt; }
.standalone-back { color: #fff; text-decoration: none; background: rgba(255,255,255,0.18); padding: 4pt 12pt; border-radius: 14pt; font-size: 10pt; }
.standalone-back:hover { background: rgba(255,255,255,0.32); }
.standalone-banner { background: #FEF3C7; border: 2pt solid #F59E0B; padding: 10pt 16pt; margin: 0 0 18pt; border-radius: 6pt; font-size: 10.5pt; color: #78350F; }
"""
    main = main.replace("</style>", extra_css + "\n</style>", 1)
    main = _rewrite_subpage_links(main, sub_pages)

    body_open = re.search(r"<body[^>]*>", main)
    if not body_open:
        raise ValueError("Cannot locate <body>")
    insert_pos = body_open.end()
    top_anchor = '\n<a id="top"></a>\n'
    banner = (
        '<div class="standalone-banner"><strong>📦 单一独立 HTML 版</strong> · '
        '已合并主页 + 全部子页 + 全部 PNG (base64 内嵌) · 零依赖,双击浏览器即可阅读</div>\n'
    )
    main = main[:insert_pos] + top_anchor + banner + main[insert_pos:]

    sections = "\n".join(_build_section_for_subpage(s, intra_page_anchors) for s in subs)
    end_main = main.rfind("</main>")
    if end_main == -1:
        end_main = main.rfind("</body>")
    main = main[:end_main] + sections + "\n" + main[end_main:]

    main, png_count, _png_bytes, missing_pngs = _inline_all_png(main, png_dir)

    out_path.write_text(main, encoding="utf-8")
    out_size = out_path.stat().st_size

    validation = _validate_output(main, out_size, sub_pages) if auto_validate else None
    ok = (validation is None) or (
        validation["size_ok"]
        and validation["anchor_count"] == validation["anchor_target"]
        and validation["toc_ok"]
    )

    # A3 修复:暴露 toc_warning 给调用方(build_all_deliverables 写入 manifest)
    toc_warning = validation is not None and not validation["toc_ok"]

    return {
        "ok": ok,
        "out_path": str(out_path),
        "size_mb": round(out_size / (1024 * 1024), 2),
        "png_count": png_count,
        "missing_pngs": missing_pngs,
        "validation": validation,
        "toc_warning": toc_warning,
    }
