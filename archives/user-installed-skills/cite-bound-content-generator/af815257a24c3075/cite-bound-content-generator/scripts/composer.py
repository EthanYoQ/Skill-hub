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
    r"\[(guideline|pmid|nct|aact|europepmc|bioc|pubtator|nmpa-page|evidence):([^\]]+)\]"
)
_ALLOWED_CLAIM_CLASSIFICATIONS = {
    "drug",
    "general",
    "model_output",
    "scenario_assumption",
    "stat",
    "treatment",
}


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
_MIN_H2_H3 = 10
_MIN_MERMAID_CHARS = 70
_MIN_MERMAID_EDGES = 3
_DEFERRED_PROCESS_TERMS = (
    "待 worker",
    "待Worker",
    "worker 继续",
    "后续量化模型",
    "再补足量化模型",
    "后续补足",
    "继续估算",
    "定性描述",
    "专家访谈判断",
    "暂按",
)
_QUANTIFIED_NUMBER_RE = re.compile(
    r"\d+(?:\.\d+)?\s*(?:万|亿|%|例|人|元|rmb|cny|million|billion|patients|cases)",
    re.I,
)
_LP_MENTION_RE = re.compile(
    r"(?<![A-Za-z])LP\s*\d*(?![A-Za-z])|策略干预点|leverage point",
    re.I,
)
_MERMAID_BLOCK_RE = re.compile(
    r'<div\b[^>]*class=["\'][^"\']*\bmermaid\b[^"\']*["\'][^>]*>(.*?)</div>',
    re.I | re.S,
)


def _strip_html(html: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html)).strip()


def _extract_section_html(html: str, section: str) -> str:
    pattern = (
        r'<section\b[^>]*data-section=["\']'
        + re.escape(section)
        + r'["\'][^>]*>(.*?)(?=<section\b[^>]*data-section=|</body>|$)'
    )
    match = re.search(pattern, html, re.I | re.S)
    return match.group(1) if match else ""


