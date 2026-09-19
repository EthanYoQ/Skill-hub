"""Phase 5 · report-bundle-builder (upgraded): force design-injector + verdict assertion + TOC assertion."""
from __future__ import annotations
import base64
from html.parser import HTMLParser
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


_HERE = Path(__file__).resolve()
_RBB_SCRIPTS = _HERE.parent
if str(_RBB_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_RBB_SCRIPTS))
_DSI_SCRIPTS = _HERE.parents[2] / "design-system-injector" / "scripts"
if str(_DSI_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_DSI_SCRIPTS))
from injector import inject, validate_design, DESIGN_TOKENS  # noqa: E402
from build_pdf import build_pdf as _render_pdf  # noqa: E402
from build_xlsx import build_xlsx as _render_xlsx  # noqa: E402


_PLACEHOLDER_PDF = b"%PDF-1.4 placeholder"
_PLACEHOLDER_XLSX = b"PK\x03\x04 placeholder"
_VISIBLE_COPY_LEAK_TERMS = (
    "todo",
    "dry-run",
    "fake callback",
    "placeholder",
    "lorem ipsum",
    "as an ai",
    "占位",
    "待补",
    "待完善",
    "待定",
)
_REPORT_SUBSTANCE_BLOCK_TERMS = (
    "后续量化模型",
    "待 worker",
    "worker b",
    "deferred worker",
    "deferred model",
)


class BundleError(Exception):
    pass


class _VisibleTextParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._skip_depth = 0
        self.parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() in {"script", "style", "noscript"}:
            self._skip_depth += 1

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() in {"script", "style", "noscript"} and self._skip_depth:
            self._skip_depth -= 1

    def handle_data(self, data: str) -> None:
        if not self._skip_depth and data.strip():
            self.parts.append(data)

    @property
    def visible_text(self) -> str:
        return " ".join(self.parts)


def _assert_verdict_ok(slug_dir: Path) -> None:
    vr = slug_dir / "verification_report.json"
    if not vr.exists():
        raise BundleError(f"verification_report.json not found in {slug_dir}")
    payload = json.loads(vr.read_text(encoding="utf-8"))
    if payload.get("verdict") != "ok":
        raise BundleError(
            f"verdict is {payload.get('verdict')!r}, not 'ok'. "
            f"Phase 4 audit failed; cannot proceed to bundle."
        )


def _assert_visible_copy_clean(html: str, source_label: str) -> None:
    parser = _VisibleTextParser()
    parser.feed(html)
    visible = parser.visible_text.lower()
    leaks = [term for term in _VISIBLE_COPY_LEAK_TERMS if term in visible]
    if leaks:
        raise BundleError(
            "visible copy leak detected in "
            f"{source_label}: {', '.join(sorted(set(leaks)))}"
        )


def _visible_copy_leaks(html: str) -> list[str]:
    parser = _VisibleTextParser()
    parser.feed(html)
    visible = parser.visible_text.lower()
    return sorted(set(term for term in _VISIBLE_COPY_LEAK_TERMS if term in visible))


def _assert_report_substance_clean(
    html: str,
    source_label: str,
    *,
    reader_audit_mode: bool = False,
) -> None:
    parser = _VisibleTextParser()
    parser.feed(html)
    visible = re.sub(r"\s+", " ", parser.visible_text)
    visible_lower = visible.lower()
    reasons: list[str] = []

    if "来源类别 Source ID 索引状态" in visible or visible.count("已保存") >= 6:
        reasons.append("source inventory/process filler")

    deferred_terms = [
        term for term in _REPORT_SUBSTANCE_BLOCK_TERMS if term.lower() in visible_lower
    ]
    if deferred_terms:
        reasons.append(f"deferred worker/model language: {', '.join(deferred_terms)}")

    if source_label.startswith("sub_page:"):
        h2_h3 = len(re.findall(r"<h[23]\b", html, re.I))
        anchors = len(re.findall(r"\[(?:guideline|pmid|nct|aact|nmpa-page|evidence):[^\]]+\]", html))
        tables = len(re.findall(r"<table\b", html, re.I))
        evidence_badges = len(re.findall(r"\bevidence-badge\b|data-evidence-badge=", html, re.I))
        if (
            len(visible) < 500
            or h2_h3 < 1
            or tables < 1
            or (anchors < 1 and not (reader_audit_mode and evidence_badges >= 1))
        ):
            reasons.append(
                "shallow sub-page: requires substantive visible copy, H2/H3, table, and citation/evidence badge"
            )

    for block in re.findall(r'<div\s+class=["\']mermaid["\'][^>]*>(.*?)</div>', html, re.I | re.S):
        arrows = len(re.findall(r"(?:-->|---|\-\.)", block))
        semantic_lines = [
            line.strip()
            for line in block.splitlines()
            if line.strip() and not line.strip().lower().startswith(("flowchart", "graph "))
        ]
        if arrows < 2 or len(semantic_lines) < 3:
            reasons.append("shallow Mermaid block")
            break

    if reasons:
        raise BundleError(
            f"report substance gate failed for {source_label}: "
            f"{'; '.join(reasons)}"
        )


