"""citation-anchor-resolver — 公开 API。

3 个函数:
- ``parse_citations_in_text(text)``:扫描文本提取所有锚点 + 上下文 claim
- ``resolve_citation(anchor, sources_dir)``:锚点 → 源文本片段
- ``verify_claim_against_source(claim_text, citation, sources_dir, *, keywords=None)``:
  核对 claim 关键词是否在引用源里出现

P0 守护:
- 锚点解析失败 / 文件不存在 / locator 找不到 → 返回 None 或 verified=False
- **不**fallback 到任何"内置答案" / "已知字典"
- 关键词核对用严格 substring(规范化后),不做语义匹配
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Iterable

# 兼容两种导入姿势:
#   1) 作为包导入:from scripts.resolver import ...
#   2) 直接 sys.path.insert 后:import resolver(测试中用)
try:  # pragma: no cover
    from ._anchor_schema import Citation, find_all_anchors, parse_anchor
    from ._source_loader import dispatch_load
    from ._keyword_match import (
        auto_match_claim_to_source,
        match_keywords,
    )
except ImportError:  # pragma: no cover
    from _anchor_schema import Citation, find_all_anchors, parse_anchor  # type: ignore
    from _source_loader import dispatch_load  # type: ignore
    from _keyword_match import (  # type: ignore
        auto_match_claim_to_source,
        match_keywords,
    )


__all__ = [
    "Citation",
    "parse_citations_in_text",
    "resolve_citation",
    "verify_claim_against_source",
]


# 句子边界:中英文常见标点
_SENT_END_RE = re.compile(r"[。!?!?\n]")
_MAX_CONTEXT_CHARS = 240


def _claim_sentence_around(text: str, anchor_start: int, anchor_end: int) -> str:
    """从锚点位置向左/向右各扩到最近的句子边界,作为 claim 句子。"""
    if not text:
        return ""

    # 向左找句末
    left = anchor_start
    for i in range(anchor_start - 1, max(-1, anchor_start - _MAX_CONTEXT_CHARS) - 1, -1):
        if _SENT_END_RE.match(text[i]):
            left = i + 1
            break
    else:
        left = max(0, anchor_start - _MAX_CONTEXT_CHARS)

    # 向右找句末
    right = anchor_end
    end_limit = min(len(text), anchor_end + _MAX_CONTEXT_CHARS)
    for i in range(anchor_end, end_limit):
        if _SENT_END_RE.match(text[i]):
            right = i + 1
            break
    else:
        right = end_limit

    return text[left:right].strip()


def parse_citations_in_text(text: str) -> list[dict]:
    """扫描文本,返回所有 citation 锚点 + 上下文 claim。

    Returns:
        [
          {
            "anchor": Citation(...),
            "anchor_str": "[pmid:12345678:abstract]",
            "claim_sentence": "...含锚点的整句话...",
            "position": int,   # 锚点在原文中的起始字符位置
          },
          ...
        ]

    非法格式的"假锚点"会被跳过(不会报错)。
    """
    if not text:
        return []

    out: list[dict] = []
    for cit, start, end in find_all_anchors(text):
        out.append(
            {
                "anchor": cit,
                "anchor_str": cit.raw,
                "claim_sentence": _claim_sentence_around(text, start, end),
                "position": start,
            }
        )
    return out


def _coerce_citation(citation: "Citation | str") -> Citation | None:
    if isinstance(citation, Citation):
        return citation
    if isinstance(citation, str):
        return parse_anchor(citation)
    return None


def resolve_citation(
    anchor: "Citation | str",
    sources_dir: Path | str,
) -> str | None:
    """把锚点解析为源文本片段。

    Args:
        anchor: Citation 或锚点字符串 ``[type:id:locator]``
        sources_dir: 源文件根目录(``.cache/<slug>/sources/``)

    Returns:
        源文本片段(用于关键词核对) or ``None``。

    P0 守护:
    - 锚点形式不合法 → None
    - source_type 不在枚举 → None
    - 文件不存在 / locator 解析失败 → None
    - **不 fallback 到任何"已知答案"**
    """
    cit = _coerce_citation(anchor)
    if cit is None:
        return None
    if not cit.is_known_source_type:
        return None

    sources_path = Path(sources_dir)
    if not sources_path.exists():
        return None

    return dispatch_load(cit, sources_path)


def verify_claim_against_source(
    claim_text: str,
    citation: "Citation | str",
    sources_dir: Path | str,
    *,
    keywords: Iterable[str] | None = None,
) -> dict:
    """核对 claim 里的关键词是否在锚点指向的源里出现。

    Args:
        claim_text: 报告里的事实声明文本
        citation: Citation 或锚点字符串
        sources_dir: 源文件根目录
        keywords: 显式给出要核对的关键词;None → 从 claim_text 自动提取

    Returns:
        {
            "verified": bool,
            "matched_keywords": [...],
            "missing_keywords": [...],
            "source_excerpt": "..."[:300],
            "reason": "...",
        }

    P0 守护:
    - 锚点不可解析 → verified=False, reason="anchor unresolvable",**不兜底**
    - 关键词列表为空(claim 抽不出词) → verified=False, reason="no keywords to verify"
    - 任一关键词不在源里 → verified=False, missing_keywords 非空
    """
    src = resolve_citation(citation, sources_dir)
    if src is None:
        anchor_str = citation.raw if isinstance(citation, Citation) else str(citation)
        return {
            "verified": False,
            "matched_keywords": [],
            "missing_keywords": list(keywords) if keywords else [],
            "source_excerpt": "",
            "reason": f"anchor unresolvable: {anchor_str}",
        }

    if keywords is None:
        # auto 模式:源驱动贪心切片(dictionary-free,源即字典)
        matched, missing = auto_match_claim_to_source(claim_text or "", src)
        if not matched and not missing:
            return {
                "verified": False,
                "matched_keywords": [],
                "missing_keywords": [],
                "source_excerpt": src[:300],
                "reason": "no keywords to verify",
            }
        if missing:
            return {
                "verified": False,
                "matched_keywords": matched,
                "missing_keywords": missing,
                "source_excerpt": src[:300],
                "reason": f"source missing: {', '.join(missing)}",
            }
        return {
            "verified": True,
            "matched_keywords": matched,
            "missing_keywords": [],
            "source_excerpt": src[:300],
            "reason": "all keywords matched",
        }

    # 显式 keywords 模式:严格 substring 核对
    kw_list = [str(k) for k in keywords if k]
    if not kw_list:
        return {
            "verified": False,
            "matched_keywords": [],
            "missing_keywords": [],
            "source_excerpt": src[:300],
            "reason": "no keywords to verify",
        }

    matched, missing = match_keywords(kw_list, src)
    if missing:
        return {
            "verified": False,
            "matched_keywords": matched,
            "missing_keywords": missing,
            "source_excerpt": src[:300],
            "reason": f"source missing: {', '.join(missing)}",
        }

    return {
        "verified": True,
        "matched_keywords": matched,
        "missing_keywords": [],
        "source_excerpt": src[:300],
        "reason": "all keywords matched",
    }
