"""中英文混合关键词在源文本里的核对。

P0 守护:
- 严格 substring 匹配(经过文本规范化:全角→半角、统一空白、统一大小写)
- **不**做语义匹配(不调 LLM、不查 embedding)
- **不**维护"已知关键词字典"

候选关键词提取(用于 verify_claim_against_source 的默认关键词):
- 中文:连续 ≥ 2 字的汉字串
- 英文/数字/连字符:连续 ≥ 2 字符的 [A-Za-z0-9-] 串
- 单纯虚词(stop tokens)排除:仅过滤特别明显的虚词,不维护任何"业务字典"
"""

from __future__ import annotations

import re
import unicodedata


# 极小的虚词集合(中英文通用虚词,与业务领域无关)
# P0 注:此集合**不是**业务知识字典(没有任何药品/疾病/数字等业务词),
# 仅为"中文连接词 + 英文冠词介词"层面的去噪。
_STOP_TOKENS: frozenset[str] = frozenset(
    {
        # 中文虚词
        "的", "和", "与", "及", "在", "是", "为", "对", "等",
        "把", "被", "向", "从", "了", "也",
        # 英文冠词介词连词
        "the", "a", "an", "of", "in", "on", "to", "and", "or",
        "is", "are", "was", "were", "be", "for", "with", "by",
        "at", "as", "from", "this", "that",
    }
)


# 中文连续汉字 ≥ 2
_CJK_RUN_RE = re.compile(r"[一-鿿]{2,}")
# 英文/数字/连字符 ≥ 2
_LATIN_RUN_RE = re.compile(r"[A-Za-z][A-Za-z0-9\-]{1,}|\d{2,}")


def normalize_text(text: str) -> str:
    """文本规范化:NFKC(全角→半角)+ 统一空白 + 小写。

    NFKC 会把全角数字/字母/标点折成半角,把全角中文标点保持中文标点;
    Unicode 数字仅在为半角时进入后续匹配。这一步是无损的形式转换,
    不引入"已知词表"。
    """
    if text is None:
        return ""
    norm = unicodedata.normalize("NFKC", text)
    # 折叠所有空白(空格/制表符/换行)为单空格
    norm = re.sub(r"\s+", " ", norm)
    return norm.lower()


def normalize_for_match(text: str) -> str:
    """用于子串匹配的更宽松规范化:在 normalize_text 基础上去掉所有空白。

    这样 ``"PFS 24 月"`` 与 ``"PFS24月"`` 能匹配。
    """
    return re.sub(r"\s+", "", normalize_text(text))


def extract_candidate_keywords(claim_text: str) -> list[str]:
    """从一段 claim 文本里提取候选关键词(无源)。

    规则:
    - 中文连续汉字串 ≥ 2 字
    - 英文/数字 token ≥ 2 字符
    - 去掉极小虚词集合
    - 去重保序

    P0 注:本函数只是"切词去虚词",不维护任何业务字典。
    用于显式 keywords 路径之外的场景(如 introspection 用)。
    """
    if not claim_text:
        return []

    candidates: list[str] = []

    for m in _CJK_RUN_RE.finditer(claim_text):
        candidates.append(m.group(0))
    for m in _LATIN_RUN_RE.finditer(claim_text):
        candidates.append(m.group(0))

    seen: set[str] = set()
    out: list[str] = []
    for k in candidates:
        key = k.lower()
        if key in _STOP_TOKENS:
            continue
        if key in seen:
            continue
        seen.add(key)
        out.append(k)
    return out


def keyword_in_source(keyword: str, source_text: str) -> bool:
    """判断 keyword 是否在 source_text 里(经规范化后的子串匹配)。"""
    if not keyword or not source_text:
        return False
    kw = normalize_for_match(keyword)
    if not kw:
        return False
    src = normalize_for_match(source_text)
    return kw in src


