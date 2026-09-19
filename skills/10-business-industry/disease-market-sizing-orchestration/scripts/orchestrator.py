"""Disease Market Sizing Orchestration · thin entry skill (Phase 1.6 真 skill 化).

Wires 5 phases:
  1. contract-elicitor
  2. disease-stratifier
  3. evidence recall (inline 7 retrieval + A1' guidelines fetch)
  4. compose-then-audit (cite-bound-content-generator + content-verification-layer, ≤3 turns)
  5. report-bundle-builder + design-system-injector

Resumable mid-run via session-resume (A12).
"""
from __future__ import annotations
import importlib.util
import json
import re
import sys
from pathlib import Path
from typing import Any, Callable, TypedDict

_HERE = Path(__file__).resolve()
_SKILLS_DIR = _HERE.parents[2]


def _load_module(skill_name: str, module_name: str, alias: str):
    """Load a module from a skill's scripts/ directory under a unique alias."""
    file_path = _SKILLS_DIR / skill_name / "scripts" / f"{module_name}.py"
    if not file_path.exists():
        raise ImportError(f"Module not found: {file_path}")
    spec = importlib.util.spec_from_file_location(alias, file_path)
    if not spec or not spec.loader:
        raise ImportError(f"Cannot create spec for {file_path}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[alias] = mod
    spec.loader.exec_module(mod)
    return mod


# Add contract-elicitor scripts dir so its relative imports work
_p_elicitor = _SKILLS_DIR / "contract-elicitor" / "scripts"
if _p_elicitor.exists() and str(_p_elicitor) not in sys.path:
    sys.path.insert(0, str(_p_elicitor))

# Internal helpers migrated 2026-04-27 from former session-resume / mermaid-renderer skills
# (architect af265bdc revision 5 — preserve INVALIDATION_RULES + 3-tier mmdc fallback).
from _resume_helper import detect_partial_state  # noqa: E402
from _mermaid_helper import render_mermaid_to_png  # noqa: E402

_elicitor_mod = _load_module("contract-elicitor", "elicitor", "_orch_elicitor")
_stratifier_mod = _load_module("disease-stratifier", "stratifier", "_orch_stratifier")
_composer_mod = _load_module("cite-bound-content-generator", "composer", "_orch_composer")
_cv_mod = _load_module("content-verification-layer", "verifier", "_orch_cv")
_builder_mod = _load_module("report-bundle-builder", "builder", "_orch_builder")
elicit_contract = _elicitor_mod.elicit_contract
assert_contract_complete = _elicitor_mod.assert_contract_complete
_slugify = _elicitor_mod._slugify
ContractElicitationError = _elicitor_mod.ContractElicitationError
stratify = _stratifier_mod.stratify
StratificationError = _stratifier_mod.StratificationError
compose = _composer_mod.compose
ComposeError = _composer_mod.ComposeError
verify_full_report = _cv_mod.verify_full_report
build_all_deliverables = _builder_mod.build_all_deliverables


MAX_AUDIT_TURNS = 3


class OrchestrationError(Exception):
    pass


class Callbacks(TypedDict, total=False):
    ask_user_contract: Callable[[str, str, str], Any]
    ask_llm_stratify: Callable[[dict, str], list[dict]]
    fetch_guidelines: Callable[[Path], None]
    recall_evidence: Callable[[Path], None]
    ask_llm_compose: Callable[..., dict]
    ask_llm_semantic: Callable[..., dict]  # R2: Tier 2 LLM semantic check
    enforce_ifi: bool  # R1: composer 强制 IFI 章节结构 (opt-in, production=True)


def run(
    user_one_liner: str,
    project_root: Path,
    callbacks: Callbacks,
) -> dict[str, Any]:
    """Entry point. Returns delivery_manifest dict."""
    project_root = Path(project_root).resolve()

    # Phase 1: Contract — resume if existing contract.json found in any .cache slug
    cache_root = project_root / ".cache"
    existing_contract: Path | None = None
    if cache_root.exists():
        for slug_dir_candidate in cache_root.iterdir():
            cp = slug_dir_candidate / "contract.json"
            if cp.exists():
                existing_contract = cp
                break

    if existing_contract is not None:
        contract_path = existing_contract
    else:
        if "ask_user_contract" not in callbacks:
            raise OrchestrationError("callback ask_user_contract required for phase 1")
        contract_path = elicit_contract(
            user_one_liner, project_root, callbacks["ask_user_contract"]
        )

    assert_contract_complete(contract_path)
    slug_dir = contract_path.parent

    # Phase 2: Stratification (requires guidelines first)
    if not (slug_dir / "staging.json").exists():
        if "fetch_guidelines" in callbacks:
            callbacks["fetch_guidelines"](slug_dir)
        if "ask_llm_stratify" not in callbacks:
            raise OrchestrationError("callback ask_llm_stratify required for phase 2")
        stratify(slug_dir, ask_llm=callbacks["ask_llm_stratify"])

    # Phase 3: Evidence Recall — populate sources/pubmed/ if missing
    sources_dir = slug_dir / "sources"
    sources_pubmed = sources_dir / "pubmed"
    if not sources_pubmed.exists() or not any(sources_pubmed.glob("*.json")):
        if "recall_evidence" in callbacks:
            callbacks["recall_evidence"](slug_dir)

    # Phase 4: Compose-then-Audit (≤ MAX_AUDIT_TURNS turns)
    if "ask_llm_compose" not in callbacks:
        raise OrchestrationError("callback ask_llm_compose required for phase 4")

    previous_violations: list[dict] = []
    final_verdict: dict | None = None
    last_failure_reason: str = ""
    for turn in range(1, MAX_AUDIT_TURNS + 1):
        try:
            html_path, _idx_path = compose(
                slug_dir,
                ask_llm=callbacks["ask_llm_compose"],
                previous_violations=previous_violations or None,
                enforce_ifi=bool(callbacks.get("enforce_ifi", False)),
            )
        except ComposeError as exc:
            last_failure_reason = f"compose-error (turn {turn}): {exc}"
            previous_violations = [{
                "severity": "critical",
                "claim": "",
                "anchor": "",
                "reason": str(exc),
                "suggestion": "fix anchor resolution / claim format and recompose",
            }]
            continue

        # R2 Phase-2-Quality-Fix: opt-in 语义层 (callbacks 必须含 ask_llm_semantic).
        # 默认不传 budget_state, 行为与 119 现有测试一致 (fake demo / 无 LLM 场景跳过语义检查).
        ask_llm_semantic = callbacks.get("ask_llm_semantic")
        if ask_llm_semantic is not None:
            budget_state: dict | None = {
                "calls_remaining": 10,
                "audit_log_path": slug_dir / "semantic_audit_log.jsonl",
            }
        else:
            budget_state = None
        verdict = verify_full_report(
            html_path.read_text(encoding="utf-8"),
            sources_dir,
            ask_llm_semantic=ask_llm_semantic,
            budget_state=budget_state,
        )
        verdict_payload = {
            "verdict": verdict["verdict"],
            "violations": verdict["violations"],
            "turn_count": turn,
            "version": "1.0",
        }
        (slug_dir / "verification_report.json").write_text(
            json.dumps(verdict_payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        if verdict["verdict"] == "ok":
            final_verdict = verdict
            break
        previous_violations = list(verdict["violations"])
        last_failure_reason = (
            f"verify-blocked (turn {turn}): {len(previous_violations)} violations"
        )

    if final_verdict is None or final_verdict.get("verdict") != "ok":
        vr_path = slug_dir / "verification_report.json"
        raise OrchestrationError(
            f"Phase 4 verification failed after {MAX_AUDIT_TURNS} turns "
            f"({last_failure_reason}). See {vr_path} for full violation list. "
            f"Possible mitigations: extend evidence_window, lower report_depth=executive, "
            f"or wait for guideline update."
        )

    # Phase 4.5 (migrated from former mermaid-renderer skill): Mermaid blocks → PNG via mmdc.
    # graceful fallback: render_mermaid_to_png ok=False → 保留 inline <div class="mermaid"> 不阻塞.
    output_dir = project_root / "output"
    if (output_dir / "report_raw.html").exists():
        report_path = output_dir / "report_raw.html"
        report_html = report_path.read_text(encoding="utf-8")
        mermaid_blocks = re.findall(
            r'<div class="mermaid">(.*?)</div>', report_html, re.DOTALL
        )
        assets_dir = output_dir / "assets"
        for i, block in enumerate(mermaid_blocks):
            png_path = assets_dir / f"decision-tree-{i}.png"
            result = render_mermaid_to_png(block, png_path)
            if result["ok"]:
                # 替换 inline Mermaid → <img>
                report_html = report_html.replace(
                    f'<div class="mermaid">{block}</div>',
                    f'<img src="assets/decision-tree-{i}.png" alt="decision tree {i}">',
                    1,
                )
            # else: 保留 inline 不阻塞
        if mermaid_blocks:
            report_path.write_text(report_html, encoding="utf-8")

    # Phase 5: Bundle + Design + TOC
    # R3a Phase-2-Quality-Fix: 把 ComposedReport.sub_pages / toc_anchors 传给 builder.
    # composer 当前未升级输出 ComposedReport (R3b T12-T13 待做), 此处先用 hasattr 防御兼容.
    composed_sub_pages = None
    composed_toc_anchors = None
    composed_obj = locals().get("_idx_path")  # placeholder, R3b 升级后改为 ComposedReport
    if composed_obj is not None and hasattr(composed_obj, "sub_pages"):
        composed_sub_pages = composed_obj.sub_pages
        composed_toc_anchors = getattr(composed_obj, "toc_anchors", None)

    manifest = build_all_deliverables(
        slug_dir,
        project_root,
        skip_pdf=True,
        skip_xlsx=True,
        sub_pages=composed_sub_pages,
        toc_anchors=composed_toc_anchors,
    )
    return manifest
