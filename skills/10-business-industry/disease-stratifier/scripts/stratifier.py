"""Phase 2 · disease-stratifier: cite-based stratification dimension discovery.

P0 守门: NEVER use built-in stratification templates. ALL dimensions must cite
guideline sections actually present in sources/guidelines/.
"""
from __future__ import annotations
import json
import re
import sys
from pathlib import Path
from typing import Callable

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
    return False  # unknown types: conservative


def stratify(
    slug_dir: Path,
    ask_llm: Callable[[dict, str], list[dict]],
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

    raw_dims = ask_llm(contract, guidelines_summary)
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

    staging = {"dimensions": validated, "version": "1.0"}
    staging_path = slug_dir / "staging.json"
    staging_path.write_text(
        json.dumps(staging, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return staging_path
