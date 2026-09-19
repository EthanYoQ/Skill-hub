"""Citation 锚点的 schema 与解析。

锚点格式:``[<source_type>:<source_id>:<locator>]``

- ``source_type``:8 种枚举(见 ``ALLOWED_SOURCE_TYPES``)
- ``source_id``:不含 ``:`` 与 ``]``,允许字母数字、下划线、连字符、点
- ``locator``:可空;包含章节号(§5.5.2)、行号(line:42)、行号区间(line:42-58)、
  关键字(abstract/title/results/methods 等)。允许内含一个 ``:``(如 ``line:42``)。

P0 守护:本模块仅做"字符串 → 数据类"的形式转换,不做任何"锚点是否真实存在"的判断,
也不维护任何"已知锚点字典"。
"""

from __future__ import annotations

import re
from dataclasses import dataclass


# 8 种 source_type 枚举
ALLOWED_SOURCE_TYPES: frozenset[str] = frozenset(
    {
        "guideline",
        "pmid",
        "nct",
        "aact",
        "europepmc",
        "bioc",
        "evidence",
        "nmpa-page",
    }
)


# 锚点正则:
# - source_type:    \w 含连字符
# - source_id:      除 ``:`` 与 ``]`` 外的任意非空
# - locator (opt):  除 ``]`` 外的任意非空(允许内含 ``:`` 用于 line:42)
_ANCHOR_RE = re.compile(
    r"\[([A-Za-z][\w-]*):([^:\]]+)(?::([^\]]+))?\]"
)


@dataclass(frozen=True)
class Citation:
    """单个 citation 锚点的结构化表示。

    Attributes:
        source_type: 8 种枚举之一(见 ``ALLOWED_SOURCE_TYPES``)
        source_id: 源 id(指南 slug / PMID / NCT / 文件名 / 批准文号 ...)
        locator: 章节号 / 行号 / 段名(可为空字符串)
        raw: 原始锚点字符串 ``[...]``
    """

    source_type: str
    source_id: str
    locator: str
    raw: str

    @property
    def is_known_source_type(self) -> bool:
        """source_type 是否在 8 种枚举内。"""
        return self.source_type in ALLOWED_SOURCE_TYPES


def parse_anchor(anchor_str: str) -> Citation | None:
    """把锚点字符串解析为 Citation。

    成功:返回 Citation。
    失败(格式不对 / 缺失必要字段):返回 None。

    注意:不校验 source_type 是否在枚举内,只校验形式。
    枚举校验交给上层(resolve_citation)。
    """
    if not isinstance(anchor_str, str):
        return None

    s = anchor_str.strip()
    if not s:
        return None

    # 必须严格地是单个完整锚点(允许两侧空白,但不允许其他内容)
    m = _ANCHOR_RE.fullmatch(s)
    if m is None:
        return None

    source_type = m.group(1).strip()
    source_id = m.group(2).strip()
    locator = (m.group(3) or "").strip()

    if not source_type or not source_id:
        return None

    return Citation(
        source_type=source_type,
        source_id=source_id,
        locator=locator,
        raw=s,
    )


def find_all_anchors(text: str) -> list[tuple[Citation, int, int]]:
    """在长文本里找出所有锚点。

    Returns:
        [(Citation, start_pos, end_pos), ...] 按出现顺序。
        非法格式的"假锚点"会被跳过(不报错)。
    """
    if not text:
        return []

    found: list[tuple[Citation, int, int]] = []
    for m in _ANCHOR_RE.finditer(text):
        raw = m.group(0)
        cit = parse_anchor(raw)
        if cit is not None:
            found.append((cit, m.start(), m.end()))
    return found