def _assert_not_placeholder(path: Path, marker: bytes, label: str) -> None:
    payload = path.read_bytes()
    if payload == marker or marker in payload[:128]:
        raise BundleError(f"placeholder {label} output is not allowed in production bundle mode")


def _artifact_manifest(path: Path, label: str, marker: bytes | None = None) -> dict[str, Any]:
    validation: dict[str, Any] = {"exists": path.exists(), "placeholder_checked": marker is not None}
    if marker is not None:
        payload = path.read_bytes()
        placeholder_found = payload == marker or marker in payload[:128]
        validation["placeholder_found"] = placeholder_found
        if placeholder_found:
            raise BundleError(f"placeholder {label} output is not allowed in production bundle mode")
    elif label.upper() == "HTML":
        html = path.read_text(encoding="utf-8", errors="ignore")
        leaks = _visible_copy_leaks(html)
        validation["placeholder_checked"] = True
        validation["placeholder_found"] = bool(leaks)
        validation["placeholder_terms"] = leaks
        if leaks:
            raise BundleError(f"placeholder {label} output is not allowed in production bundle mode: {leaks}")
    return {
        "ok": True,
        "out_path": str(path),
        "size_bytes": path.stat().st_size,
        "size_mb": round(path.stat().st_size / 1024 / 1024, 4),
        "validation": validation,
    }


def _inline_pngs(html: str, base_dir: Path) -> tuple[str, int]:
    pattern = re.compile(r'<img\s+([^>]*?)src="([^"]+\.png)"([^>]*)>', re.IGNORECASE)
    count = 0

    def repl(m: re.Match[str]) -> str:
        nonlocal count
        pre, src, post = m.group(1), m.group(2), m.group(3)
        png = (base_dir / src).resolve()
        if not png.exists():
            return m.group(0)
        b64 = base64.b64encode(png.read_bytes()).decode("ascii")
        count += 1
        return f'<img {pre}src="data:image/png;base64,{b64}"{post}>'

    return pattern.sub(repl, html), count


def build_standalone_html(raw_html_path: Path, output_dir: Path) -> Path:
    html = raw_html_path.read_text(encoding="utf-8")
    injected = inject(html, DESIGN_TOKENS)

    report = validate_design(injected)
    if report["toc_block"]:
        raise BundleError(
            f"Floating TOC li count {report['toc_li_count']} < 5 (B3 守门). "
            f"Headings in report are insufficient. Add more <h2 id> sections."
        )

    inlined, _ = _inline_pngs(injected, raw_html_path.parent)
    out = output_dir / "report_standalone.html"
    out.write_text(inlined, encoding="utf-8")
    return out


def _html_body_fragment(html: str) -> str:
    body = re.search(r"<body\b[^>]*>(.*?)</body>", html, re.I | re.S)
    fragment = body.group(1) if body else html
    fragment = re.sub(r"<!doctype[^>]*>", "", fragment, flags=re.I)
    fragment = re.sub(r"<head\b[^>]*>.*?</head>", "", fragment, flags=re.I | re.S)
    fragment = re.sub(r"</?(?:html|body)\b[^>]*>", "", fragment, flags=re.I)
    return fragment


