# -*- coding: utf-8 -*-
"""通用化报告 PDF 渲染脚本(领域无关).

功能:
- 单遍模式:Chrome headless 直接 HTML → PDF
- 两遍模式:Pass 1 渲染 + 扫描 TOC 章节首次出现页 → 注入页码 → Pass 2 终稿

来源:从 output/build_pdf_two_pass.py 通用化而来,移除 37 条血液 TOC_ANCHORS 硬编码。
"""
from __future__ import annotations
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

CHROME_CANDIDATES_WIN = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
]
CHROME_CANDIDATES_UNIX = [
    "/usr/bin/google-chrome",
    "/usr/bin/chromium",
    "/usr/bin/chromium-browser",
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
]
PDF_MIN_SIZE_BYTES = 1 * 1024 * 1024  # 1 MB · build_pdf size_ok 阈值
PDF_MIN_PAGES = 1


def _detect_chrome() -> str | None:
    """跨平台检测 Chrome / Edge / Chromium 可执行文件路径."""
    candidates = CHROME_CANDIDATES_WIN if sys.platform == "win32" else CHROME_CANDIDATES_UNIX
    for c in candidates:
        if Path(c).exists():
            return c
    return None


def _render_one_pass(html_path: Path, pdf_path: Path, chrome: str) -> None:
    cmd = [
        chrome, "--headless=new", "--disable-gpu", "--no-sandbox",
        "--no-pdf-header-footer",
        f"--print-to-pdf={pdf_path}",
        f"file:///{html_path.as_posix()}",
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, timeout=300)
    except (FileNotFoundError, OSError) as exc:
        # Chrome 可执行文件不存在或无法启动 → 转为 RuntimeError 以便上层备份恢复
        raise RuntimeError(f"Chrome headless launch failed: {exc}") from exc
    if result.returncode != 0:
        raise RuntimeError(
            f"Chrome headless failed: {result.stderr.decode('utf-8', errors='ignore')[:300]}"
        )
    if not pdf_path.exists():
        raise RuntimeError(f"PDF not generated: {pdf_path}")


def _measure_pages(pdf_path: Path, toc_anchors: list[tuple[str, str]]) -> dict[str, int | None]:
    """扫描 PDF 文本,搜每个 TOC 关键词首次出现页(1-indexed)."""
    try:
        from pypdf import PdfReader  # type: ignore
    except ImportError:
        try:
            from PyPDF2 import PdfReader  # type: ignore
        except ImportError:
            return {href: None for href, _ in toc_anchors}

    reader = PdfReader(str(pdf_path))
    pages = []
    for p in reader.pages:
        try:
            pages.append(p.extract_text() or "")
        except Exception:
            pages.append("")

    result: dict[str, int | None] = {}
    for href, keyword in toc_anchors:
        found = None
        # 跳过封面 + TOC + 索引(前 3 页)
        for i in range(min(3, len(pages)), len(pages)):
            if keyword in pages[i]:
                found = i + 1
                break
        result[href] = found
    return result


def _strip_page_nums(html_path: Path) -> None:
    html = html_path.read_text(encoding="utf-8")
    html = re.sub(r'(<span class="page">)[^<]*(</span>)', r"\g<1>\g<2>", html)
    html_path.write_text(html, encoding="utf-8")


def _inject_page_nums(html_path: Path, page_map: dict[str, int | None]) -> int:
    html = html_path.read_text(encoding="utf-8")
    replaced = 0
    for href, page_num in page_map.items():
        pn = str(page_num) if page_num else "—"
        pattern = (
            r'(<a href="' + re.escape(href) + r'">'
            r'.*?<span class="page">)\s*(</span>)'
        )
        new, n = re.subn(pattern, r"\g<1>" + pn + r"\g<2>", html, flags=re.DOTALL)
        if n > 0:
            html = new
            replaced += n
    html_path.write_text(html, encoding="utf-8")
    return replaced


