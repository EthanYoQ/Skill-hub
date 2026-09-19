"""Phase 5 · report-bundle-builder (upgraded): force design-injector + verdict assertion + TOC assertion."""
from __future__ import annotations
import base64
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


_HERE = Path(__file__).resolve()
_DSI_SCRIPTS = _HERE.parents[2] / "design-system-injector" / "scripts"
if str(_DSI_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_DSI_SCRIPTS))
from injector import inject, validate_design, DESIGN_TOKENS  # noqa: E402


class BundleError(Exception):
    pass


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


def build_pdf(html_path: Path, output_dir: Path) -> Path:
    """Stub: orchestrator delegates Chrome headless conversion outside this skill."""
    pdf = output_dir / "report_standalone.pdf"
    pdf.write_bytes(b"%PDF-1.4 placeholder")
    return pdf


def build_xlsx(slug_dir: Path, output_dir: Path) -> Path:
    """Stub: minimal xlsx producer for tests; orchestrator can override."""
    xlsx = output_dir / "report_data.xlsx"
    xlsx.write_bytes(b"PK\x03\x04 placeholder")
    return xlsx


def build_all_deliverables(
    slug_dir: Path,
    project_root: Path,
    *,
    skip_pdf: bool = False,
    skip_xlsx: bool = False,
    sub_pages: list[dict] | None = None,  # R3a: composer ComposedReport.sub_pages
    toc_anchors: list[str] | None = None,  # R3b: TOC 浮动锚点列表
) -> dict[str, Any]:
    _assert_verdict_ok(slug_dir)

    output_dir = project_root / "output"
    output_dir.mkdir(parents=True, exist_ok=True)
    raw = output_dir / "report_raw.html"
    if not raw.exists():
        raise BundleError(f"report_raw.html not found at {raw}")

    # R3a Phase-2-Quality-Fix: 落盘 sub_pages dict → page_<slug>.html (architect 修订 1, 盲点 E).
    # 解决 R3a→R3b 数据流类型不兼容: dict (内存字符串) → tuple (file path).
    # sub_pages=None 或 [] 时不落盘, 行为与 119 现有测试一致.
    if sub_pages:
        from _persist_sub_pages import persist_sub_pages
        persist_sub_pages(sub_pages, output_dir)

    html_path = build_standalone_html(raw, output_dir)
    pdf_path = build_pdf(html_path, output_dir) if not skip_pdf else None
    xlsx_path = build_xlsx(slug_dir, output_dir) if not skip_xlsx else None

    final_html = html_path.read_text(encoding="utf-8")
    design_report = validate_design(final_html)

    manifest: dict[str, Any] = {
        "deliverables": {
            "html": {"ok": True, "out_path": str(html_path),
                     "size_mb": round(html_path.stat().st_size / 1024 / 1024, 2)},
            "pdf": ({"ok": True, "out_path": str(pdf_path)} if pdf_path else {"ok": False, "skipped": True}),
            "xlsx": ({"ok": True, "out_path": str(xlsx_path)} if xlsx_path else {"ok": False, "skipped": True}),
        },
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "skill_version": "report-bundle-builder/2.0",
        "disease_slug": slug_dir.name,
        "design_warnings": design_report["warnings"],
        "design_token_coverage": design_report["token_coverage"],
        "toc_li_count": design_report["toc_li_count"],
    }
    (output_dir / "delivery_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return manifest
