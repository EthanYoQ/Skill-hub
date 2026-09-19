#!/usr/bin/env python3
"""Validate independent review artifacts for an article-style run."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


REQUIRED_REVIEWS = {
    "source-auditor": {
        "marker": "source-audit",
        "must_mention": ["source-fetch-log", "style-reference-corpus"],
    },
    "style-auditor": {
        "marker": "style-audit",
        "must_mention": ["style-mechanism-breakdown", "imitation-draft"],
    },
    "fact-auditor": {
        "marker": "fact-audit",
        "must_mention": ["evidence-ledger", "imitation-draft"],
    },
}

PLATFORM_REVIEW = {
    "platform-auditor": {
        "marker": "platform-audit",
        "must_mention": ["platform-patterns"],
    }
}

VALID_VERDICTS = {"pass", "revise", "block"}
BLOCKING_VERDICTS = {"revise", "block"}


def find_review_file(reviews_dir: Path, marker: str) -> Path | None:
    matches = sorted(
        path
        for path in reviews_dir.glob("*.md")
        if marker.lower() in path.name.lower()
    )
    return matches[0] if matches else None


def extract_field(text: str, field: str) -> str:
    pattern = re.compile(rf"^\s*[-*]?\s*`?{re.escape(field)}`?\s*[:：]\s*(.+)$", re.I | re.M)
    match = pattern.search(text)
    return match.group(1).strip() if match else ""


def validate_review(path: Path, expected_role: str, must_mention: list[str]) -> list[str]:
    findings: list[str] = []
    text = path.read_text(encoding="utf-8")
    lowered = text.lower()

    role = extract_field(text, "reviewer_role").lower()
    if role != expected_role:
        findings.append(
            f"{path.name}: reviewer_role is {role or '<missing>'}, expected {expected_role}"
        )

    verdict = extract_field(text, "verdict").lower()
    if verdict not in VALID_VERDICTS:
        findings.append(
            f"{path.name}: verdict is {verdict or '<missing>'}, expected PASS, REVISE, or BLOCK"
        )
    elif verdict in BLOCKING_VERDICTS:
        findings.append(f"{path.name}: unresolved verdict is {verdict.upper()}")

    for field in [
        "checked_files",
        "critical_findings",
        "required_changes",
        "independence_note",
    ]:
        if not extract_field(text, field):
            findings.append(f"{path.name}: missing field {field}")

    for marker in must_mention:
        if marker.lower() not in lowered:
            findings.append(f"{path.name}: checked_files must mention {marker}")

    return findings


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("run_directory", type=Path)
    parser.add_argument("--require-platform-review", action="store_true")
    args = parser.parse_args()

    run_dir = args.run_directory
    reviews_dir = run_dir / "reviews"
    findings: list[str] = []

    if not run_dir.exists() or not run_dir.is_dir():
        print(f"run directory not found: {run_dir}")
        return 1

    if not reviews_dir.exists() or not reviews_dir.is_dir():
        print(f"reviews directory not found: {reviews_dir}")
        return 1

    required = dict(REQUIRED_REVIEWS)
    if args.require_platform_review:
        required.update(PLATFORM_REVIEW)

    for role, spec in required.items():
        path = find_review_file(reviews_dir, spec["marker"])
        if path is None:
            findings.append(f"missing review file containing: {spec['marker']}")
            continue
        findings.extend(validate_review(path, role, spec["must_mention"]))

    if findings:
        print("\n".join(findings))
        return 1

    print(f"OK: independent review package is valid in {reviews_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
