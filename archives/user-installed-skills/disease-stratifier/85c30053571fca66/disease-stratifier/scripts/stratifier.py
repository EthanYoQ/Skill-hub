"""Phase 2 · disease-stratifier: cite-based stratification dimension discovery.

P0 守门: NEVER use built-in stratification templates. ALL dimensions must cite
guideline sections actually present in sources/guidelines/.
"""
from __future__ import annotations
import json
import re
import sys
from pathlib import Path
from typing import Any, Callable

# Add contract-elicitor to path for assert_contract_complete
_HERE = Path(__file__).resolve()
_CONTRACT_ELICITOR_SCRIPTS = _HERE.parents[2] / "contract-elicitor" / "scripts"
if str(_CONTRACT_ELICITOR_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_CONTRACT_ELICITOR_SCRIPTS))
from elicitor import assert_contract_complete  # noqa: E402


class StratificationError(Exception):
    """Raised when stratification produces invalid output."""


_ANCHOR_RE = re.compile(
    r"^\[(guideline|pmid|nct|aact|nmpa-page|evidence):([^\]]+)\]$"
)

_VALID_DISPOSITIONS = {
    "CORE_SUBPAGE",
    "SECONDARY_SUBPAGE",
    "CROSS_CUTTING_LP",
    "EVIDENCE_RADAR",
    "REJECTED",
}
_VALID_BRANCH_TYPES = {
    "patient_pool",
    "diagnostic_infrastructure",
    "risk_factor",
    "evidence_radar",
    "cross_cutting_workflow",
}
_NON_PATIENT_POOL_TYPES = {
    "diagnostic_infrastructure",
    "risk_factor",
    "evidence_radar",
    "cross_cutting_workflow",
}
_VALID_OWNERSHIP_STRENGTHS = {"strong", "partial", "weak"}
_BRANCH_REQUIRED_FIELDS = (
    "slug",
    "title",
    "branch_type",
    "disposition",
)
_SUBPAGE_REQUIRED_FIELDS = (
    "independent_patient_pool",
    "drug_class_strategy",
    "pharma_actionability",
    "drug_class_relevance",
    "market_sizing_feasibility",
    "respiratory_ownership_strength",
    "market_value_summary",
    "respiratory_or_target_department_ownership",
    "actions",
)
_ACTION_REQUIRED_FIELDS = ("trigger", "owner", "pharma_action", "material_output", "kpi")


def _parse_anchor(anchor: str) -> tuple[str, str]:
    m = _ANCHOR_RE.match(anchor)
    if not m:
        raise StratificationError(f"Malformed citation anchor: {anchor!r}")
    return m.group(1), m.group(2)


def _verify_anchor_resolves(anchor: str, sources_dir: Path) -> bool:
    """Check that the anchor's source_id has a backing file in sources/."""
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
    if src_type == "evidence":
        locator_path = locator.split(":line:", 1)[0]
        normalized = locator_path.replace("\\", "/")
        candidates = [normalized]
        if "/sources/" in normalized:
            candidates.append(normalized.split("/sources/", 1)[1])
        return any((sources_dir / candidate).exists() for candidate in candidates)
    return False  # unknown types: conservative


def _nonempty(value: Any) -> bool:
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, list):
        return bool(value) and all(_nonempty(item) for item in value)
    return value is not None


def _normalize_llm_result(raw: Any) -> tuple[list[dict], list[dict]]:
    if isinstance(raw, list):
        return raw, []
    if isinstance(raw, dict):
        raw_dims = raw.get("dimensions")
        raw_scorecard = raw.get("branch_scorecard", [])
        if not isinstance(raw_dims, list):
            raise StratificationError(f"LLM returned no dimensions: {raw!r}")
        if raw_scorecard is None:
            raw_scorecard = []
        if not isinstance(raw_scorecard, list):
            raise StratificationError("branch_scorecard must be a list when provided")
        return raw_dims, [item for item in raw_scorecard if isinstance(item, dict)]
    raise StratificationError(f"LLM returned no dimensions: {raw!r}")


