# -*- coding: utf-8 -*-
"""report-bundle-builder · 一键封装 build_all_deliverables.

依次跑 build_standalone_html → build_pdf → build_xlsx,部分失败继续,
输出 delivery_manifest.json 记录三件交付物状态。
"""
from __future__ import annotations
import json
import re
import datetime as _dt
from pathlib import Path
from typing import Any, Callable

from build_standalone_html import build_standalone_html
from build_pdf import build_pdf
from build_xlsx import build_xlsx

SKILL_VERSION = "report-bundle-builder/1.0"


def _safe_call(fn: Callable[..., Any], label: str, *args: Any, **kwargs: Any) -> dict:
    """跑一个 build 函数,任何异常都包成 {ok: False, error: ..., label}."""
    try:
        return fn(*args, **kwargs)
    except Exception as exc:  # 故意宽抓:任一函数失败不阻塞下游
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}", "label": label}


def _version_sort_key(path: Path) -> tuple[int, str]:
    """从 report_v<N>.html 提取版本号 N 作为排序键。

    非纯数字版本号(如 report_va.html)返回 (-1, name) 排在最后,
    避免字典序导致 v9 > v10 的 bug。
    """
    match = re.match(r"report_v(\d+)", path.stem)
    if match:
        return (int(match.group(1)), path.stem)
    return (-1, path.stem)


def build_all_deliverables(
    report_dir: Path,
    out_dir: Path,
    *,
    sub_pages: list[tuple[str, Path]] | None = None,
    toc_anchors: list[tuple[str, str]] | None = None,
    xlsx_schema: Path | None = None,
    xlsx_data: dict[str, list[list[Any]]] | None = None,
    disease_slug: str = "unknown",
) -> dict:
    """一键产出 standalone HTML + PDF + XLSX 三件交付物。

    部分失败继续:HTML 失败 → PDF 仍跑;PDF 失败 → XLSX 仍跑。
    输出 delivery_manifest.json 总览。

    Args:
        report_dir: 输入目录,需含 main.html(或自动检测 report*.html)和 PNG 资产
        out_dir: 输出目录(不存在则自动创建)
        sub_pages: [(slug, path), ...] · None 时自动扫描 report_dir/page_*.html
        toc_anchors: 给 build_pdf 用,None 时单遍渲染
        xlsx_schema: 给 build_xlsx 用,None 时跳过 xlsx
        xlsx_data: 给 build_xlsx 用,None 时跳过 xlsx
        disease_slug: 写入 manifest 元数据

    Returns:
        {
            "deliverables": {"html": {...}, "pdf": {...}, "xlsx": {...}},
            "manifest_path": str,
            "generated_at": "ISO 8601",
            "skill_version": "report-bundle-builder/1.0",
            "disease_slug": str,
            "input_dir": str,
            "output_dir": str,
        }
    """
    out_dir.mkdir(parents=True, exist_ok=True)

    # 自动定位 main.html
    # 注意:report_v*.html 必须按版本号数值降序,否则字典序 v9 > v10 会选错版本
    report_v_candidates = sorted(
        report_dir.glob("report_v*.html"),
        key=_version_sort_key,
        reverse=True,
    )
    main_html_candidates = [
        report_dir / "main.html",
        report_dir / "report.html",
        *report_v_candidates,
    ]
    main_html = next((p for p in main_html_candidates if p.exists()), None)
    if main_html is None:
        main_html = report_dir / "main.html"  # 故意指向不存在,让下游 raise 进 _safe_call

    # 自动扫描 sub_pages
    if sub_pages is None:
        sub_pages = []
        for p in sorted(report_dir.glob("page_*.html")):
            slug = p.stem.replace("page_", "")
            sub_pages.append((slug, p))

    # ① HTML
    html_out = out_dir / "report_standalone.html"
    html_result = _safe_call(
        build_standalone_html,
        "html",
        main_html=main_html,
        sub_pages=sub_pages,
        png_dir=report_dir,
        out_path=html_out,
    )
    # A3 修复:html_result["toc_warning"] 为 True 时,manifest 加可读 reason
    if html_result.get("toc_warning"):
        html_result.setdefault(
            "toc_warning_reason",
            "subpages missing <h1>/<h2> id anchors — floating TOC empty",
        )

    # ② PDF — 优先用合并好的 standalone,fallback main_html
    pdf_input = html_out if html_result.get("ok") else main_html
    pdf_used_fallback = not html_result.get("ok")
    pdf_out = out_dir / "report_standalone.pdf"
    pdf_result = _safe_call(
        build_pdf,
        "pdf",
        html_path=pdf_input,
        out_path=pdf_out,
        toc_anchors=toc_anchors,
    )
    # 不论 PDF 成功失败,标记 fallback 标志,让调用方知道 PDF 实际渲染源
    if pdf_used_fallback:
        pdf_result["fallback_input"] = True
        pdf_result["fallback_reason"] = "html_build_failed_used_main_html"

    # ③ XLSX
    if xlsx_schema and xlsx_data:
        xlsx_out = out_dir / "report_data.xlsx"
        xlsx_result = _safe_call(
            build_xlsx,
            "xlsx",
            data=xlsx_data,
            schema_yaml=xlsx_schema,
            out_path=xlsx_out,
        )
    else:
        xlsx_result = {
            "ok": False,
            "error": "xlsx_schema or xlsx_data missing — skipped",
            "label": "xlsx",
        }

    manifest = {
        "deliverables": {
            "html": html_result,
            "pdf": pdf_result,
            "xlsx": xlsx_result,
        },
        "generated_at": _dt.datetime.now(_dt.timezone.utc).isoformat(),
        "skill_version": SKILL_VERSION,
        "disease_slug": disease_slug,
        "input_dir": str(report_dir),
        "output_dir": str(out_dir),
    }
    manifest_path = out_dir / "delivery_manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False, default=str),
        encoding="utf-8",
    )
    manifest["manifest_path"] = str(manifest_path)
    return manifest
