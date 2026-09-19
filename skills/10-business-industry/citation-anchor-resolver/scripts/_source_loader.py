"""8 种 source_type 的加载器。

每个 ``load_<type>(citation, sources_dir)`` 返回:
- ``str``: 锚点定位的源原文片段(纯文本,用于关键词核对)
- ``None``: 文件不存在 / locator 解析失败 / 任何无法核对的情形

P0 守护:**绝不**做任何 fallback 到内置答案。"找不到 = None",上层据此返回
``verified=False``,不允许在这一层"兜底"。

源文件路径约定(相对 sources_dir):

    guideline   → guidelines/<source_id>.{txt,md,html,pdf}  (+ 同名 .toc.json 可选)
    pmid        → pubmed/<source_id>.json
    nct         → trials/<source_id>.json
    aact        → aact/<source_id>.json
    europepmc   → europepmc/<source_id>.json
    bioc        → bioc/<source_id>.json
    evidence    → <sources_dir>/../evidence/<source_id>     (老格式向后兼容)
    nmpa-page   → nmpa/<source_id>.{html,json}
"""

from __future__ import annotations

import json
import re
from pathlib import Path

try:  # pragma: no cover
    from ._anchor_schema import Citation
except ImportError:  # pragma: no cover
    from _anchor_schema import Citation  # type: ignore


# ---------------------------------------------------------------------------
# 通用工具
# ---------------------------------------------------------------------------


def _read_text(path: Path) -> str | None:
    """读文本文件;不存在或读不出 → None。"""
    try:
        if not path.is_file():
            return None
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None


def _read_json(path: Path) -> dict | list | None:
    """读 JSON;不存在或不可解析 → None。"""
    try:
        if not path.is_file():
            return None
        return json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except (OSError, json.JSONDecodeError):
        return None


def _try_pdf_text(path: Path) -> str | None:
    """尝试用可选依赖 pypdf 读 PDF;缺失或失败 → None(无 fallback)。"""
    try:
        from pypdf import PdfReader  # type: ignore
    except Exception:
        return None
    try:
        reader = PdfReader(str(path))
        parts = [page.extract_text() or "" for page in reader.pages]
        return "\n".join(parts) if parts else None
    except Exception:
        return None


def _slice_lines(text: str, start: int, end: int | None = None) -> str | None:
    """按 1-based 行号区间切片。"""
    if not text or start < 1:
        return None
    lines = text.splitlines()
    if start > len(lines):
        return None
    end_idx = end if end is not None else start
    if end_idx < start:
        return None
    end_idx = min(end_idx, len(lines))
    return "\n".join(lines[start - 1 : end_idx])


_LINE_RANGE_RE = re.compile(r"^line:(\d+)(?:-(\d+))?$")


def _parse_line_locator(locator: str) -> tuple[int, int | None] | None:
    """解析 ``line:42`` / ``line:42-58``。"""
    m = _LINE_RANGE_RE.fullmatch(locator.strip())
    if not m:
        return None
    start = int(m.group(1))
    end = int(m.group(2)) if m.group(2) else None
    return (start, end)


# ---------------------------------------------------------------------------
# 各 source_type 的加载器
# ---------------------------------------------------------------------------


def load_guideline(cit: Citation, sources_dir: Path) -> str | None:
    """加载 guideline 源;按 locator(章节号 / 行号)切片。

    支持的文件后缀(按优先级):.txt, .md, .html, .pdf
    可选 .toc.json:章节索引 {"§5.5.2": {"start_line": 1, "end_line": 4}, ...}
    """
    base = sources_dir / "guidelines" / cit.source_id

    text: str | None = None
    for suffix in (".txt", ".md", ".html"):
        candidate = base.with_suffix(suffix)
        text = _read_text(candidate)
        if text is not None:
            break

    if text is None:
        pdf_path = base.with_suffix(".pdf")
        if pdf_path.is_file():
            text = _try_pdf_text(pdf_path)

    if text is None:
        return None

    locator = cit.locator
    if not locator:
        return text

    # 尝试 line:X / line:X-Y
    line_range = _parse_line_locator(locator)
    if line_range is not None:
        return _slice_lines(text, line_range[0], line_range[1])

    # 尝试章节号(配合 .toc.json)
    toc_path = base.with_suffix(".toc.json")
    toc = _read_json(toc_path)
    if isinstance(toc, dict) and locator in toc:
        entry = toc[locator]
        if isinstance(entry, dict):
            start = entry.get("start_line")
            end = entry.get("end_line")
            if isinstance(start, int):
                return _slice_lines(text, start, end if isinstance(end, int) else None)

    # 没有 toc 或 toc 命中失败 → 退而求其次:在原文里找该 locator 字符串作为锚点
    if locator in text:
        idx = text.index(locator)
        # 给一个 ~1500 字符的窗口
        return text[idx : idx + 1500]

    return None