def _validate_branch_scorecard(scorecard: list[dict]) -> list[dict]:
    validated: list[dict] = []
    for index, branch in enumerate(scorecard):
        missing = [
            field for field in _BRANCH_REQUIRED_FIELDS
            if not _nonempty(branch.get(field))
        ]
        if branch.get("disposition") not in _VALID_DISPOSITIONS:
            missing.append("disposition")
        if branch.get("branch_type") not in _VALID_BRANCH_TYPES:
            missing.append("branch_type")
        if branch.get("disposition") in {"CORE_SUBPAGE", "SECONDARY_SUBPAGE"}:
            missing.extend(
                field for field in _SUBPAGE_REQUIRED_FIELDS
                if not _nonempty(branch.get(field))
            )
            if branch.get("independent_patient_pool") is not True:
                missing.append("independent_patient_pool")
            if not _nonempty(branch.get("drug_class_strategy")):
                missing.append("drug_class_strategy")
            if branch.get("pharma_actionability") is not True:
                missing.append("pharma_actionability")
            if branch.get("drug_class_relevance") is not True:
                missing.append("drug_class_relevance")
            if branch.get("market_sizing_feasibility") is not True:
                missing.append("market_sizing_feasibility")
            if branch.get("respiratory_ownership_strength") not in _VALID_OWNERSHIP_STRENGTHS:
                missing.append("respiratory_ownership_strength")
            actions = branch.get("actions")
            if not isinstance(actions, list):
                missing.append("actions")
            else:
                for action_index, action in enumerate(actions):
                    if not isinstance(action, dict):
                        missing.append(f"actions[{action_index}]")
                        continue
                    for field in _ACTION_REQUIRED_FIELDS:
                        if not _nonempty(action.get(field)):
                            missing.append(f"actions[{action_index}].{field}")
        if missing:
            raise StratificationError(
                f"branch_scorecard[{index}] missing or invalid fields: {sorted(set(missing))}"
            )
        if branch.get("disposition") in {"CORE_SUBPAGE", "SECONDARY_SUBPAGE"} and branch.get("branch_type") != "patient_pool":
            raise StratificationError(
                "SUBPAGE dispositions require a patient_pool branch; diagnostic infrastructure, "
                "risk factors, evidence radar, and cross-cutting workflows must be "
                "downgraded unless they prove an independent patient pool and drug-class strategy."
            )
        if (
            branch.get("disposition") == "CORE_SUBPAGE"
            and branch.get("respiratory_ownership_strength") != "strong"
        ):
            raise StratificationError(
                "CORE_SUBPAGE requires strong respiratory_or_target_department_ownership."
            )
        clean_branch = {
            "slug": branch["slug"],
            "title": branch["title"],
            "branch_type": branch["branch_type"],
            "disposition": branch["disposition"],
        }
        for optional_field in _SUBPAGE_REQUIRED_FIELDS:
            if optional_field in branch:
                clean_branch[optional_field] = branch[optional_field]
        validated.append(clean_branch)
    return validated


def stratify(
    slug_dir: Path,
    ask_llm: Callable[[dict, str], Any],
) -> Path:
    """Phase 2 entrypoint.

    1. Hard precondition: contract.json complete.
    2. Read sources/guidelines/*.txt (must be populated by A1' v2 pre-call from orchestrator).
    3. Ask LLM to propose stratification dimensions cited to guideline sections.
    4. Validate each dimension has anchor + anchor resolves to actual source file.
    5. Write staging.json.

    `ask_llm(contract, guidelines_summary) -> list[dimension dict]`.
    """
    contract_path = slug_dir / "contract.json"
    assert_contract_complete(contract_path)
    contract = json.loads(contract_path.read_text(encoding="utf-8"))

    sources_dir = slug_dir / "sources"
    guideline_dir = sources_dir / "guidelines"
    if not guideline_dir.exists() or not any(guideline_dir.glob("*.txt")):
        raise StratificationError(
            f"No guidelines fetched in {guideline_dir}. "
            f"Run cn-clinical-guidelines-fetch (A1' v2) before stratify."
        )

    # build guideline summary for LLM
    summary_lines: list[str] = []
    for txt in sorted(guideline_dir.glob("*.txt")):
        summary_lines.append(f"## {txt.stem}\n{txt.read_text(encoding='utf-8')[:4000]}")
    guidelines_summary = "\n\n".join(summary_lines)

    raw_result = ask_llm(contract, guidelines_summary)
    raw_dims, raw_scorecard = _normalize_llm_result(raw_result)
    if not isinstance(raw_dims, list) or not raw_dims:
        raise StratificationError(f"LLM returned no dimensions: {raw_dims!r}")

    validated: list[dict] = []
    for dim in raw_dims:
        if "citation_anchor" not in dim:
            raise StratificationError(
                f"Dimension {dim.get('name')!r} missing citation_anchor (P0 violation)"
            )
        if not _verify_anchor_resolves(dim["citation_anchor"], sources_dir):
            raise StratificationError(
                f"Anchor {dim['citation_anchor']} does not resolve to any file in "
                f"{sources_dir}. Source must be present in sources/."
            )
        if not dim.get("sub_cohorts") or not isinstance(dim["sub_cohorts"], list):
            raise StratificationError(
                f"Dimension {dim.get('name')!r} must have non-empty sub_cohorts list"
            )
        validated.append({
            "name": dim["name"],
            "citation_anchor": dim["citation_anchor"],
            "sub_cohorts": dim["sub_cohorts"],
        })

    staging: dict[str, Any] = {"dimensions": validated, "version": "1.0"}
    if raw_scorecard:
        staging["branch_scorecard"] = _validate_branch_scorecard(raw_scorecard)
    staging_path = slug_dir / "staging.json"
    staging_path.write_text(
        json.dumps(staging, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return staging_path
