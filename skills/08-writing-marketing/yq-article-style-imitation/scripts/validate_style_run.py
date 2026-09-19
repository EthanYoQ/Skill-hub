#!/usr/bin/env python3
"""Validate that an article-style run has real source and teardown scaffolding."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


REQUIRED_FILE_MARKERS = [
    "source-fetch-log",
    "style-reference-corpus",
    "style-mechanism-breakdown",
    "evidence-ledger",
    "imitation-draft",
]

VALID_STYLE_GRADES = {"a", "b"}
VALID_TEXT_YES = {"yes", "y", "true", "1", "是", "有"}
INVALID_ACCESS_MARKERS = [
    "404",
    "403",
    "blocked",
    "forbidden",
    "login",
    "snippet",
    "inaccessible",
    "failed",
    "not found",
]
INTERVIEW_SIGNALS = [
    r"我问他",
    r"我问她",
    r"后来他告诉我",
    r"后来她告诉我",
    r"他告诉我",
    r"她告诉我",
    r"他对我说",
    r"她对我说",
    r"“[^”]{1,80}”\s*他说",
    r"“[^”]{1,80}”\s*她说",
]
CASE_EVIDENCE_MARKERS = [
    "user-case",
    "interview",
    "访谈",
    "采访",
    "用户提供",
    "case notes",
    "transcript",
    "screenshot",
]


def find_marker_file(run_dir: Path, marker: str) -> Path | None:
    matches = sorted(
        path for path in run_dir.glob("*.md") if marker in path.name.lower()
    )
    return matches[0] if matches else None


def parse_markdown_table(path: Path) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    lines = path.read_text(encoding="utf-8").splitlines()
    header: list[str] | None = None

    for line in lines:
        stripped = line.strip()
        if not stripped.startswith("|") or not stripped.endswith("|"):
            continue
        cells = [cell.strip() for cell in stripped.strip("|").split("|")]
        if cells and all(re.fullmatch(r":?-{3,}:?", cell) for cell in cells):
            continue
        if header is None:
            header = [normalize_key(cell) for cell in cells]
            continue
        if len(cells) != len(header):
            continue
        rows.append(dict(zip(header, cells)))

    return rows


def normalize_key(value: str) -> str:
    return re.sub(r"[\s/\-]+", "_", value.strip().lower()).strip("_")


def get_field(row: dict[str, str], *names: str) -> str:
    lowered = {normalize_key(key): value for key, value in row.items()}
    for name in names:
        value = lowered.get(normalize_key(name))
        if value is not None:
            return value.strip()
    return ""


def split_source_ids(text: str) -> set[str]:
    return set(re.findall(r"\bS\d+\b", text))


def is_invalid_access(access_status: str) -> bool:
    lower = access_status.lower()
    return any(marker in lower for marker in INVALID_ACCESS_MARKERS)


def has_case_evidence(text: str) -> bool:
    lower = text.lower()
    return any(marker.lower() in lower for marker in CASE_EVIDENCE_MARKERS)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("run_directory", type=Path)
    parser.add_argument("--target-writer", action="append", default=[])
    parser.add_argument("--min-primary-per-writer", type=int, default=2)
    parser.add_argument("--allow-pseudo-documentary", action="store_true")
    args = parser.parse_args()

    run_dir = args.run_directory
    findings: list[str] = []

    if not run_dir.exists() or not run_dir.is_dir():
        findings.append(f"run directory not found: {run_dir}")
        print("\n".join(findings))
        return 1

    marker_files: dict[str, Path] = {}
    for marker in REQUIRED_FILE_MARKERS:
        path = find_marker_file(run_dir, marker)
        if path is None:
            findings.append(f"missing separate output file containing: {marker}")
        else:
            marker_files[marker] = path

    corpus_path = marker_files.get("style-reference-corpus")
    valid_style_source_ids: set[str] = set()
    invalid_style_source_ids: set[str] = set()

    if corpus_path is not None:
        rows = parse_markdown_table(corpus_path)
        if not rows:
            findings.append("style-reference-corpus has no parseable markdown table")

        required_columns = [
            "source_id",
            "target_writer",
            "role",
            "source_grade",
            "access_status",
            "text_available",
            "local_text_path",
            "byline",
            "authorship_evidence",
            "accepted_for",
        ]
        if rows:
            present = {key.lower() for key in rows[0].keys()}
            for column in required_columns:
                if column not in present:
                    findings.append(
                        f"style-reference-corpus missing required column: {column}"
                    )

        style_rows: list[dict[str, str]] = []
        for row in rows:
            source_id = get_field(row, "source_id")
            writer = get_field(row, "target_writer")
            accepted_for = get_field(row, "accepted_for").lower()
            role = get_field(row, "role").lower()
            grade = get_field(row, "source_grade").lower()
            access_status = get_field(row, "access_status")
            text_available = get_field(row, "text_available").lower()
            local_text_path = get_field(row, "local_text_path")
            byline = get_field(row, "byline") or get_field(row, "author")
            authorship_evidence = get_field(row, "authorship_evidence")

            wants_style = "style" in accepted_for or "primary-style-source" in role
            if not wants_style:
                continue

            style_rows.append(row)
            row_findings: list[str] = []

            if grade not in VALID_STYLE_GRADES:
                row_findings.append(f"grade {grade or '<blank>'} is not A/B")
            if is_invalid_access(access_status):
                row_findings.append(f"access_status is not usable: {access_status}")
            if text_available not in VALID_TEXT_YES:
                row_findings.append("text_available is not yes")
            if not byline:
                row_findings.append("byline is blank")
            elif writer and writer.lower() not in byline.lower():
                row_findings.append(f"byline does not identify target writer: {byline}")
            if not authorship_evidence:
                row_findings.append("authorship_evidence is blank")
            if not local_text_path:
                row_findings.append("local_text_path is blank")
            else:
                local_path = Path(local_text_path)
                if not local_path.is_absolute():
                    local_path = run_dir / local_path
                if not local_path.exists():
                    row_findings.append(f"local_text_path does not exist: {local_path}")
                elif len(local_path.read_text(encoding="utf-8").strip()) < 800:
                    row_findings.append(
                        f"local_text_path has less than 800 chars: {local_path}"
                    )

            if row_findings:
                invalid_style_source_ids.add(source_id)
                findings.append(
                    f"{source_id or '<missing source_id>'}: invalid style source "
                    f"for {writer or '<missing writer>'}: {'; '.join(row_findings)}"
                )
            else:
                valid_style_source_ids.add(source_id)

        writers = args.target_writer or []
        for writer in writers:
            count = 0
            for row in style_rows:
                source_id = get_field(row, "source_id")
                if source_id in valid_style_source_ids and writer in get_field(
                    row, "target_writer"
                ):
                    count += 1
            if count < args.min_primary_per_writer:
                findings.append(
                    f"{writer}: only {count} valid style source rows; "
                    f"need {args.min_primary_per_writer} or explicit user approval"
                )

    breakdown_path = marker_files.get("style-mechanism-breakdown")
    if breakdown_path is not None:
        breakdown = breakdown_path.read_text(encoding="utf-8")
        if not re.search(r"\bS\d+\b|source_id|语料ID|来源ID", breakdown):
            findings.append(
                "style-mechanism-breakdown has no source-id traceability markers"
            )
        referenced_ids = split_source_ids(breakdown)
        bad_refs = sorted(source_id for source_id in referenced_ids if source_id in invalid_style_source_ids)
        if bad_refs:
            findings.append(
                "style-mechanism-breakdown references invalid style sources: "
                + ", ".join(bad_refs)
            )
        unknown_refs = sorted(
            source_id
            for source_id in referenced_ids
            if source_id not in valid_style_source_ids
            and source_id not in invalid_style_source_ids
        )
        if unknown_refs:
            findings.append(
                "style-mechanism-breakdown references unknown source IDs: "
                + ", ".join(unknown_refs)
            )

    draft_path = marker_files.get("imitation-draft")
    evidence_path = marker_files.get("evidence-ledger")
    if draft_path is not None:
        draft = draft_path.read_text(encoding="utf-8")
        interview_hits = [
            pattern for pattern in INTERVIEW_SIGNALS if re.search(pattern, draft)
        ]
        if interview_hits and not args.allow_pseudo_documentary:
            evidence_text = (
                evidence_path.read_text(encoding="utf-8")
                if evidence_path is not None
                else ""
            )
            if not has_case_evidence(evidence_text):
                findings.append(
                    "imitation-draft contains interview/reportage signals without "
                    "user-case or interview evidence: "
                    + ", ".join(interview_hits)
                )

    if findings:
        print("\n".join(findings))
        return 1

    print(f"OK: style run scaffolding is valid in {run_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