def _extract_subsection_text(section_html: str, subsection: str) -> str:
    pattern = (
        r'<section\b[^>]*data-subsection=["\']'
        + re.escape(subsection)
        + r'["\'][^>]*>(.*?)</section>'
    )
    match = re.search(pattern, section_html, re.I | re.S)
    return _strip_html(match.group(1)) if match else ""


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
        shallow_subs = []
        for subsection in _MARKET_SUBSECTIONS:
            text = _extract_subsection_text(market_html, subsection)
            deferred_hits = [
                term for term in _DEFERRED_PROCESS_TERMS
                if term.lower() in text.lower()
            ]
            if not text or not _QUANTIFIED_NUMBER_RE.search(text) or deferred_hits:
                shallow_subs.append({
                    "subsection": subsection,
                    "chars": len(text),
                    "quantified": bool(_QUANTIFIED_NUMBER_RE.search(text)),
                    "deferred_hits": deferred_hits,
                })
        if shallow_subs:
            violations.append(
                "market model quantification gap: TAM/SAM/SOM must each include "
                f"concrete numbers/units and no deferred language: {shallow_subs}"
            )

    mermaid_blocks = _MERMAID_BLOCK_RE.findall(html)
    mermaid_count = len(mermaid_blocks)
    if mermaid_count < _MIN_MERMAID:
        violations.append(f"Mermaid blocks {mermaid_count} < {_MIN_MERMAID}")
    shallow_mermaids = []
    for i, block in enumerate(mermaid_blocks):
        text = re.sub(r"\s+", " ", block).strip()
        edge_count = len(re.findall(r"(?:-->|---|==>|-.->)", text))
        if len(text) < _MIN_MERMAID_CHARS or edge_count < _MIN_MERMAID_EDGES:
            shallow_mermaids.append({
                "index": i,
                "chars": len(text),
                "edges": edge_count,
            })
    if shallow_mermaids:
        violations.append(
            f"Mermaid substance too shallow: {shallow_mermaids[:4]} "
            f"(each needs >= {_MIN_MERMAID_CHARS} chars and >= {_MIN_MERMAID_EDGES} edges)"
        )

    lp_count = len(_LP_MENTION_RE.findall(html))
    if lp_count < _MIN_LP:
        violations.append(f"LP mentions {lp_count} < {_MIN_LP}")
    lp_html = _extract_section_html(html, "lp-framework")
    lp_text = _strip_html(lp_html)
    lp_operating_terms = [
        term for term in ("触发", "责任", "KPI", "漏斗", "转化", "科室", "路径", "时限")
        if term.lower() in lp_text.lower()
    ]
    numbered_lp_count = len(
        re.findall(r"(?<![A-Za-z])LP\s*\d+(?![A-Za-z])|策略干预点\s*\d+", lp_text, re.I)
    )
    if numbered_lp_count < 4 or len(lp_operating_terms) < 4:
        violations.append(
            "LP analysis depth gap: require >=4 numbered LPs plus operating-model "
            f"details; numbered_lp_count={numbered_lp_count}, terms={lp_operating_terms}"
        )

    cohort_markers: set[str] = set()
    for attr in ("data-cohort", "data-segment"):
        cohort_markers.update(
            value.strip()
            for value in re.findall(attr + r'=["\']([^"\']+)["\']', html, re.I)
            if value.strip()
        )
    cohort_markers.update(
        value.strip()
        for value in re.findall(r'<sub-page\s+slug=["\']([^"\']+)["\']', html, re.I)
        if value.strip()
    )
    if len(cohort_markers) < 3:
        violations.append(
            f"cohort/segment depth gap: require >=3 cohort/subpage/segment markers, found {len(cohort_markers)}"
        )

    text_only = re.sub(r"<[^>]+>", "", html)
    h2_h3_count = len(re.findall(r"<h[23]\b", html, re.I))
    if h2_h3_count < _MIN_H2_H3:
        violations.append(f"H2/H3 headings {h2_h3_count} < {_MIN_H2_H3}")
    source_saved_count = text_only.count("已保存")
    appendix_filler_count = text_only.count("附录证据说明")
    source_index_count = text_only.count("来源索引")
    if source_saved_count >= 30 or appendix_filler_count >= 20 or source_index_count >= 20:
        violations.append(
            "source-index/process filler dominates report body: "
            f"已保存={source_saved_count}, 附录证据说明={appendix_filler_count}, 来源索引={source_index_count}"
        )
    deferred_hits = [term for term in _DEFERRED_PROCESS_TERMS if term in text_only]
    if deferred_hits:
        violations.append(
            f"deferred-model/process language in final report: {deferred_hits}"
        )
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
    r'<sub-page\s+[^>]*\bslug="([^"]+)"[^>]*>(.*?)</sub-page>',
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
    audit_layer: dict[str, Any] | None = None
    reader_layer_contract: dict[str, Any] | None = None
    raw_html: str = ""
    html_path: Path | None = None
    citations_index_path: Path | None = None


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
        return any(
            (sources_dir / dirname / f"{nct}.json").exists()
            for dirname in ("trials", "clinical_trials")
        )
    if src_type in {"aact", "europepmc", "bioc", "pubtator"}:
        source_id = locator.split(":")[0]
        return (sources_dir / src_type / f"{source_id}.json").exists()
    if src_type == "evidence":
        rel = locator.split(":")[0]
        local_evidence = sources_dir / "evidence" / rel
        if local_evidence.exists():
            return True
        if not Path(rel).suffix:
            for suffix in (".txt", ".json", ".md"):
                if local_evidence.with_suffix(suffix).exists():
                    return True
        evidence_path = Path(rel)
        if evidence_path.is_absolute():
            return evidence_path.exists()
        return (sources_dir.parent.parent / evidence_path).exists()
    return False


