"""R2 Phase-2-Quality-Fix · T1: token classifier.

把 claim 文本切分为 (decisive, non_decisive) 两类 token,服务 verifier Tier 1 substring 检查:
- decisive: 代号药 / NCT id / PMID / 中文药名后缀 — 1 个不命中即 Tier 1 fail
- non_decisive: 病种通名 / HER2± 状态 / 数字单位 / 章节词 — 用 ≥ 70% hit rate

P0 设计意图: 全部基于正则模式识别,**不维护任何药名/疾病名穷举字典**(Cite-or-Block 铁律)。
"""
from __future__ import annotations

import re
from typing import List, Tuple

# decisive token 正则 (P0: 模式识别, 非字典)
_DRUG_CODE_RE = re.compile(r"\b[A-Z]{2,4}-[A-Z]\d{3,5}\b")  # SHR-A1811 必须字母前缀, 不匹配年份型 DEMO-2024
_RC_DRUG_RE = re.compile(r"\bRC\d+\b")  # RC48
_NCT_RE = re.compile(r"\bNCT\d{8}\b")
_PMID_RE = re.compile(r"PMID[:\s]?(\d{6,9})\b")
_CHINESE_DRUG_RE = re.compile(
    r"[一-鿿]{2}(?:替尼|单抗|司他|那尼|那肽|妥珠|鲁肽|那珠|拉肽|西尼)"
)


def classify_tokens(claim_text: str) -> Tuple[List[str], List[str]]:
    """把 claim 切成 (decisive, non_decisive) 两类 token.

    Args:
        claim_text: 自然语言 claim, 例如 "SHR-A1811 III 期 HER2+ MBC".

    Returns:
        (decisive, non_decisive): 两个去重保序的 list[str].
    """
    decisive: List[str] = []
    decisive.extend(_DRUG_CODE_RE.findall(claim_text))
    decisive.extend(_RC_DRUG_RE.findall(claim_text))
    decisive.extend(_NCT_RE.findall(claim_text))
    decisive.extend(_PMID_RE.findall(claim_text))
    decisive.extend(_CHINESE_DRUG_RE.findall(claim_text))
    decisive = list(dict.fromkeys(decisive))  # dedupe 保序

    word_re = re.compile(r"[一-鿿A-Za-z0-9]{2,}")
    all_words = word_re.findall(claim_text)
    non_decisive = [w for w in all_words if w not in decisive and len(w) >= 2]
    non_decisive = list(dict.fromkeys(non_decisive))

    return decisive, non_decisive
