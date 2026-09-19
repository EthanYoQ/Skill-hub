"""把药品提及与文中 citation 锚点关联(就近匹配)。

策略层级:
1. 同句子(在最近的"句末标点"之间)→ 最优
2. 同段落(以 "\\n\\n" 或 "\\n" 划分)→ 次优
3. 跨段(无法关联)→ 视为 missing,critical violation

P0 守护:本模块只做位置匹配,**不**对锚点合法性 / 源是否存在做判断 — 那是 verifier 的事。
"""

from __future__ import annotations

import re

# 句末标点(中英文):用于划分句子
_SENT_END_RE = re.compile(r"[。!?!?\n]")

# 段落分隔:连续两个换行 / Markdown 段落空行
_PARA_SEP_RE = re.compile(r"\n\s*\n")


def _sentence_span(text: str, position: int) -> tuple[int, int]:
    """返回包含 position 的句子 [start, end)。"""
    if not text:
        return (0, 0)

    left = 0
    for i in range(position - 1, -1, -1):
        if _SENT_END_RE.match(text[i]):
            left = i + 1
            break

    right = len(text)
    for i in range(position, len(text)):
        if _SENT_END_RE.match(text[i]):
            right = i + 1
            break

    return (left, right)


def _paragraph_span(text: str, position: int) -> tuple[int, int]:
    """返回包含 position 的段落 [start, end)。"""
    if not text:
        return (0, 0)

    left = 0
    for m in _PARA_SEP_RE.finditer(text[:position]):
        left = m.end()

    right_match = _PARA_SEP_RE.search(text, position)
    right = right_match.start() if right_match else len(text)

    return (left, right)


def find_nearest_citation(
    mention_position: int,
    citations: list[dict],
    text: str,
) -> dict | None:
    """给定药品提及的位置,找到"最近"的 citation。

    Args:
        mention_position: 药名在原文中的起始位置
        citations: A11.parse_citations_in_text 返回的列表
        text: 原文(用于计算句子/段落边界)

    Returns:
        匹配到的 citation dict,或 None。

    匹配策略:
    1. 同句:位于 mention 所在句子内的所有锚点 → 取距离最近的
    2. 同段:位于 mention 所在段落内的所有锚点 → 取距离最近的
    3. 否则 → None
    """
    if not citations:
        return None

    sent_left, sent_right = _sentence_span(text, mention_position)
    para_left, para_right = _paragraph_span(text, mention_position)

    same_sentence: list[tuple[int, dict]] = []
    same_paragraph: list[tuple[int, dict]] = []

    for cit in citations:
        cpos = cit.get("position", -1)
        if cpos < 0:
            continue
        distance = abs(cpos - mention_position)
        if sent_left <= cpos < sent_right:
            same_sentence.append((distance, cit))
        elif para_left <= cpos < para_right:
            same_paragraph.append((distance, cit))

    if same_sentence:
        same_sentence.sort(key=lambda x: x[0])
        return same_sentence[0][1]

    if same_paragraph:
        same_paragraph.sort(key=lambda x: x[0])
        return same_paragraph[0][1]

    return None