def compose(
    slug_dir: Path,
    ask_llm: Callable[..., dict],
    previous_violations: list[dict] | None = None,
    *,
    enforce_ifi: bool = False,
    output_dir: Path | None = None,
    return_report: bool = False,
) -> tuple[Path, Path] | ComposedReport:
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

    audit_layer = result.get("audit_layer")
    reader_layer_contract = result.get("reader_layer_contract")
    has_audit_layer = isinstance(audit_layer, dict)

    if not _ANCHOR_RE.search(html) and not has_audit_layer:
        raise ComposeError("HTML contains no citation anchors at all")

    # R1 Phase-2-Quality-Fix · IFI 章节强制 (opt-in via enforce_ifi=True).
    # 默认 False → backward compat with 6 现有 fake-LLM tests; production callbacks 显式开.
    if enforce_ifi:
        _assert_ifi_structure(html)

    for claim in claims:
        anchor = claim.get("anchor", "")
        if not anchor:
            raise ComposeError(f"Claim {claim!r} missing anchor")
        classification = claim.get("classification")
        if classification not in _ALLOWED_CLAIM_CLASSIFICATIONS:
            raise ComposeError(
                f"Claim {claim!r} has invalid classification {classification!r}; "
                f"must be one of {sorted(_ALLOWED_CLAIM_CLASSIFICATIONS)}"
            )
        if not _anchor_resolves(anchor, sources_dir):
            raise ComposeError(
                f"Anchor {anchor} not found in sources/ for claim {claim.get('claim_text', '')!r}"
            )

    main_html, sub_pages = _parse_sub_pages(html)
    toc_anchors = _extract_toc_anchors(main_html)

    output_dir = Path(output_dir) if output_dir is not None else slug_dir.parent.parent / "output"
    output_dir.mkdir(parents=True, exist_ok=True)
    html_path = output_dir / "report_raw.html"
    html_path.write_text(main_html, encoding="utf-8")

    authoring_provenance = result.get("authoring_provenance")
    idx: dict[str, Any] = {"claims": claims, "version": "1.0"}
    if isinstance(authoring_provenance, dict):
        provenance_path = slug_dir / "compose_authoring_provenance.json"
        provenance_path.write_text(
            json.dumps(authoring_provenance, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        idx["authoring_provenance"] = authoring_provenance
    idx_path = slug_dir / "citations_index.json"
    idx_path.write_text(json.dumps(idx, ensure_ascii=False, indent=2), encoding="utf-8")

    if has_audit_layer:
        audit_payload = dict(audit_layer)
        audit_payload.setdefault("version", "1.0")
        audit_payload.setdefault("compose_layer", "reader_layer_first")
        if isinstance(reader_layer_contract, dict):
            audit_payload["reader_layer_contract"] = reader_layer_contract
        (slug_dir / "reader_compose_audit_layer.json").write_text(
            json.dumps(audit_payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    if return_report:
        return ComposedReport(
            main_html=main_html,
            sub_pages=sub_pages,
            toc_anchors=toc_anchors,
            claims=claims,
            audit_layer=audit_layer if has_audit_layer else None,
            reader_layer_contract=(
                reader_layer_contract if isinstance(reader_layer_contract, dict) else None
            ),
            raw_html=html,
            html_path=html_path,
            citations_index_path=idx_path,
        )
    return html_path, idx_path


def _summarize_sources(sources_dir: Path) -> dict:
    """Build a concise summary the LLM can browse to construct citations."""
    summary: dict = {
        "guidelines": [],
        "pubmed": [],
        "trials": [],
        "europepmc": [],
        "bioc": [],
        "pubtator": [],
    }
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
    trial_files: list[Path] = []
    for dirname in ("trials", "clinical_trials"):
        t_dir = sources_dir / dirname
        if t_dir.exists():
            trial_files.extend(sorted(t_dir.glob("*.json")))
    seen_trial_ids: set[str] = set()
    for js in trial_files[:50]:
        if js.stem in seen_trial_ids:
            continue
        seen_trial_ids.add(js.stem)
        data = json.loads(js.read_text(encoding="utf-8"))
        summary["trials"].append({
            "source_id": js.stem,
            "title": (data.get("title") or "")[:200],
            "phase": data.get("phase"),
            "status": data.get("status"),
        })
    for source_type in ("europepmc", "bioc", "pubtator"):
        s_dir = sources_dir / source_type
        if not s_dir.exists():
            continue
        for js in sorted(s_dir.glob("*.json"))[:50]:
            data = json.loads(js.read_text(encoding="utf-8"))
            preview = json.dumps(data, ensure_ascii=False)[:800]
            summary[source_type].append({
                "source_id": js.stem,
                "preview": preview,
            })
    return summary
