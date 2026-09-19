"""A12 · Session resume: scan .cache/<slug>/ to determine which phase to run next."""
from __future__ import annotations
import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class PhaseState:
    last_completed_phase: int  # 0 (nothing) .. 5 (all done)
    next_phase: int            # 1 .. 6 (6 == nothing to do)
    reason: str

    @property
    def all_done(self) -> bool:
        return self.last_completed_phase >= 5


_PHASE_NAMES = {
    1: "Contract Elicitation",
    2: "Disease Stratification",
    3: "Evidence Recall",
    4: "Compose-then-Audit",
    5: "Bundle + Design + TOC",
}


def detect_partial_state(slug_dir: Path) -> PhaseState:
    """Inspect .cache/<slug>/ directory and infer phase progress.

    Returns PhaseState with last_completed_phase 0..5, next_phase 1..6.
    """
    if not slug_dir.exists():
        return PhaseState(0, 1, "cache directory missing")

    last = 0
    if (slug_dir / "contract.json").exists():
        last = 1
    if last == 1 and (slug_dir / "staging.json").exists():
        last = 2
    sources_dir = slug_dir / "sources"
    if last == 2 and sources_dir.exists() and any(sources_dir.iterdir()):
        last = 3
    output_dir = slug_dir.parent.parent / "output"
    if (
        last == 3
        and (slug_dir / "citations_index.json").exists()
        and (slug_dir / "verification_report.json").exists()
    ):
        try:
            verification = json.loads(
                (slug_dir / "verification_report.json").read_text(encoding="utf-8")
            )
            if verification.get("verdict") == "ok":
                last = 4
        except (json.JSONDecodeError, OSError):
            pass  # 损坏的 verification 视为 phase 4 未完成
    if last == 4 and output_dir.exists() and (output_dir / "delivery_manifest.json").exists():
        last = 5

    next_phase = last + 1 if last < 5 else 6
    reason = (
        "all phases complete"
        if last == 5
        else f"last completed: phase {last}, next: phase {next_phase} ({_PHASE_NAMES.get(next_phase, '<done>')})"
    )
    return PhaseState(last, next_phase, reason)


def resume_from(slug_dir: Path) -> str:
    """Human-readable resume message for users."""
    state = detect_partial_state(slug_dir)
    if state.all_done:
        return f"All 5 phases complete for {slug_dir.name}. Output ready."
    return f"Resuming {slug_dir.name}: phase {state.next_phase} ({_PHASE_NAMES[state.next_phase]}). Reason: {state.reason}."


import shutil


# Field → list of cache artifacts to clear when this contract field changes.
# 'sources' (str) means the sources/ directory tree.
INVALIDATION_RULES: dict[str, tuple[str, ...]] = {
    "disease": (
        "contract.json", "staging.json", "sources",
        "citations_index.json", "verification_report.json",
    ),
    "geography": (
        "contract.json", "staging.json", "sources",
        "citations_index.json", "verification_report.json",
    ),
    "locale": (
        "staging.json", "sources",
        "citations_index.json", "verification_report.json",
    ),
    "evidence_window": (
        "sources",
        "citations_index.json", "verification_report.json",
    ),
    "include_intl_comparison": (
        "sources",
        "citations_index.json", "verification_report.json",
    ),
    "report_depth": (
        "citations_index.json", "verification_report.json",
    ),
    "user_role": (
        "citations_index.json", "verification_report.json",
    ),
}


def invalidate_dependents(slug_dir: Path, changed_field: str) -> list[Path]:
    """Precisely invalidate cache artifacts dependent on a changed contract field.

    Returns the list of paths that were removed.
    """
    if changed_field not in INVALIDATION_RULES:
        return []
    if not slug_dir.exists():
        return []

    removed: list[Path] = []
    for target in INVALIDATION_RULES[changed_field]:
        target_path = slug_dir / target
        if target_path.is_file():
            target_path.unlink()
            removed.append(target_path)
        elif target_path.is_dir():
            shutil.rmtree(target_path)
            removed.append(target_path)
    return removed