def match_keywords(
    keywords: list[str], source_text: str
) -> tuple[list[str], list[str]]:
    """对一组显式关键词逐一核对。

    Returns:
        (matched, missing)
    """
    matched: list[str] = []
    missing: list[str] = []
    for kw in keywords:
        if keyword_in_source(kw, source_text):
            matched.append(kw)
        else:
            missing.append(kw)
    return matched, missing


# ---------------------------------------------------------------------------
# 源驱动的 claim 切片(auto 模式核心)
# ---------------------------------------------------------------------------


def _greedy_longest_match_split(
    run: str, source_norm: str, *, min_len: int = 2, max_len: int = 16
) -> tuple[list[str], list[str]]:
    """对单段连续文本(已规范化、无空白),贪心切出"在源里出现的最长子串"。

    Returns:
        (matched_pieces, missing_chars)

    - matched_pieces:claim 中能在源里找到的子串(连续、无重叠、贪心最长)
    - missing_chars:既不在任何匹配片段里、也不是极小虚词的"游离字符"
                    (用于触发 verified=False)

    P0 注:本函数完全由"源里有什么"驱动,不引入任何业务字典。
    """
    matched: list[str] = []
    missing: list[str] = []
    pos = 0
    n = len(run)

    while pos < n:
        # 试图在 pos 起 [min_len, max_len] 范围内找到最长存在的子串
        best_len = 0
        upper = min(n - pos, max_len)
        for L in range(upper, min_len - 1, -1):
            if run[pos : pos + L] in source_norm:
                best_len = L
                break

        if best_len >= min_len:
            matched.append(run[pos : pos + best_len])
            pos += best_len
        else:
            # 单字游离:虚词忽略,实词记 missing
            ch = run[pos]
            if ch not in _STOP_TOKENS:
                missing.append(ch)
            pos += 1

    return matched, missing


def auto_match_claim_to_source(
    claim_text: str, source_text: str
) -> tuple[list[str], list[str]]:
    """auto 模式:从 claim 抽出"在源里出现的最长片段",报告完整覆盖情况。

    返回:
        matched: 在源里找到的 claim 片段(中文连续汉字 + 英文数字 token)
        missing: claim 中既不在源、也非虚词的字符/token
                 (任一非空 → verified=False)

    P0 注:本函数 dictionary-free —— "字典"就是源本身。
    """
    if not claim_text:
        return [], []

    src_norm = normalize_for_match(source_text or "")

    matched_all: list[str] = []
    missing_all: list[str] = []

    # 1. 中文连续汉字串
    for m in _CJK_RUN_RE.finditer(claim_text):
        run_norm = normalize_for_match(m.group(0))
        if not run_norm:
            continue
        matched, missing = _greedy_longest_match_split(run_norm, src_norm)
        matched_all.extend(matched)
        missing_all.extend(missing)
        # 富化:对长度 ≥ 4 的 matched chunk,补充长度 2-4 的子串
        # (要求子串本身也在源里出现 —— 仍是 source-driven,无业务字典)
        for chunk in matched:
            if len(chunk) >= 4:
                for window in (2, 3, 4):
                    for i in range(0, len(chunk) - window + 1):
                        sub = chunk[i : i + window]
                        if sub == chunk:
                            continue
                        if sub in src_norm:
                            matched_all.append(sub)

    # 2. 英文/数字 token(整体匹配,失败即 missing)
    for m in _LATIN_RUN_RE.finditer(claim_text):
        token = m.group(0)
        if token.lower() in _STOP_TOKENS:
            continue
        token_norm = normalize_for_match(token)
        if not token_norm:
            continue
        if token_norm in src_norm:
            matched_all.append(token)
        else:
            missing_all.append(token)

    # 去重保序
    def _dedup(seq: list[str]) -> list[str]:
        seen: set[str] = set()
        out: list[str] = []
        for s in seq:
            key = s.lower()
            if key in seen:
                continue
            seen.add(key)
            out.append(s)
        return out

    return _dedup(matched_all), _dedup(missing_all)
