"""Phase 5 part · design-system-injector: consulting palette + floating TOC + section dividers."""
from __future__ import annotations
import re
from typing import TypedDict


DESIGN_TOKENS: dict[str, str] = {
    "navy": "oklch(28% 0.05 250)",
    "navy-deep": "oklch(20% 0.04 250)",
    "gold": "oklch(76% 0.15 80)",
    "gold-deep": "oklch(58% 0.13 75)",
    "blue": "oklch(50% 0.12 240)",
    "gray-100": "oklch(96% 0 0)",
    "gray-300": "oklch(82% 0 0)",
    "gray-500": "oklch(58% 0 0)",
    "gray-700": "oklch(38% 0 0)",
    "background": "oklch(98% 0 0)",
    "surface": "oklch(100% 0 0)",
    "text": "oklch(18% 0 0)",
}


class DesignReport(TypedDict):
    token_coverage: float
    toc_li_count: int
    toc_block: bool
    warnings: list[str]


class InjectorError(Exception):
    pass


def _root_block(tokens: dict[str, str]) -> str:
    decls = "\n".join(f"  --{k}: {v};" for k, v in tokens.items())
    return f":root {{\n{decls}\n}}"


_BASE_CSS = """
body { background: var(--background); color: var(--text); font-family: 'Inter', system-ui, sans-serif; line-height: 1.6; }
h1, h2, h3 { color: var(--navy); }
a { color: var(--blue); }
section + section { border-top: 1px solid var(--gray-300); margin-top: 24pt; padding-top: 24pt; }
.ftoc-l1 > a { font-weight: 600; color: var(--navy); }
.ftoc-l2 > a { color: var(--gray-700); padding-left: 16pt; }
.ftoc-l3 > a { color: var(--gray-500); padding-left: 30pt; }
"""


_FTOC_BUTTON = """
<button id="ftoc-button" type="button" aria-label="Open TOC">
  <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor"><rect x="4" y="6" width="14" height="2"/><rect x="4" y="11" width="14" height="2"/><rect x="4" y="16" width="10" height="2"/></svg>
</button>
"""


def _build_toc_from_headings(html: str) -> str:
    items: list[str] = []
    for m in re.finditer(r'<h([123])\s+id="([^"]+)"[^>]*>(.*?)</h\1>', html, re.DOTALL):
        level = m.group(1)
        anchor = m.group(2)
        text = re.sub(r"<[^>]+>", "", m.group(3)).strip()
        items.append(f'<li class="ftoc-l{level}"><a href="#{anchor}">{text}</a></li>')
    return f"<ul>{''.join(items)}</ul>"


def inject(html: str, tokens: dict[str, str]) -> str:
    """Inject :root design tokens + base CSS + floating TOC button."""
    style_block = f"<style>\n{_root_block(tokens)}\n{_BASE_CSS}\n</style>"
    toc_html = _build_toc_from_headings(html)
    ftoc_overlay = (
        f'<div id="ftoc-overlay" hidden><aside id="ftoc-panel">'
        f'<header><span>Contents</span><button id="ftoc-close">close</button></header>'
        f'<div class="ftoc-body">{toc_html}</div></aside></div>'
    )
    if "</head>" in html:
        out = html.replace("</head>", f"{style_block}</head>", 1)
    else:
        out = style_block + html
    if "</body>" in out:
        out = out.replace("</body>", f"{_FTOC_BUTTON}{ftoc_overlay}</body>", 1)
    else:
        out = out + _FTOC_BUTTON + ftoc_overlay
    return out


def validate_design(html: str) -> DesignReport:
    """Compute token coverage + floating TOC li count."""
    token_count = len(DESIGN_TOKENS)
    used = sum(1 for k in DESIGN_TOKENS if f"var(--{k})" in html)
    coverage = used / token_count if token_count else 0.0
    li_count = len(re.findall(r'<li[^>]*class="[^"]*ftoc-l[123]', html))
    warnings: list[str] = []
    if coverage < 0.6:
        warnings.append(f"design token coverage {coverage:.0%} below 60% (warn, not block)")
    return DesignReport(
        token_coverage=coverage,
        toc_li_count=li_count,
        toc_block=li_count < 5,
        warnings=warnings,
    )
