"""Phase 4 Turn 1 · cite-bound-content-generator: compose report HTML with mandatory citations."""
from __future__ import annotations
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, List, Tuple

_HERE = Path(__file__).resolve()
_CONTRACT_SCRIPTS = _HERE.parents[2] / "contract-elicitor" / "scripts"
if str(_CONTRACT_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_CONTRACT_SCRIPTS))
from elicitor import assert_contract_complete  # noqa: E402


class ComposeError(Exception):
    """Raised when composed content fails Cite-or-Block preconditions."""


_ANCHOR_RE = re.compile(
    r"\[(guideline|pmid|nct|aact|nmpa-page|evidence):([^\]]+)\]"
)


# ---------------------------------------------------------------------------
# R1 Phase-2-Quality-Fix · _assert_ifi_structure (collect-all-violations)
# ---------------------------------------------------------------------------
_REQUIRED_IFI_SECTIONS = (
    "exec-summary",
    "epidemiology",
    "treatment-landscape",
    "market-sizing",
    "competitive-dynamics",
    "lp-framework",
    "appendix",
)
_MARKET_SUBSECTIONS = ("tam", "sam", "som")
_MIN_MERMAID = 4
_MIN_LP = 50
_MIN_MAIN_TEXT_CHARS = 4000


def _assert_ifi_structure(html: str) -> None:
    """检查 IFI 章节强制结构, **收集所有缺失** 一次性 raise (architect 修订 2 collect-all-violations once).

    7 sections + TAM/SAM/SOM subsection + Mermaid ≥ 4 + LP 提及 ≥ 50 + 主报告 ≥ 4000 字.
    任一不达 → ComposeError 含**所有缺失项**, orchestrator retry loop 反馈给 LLM 一次性补齐.

    详见 references/ifi-section-template.md.
    """
    violations: list[str] = []

    missing_sections = [
        s for s in _REQUIRED_IFI_SECTIONS if f'data-section="{s}"' not in html
    ]
    if missing_sections:
        violations.append(f"sections missing: {missing_sections}")

    market_match = re.search(
        r'data-section="market-sizing">(.*?)(?=<section data-section=|</section>\s*<section data-section|$)',
        html,
        re.S,
    )
    if market_match:
        market_html = market_match.group(1)
        missing_subs = [
            s for s in _MARKET_SUBSECTIONS
            if f'data-subsection="{s}"' not in market_html
        ]
        if missing_subs:
            violations.append(f"market-sizing subsections missing: {missing_subs}")

    mermaid_count = html.count('<div class="mermaid">')
    if mermaid_count < _MIN_MERMAID:
        violations.append(f"Mermaid blocks {mermaid_count} < {_MIN_MERMAID}")

    lp_count = len(re.findall(r"\b(?:LP|策略干预点|leverage point)\b", html))
    if lp_count < _MIN_LP:
        violations.append(f"LP mentions {lp_count} < {_MIN_LP}")

    text_only = re.sub(r"<[^>]+>", "", html)
    text_chars = len(text_only.strip())
    if text_chars < _MIN_MAIN_TEXT_CHARS:
        violations.append(f"main text {text_chars} chars < {_MIN_MAIN_TEXT_CHARS} 字")

    if violations:
        raise ComposeError(
            "IFI structure violations (all collected for one-shot retry):\n"
            + "\n".join(f"  - {v}" for v in violations)
        )


# ---------------------------------------------------------------------------
# R3b Phase-2-Quality-Fix · ComposedReport dataclass + sub-page parsing
# ---------------------------------------------------------------------------
_SUB_PAGE_RE = re.compile(
    r'<sub-page\s+slug="([^"]+)">(.*?)</sub-page>',
    re.DOTALL,
)


@dataclass
class ComposedReport:
    """Composer 升级输出 schema (R3b).

    fields:
        main_html: 主报告 (7 章框架, 不含 sub-page wrapper).
        sub_pages: 子页 list[dict {slug, html}], 与 R3a _persist_sub_pages 兼容.
        toc_anchors: 浮动 TOC 锚点列表 (从 main_html H2/H3 id 抽).
        claims: 用于 verifier 提取的 fact claim list.
        raw_html: backward compat (main + sub-page 拼合, verifier 可消费).
    """
    main_html: str
    sub_pages: List[dict] = field(default_factory=list)
    toc_anchors: List[str] = field(default_factory=list)
    claims: List[dict] = field(default_factory=list)
    raw_html: str = ""


def _parse_sub_pages(raw_html: str) -> Tuple[str, List[dict]]:
    """从 LLM 输出抽 <sub-page slug="..."> 包裹的子页.

    Returns:
        (main_html, sub_pages): main_html 不含 sub-page wrapper;
        sub_pages = [{"slug": str, "html": str}, ...] 与 _persist_sub_pages 兼容.
    """
    sub_pages: List[dict] = []
    for match in _SUB_PAGE_RE.finditer(raw_html):
        slug, html = match.group(1), match.group(2).strip()
        sub_pages.append({"slug": slug, "html": html})
    main_html = _SUB_PAGE_RE.sub("", raw_html)
    return main_html, sub_pages