def _embed_sub_pages_in_standalone(
    html_path: Path,
    persisted_sub_pages: list[tuple[str, Path]],
) -> None:
    if not persisted_sub_pages:
        return
    html = html_path.read_text(encoding="utf-8")
    blocks: list[str] = [
        '<section class="standalone-subpages" data-section="standalone-subpages">',
        '<h2 id="embedded-subpages">患者池子页</h2>',
        '<nav class="subpage-jump-list">',
    ]
    for slug, _path in persisted_sub_pages:
        blocks.append(f'<a href="#page-{slug}">{slug}</a>')
    blocks.append("</nav>")
    for slug, path in persisted_sub_pages:
        page_html = path.read_text(encoding="utf-8")
        embedded_page_html = re.sub(
            r'<div\b[^>]*class=["\'][^"\']*\b(?:mermaid|subpage-pathway-placeholder)\b[^"\']*["\'][^>]*>.*?</div>',
            "",
            _html_body_fragment(page_html),
            flags=re.I | re.S,
        )
        blocks.append(
            f'<section class="standalone-subpage" id="page-{slug}" '
            f'data-subpage-slug="{slug}">'
            f'<p><a href="{path.name}">打开独立子页: {slug}</a></p>'
            f'{embedded_page_html}</section>'
        )
    blocks.append("</section>")
    insert = "\n".join(blocks)
    if "</body>" in html:
        html = html.replace("</body>", f"{insert}\n</body>", 1)
    else:
        html = f"{html}\n{insert}"
    html_path.write_text(html, encoding="utf-8")


def build_pdf(
    html_path: Path,
    output_dir: Path,
    toc_anchors: list[tuple[str, str]] | None = None,
) -> Path:
    pdf = output_dir / "report_standalone.pdf"
    try:
        result = _render_pdf(
            html_path=html_path,
            out_path=pdf,
            toc_anchors=toc_anchors,
            auto_validate=False,
        )
    except Exception as exc:
        raise BundleError(f"PDF generation failed: {type(exc).__name__}: {exc}") from exc
    if not result.get("ok"):
        raise BundleError(f"PDF generation returned not ok: {result}")
    _assert_not_placeholder(pdf, _PLACEHOLDER_PDF, "PDF")
    return pdf


def _read_json(path: Path) -> Any:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _compact(value: Any, *, max_chars: int = 240) -> str:
    if value is None:
        return ""
    if isinstance(value, (str, int, float, bool)):
        text = str(value)
    else:
        text = json.dumps(value, ensure_ascii=False, sort_keys=True)
    return text if len(text) <= max_chars else text[: max_chars - 1] + "…"


def _source_raw_path(raw_path: Any, slug_dir: Path) -> str:
    if not raw_path:
        return ""
    path = Path(str(raw_path))
    try:
        if path.is_absolute():
            return str(path.resolve().relative_to(slug_dir.resolve()))
    except ValueError:
        pass
    return path.as_posix()


