"""drug-citation-verifier — 公开 API。

只 1 个公开函数:``verify_drug_mentions_in_text``

工作流:
1. ``_drug_extract.extract_drug_mentions_with_context(text)`` — 命名学抽取疑似药提及
2. A11.``parse_citations_in_text(text)`` — 找文中所有 citation 锚点
3. ``_citation_match.find_nearest_citation(...)`` — 对每个药提及找最近锚点
4. A11.``verify_claim_against_source(...)`` — 拿"药名 + 商品名"组合短语去核对源
5. 计算 violation_severity

P0 守护:
- 任何"已知药品列表" / "fallback 字典" 都禁止
- 抽取后必须**核对源**才能判定;源里没 → critical
- 不依赖任何"查表式"药品库 skill(老 A5 已作废)
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# 加载 A11 citation-anchor-resolver
# ---------------------------------------------------------------------------

_A11_SCRIPTS = Path.home() / ".claude" / "skills" / "citation-anchor-resolver" / "scripts"
if _A11_SCRIPTS.exists() and str(_A11_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_A11_SCRIPTS))

try:  # pragma: no cover
    from .resolver import (  # type: ignore
        parse_citations_in_text,
        verify_claim_against_source,
    )
except ImportError:  # pragma: no cover
    from resolver import (  # type: ignore
        parse_citations_in_text,
        verify_claim_against_source,
    )

try:  # pragma: no cover
    from ._drug_extract import extract_drug_mentions_with_context
    from ._citation_match import find_nearest_citation
except ImportError:  # pragma: no cover
    from _drug_extract import extract_drug_mentions_with_context  # type: ignore
    from _citation_match import find_nearest_citation  # type: ignore


__all__ = ["verify_drug_mentions_in_text"]


def _split_brand(brand: str) -> list[str]:
    """把括号注释拆成关键词:可能是 "商品名:<品牌>;<英文名>" 等。

    简单按常见分隔符切;空白/标点之间的 token 都纳入。
    每个 token 之后都会送到 A11 严格 substring 核对源。
    """
    raw = re.split(r"[,;,;:::/\s]+", brand)
    out: list[str] = []
    for token in raw:
        token = token.strip()
        if not token:
            continue
        # 过滤掉常见标签词(非药名)
        if token in {"商品名", "通用名", "原研", "英文名", "Brand", "Generic"}:
            continue
        out.append(token)
    return out


def _build_claim_phrase(mention: dict) -> tuple[str, list[str]]:
    """把"药名 + 商品名"组合成一条 claim,用于送到 A11 核对。

    Returns:
        (claim_text, keywords):
        - claim_text:用于显示 / 上下文
        - keywords:严格 substring 核对的关键词列表(药名,商品名,英文名)
    """
    name = mention.get("text", "").strip()
    brand = mention.get("brand_in_context", "").strip()
    keywords: list[str] = []
    if name:
        keywords.append(name)
    if brand:
        for piece in _split_brand(brand):
            if piece and piece not in keywords:
                keywords.append(piece)

    if brand:
        claim = f"{name}({brand})"
    else:
        claim = name
    return claim, keywords


def _severity_from_mentions(mentions: list[dict]) -> str:
    has_critical = any(m.get("severity") == "critical" for m in mentions)
    if has_critical:
        return "critical"
    has_warning = any(m.get("severity") == "warning" for m in mentions)
    if has_warning:
        return "warning"
    return "none"


def verify_drug_mentions_in_text(
    text: str,
    sources_dir: Path | str,
) -> dict[str, Any]:
    """扫描每个药品提及 → 看是否带 citation → 核对源。

    Args:
        text: 报告 HTML/Markdown 段落
        sources_dir: 源材料根目录(``.cache/<slug>/sources/``)

    Returns:
        {
            "ok": bool,
            "drug_mentions": [
                {
                    "text": "<通用名>",
                    "brand_in_context": "<括号内容>",
                    "citation": "<anchor>" | None,
                    "verified": True/False,
                    "missing_in_source": [...],
                    "reason": "...",
                    "severity": "none" | "warning" | "critical",
                },
                ...
            ],
            "violation_severity": "none" | "warning" | "critical",
        }

    P0 守护:
    - 文中无任何疑似药 → ok=True, severity=none
    - 药提及但**无 citation** → critical
    - 有 citation 但源里没此药 → critical
    """
    sources_path = Path(sources_dir)

    drug_mentions = extract_drug_mentions_with_context(text or "")
    if not drug_mentions:
        return {
            "ok": True,
            "drug_mentions": [],
            "violation_severity": "none",
        }

    citations = parse_citations_in_text(text or "")

    out_mentions: list[dict] = []
    for mention in drug_mentions:
        claim, keywords = _build_claim_phrase(mention)
        nearest = find_nearest_citation(
            mention["position"],
            citations,
            text or "",
        )

        if nearest is None:
            out_mentions.append(
                {
                    "text": mention["text"],
                    "brand_in_context": mention.get("brand_in_context", ""),
                    "citation": None,
                    "verified": False,
                    "missing_in_source": keywords,
                    "reason": "no citation near drug mention",
                    "severity": "critical",
                }
            )
            continue

        anchor_str = nearest.get("anchor_str", "")
        anchor_obj = nearest.get("anchor")
        verify_result = verify_claim_against_source(
            claim,
            anchor_obj if anchor_obj is not None else anchor_str,
            sources_path,
            keywords=keywords,
        )

        verified = bool(verify_result.get("verified", False))
        missing = list(verify_result.get("missing_keywords", []))
        reason = verify_result.get("reason", "")

        out_mentions.append(
            {
                "text": mention["text"],
                "brand_in_context": mention.get("brand_in_context", ""),
                "citation": anchor_str,
                "verified": verified,
                "missing_in_source": missing,
                "reason": reason,
                "severity": "none" if verified else "critical",
            }
        )

    severity = _severity_from_mentions(out_mentions)
    return {
        "ok": severity == "none",
        "drug_mentions": out_mentions,
        "violation_severity": severity,
    }