def _extract_toc_anchors(html: str) -> List[str]:
    """从 main_html 抽 H2/H3 id 作 TOC 浮动锚点列表."""
    return re.findall(r'<h[23][^>]*id="([^"]+)"', html)


def _parse_anchor(anchor: str) -> tuple[str, str]:
    m = _ANCHOR_RE.fullmatch(anchor)
    if not m:
        raise ComposeError(f"Malformed anchor: {anchor!r}")
    return m.group(1), m.group(2)


def _anchor_resolves(anchor: str, sources_dir: Path) -> bool:
    src_type, locator = _parse_anchor(anchor)
    if src_type == "guideline":
        source_id = locator.split(":")[0]
        return (sources_dir / "guidelines" / f"{source_id}.txt").exists()
    if src_type == "pmid":
        pmid = locator.split(":")[0]
        return (sources_dir / "pubmed" / f"{pmid}.json").exists()
    if src_type == "nct":
        nct = locator.split(":")[0]
        return (sources_dir / "trials" / f"{nct}.json").exists()
    return False


def compose(
    slug_dir: Path,
    ask_llm: Callable[..., dict],
    previous_violations: list[dict] | None = None,
    *,
    enforce_ifi: bool = False,
) -> tuple[Path, Path]:
    """Phase 4 Turn 1.

    Returns: (report_raw.html path, citations_index.json path).
    `ask_llm(contract, staging, sources_summary, previous_violations) -> {html, claims}`.

    Preconditions:
      - contract.json valid
      - staging.json present
      - sources/ non-empty

    Postconditions:
      - HTML contains at least 1 anchor pattern
      - claims list non-empty
      - every claim's anchor resolves to a file in sources/
    """
    contract_path = slug_dir / "contract.json"
    assert_contract_complete(contract_path)
    contract = json.loads(contract_path.read_text(encoding="utf-8"))

    staging_path = slug_dir / "staging.json"
    if not staging_path.exists():
        raise ComposeError(f"staging.json missing in {slug_dir}. Run phase 2 first.")
    staging = json.loads(staging_path.read_text(encoding="utf-8"))

    sources_dir = slug_dir / "sources"
    if not sources_dir.exists():
        raise ComposeError(f"sources/ missing in {slug_dir}. Run phase 3 first.")

    sources_summary = _summarize_sources(sources_dir)

    result = ask_llm(contract, staging, sources_summary, previous_violations=previous_violations or [])
    if not isinstance(result, dict) or "html" not in result or "claims" not in result:
        raise ComposeError(f"LLM did not return required keys: {result!r}")

    html: str = result["html"]
    claims: list[dict] = result["claims"]

    if not claims:
        raise ComposeError("LLM returned 0 claims - fact-bearing report must have >=1 citation")

    if not _ANCHOR_RE.search(html):
        raise ComposeError("HTML contains no citation anchors at all")

    # R1 Phase-2-Quality-Fix · IFI 章节强制 (opt-in via enforce_ifi=True).
    # 默认 False → backward compat with 6 现有 fake-LLM tests; production callbacks 显式开.
    if enforce_ifi:
        _assert_ifi_structure(html)

    for claim in claims:
        anchor = claim.get("anchor", "")
        if not anchor:
            raise ComposeError(f"Claim {claim!r} missing anchor")
        if not _anchor_resolves(anchor, sources_dir):
            raise ComposeError(
                f"Anchor {anchor} not found in sources/ for claim {claim.get('claim_text', '')!r}"
            )

    output_dir = slug_dir.parent.parent / "output"
    output_dir.mkdir(parents=True, exist_ok=True)
    html_path = output_dir / "report_raw.html"
    html_path.write_text(html, encoding="utf-8")

    idx = {"claims": claims, "version": "1.0"}
    idx_path = slug_dir / "citations_index.json"
    idx_path.write_text(json.dumps(idx, ensure_ascii=False, indent=2), encoding="utf-8")

    return html_path, idx_path


def _summarize_sources(sources_dir: Path) -> dict:
    """Build a concise summary the LLM can browse to construct citations."""
    summary: dict = {"guidelines": [], "pubmed": [], "trials": []}
    g_dir = sources_dir / "guidelines"
    if g_dir.exists():
        for txt in sorted(g_dir.glob("*.txt")):
            summary["guidelines"].append({
                "source_id": txt.stem,
                "preview": txt.read_text(encoding="utf-8")[:2000],
            })
    p_dir = sources_dir / "pubmed"
    if p_dir.exists():
        for js in sorted(p_dir.glob("*.json"))[:50]:
            data = json.loads(js.read_text(encoding="utf-8"))
            summary["pubmed"].append({
                "source_id": js.stem,
                "abstract": (data.get("abstract") or "")[:600],
            })
    t_dir = sources_dir / "trials"
    if t_dir.exists():
        for js in sorted(t_dir.glob("*.json"))[:50]:
            data = json.loads(js.read_text(encoding="utf-8"))
            summary["trials"].append({
                "source_id": js.stem,
                "title": (data.get("title") or "")[:200],
                "phase": data.get("phase"),
                "status": data.get("status"),
            })
    return summary