def _cached_source_files(slug_dir: Path) -> list[dict[str, Any]]:
    sources_dir = slug_dir / "sources"
    if not sources_dir.exists():
        return []

    rows: list[dict[str, Any]] = []
    for path in sorted(sources_dir.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(slug_dir)
        parts = rel.parts
        if len(parts) > 1 and parts[1].lower() == "raw":
            continue
        source_parts = path.relative_to(sources_dir).parts
        rows.append(
            {
                "source_id": path.stem,
                "source_type": source_parts[0] if source_parts else "",
                "source_tier": "cached",
                "source_url": "",
                "checksum": "",
                "raw_path": rel.as_posix(),
            }
        )
    return rows


def _merge_sources(
    selected_sources: list[dict[str, Any]], cached_sources: list[dict[str, Any]], slug_dir: Path
) -> list[dict[str, Any]]:
    merged: dict[str, dict[str, Any]] = {}

    def key_for(src: dict[str, Any]) -> str:
        raw_path = _source_raw_path(src.get("raw_path"), slug_dir)
        if raw_path:
            return f"path:{raw_path}"
        return f"id:{src.get('source_type', '')}:{src.get('source_id', '')}"

    for src in cached_sources:
        merged[key_for(src)] = dict(src)

    for src in selected_sources:
        row = dict(src)
        raw_path = _source_raw_path(row.get("raw_path"), slug_dir)
        if raw_path:
            row["raw_path"] = raw_path
        key = key_for(row)
        existing = merged.get(key, {})
        merged[key] = {**existing, **row}

    return list(merged.values())


def _relative_path(path: Path, slug_dir: Path) -> str:
    try:
        return path.resolve().relative_to(slug_dir.resolve()).as_posix()
    except ValueError:
        return str(path)


def _candidate_path(slug_dir: Path, value: Any) -> Path | None:
    if not value:
        return None
    text = str(value).replace("\\", "/")
    path = Path(text)
    return path if path.is_absolute() else slug_dir / text


def _market_model_files(slug_dir: Path) -> list[Path]:
    candidates: list[Path] = []
    market_dir = slug_dir / "sources" / "market"
    if market_dir.exists():
        candidates.extend(
            path
            for path in sorted(market_dir.glob("*"))
            if path.is_file() and "model" in path.name.lower()
        )

    for manifest_name in ("market_source_manifest.json", "source_manifest.json"):
        manifest = _read_json(slug_dir / manifest_name)
        stack: list[Any] = [manifest]
        while stack:
            item = stack.pop()
            if isinstance(item, dict):
                for key in ("text_path", "raw_path"):
                    path = _candidate_path(slug_dir, item.get(key))
                    if path and path.exists() and path.suffix.lower() == ".txt":
                        text = f"{item.get('source_id', '')} {path.name}".lower()
                        if "model" in text or item.get("source_type") in {"market", "derived_market_model"}:
                            candidates.append(path)
                stack.extend(item.values())
            elif isinstance(item, list):
                stack.extend(item)

    unique: dict[str, Path] = {}
    for path in candidates:
        if path.exists():
            unique[str(path.resolve()).lower()] = path
    return list(unique.values())


def _market_model_rows(slug_dir: Path) -> list[list[Any]]:
    rows: list[list[Any]] = []
    interesting = (
        "tam",
        "sam",
        "som",
        "pool",
        "input_",
        "lp",
        "matrix",
        "policy",
    )
    for path in _market_model_files(slug_dir):
        for line_no, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            line = raw_line.strip()
            if not line or ":" not in line:
                continue
            field, value = line.split(":", 1)
            field = field.strip()
            if not any(token in field.lower() for token in interesting):
                continue
            rows.append(
                [
                    _compact(field, max_chars=80),
                    _compact(value.strip(), max_chars=220),
                    f"{_relative_path(path, slug_dir)}:line:{line_no}",
                ]
            )
    return rows or [["", "", ""]]


def _lp_framework_rows(staging: dict[str, Any], market_model_rows: list[list[Any]]) -> list[list[Any]]:
    rows: list[list[Any]] = []
    seen: set[tuple[str, str]] = set()

    def add(lp_id: str, trigger: str, value: str, evidence: str) -> None:
        key = (lp_id, trigger)
        if key in seen:
            return
        seen.add(key)
        rows.append([lp_id, trigger, value, evidence])

    for field, value, evidence in market_model_rows:
        match = re.match(r"^(LP\d+)\s+(.+)$", str(field), re.I)
        if match:
            add(match.group(1).upper(), match.group(2), str(value), str(evidence))

    for dimension in staging.get("dimensions", []) if isinstance(staging, dict) else []:
        if not isinstance(dimension, dict):
            continue
        evidence = _compact(dimension.get("citation_anchor"))
        for cohort in dimension.get("sub_cohorts", []):
            match = re.match(r"^(LP\d+)\s*(.*)$", str(cohort), re.I)
            if match:
                add(match.group(1).upper(), match.group(2).strip(), "", evidence)

    return rows or [["", "", "", ""]]


def _cohort_matrix_rows(staging: dict[str, Any]) -> list[list[Any]]:
    rows: list[list[Any]] = []
    if not isinstance(staging, dict):
        return [["", "", "", ""]]

    for dimension in staging.get("dimensions", []):
        if not isinstance(dimension, dict):
            continue
        cohorts = dimension.get("sub_cohorts") or [""]
        for cohort in cohorts:
            rows.append(
                [
                    _compact(dimension.get("name")),
                    _compact(dimension.get("citation_anchor")),
                    _compact(cohort),
                    _compact(dimension, max_chars=360),
                ]
            )

    for cohort in staging.get("cohorts", staging.get("strata", [])):
        if isinstance(cohort, dict):
            rows.append(
                [
                    _compact(cohort.get("name")),
                    _compact(cohort.get("citation_anchor")),
                    _compact(cohort.get("cohort", cohort.get("segment", ""))),
                    _compact(cohort, max_chars=360),
                ]
            )

    return rows or [["", "", "", ""]]


def _citation_audit_rows(slug_dir: Path) -> list[list[Any]]:
    rows: list[list[Any]] = []
    citations = _read_json(slug_dir / "citations_index.json") or {}
    for claim in citations.get("claims", []) if isinstance(citations, dict) else []:
        if isinstance(claim, dict):
            rows.append(
                [
                    _compact(claim.get("anchor"), max_chars=100),
                    _compact(claim.get("claim_text"), max_chars=220),
                    _compact(claim.get("classification")),
                    _compact(claim.get("position")),
                    str(slug_dir / "citations_index.json"),
                ]
            )

    grading = _read_json(slug_dir / "medical_evidence_grading_manifest.json") or {}
    by_grade = grading.get("by_grade", {}) if isinstance(grading, dict) else {}
    if isinstance(by_grade, dict):
        for grade, count in sorted(by_grade.items()):
            rows.append(
                [
                    f"evidence_grade:{grade}",
                    _compact(count),
                    "evidence_grade",
                    "",
                    str(slug_dir / "medical_evidence_grading_manifest.json"),
                ]
            )

    return rows or [["", "", "", "", ""]]


def _mermaid_asset_rows(slug_dir: Path) -> list[list[Any]]:
    manifest = _read_json(slug_dir / "mermaid_render_manifest.json") or {}
    rows: list[list[Any]] = []
    for block in manifest.get("blocks", []) if isinstance(manifest, dict) else []:
        if isinstance(block, dict):
            rows.append(
                [
                    _compact(block.get("index")),
                    _compact(block.get("ok")),
                    _compact(block.get("path"), max_chars=140),
                    _compact(block.get("reason"), max_chars=160),
                    _compact(block.get("source"), max_chars=220),
                ]
            )
    return rows or [["", "", "", "", ""]]


def _verification_rows(slug_dir: Path, verification: dict[str, Any]) -> list[list[Any]]:
    violations = verification.get("violations", []) if isinstance(verification, dict) else []
    rows: list[list[Any]] = [
        ["verdict", _compact(verification.get("verdict", "")), str(slug_dir / "verification_report.json"), ""],
        ["turn_count", _compact(verification.get("turn_count")), str(slug_dir / "verification_report.json"), ""],
        ["verified_count", _compact(verification.get("verified_count")), str(slug_dir / "verification_report.json"), ""],
        ["violation_count", _compact(len(violations) if isinstance(violations, list) else 0), str(slug_dir / "verification_report.json"), ""],
    ]

    for key in ("audit_verdict", "deliverable_verdict"):
        if key in verification:
            rows.append([key, _compact(verification.get(key)), str(slug_dir / "verification_report.json"), ""])

    for section_name in ("anchor_audit_summary", "deliverable_audit", "metrics"):
        section = verification.get(section_name)
        if isinstance(section, dict):
            for key, value in sorted(section.items()):
                rows.append(
                    [
                        f"{section_name}.{key}",
                        _compact(value),
                        str(slug_dir / "verification_report.json"),
                        "",
                    ]
                )

    if isinstance(violations, list):
        for idx, item in enumerate(violations, start=1):
            if isinstance(item, dict):
                rows.append(
                    [
                        f"violation.{idx}.{_compact(item.get('severity'))}",
                        _compact(item.get("claim"), max_chars=160),
                        _compact(item.get("anchor"), max_chars=80),
                        _compact(item.get("reason"), max_chars=160),
                    ]
                )

    return rows


def _xlsx_payload(slug_dir: Path) -> tuple[dict[str, list[list[Any]]], dict[str, Any]]:
    contract = _read_json(slug_dir / "contract.json") or {}
    staging = _read_json(slug_dir / "staging.json") or {}
    verification = _read_json(slug_dir / "verification_report.json") or {}
    source_manifest = _read_json(slug_dir / "source_manifest.json") or {}

    summary_rows = [
        ["disease_slug", slug_dir.name, str(slug_dir)],
        ["disease", _compact(contract.get("disease")), str(slug_dir / "contract.json")],
        ["geography", _compact(contract.get("geography")), str(slug_dir / "contract.json")],
        ["report_depth", _compact(contract.get("report_depth")), str(slug_dir / "contract.json")],
        ["verification_verdict", _compact(verification.get("verdict")), str(slug_dir / "verification_report.json")],
        ["audit_turn_count", _compact(verification.get("turn_count")), str(slug_dir / "verification_report.json")],
    ]

    selected_sources: list[dict[str, Any]] = []
    for disease in source_manifest.get("diseases", []) if isinstance(source_manifest, dict) else []:
        if disease.get("slug") == slug_dir.name or not selected_sources:
            selected_sources = list(disease.get("selected_sources", []))
            if disease.get("slug") == slug_dir.name:
                break
    selected_sources = [
        source for source in selected_sources if isinstance(source, dict)
    ]
    selected_sources = _merge_sources(selected_sources, _cached_source_files(slug_dir), slug_dir)
    summary_rows.append(["source_file_count", str(len(selected_sources)), str(slug_dir / "sources")])
    source_rows = [
        [
            _compact(src.get("source_id")),
            _compact(src.get("source_type")),
            _compact(src.get("source_tier")),
            _compact(src.get("source_url"), max_chars=120),
            _compact(src.get("checksum"), max_chars=80),
            _compact(src.get("raw_path"), max_chars=120),
        ]
        for src in selected_sources
    ] or [["", "", "", "", "", ""]]

    verification_rows = _verification_rows(slug_dir, verification)

    cohorts = staging.get("cohorts", staging.get("strata", [])) if isinstance(staging, dict) else []
    staging_rows = [
        [_compact(item.get("name")), _compact(item.get("citation_anchor")), _compact(item)]
        for item in cohorts
        if isinstance(item, dict)
    ] or [["", "", ""]]
    market_model_rows = _market_model_rows(slug_dir)

    data = {
        "summary": summary_rows,
        "sources": source_rows,
        "verification": verification_rows,
        "staging": staging_rows,
        "market_model": market_model_rows,
        "lp_framework": _lp_framework_rows(staging, market_model_rows),
        "cohort_matrix": _cohort_matrix_rows(staging),
        "citation_audit": _citation_audit_rows(slug_dir),
        "mermaid_assets": _mermaid_asset_rows(slug_dir),
    }
    schema = {
        "metadata": {"source_file_count": len(selected_sources)},
        "sheets": [
            {
                "name": "Summary",
                "headers": ["Field", "Value", "Evidence path"],
                "data_key": "summary",
                "column_widths": [24, 48, 72],
            },
            {
                "name": "Sources",
                "headers": ["Source ID", "Type", "Tier", "URL", "Checksum", "Raw path"],
                "data_key": "sources",
                "column_widths": [28, 18, 18, 48, 42, 48],
            },
            {
                "name": "Verification",
                "headers": ["Field", "Value", "Evidence path", "Detail"],
                "data_key": "verification",
                "column_widths": [16, 60, 36, 60],
            },
            {
                "name": "Staging",
                "headers": ["Name", "Citation anchor", "Raw row"],
                "data_key": "staging",
                "column_widths": [28, 36, 80],
            },
            {
                "name": "MarketModel",
                "headers": ["Field", "Value", "Evidence path"],
                "data_key": "market_model",
                "column_widths": [34, 72, 64],
            },
            {
                "name": "LPFramework",
                "headers": ["LP", "Trigger", "Value", "Evidence path"],
                "data_key": "lp_framework",
                "column_widths": [12, 44, 72, 56],
            },
            {
                "name": "CohortMatrix",
                "headers": ["Dimension", "Citation anchor", "Cohort", "Raw row"],
                "data_key": "cohort_matrix",
                "column_widths": [30, 44, 44, 80],
            },
            {
                "name": "CitationAudit",
                "headers": ["Anchor", "Claim or count", "Classification or grade", "Position", "Evidence path"],
                "data_key": "citation_audit",
                "column_widths": [44, 72, 24, 16, 64],
            },
            {
                "name": "MermaidAssets",
                "headers": ["Index", "OK", "Path", "Reason", "Source excerpt"],
                "data_key": "mermaid_assets",
                "column_widths": [10, 10, 56, 48, 72],
            },
        ]
    }
    return data, schema


def build_xlsx(slug_dir: Path, output_dir: Path) -> Path:
    xlsx = output_dir / "report_data.xlsx"
    schema_path = output_dir / "report_data_schema.yaml"
    data, schema = _xlsx_payload(slug_dir)
    try:
        import yaml  # type: ignore
        schema_path.write_text(
            yaml.safe_dump(schema, allow_unicode=True, sort_keys=False),
            encoding="utf-8",
        )
        result = _render_xlsx(
            data=data,
            schema_yaml=schema_path,
            out_path=xlsx,
            auto_validate=True,
        )
    except Exception as exc:
        raise BundleError(f"XLSX generation failed: {type(exc).__name__}: {exc}") from exc
    if not result.get("ok"):
        raise BundleError(f"XLSX generation returned not ok: {result}")
    _assert_not_placeholder(xlsx, _PLACEHOLDER_XLSX, "XLSX")
    return xlsx


def build_all_deliverables(
    slug_dir: Path,
    project_root: Path,
    *,
    skip_pdf: bool = True,
    skip_xlsx: bool = False,
    skip_visible_copy_audit: bool = False,
    output_dir: Path | None = None,
    sub_pages: list[dict] | None = None,  # R3a: composer ComposedReport.sub_pages
    toc_anchors: list[tuple[str, str]] | None = None,  # R3b: TOC 浮动锚点列表
) -> dict[str, Any]:
    _assert_verdict_ok(slug_dir)

    output_dir = Path(output_dir) if output_dir is not None else project_root / "output"
    output_dir.mkdir(parents=True, exist_ok=True)
    raw = output_dir / "report_raw.html"
    if not raw.exists():
        raise BundleError(f"report_raw.html not found at {raw}")
    raw_html = raw.read_text(encoding="utf-8")
    reader_audit_mode = (slug_dir / "reader_compose_audit_layer.json").exists()
    _assert_report_substance_clean(raw_html, str(raw), reader_audit_mode=reader_audit_mode)
    if not skip_visible_copy_audit:
        _assert_visible_copy_clean(raw_html, str(raw))
    persisted_sub_pages: list[tuple[str, Path]] = []

    # R3a Phase-2-Quality-Fix: 落盘 sub_pages dict → page_<slug>.html (architect 修订 1, 盲点 E).
    # 解决 R3a→R3b 数据流类型不兼容: dict (内存字符串) → tuple (file path).
    # sub_pages=None 或 [] 时不落盘, 行为与 119 现有测试一致.
    if sub_pages:
        for page in sub_pages:
            if isinstance(page, dict) and "html" in page:
                _assert_report_substance_clean(
                    str(page["html"]),
                    f"sub_page:{page.get('slug', '?')}",
                    reader_audit_mode=reader_audit_mode,
                )
                if not skip_visible_copy_audit:
                    _assert_visible_copy_clean(str(page["html"]), f"sub_page:{page.get('slug', '?')}")
        from _persist_sub_pages import persist_sub_pages
        persisted_sub_pages = persist_sub_pages(sub_pages, output_dir)

    html_path = build_standalone_html(raw, output_dir)
    _embed_sub_pages_in_standalone(html_path, persisted_sub_pages)
    pdf_path = build_pdf(html_path, output_dir, toc_anchors=toc_anchors) if not skip_pdf else None
    xlsx_path = build_xlsx(slug_dir, output_dir) if not skip_xlsx else None

    final_html = html_path.read_text(encoding="utf-8")
    design_report = validate_design(final_html)

    manifest: dict[str, Any] = {
        "deliverables": {
            "html": _artifact_manifest(html_path, "HTML"),
            "pdf": (
                _artifact_manifest(pdf_path, "PDF", _PLACEHOLDER_PDF)
                if pdf_path else {"ok": False, "skipped": True, "validation": {"skipped": True}}
            ),
            "xlsx": (
                _artifact_manifest(xlsx_path, "XLSX", _PLACEHOLDER_XLSX)
                if xlsx_path else {"ok": False, "skipped": True, "validation": {"skipped": True}}
            ),
        },
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "skill_version": "report-bundle-builder/2.0",
        "disease_slug": slug_dir.name,
        "output_dir": str(output_dir),
        "sub_pages": [
            {"slug": slug, "out_path": str(path), "size_bytes": path.stat().st_size}
            for slug, path in persisted_sub_pages
        ],
        "design_warnings": design_report["warnings"],
        "design_token_coverage": design_report["token_coverage"],
        "toc_li_count": design_report["toc_li_count"],
    }
    (output_dir / "delivery_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return manifest
