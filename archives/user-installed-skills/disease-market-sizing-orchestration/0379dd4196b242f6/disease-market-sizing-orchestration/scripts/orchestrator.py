"""Disease Market Sizing Orchestration · thin entry skill (Phase 1.6 真 skill 化).

Wires 5 phases:
  1. contract-elicitor
  2. disease-stratifier
  3. evidence recall (inline 7 retrieval + A1' guidelines fetch)
  4. compose-then-audit (cite-bound-content-generator + content-verification-layer
     + citation-anchor-resolver + drug-citation-verifier, ≤3 turns)
  5. report-bundle-builder + design-system-injector

Resumable mid-run via session-resume (A12).
"""
from __future__ import annotations
import importlib.util
import json
import re
import sys
from dataclasses import asdict, is_dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, TypedDict
from uuid import uuid4

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


# Add local skill script dirs to sys.path so cross-skill imports use snapshots, not
# stale globally installed skills.
for _sub in ("citation-anchor-resolver", "contract-elicitor", "session-resume"):
    _p = _SKILLS_DIR / _sub / "scripts"
    if _p.exists():
        while str(_p) in sys.path:
            sys.path.remove(str(_p))
        sys.path.insert(0, str(_p))
if (_SKILLS_DIR / "citation-anchor-resolver" / "scripts").exists():
    _a11_path = (_SKILLS_DIR / "citation-anchor-resolver" / "scripts").resolve()
    for _module_name in ("resolver", "_source_loader", "_anchor_schema", "_keyword_match"):
        _loaded = sys.modules.get(_module_name)
        _loaded_file = Path(getattr(_loaded, "__file__", "") or "") if _loaded else None
        if _loaded_file and _a11_path not in _loaded_file.resolve().parents:
            sys.modules.pop(_module_name, None)

_resume_mod = _load_module("session-resume", "resume", "_orch_resume")
_elicitor_mod = _load_module("contract-elicitor", "elicitor", "_orch_elicitor")
_stratifier_mod = _load_module("disease-stratifier", "stratifier", "_orch_stratifier")
_composer_mod = _load_module("cite-bound-content-generator", "composer", "_orch_composer")
_cv_mod = _load_module("content-verification-layer", "verifier", "_orch_cv")
_citation_resolver_mod = _load_module("citation-anchor-resolver", "resolver", "_orch_citation_resolver")
_drug_verifier_mod = _load_module("drug-citation-verifier", "verifier", "_orch_drug_verifier")
_builder_mod = _load_module("report-bundle-builder", "builder", "_orch_builder")
# R3c Phase-2-Quality-Fix: mermaid-renderer skill (graceful fallback 无 mmdc 不阻塞)
try:
    _renderer_mod = _load_module("mermaid-renderer", "renderer", "_orch_mermaid_renderer")
    render_mermaid_to_png = _renderer_mod.render_mermaid_to_png
except ImportError:
    render_mermaid_to_png = None  # skill 未安装 → Phase 4.5 跳过

detect_partial_state = _resume_mod.detect_partial_state
elicit_contract = _elicitor_mod.elicit_contract
assert_contract_complete = _elicitor_mod.assert_contract_complete
_slugify = _elicitor_mod._slugify
ContractElicitationError = _elicitor_mod.ContractElicitationError
stratify = _stratifier_mod.stratify
StratificationError = _stratifier_mod.StratificationError
compose = _composer_mod.compose
ComposeError = _composer_mod.ComposeError
verify_full_report = _cv_mod.verify_full_report
parse_citations_in_text = _citation_resolver_mod.parse_citations_in_text
resolve_citation = _citation_resolver_mod.resolve_citation
verify_drug_mentions_in_text = _drug_verifier_mod.verify_drug_mentions_in_text
extract_drug_mentions_with_context = _drug_verifier_mod.extract_drug_mentions_with_context
build_all_deliverables = _builder_mod.build_all_deliverables