def _validate_pdf(pdf_path: Path, min_pages: int = PDF_MIN_PAGES) -> dict:
    pages: int | None
    try:
        from pypdf import PdfReader  # type: ignore
        pages = len(PdfReader(str(pdf_path)).pages)
    except ImportError:
        try:
            from PyPDF2 import PdfReader  # type: ignore
            pages = len(PdfReader(str(pdf_path)).pages)
        except ImportError:
            pages = None  # pypdf 与 PyPDF2 均不可用
    except Exception:
        pages = None  # PDF 读取异常,无法判定页数
    size = pdf_path.stat().st_size
    return {
        "size_ok": size > PDF_MIN_SIZE_BYTES,
        "size_bytes": size,
        "pages": pages,                                    # int 或 None
        "pages_unknown": pages is None,
        "pages_ok": pages is None or pages >= min_pages,   # 无法判定不算失败
    }


def build_pdf(
    html_path: Path,
    out_path: Path,
    toc_anchors: list[tuple[str, str]] | None = None,
    *,
    auto_validate: bool = True,
    chrome_path: str | None = None,
) -> dict:
    """渲染 HTML 为 PDF。toc_anchors 为 None 时单遍渲染,否则两遍(注入页码)。

    两遍模式说明:
    - 函数会先把 html_path 备份到同目录(扩展名追加 .pdf-backup)
    - 在原文件上做 _strip_page_nums + _inject_page_nums + Pass 2 渲染
    - 全部成功后删除备份;任一步失败则从备份恢复并 raise
    - 因此即使 Pass 2 崩溃,原 HTML 也不会丢失

    Args:
        html_path: HTML 文件路径(若两遍模式,会被原地修改写入页码;失败时自动恢复)
        out_path: 输出 PDF 路径
        toc_anchors: [(href, keyword), ...] · 例 [("#ch1","一、执行摘要")]
        auto_validate: 自动验证(size > PDF_MIN_SIZE_BYTES)
        chrome_path: 显式指定 Chrome 路径,None 时自动检测

    Returns:
        {"ok", "out_path", "size_mb", "pages", "validation", "mode": "one-pass" | "two-pass"}
        其中 pages 为 int 或 None(无法判定页数时)

    Raises:
        RuntimeError: Chrome 未找到或渲染失败(两遍模式失败时原 HTML 已自动恢复)
    """
    chrome = chrome_path or _detect_chrome()
    if not chrome:
        raise RuntimeError(
            "No Chrome/Edge/Chromium found. Set chrome_path explicitly or install one of:\n"
            "  Windows: C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe\n"
            "  Linux:   /usr/bin/google-chrome (or chromium)\n"
            "  macOS:   /Applications/Google Chrome.app"
        )

    mode = "one-pass" if not toc_anchors else "two-pass"

    if toc_anchors:
        # 备份原 HTML(覆盖式,即使遗留旧备份也以最新为准)
        # 用字符串拼接到原后缀末尾,避免 with_suffix 丢主后缀
        backup = html_path.with_name(html_path.name + ".pdf-backup")
        shutil.copy2(html_path, backup)

        # 在 out_path 父目录创建唯一临时 PDF,避免并发时文件名碰撞
        fd, tmp_pdf_str = tempfile.mkstemp(
            prefix=f"{out_path.stem}_pass1_", suffix=".pdf",
            dir=str(out_path.parent),
        )
        os.close(fd)
        tmp_pdf = Path(tmp_pdf_str)

        try:
            _strip_page_nums(html_path)
            _render_one_pass(html_path, tmp_pdf, chrome)
            page_map = _measure_pages(tmp_pdf, toc_anchors)
            _inject_page_nums(html_path, page_map)
            _render_one_pass(html_path, out_path, chrome)
        except Exception:
            # 任一步失败 → 从备份恢复用户原文件,然后 re-raise
            shutil.copy2(backup, html_path)
            raise
        finally:
            # 清理 pass1 临时 PDF + 备份(成功或失败都清)
            for p in (tmp_pdf, backup):
                try:
                    p.unlink()
                except FileNotFoundError:
                    pass
                except Exception:
                    pass
    else:
        _render_one_pass(html_path, out_path, chrome)

    validation = _validate_pdf(out_path) if auto_validate else None
    ok = (validation is None) or validation["size_ok"]
    pages = validation["pages"] if validation else None

    return {
        "ok": ok,
        "out_path": str(out_path),
        "size_mb": round(out_path.stat().st_size / (1024 * 1024), 2),
        "pages": pages,
        "validation": validation,
        "mode": mode,
    }