def load_pmid(cit: Citation, sources_dir: Path) -> str | None:
    """加载 PubMed PMID JSON。

    JSON schema(本 skill 假定):
        {"title": "...", "abstract": "...", "authors": [...], ...}

    locator:
        "abstract"   → 返回 abstract
        "title"      → 返回 title
        ""           → 返回 title + "\\n" + abstract(全文核对场景)
    """
    path = sources_dir / "pubmed" / f"{cit.source_id}.json"
    data = _read_json(path)
    if not isinstance(data, dict):
        return None

    locator = cit.locator
    title = str(data.get("title") or "")
    abstract = str(data.get("abstract") or "")

    if locator == "title":
        return title or None
    if locator == "abstract":
        return abstract or None
    if not locator:
        joined = "\n".join(p for p in (title, abstract) if p)
        return joined or None
    # 未知 locator:尝试按 key 取
    val = data.get(locator)
    if isinstance(val, str):
        return val
    return None


def _load_generic_json_field(
    cit: Citation, sources_dir: Path, subdir: str
) -> str | None:
    """nct / aact / europepmc / bioc 共用的 JSON 字段读取。

    locator 当 key 用,空 → 整个 JSON 拼字符串。
    """
    path = sources_dir / subdir / f"{cit.source_id}.json"
    data = _read_json(path)
    if not isinstance(data, dict):
        return None

    locator = cit.locator
    if not locator:
        # 把所有 string 字段拼起来
        parts: list[str] = []
        for k, v in data.items():
            if isinstance(v, str):
                parts.append(v)
            elif isinstance(v, list):
                parts.extend(str(x) for x in v if isinstance(x, str))
        return "\n".join(parts) if parts else None

    val = data.get(locator)
    if val is None:
        return None
    if isinstance(val, str):
        return val
    if isinstance(val, list):
        return "\n".join(str(x) for x in val if x)
    if isinstance(val, dict):
        return json.dumps(val, ensure_ascii=False)
    return str(val)


def load_nct(cit: Citation, sources_dir: Path) -> str | None:
    return _load_generic_json_field(cit, sources_dir, "trials")


def load_aact(cit: Citation, sources_dir: Path) -> str | None:
    return _load_generic_json_field(cit, sources_dir, "aact")


def load_europepmc(cit: Citation, sources_dir: Path) -> str | None:
    return _load_generic_json_field(cit, sources_dir, "europepmc")


def load_bioc(cit: Citation, sources_dir: Path) -> str | None:
    return _load_generic_json_field(cit, sources_dir, "bioc")


def load_evidence(cit: Citation, sources_dir: Path) -> str | None:
    """evidence 老格式:文件存在项目根的 evidence/ 目录(sources_dir 同级)。

    locator:line:X / line:X-Y / "" (整个文件)
    """
    # evidence/ 在 sources_dir 的父目录
    base = sources_dir.parent / "evidence" / cit.source_id
    text = _read_text(base)
    if text is None:
        return None

    locator = cit.locator
    if not locator:
        return text

    line_range = _parse_line_locator(locator)
    if line_range is not None:
        return _slice_lines(text, line_range[0], line_range[1])

    # 未知 locator:在原文里找
    if locator in text:
        idx = text.index(locator)
        return text[idx : idx + 1500]
    return None


def load_nmpa_page(cit: Citation, sources_dir: Path) -> str | None:
    """nmpa-page:HTML 或 JSON。"""
    base = sources_dir / "nmpa" / cit.source_id
    for suffix in (".html", ".htm", ".txt", ".md"):
        candidate = base.with_suffix(suffix)
        text = _read_text(candidate)
        if text is not None:
            if cit.locator and cit.locator in text:
                idx = text.index(cit.locator)
                return text[idx : idx + 1500]
            return text
    json_data = _read_json(base.with_suffix(".json"))
    if isinstance(json_data, dict):
        if cit.locator:
            val = json_data.get(cit.locator)
            if isinstance(val, str):
                return val
            return None
        # 拼所有字符串字段
        parts = [v for v in json_data.values() if isinstance(v, str)]
        return "\n".join(parts) if parts else None
    return None


# ---------------------------------------------------------------------------
# 调度器
# ---------------------------------------------------------------------------


_LOADERS = {
    "guideline": load_guideline,
    "pmid": load_pmid,
    "nct": load_nct,
    "aact": load_aact,
    "europepmc": load_europepmc,
    "bioc": load_bioc,
    "evidence": load_evidence,
    "nmpa-page": load_nmpa_page,
}


def dispatch_load(cit: Citation, sources_dir: Path) -> str | None:
    """按 source_type 调对应 loader。

    P0 守护:source_type 不在枚举里 → 直接返回 None,不 fallback。
    """
    loader = _LOADERS.get(cit.source_type)
    if loader is None:
        return None
    return loader(cit, sources_dir)