MAX_AUDIT_TURNS = 3
DEFAULT_MIN_PUBMED_SOURCES = 5
PRODUCTION_SEMANTIC_AUDIT_CALL_BUDGET = 1000
ORCHESTRATION_ENTRYPOINT = "disease-market-sizing-orchestration"
PRODUCTION_EVIDENCE_REQUIRED_CHANNELS = {
    "bioc-fulltext-fetch": [
        "bioc_fulltext_manifest.json",
        "sources/bioc",
        "sources/pmc",
        "sources/fulltext",
    ],
    "pubtator-entity-search": [
        "pubtator_entity_manifest.json",
        "pubtator_entities.json",
        "sources/pubtator",
    ],
    "medical-evidence-grading": [
        "medical_evidence_grading_report.json",
        "medical_evidence_grading_manifest.json",
        "sources/medical_evidence_grading",
    ],
}
_MERMAID_BLOCK_RE = re.compile(
    r"<div\b(?=[^>]*\bclass\s*=\s*(['\"])[^'\"]*\bmermaid\b[^'\"]*\1)[^>]*>(?P<body>.*?)</div>",
    re.I | re.S,
)
_MERMAID_EDGE_RE = re.compile(r"(?:-->|---|==>|-.->|--[^-\n]*-->)")
_MERMAID_DECISION_RE = re.compile(r"\{[^{}\n]{2,}\}")
_MERMAID_NUMERIC_ANCHOR_RE = re.compile(
    r"\d+(?:,\d{3})*(?:\.\d+)?\s*(?:%|‰|万|亿|例|人|人次|元|亿元|万元|/1000|per\s*1000|小时|天|月|年)?[^\n\]]{0,80}\[(?:guideline|pmid|nct|aact|europepmc|bioc|pubtator|evidence):",
    re.I,
)
_MERMAID_CROSS_POINT_RE = re.compile(
    r"(?:交叉点|交叉|cross[- ]?point|intersection|cohort\s*[x×]|人群\s*[x×]|病原\s*[x×])",
    re.I,
)
_MERMAID_LP_RE = re.compile(r"\bLP\s*\d+|LP\d+_|策略干预点|classDef\s+lp|-.->.*LP", re.I)


class OrchestrationError(Exception):
    pass


def _count_pubmed_sources(slug_dir: Path) -> int:
    pubmed_dir = slug_dir / "sources" / "pubmed"
    if not pubmed_dir.exists():
        return 0
    return len([p for p in pubmed_dir.glob("*.json") if p.is_file()])


def _count_nonempty_lines(path: Path) -> int:
    try:
        with path.open("r", encoding="utf-8") as handle:
            return sum(1 for line in handle if line.strip())
    except OSError:
        return 0


_MERMAID_NUMERIC_VALUE_RE = re.compile(
    r"\d+(?:,\d{3})*(?:\.\d+)?\s*(?:%|‰|万|亿|例|人|人次|元|亿元|万元|/1000|per\s*1000|小时|天|月|年)?",
    re.I,
)


def _mermaid_manifest_metrics(source: str, *, reader_audit_mode: bool = False) -> dict[str, int]:
    cross_point_count = 0
    for line in re.split(r"[\n;]+", source):
        if _MERMAID_CROSS_POINT_RE.search(line) and (
            _MERMAID_NUMERIC_ANCHOR_RE.search(line)
            or (reader_audit_mode and _MERMAID_NUMERIC_VALUE_RE.search(line))
        ):
            cross_point_count += 1
    numeric_count = len(_MERMAID_NUMERIC_ANCHOR_RE.findall(source))
    if reader_audit_mode:
        numeric_count = max(numeric_count, len(_MERMAID_NUMERIC_VALUE_RE.findall(source)))
    return {
        "edge_count": len(_MERMAID_EDGE_RE.findall(source)),
        "decision_node_count": len(_MERMAID_DECISION_RE.findall(source)),
        "numeric_evidence_count": numeric_count,
        "cross_point_count": cross_point_count,
        "lp_embedding_count": len(_MERMAID_LP_RE.findall(source)),
    }


def _load_agent_run_context(slug_dir: Path) -> dict[str, Any]:
    path = slug_dir / "agent_run_context.json"
    if not path.exists():
        raise OrchestrationError(
            f"production retrieval contract missing agent_run_context.json: {path}"
        )
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise OrchestrationError(
            f"production retrieval contract has invalid agent_run_context.json: {exc}"
        ) from exc
    if not isinstance(payload, dict):
        raise OrchestrationError("production retrieval contract must be a JSON object")
    return payload


def _read_skill_log_steps(slug_dir: Path) -> list[dict[str, Any]]:
    path = slug_dir / "skill_run_log.json"
    if not path.exists():
        return []
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []
    steps = payload.get("steps") if isinstance(payload, dict) else None
    if not isinstance(steps, list):
        return []
    return [step for step in steps if isinstance(step, dict)]


def _path_has_existing_evidence(slug_dir: Path, value: Any) -> bool:
    if not isinstance(value, str) or not value.strip():
        return False
    path = Path(value)
    if not path.is_absolute():
        path = slug_dir / path
    return path.exists()


def _step_has_existing_evidence(slug_dir: Path, step: dict[str, Any]) -> bool:
    evidence = step.get("evidence")
    if _path_has_existing_evidence(slug_dir, evidence):
        return True
    for key in ("manifest", "manifest_path", "source_manifest_path", "output_path"):
        if _path_has_existing_evidence(slug_dir, step.get(key)):
            return True
    return False


def _logged_evidence_channels(slug_dir: Path) -> set[str]:
    channels: set[str] = set()
    for step in _read_skill_log_steps(slug_dir):
        if str(step.get("status", "")).lower() not in {"ok", "pass", "passed", "success"}:
            continue
        if not _step_has_existing_evidence(slug_dir, step):
            continue
        for key in ("skill", "channel", "retrieval_channel", "source_channel"):
            value = step.get(key)
            if isinstance(value, str) and value.strip():
                channels.add(value.strip())
    return channels


