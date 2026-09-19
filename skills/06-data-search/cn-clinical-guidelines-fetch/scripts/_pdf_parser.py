"""PDF 章节解析器。

用 pypdf 读 CSCO PDF，按页面文本切分章节。当前实现 minimal：扫描包含
"§5.5.2" / "ALK 融合" 等关键字的页面，提取附近段落作为治疗表上下文。
完整 PDF→治疗表结构化是 P2 task。
"""

from __future__ import annotations

from pathlib import Path


def extract_pdf_text(pdf_path: Path) -> str:
    """提取 PDF 全文为字符串。失败抛 RuntimeError。"""
    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise RuntimeError(
            "pypdf not installed; pip install pypdf"
        ) from exc

    pdf_path = Path(pdf_path)
    if not pdf_path.exists():
        raise RuntimeError(f"PDF not found: {pdf_path}")

    reader = PdfReader(str(pdf_path))
    pages_text = []
    for page in reader.pages:
        try:
            pages_text.append(page.extract_text() or "")
        except Exception:  # noqa: BLE001
            pages_text.append("")
    return "\n".join(pages_text)


def find_section(full_text: str, section_marker: str) -> str | None:
    """在全文中找指定章节标题，返回该章节到下一章节标题之间的文本。"""
    idx = full_text.find(section_marker)
    if idx < 0:
        return None
    # 简陋：取后续 4000 字符（约一章节长度）
    return full_text[idx : idx + 4000]