def _count_non_raw_sources(slug_dir: Path) -> int:
    sources_dir = slug_dir / "sources"
    raw_dir = sources_dir / "raw"
    if not sources_dir.exists():
        return 0
    count = 0
    for path in sources_dir.rglob("*"):
        if not path.is_file():
            continue
        try:
            path.relative_to(raw_dir)
            continue
        except ValueError:
            count += 1
    return count


def _required_int(context: dict[str, Any], key: str) -> int:
    value = context.get(key)
    if isinstance(value, bool) or value is None:
        raise OrchestrationError(f"production retrieval contract missing numeric {key}")
    try:
        number = int(value)
    except (TypeError, ValueError) as exc:
        raise OrchestrationError(
            f"production retrieval contract has non-numeric {key}: {value!r}"
        ) from exc
    if number < 0:
        raise OrchestrationError(f"production retrieval contract has negative {key}: {number}")
    return number


def _target_channels(context: dict[str, Any]) -> list[str]:
    channels = context.get("retrieval_channels")
    if not isinstance(channels, list) or not channels:
        raise OrchestrationError(
            "production retrieval contract missing retrieval_channels target list"
        )
    result = [str(channel).strip() for channel in channels if str(channel).strip()]
    if not result:
        raise OrchestrationError(
            "production retrieval contract missing retrieval_channels target list"
        )
    return list(dict.fromkeys(result))


def _channel_has_manifest_or_source_evidence(slug_dir: Path, channel: str) -> bool:
    for relative in PRODUCTION_EVIDENCE_REQUIRED_CHANNELS.get(channel, []):
        if (slug_dir / relative).exists():
            return True
    return False


def _assert_production_retrieval_contract(slug_dir: Path) -> None:
    context = _load_agent_run_context(slug_dir)
    target_channels = _target_channels(context)
    minimum_retrieval_channels = _required_int(context, "minimum_retrieval_channels")
    target_retrieval_channels = _required_int(context, "target_retrieval_channels")
    minimum_total_sources = _required_int(context, "minimum_total_sources")
    target_total_sources = _required_int(context, "target_total_sources")

    logged_channels = _logged_evidence_channels(slug_dir)
    required_channel_count = max(minimum_retrieval_channels, target_retrieval_channels)
    missing_channels = [
        channel for channel in target_channels if channel not in logged_channels
    ]
    if len(logged_channels.intersection(target_channels)) < required_channel_count:
        raise OrchestrationError(
            "production retrieval contract failed: missing required channels "
            f"{missing_channels or target_channels}; logged evidence channels="
            f"{sorted(logged_channels)}; required distinct channels={required_channel_count}"
        )
    missing_evidence_channels = [
        channel
        for channel in target_channels
        if channel in PRODUCTION_EVIDENCE_REQUIRED_CHANNELS
        and not _channel_has_manifest_or_source_evidence(slug_dir, channel)
    ]
    if missing_evidence_channels:
        raise OrchestrationError(
            "production retrieval contract failed: missing required channels "
            f"{missing_evidence_channels} manifest/source evidence"
        )
    source_count = _count_non_raw_sources(slug_dir)
    required_source_count = max(minimum_total_sources, target_total_sources)
    if source_count < required_source_count:
        raise OrchestrationError(
            "production retrieval contract failed: non-raw sources insufficient "
            f"{source_count} saved sources < target {required_source_count}; "
            "sources/raw/** is excluded from this count"
        )


class Callbacks(TypedDict, total=False):
    ask_user_contract: Callable[[str, str, str], Any]
    ask_llm_stratify: Callable[[dict, str], list[dict]]
    fetch_guidelines: Callable[[Path], None]
    recall_evidence: Callable[[Path], None]
    ask_llm_compose: Callable[..., dict]
    ask_llm_semantic: Callable[..., dict]  # R2: Tier 2 LLM semantic check
    enforce_ifi: bool  # R1: composer 强制 IFI 章节结构 (opt-in, production=True)
    audit_production_smoke: Callable[..., Any]


def _jsonable(value: Any) -> Any:
    if is_dataclass(value):
        return _jsonable(asdict(value))
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, dict):
        return {str(k): _jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(v) for v in value]
    if hasattr(value, "__dict__"):
        return _jsonable(vars(value))
    return value


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _append_skill_log_step(
    slug_dir: Path,
    *,
    skill: str,
    run_id: str,
    evidence: Path | str | None = None,
    status: str = "ok",
    **extra: Any,
) -> None:
    path = slug_dir / "skill_run_log.json"
    if path.exists():
        payload = json.loads(path.read_text(encoding="utf-8"))
    else:
        payload = {
            "version": "1.0",
            "slug": slug_dir.name,
            "created_at": _now_iso(),
            "steps": [],
        }
    steps = payload.get("steps", [])
    if not isinstance(steps, list):
        steps = []
    steps = [
        step
        for step in steps
        if not (
            isinstance(step, dict)
            and step.get("skill") == skill
            and step.get("generated_by") == ORCHESTRATION_ENTRYPOINT
        )
    ]
    entry: dict[str, Any] = {
        "skill": skill,
        "status": status,
        "generated_by": ORCHESTRATION_ENTRYPOINT,
        "run_id": run_id,
        "ran_at": _now_iso(),
    }
    if evidence is not None:
        entry["evidence"] = str(Path(evidence).resolve())
    entry.update(_jsonable(extra))
    steps.append(entry)
    payload["steps"] = steps
    payload["updated_at"] = _now_iso()
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _new_trace(slug_dir: Path) -> dict[str, Any]:
    return {
        "version": "1.0",
        "entrypoint": ORCHESTRATION_ENTRYPOINT,
        "agent_runtime": "codex_or_claude_code_plugin_session",
        "run_id": str(uuid4()),
        "slug": slug_dir.name,
        "started_at": _now_iso(),
        "status": "running",
        "phases": [],
        "loaded_skill_modules": {
            "disease-stratifier": str((_SKILLS_DIR / "disease-stratifier").resolve()),
            "cite-bound-content-generator": str((_SKILLS_DIR / "cite-bound-content-generator").resolve()),
            "content-verification-layer": str((_SKILLS_DIR / "content-verification-layer").resolve()),
            "citation-anchor-resolver": str((_SKILLS_DIR / "citation-anchor-resolver").resolve()),
            "drug-citation-verifier": str((_SKILLS_DIR / "drug-citation-verifier").resolve()),
            "mermaid-renderer": str((_SKILLS_DIR / "mermaid-renderer").resolve()),
            "report-bundle-builder": str((_SKILLS_DIR / "report-bundle-builder").resolve()),
        },
    }


def _write_trace(slug_dir: Path, trace: dict[str, Any]) -> None:
    (slug_dir / "orchestration_trace.json").write_text(
        json.dumps(_jsonable(trace), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def _record_trace_phase(
    slug_dir: Path,
    trace: dict[str, Any],
    *,
    skill: str,
    evidence: Path | str | None,
    status: str = "ok",
    **extra: Any,
) -> None:
    phase: dict[str, Any] = {
        "skill": skill,
        "status": status,
        "completed_at": _now_iso(),
    }
    if evidence is not None:
        phase["evidence"] = str(Path(evidence).resolve())
    phase.update(_jsonable(extra))
    phases = trace.setdefault("phases", [])
    if isinstance(phases, list):
        phases.append(phase)
    _append_skill_log_step(
        slug_dir,
        skill=skill,
        run_id=str(trace["run_id"]),
        evidence=evidence,
        status=status,
        **extra,
    )
    _write_trace(slug_dir, trace)


def _best_existing_evidence(slug_dir: Path, names: list[str], fallback: Path) -> Path:
    for name in names:
        candidate = slug_dir / name
        if candidate.exists():
            return candidate
    return fallback


def _load_default_smoke_audit(project_root: Path) -> Callable[..., Any]:
    audit_path = project_root / "scripts" / "production_smoke_audit.py"
    if not audit_path.exists():
        raise OrchestrationError(f"production smoke audit script not found: {audit_path}")
    spec = importlib.util.spec_from_file_location("_orch_production_smoke_audit", audit_path)
    if not spec or not spec.loader:
        raise OrchestrationError(f"cannot load production smoke audit script: {audit_path}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules["_orch_production_smoke_audit"] = mod
    spec.loader.exec_module(mod)
    return mod.audit_smoke


def _run_citation_anchor_resolution_gate(
    slug_dir: Path,
    html: str,
    sources_dir: Path,
    audit_layer: dict[str, Any] | None = None,
) -> dict[str, Any]:
    citation_text = html
    if isinstance(audit_layer, dict):
        anchors: list[str] = []
        for section_name in ("evidence_support_table", "reader_to_audit_mapping", "claims"):
            section = audit_layer.get(section_name)
            if not isinstance(section, list):
                continue
            for item in section:
                if not isinstance(item, dict):
                    continue
                values = item.get("source_anchors") or item.get("anchors") or []
                if isinstance(values, str):
                    values = [values]
                if isinstance(values, list):
                    anchors.extend(str(anchor) for anchor in values if isinstance(anchor, str))
        citation_text = "\n".join(dict.fromkeys(anchors)) or html
    citations = parse_citations_in_text(citation_text)
    unresolved: list[dict[str, Any]] = []
    resolved_count = 0
    seen: set[str] = set()
    for item in citations:
        anchor_str = str(item.get("anchor_str") or "")
        if anchor_str in seen:
            continue
        seen.add(anchor_str)
        source_text = resolve_citation(item.get("anchor") or anchor_str, sources_dir)
        if source_text:
            resolved_count += 1
        else:
            unresolved.append({
                "anchor": anchor_str,
                "claim_sentence": str(item.get("claim_sentence") or "")[:240],
            })
    report = {
        "ok": not unresolved,
        "version": "1.0",
        "skill": "citation-anchor-resolver",
        "total_anchor_occurrences": len(citations),
        "unique_anchor_count": len(seen),
        "resolved_unique_count": resolved_count,
        "unresolved_count": len(unresolved),
        "unresolved": unresolved[:50],
    }
    (slug_dir / "citation_anchor_resolution_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return report


def _run_drug_citation_gate(
    slug_dir: Path,
    html: str,
    sources_dir: Path,
    audit_layer: dict[str, Any] | None = None,
) -> dict[str, Any]:
    drug_text = html
    html_mentions = extract_drug_mentions_with_context(html or "")
    if isinstance(audit_layer, dict):
        parts: list[str] = []
        for claim in audit_layer.get("claims", []):
            if not isinstance(claim, dict):
                continue
            anchors = claim.get("source_anchors") or claim.get("anchors") or []
            if isinstance(anchors, str):
                anchors = [anchors]
            anchor_text = " ".join(str(anchor) for anchor in anchors if isinstance(anchor, str))
            parts.append(f"{claim.get('claim_text', '')} {anchor_text}".strip())
        if parts:
            drug_text = "\n".join(parts)
    result = dict(verify_drug_mentions_in_text(drug_text, sources_dir))
    if isinstance(audit_layer, dict) and html_mentions:
        verified_or_seen = {
            str(mention.get("text", ""))
            for mention in result.get("drug_mentions", [])
            if isinstance(mention, dict)
        }
        html_drugs = sorted({
            str(mention.get("text", ""))
            for mention in html_mentions
            if isinstance(mention, dict) and mention.get("text")
        })
        missing_from_audit = [
            drug for drug in html_drugs
            if not any(drug in seen or seen in drug for seen in verified_or_seen if seen)
        ]
        result["html_drug_terms"] = html_drugs
        result["html_drug_terms_missing_from_audit"] = missing_from_audit
        if missing_from_audit:
            existing = list(result.get("drug_mentions", []))
            for drug in missing_from_audit:
                existing.append({
                    "text": drug,
                    "brand_in_context": "",
                    "citation": None,
                    "verified": False,
                    "missing_in_source": [drug],
                    "reason": "drug appears in reader HTML but not in audit-layer drug claims",
                    "severity": "critical",
                })
            result["drug_mentions"] = existing
            result["ok"] = False
            result["violation_severity"] = "critical"
    result.setdefault("version", "1.0")
    result.setdefault("skill", "drug-citation-verifier")
    payload_text = json.dumps(result, ensure_ascii=False, indent=2)
    (slug_dir / "drug_citation_verification.json").write_text(
        payload_text,
        encoding="utf-8",
    )
    (slug_dir / "drug_citation_verification_report.json").write_text(
        payload_text,
        encoding="utf-8",
    )
    return result


def _embed_source_corpus_if_available(
    *,
    project_root: Path,
    slug_dir: Path,
    output_dir: Path,
) -> None:
    html_path = output_dir / "report_standalone.html"
    embed_path = project_root / "scripts" / "embed_source_corpus.py"
    if not html_path.exists() or not embed_path.exists():
        return
    spec = importlib.util.spec_from_file_location("_orch_embed_source_corpus", embed_path)
    if not spec or not spec.loader:
        return
    mod = importlib.util.module_from_spec(spec)
    sys.modules["_orch_embed_source_corpus"] = mod
    spec.loader.exec_module(mod)
    mod.embed_source_corpus(html_path=html_path, slug_dir=slug_dir, include_raw=True)
    _refresh_delivery_manifest_html_size(output_dir=output_dir, html_path=html_path)


def _refresh_delivery_manifest_html_size(*, output_dir: Path, html_path: Path) -> None:
    """Keep delivery manifest artifact metadata aligned after post-build HTML mutation."""
    manifest_path = output_dir / "delivery_manifest.json"
    if not manifest_path.exists() or not html_path.exists():
        return
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return
    html_manifest = manifest.get("deliverables", {}).get("html")
    if not isinstance(html_manifest, dict):
        return
    size_bytes = html_path.stat().st_size
    html_manifest["size_bytes"] = size_bytes
    html_manifest["size_mb"] = round(size_bytes / 1024 / 1024, 4)
    html_manifest["post_bundle_updated"] = True
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def _write_and_assert_production_smoke_audit(
    *,
    project_root: Path,
    slug: str,
    output_dir: Path,
    v25_reference_html: Path | None,
    forbid_pdf: bool,
    audit_runner: Callable[..., Any] | None,
) -> None:
    if v25_reference_html is None:
        raise OrchestrationError(
            "V25 reference HTML is required for production smoke audit. "
            "Pass v25_reference_html before reporting a production bundle as passed."
        )
    reference = Path(v25_reference_html)
    if not reference.exists():
        raise OrchestrationError(f"V25 reference HTML not found: {reference}")
    runner = audit_runner or _load_default_smoke_audit(project_root)
    result = runner(project_root, slug, reference, forbid_pdf=forbid_pdf)
    payload = {
        "ok": bool(getattr(result, "ok", False)),
        "issues": _jsonable(getattr(result, "issues", [])),
        "metrics": _jsonable(getattr(result, "metrics", {})),
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "production_smoke_audit.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    if not payload["ok"]:
        codes = [
            str(issue.get("code", "unknown"))
            for issue in payload["issues"]
            if isinstance(issue, dict)
        ]
        raise OrchestrationError(
            "production smoke audit failed; cannot report production smoke pass. "
            f"Issue codes: {', '.join(codes) or 'unknown'}"
        )


def run(
    user_one_liner: str,
    project_root: Path,
    callbacks: Callbacks,
    *,
    skip_pdf: bool = True,
    skip_xlsx: bool = True,
    skip_visible_copy_audit: bool = False,
    require_rendered_mermaid: bool = False,
    min_pubmed_sources: int = DEFAULT_MIN_PUBMED_SOURCES,
    report_output_dir: Path | None = None,
    v25_reference_html: Path | None = None,
    require_production_smoke_audit: bool | None = None,
    slug: str | None = None,
) -> dict[str, Any]:
    """Entry point. Returns delivery_manifest dict.

    Unit/dry-run callers may keep the default skips. Production callers must
    pass skip_pdf=False and skip_xlsx=False so bundle generation fails closed.
    """
    project_root = Path(project_root).resolve()

    # Phase 1: Contract — resume if existing contract.json found in any .cache slug
    cache_root = project_root / ".cache"
    existing_contract: Path | None = None
    if slug:
        candidate = cache_root / slug / "contract.json"
        if candidate.exists():
            existing_contract = candidate
        else:
            raise OrchestrationError(
                f"requested slug {slug!r} has no contract.json at {candidate}; "
                "run the plugin bootstrap/source bridge for this slug first"
            )
    elif cache_root.exists():
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
    orchestration_trace = _new_trace(slug_dir)
    _write_trace(slug_dir, orchestration_trace)

    # Phase 2: Stratification (requires guidelines first)
    if not (slug_dir / "staging.json").exists():
        if "fetch_guidelines" in callbacks:
            callbacks["fetch_guidelines"](slug_dir)
        if "ask_llm_stratify" not in callbacks:
            raise OrchestrationError("callback ask_llm_stratify required for phase 2")
        stratify(slug_dir, ask_llm=callbacks["ask_llm_stratify"])
    _record_trace_phase(
        slug_dir,
        orchestration_trace,
        skill="disease-stratifier",
        evidence=slug_dir / "staging.json",
        mode="generated" if (slug_dir / "staging.json").exists() else "unknown",
    )

    # Phase 3: Evidence Recall — populate sources/pubmed/ if missing
    sources_dir = slug_dir / "sources"
    sources_pubmed = sources_dir / "pubmed"
    if not sources_pubmed.exists() or not any(sources_pubmed.glob("*.json")):
        if "recall_evidence" in callbacks:
            callbacks["recall_evidence"](slug_dir)
    pubmed_count = _count_pubmed_sources(slug_dir)
    if pubmed_count < min_pubmed_sources:
        raise OrchestrationError(
            "PubMed evidence recall is insufficient: "
            f"{pubmed_count} saved abstracts < required {min_pubmed_sources}. "
            "Run multi-channel evidence recall before compose; the PubMed floor is not "
            "the total source target, and production smoke requires >=50 saved non-raw "
            "sources plus >=5 logged retrieval channels."
        )
    evidence_recall_path = _best_existing_evidence(
        slug_dir,
        [
            "pubmed_recall_manifest.json",
            "europepmc_recall_manifest.json",
            "clinical_trials_recall_manifest.json",
        ],
        sources_dir,
    )
    _record_trace_phase(
        slug_dir,
        orchestration_trace,
        skill="evidence-recall",
        evidence=evidence_recall_path,
        pubmed_count=pubmed_count,
    )

    # Phase 4: Compose-then-Audit (≤ MAX_AUDIT_TURNS turns)
    if "ask_llm_compose" not in callbacks:
        raise OrchestrationError("callback ask_llm_compose required for phase 4")
    production_semantic_required = bool(callbacks.get("enforce_ifi", False)) or bool(
        require_production_smoke_audit
    )
    if production_semantic_required and callbacks.get("ask_llm_semantic") is None:
        raise OrchestrationError(
            "Production report generation requires semantic verification; "
            "provide ask_llm_semantic so claim -> anchor -> source support fails closed."
        )
    if production_semantic_required:
        _assert_production_retrieval_contract(slug_dir)

    semantic_audit_log_path = slug_dir / "semantic_audit_log.jsonl"
    if semantic_audit_log_path.exists():
        semantic_audit_log_path.unlink()

    previous_violations: list[dict] = []
    final_verdict: dict | None = None
    last_failure_reason: str = ""
    output_dir = Path(report_output_dir) if report_output_dir is not None else project_root / "output" / slug_dir.name
    composed_report: Any | None = None
    for turn in range(1, MAX_AUDIT_TURNS + 1):
        try:
            composed_report = compose(
                slug_dir,
                ask_llm=callbacks["ask_llm_compose"],
                previous_violations=previous_violations or None,
                enforce_ifi=bool(callbacks.get("enforce_ifi", False)),
                output_dir=output_dir,
                return_report=True,
            )
            html_path = composed_report.html_path
            if html_path is None:
                raise ComposeError("compose returned no html_path")
            _record_trace_phase(
                slug_dir,
                orchestration_trace,
                skill="cite-bound-content-generator",
                evidence=composed_report.citations_index_path or html_path,
                turn=turn,
                html_path=html_path,
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
                "calls_remaining": PRODUCTION_SEMANTIC_AUDIT_CALL_BUDGET,
                "audit_log_path": slug_dir / "semantic_audit_log.jsonl",
            }
        else:
            budget_state = None
        verify_kwargs = {
            "ask_llm_semantic": ask_llm_semantic,
            "budget_state": budget_state,
            "source_manifest_path": (
                slug_dir / "source_manifest.json"
                if (slug_dir / "source_manifest.json").exists()
                else None
            ),
            "required_source_channels": ("clinical_trials", "pubtator"),
        }
        report_audit_layer = getattr(composed_report, "audit_layer", None)
        if isinstance(report_audit_layer, dict):
            verify_kwargs["audit_layer"] = report_audit_layer
        verdict = verify_full_report(
            composed_report.raw_html or html_path.read_text(encoding="utf-8"),
            sources_dir,
            **verify_kwargs,
        )
        verdict_payload = {
            "verdict": verdict["verdict"],
            "violations": verdict["violations"],
            "verified_count": verdict.get("verified_count", 0),
            "anchor_audit": verdict.get("anchor_audit", {}),
            "turn_count": turn,
            "version": "1.0",
        }
        if budget_state is not None and budget_state.get("audit_log_path") is not None:
            semantic_audit_log = Path(budget_state["audit_log_path"])
            try:
                audit_log_path = str(semantic_audit_log.relative_to(slug_dir))
            except ValueError:
                audit_log_path = str(semantic_audit_log)
            verdict_payload["semantic_audit"] = {
                "audit_log_path": audit_log_path,
                "audit_log_entries": _count_nonempty_lines(semantic_audit_log),
                "calls_remaining": int(budget_state.get("calls_remaining", 0)),
                "call_budget": PRODUCTION_SEMANTIC_AUDIT_CALL_BUDGET,
            }
        (slug_dir / "verification_report.json").write_text(
            json.dumps(verdict_payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        if verdict["verdict"] == "ok":
            final_verdict = verdict
            _record_trace_phase(
                slug_dir,
                orchestration_trace,
                skill="content-verification-layer",
                evidence=slug_dir / "verification_report.json",
                turn=turn,
                verified_count=verdict.get("verified_count", 0),
            )
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

    gate_html = (
        composed_report.raw_html
        if composed_report is not None and getattr(composed_report, "raw_html", None)
        else html_path.read_text(encoding="utf-8")
    )
    citation_gate = _run_citation_anchor_resolution_gate(
        slug_dir,
        gate_html,
        sources_dir,
        audit_layer=getattr(composed_report, "audit_layer", None),
    )
    if not citation_gate.get("ok"):
        _record_trace_phase(
            slug_dir,
            orchestration_trace,
            skill="citation-anchor-resolver",
            evidence=slug_dir / "citation_anchor_resolution_report.json",
            status="blocked",
            unresolved_count=citation_gate.get("unresolved_count", 0),
        )
        raise OrchestrationError(
            "citation-anchor-resolver blocked report: unresolved citation anchors "
            f"{citation_gate.get('unresolved', [])[:8]}"
        )
    _record_trace_phase(
        slug_dir,
        orchestration_trace,
        skill="citation-anchor-resolver",
        evidence=slug_dir / "citation_anchor_resolution_report.json",
        unique_anchor_count=citation_gate.get("unique_anchor_count", 0),
        resolved_unique_count=citation_gate.get("resolved_unique_count", 0),
    )

    drug_gate = _run_drug_citation_gate(
        slug_dir,
        gate_html,
        sources_dir,
        audit_layer=getattr(composed_report, "audit_layer", None),
    )
    if not drug_gate.get("ok") or drug_gate.get("violation_severity") == "critical":
        _record_trace_phase(
            slug_dir,
            orchestration_trace,
            skill="drug-citation-verifier",
            evidence=slug_dir / "drug_citation_verification.json",
            status="blocked",
            violation_severity=drug_gate.get("violation_severity"),
            mention_count=len(drug_gate.get("drug_mentions", []) or []),
        )
        failed_mentions = [
            mention for mention in (drug_gate.get("drug_mentions", []) or [])
            if isinstance(mention, dict) and not mention.get("verified")
        ]
        raise OrchestrationError(
            "drug-citation-verifier blocked report: drug mentions are not source-supported "
            f"{failed_mentions[:8]}"
        )
    _record_trace_phase(
        slug_dir,
        orchestration_trace,
        skill="drug-citation-verifier",
        evidence=slug_dir / "drug_citation_verification.json",
        violation_severity=drug_gate.get("violation_severity"),
        mention_count=len(drug_gate.get("drug_mentions", []) or []),
    )

    # Phase 4.5 (R3c Phase-2-Quality-Fix): extract Mermaid blocks → PNG via mmdc.
    # graceful fallback: render_mermaid_to_png ok=False → 保留 inline <div class="mermaid"> 不阻塞.
    if (output_dir / "report_raw.html").exists():
        report_path = output_dir / "report_raw.html"
        report_html = report_path.read_text(encoding="utf-8")
        mermaid_blocks = list(_MERMAID_BLOCK_RE.finditer(report_html))
        assets_dir = output_dir / "assets"
        render_failures: list[str] = []
        render_results: list[dict[str, Any]] = []
        for i, match in enumerate(mermaid_blocks):
            block = match.group("body")
            png_path = assets_dir / f"decision-tree-{i}.png"
            if render_mermaid_to_png is None:
                result = {
                    "ok": False,
                    "reason": "mermaid-renderer skill is not installed",
                }
            else:
                result = render_mermaid_to_png(block, png_path)
            render_entry = {
                "index": i,
                "ok": bool(result.get("ok")),
                "path": str(result.get("path") or png_path),
                "reason": str(result.get("reason") or ""),
                "source": block,
            }
            render_entry.update(
                _mermaid_manifest_metrics(
                    block,
                    reader_audit_mode=isinstance(
                        getattr(composed_report, "audit_layer", None),
                        dict,
                    ),
                )
            )
            render_results.append(render_entry)
            if result["ok"]:
                # 替换 inline Mermaid → <img>
                report_html = report_html.replace(
                    match.group(0),
                    f'<img src="assets/decision-tree-{i}.png" alt="decision tree {i}">',
                    1,
                )
            else:
                render_failures.append(str(result.get("reason") or "unknown error"))
        if require_rendered_mermaid and render_failures:
            raise OrchestrationError(
                "Mermaid rendering failed; production smoke requires rendered "
                f"decision-tree assets. Reasons: {render_failures}"
            )
        if mermaid_blocks:
            mermaid_manifest_path = slug_dir / "mermaid_render_manifest.json"
            mermaid_manifest_path.write_text(
                json.dumps(
                    {
                        "version": "1.0",
                        "renderer": "mermaid-renderer",
                        "ok": not render_failures,
                        "blocks": render_results,
                    },
                    ensure_ascii=False,
                    indent=2,
                    default=str,
                ),
                encoding="utf-8",
            )
            _record_trace_phase(
                slug_dir,
                orchestration_trace,
                skill="mermaid-renderer",
                evidence=mermaid_manifest_path,
                rendered_png_count=len([item for item in render_results if item.get("ok")]),
                render_failure_count=len(render_failures),
            )
            report_path.write_text(report_html, encoding="utf-8")

    # Phase 5: Bundle + Design + TOC
    # R3a/R3b: pass ComposedReport.sub_pages / toc_anchors through to builder.
    composed_sub_pages = getattr(composed_report, "sub_pages", None)
    composed_toc_anchors = getattr(composed_report, "toc_anchors", None)

    manifest = build_all_deliverables(
        slug_dir,
        project_root,
        skip_pdf=skip_pdf,
        skip_xlsx=skip_xlsx,
        skip_visible_copy_audit=skip_visible_copy_audit,
        output_dir=output_dir,
        sub_pages=composed_sub_pages,
        toc_anchors=composed_toc_anchors,
    )
    _record_trace_phase(
        slug_dir,
        orchestration_trace,
        skill="report-bundle-builder",
        evidence=output_dir / "delivery_manifest.json",
        skip_pdf=skip_pdf,
        skip_xlsx=skip_xlsx,
    )
    audit_required = (
        (not skip_pdf) or (not skip_xlsx)
        if require_production_smoke_audit is None
        else require_production_smoke_audit
    )
    if audit_required:
        orchestration_trace["status"] = "ok"
        orchestration_trace["completed_at"] = _now_iso()
        _write_trace(slug_dir, orchestration_trace)
        _embed_source_corpus_if_available(
            project_root=project_root,
            slug_dir=slug_dir,
            output_dir=output_dir,
        )
        _write_and_assert_production_smoke_audit(
            project_root=project_root,
            slug=slug_dir.name,
            output_dir=output_dir,
            v25_reference_html=v25_reference_html,
            forbid_pdf=skip_pdf,
            audit_runner=callbacks.get("audit_production_smoke"),
        )
    orchestration_trace["status"] = "ok"
    orchestration_trace["completed_at"] = _now_iso()
    _write_trace(slug_dir, orchestration_trace)
    return manifest
