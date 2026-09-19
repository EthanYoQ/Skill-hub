"""nmpa-drug-registry-lookup · 核心 registry 模块。

提供 3 个公开函数 + DrugRecord dataclass + UnverifiedDrugError exception。

数据流:
    lookup_drug(name)
        ↓
    1. 查 cache(若 cache_dir 给定)
    2. 查 _known_drugs_fallback(权威 NMPA-validated 兜底)
    3. (可选) NMPA / CDE / DrugBank 在线抓取(默认关闭)
        ↓
    None 或 DrugRecord(frozen)

cross_check_drug_mentions(text):
    扫描文本中的药品名(优先用 fallback dict 的 alias index 做精确匹配),
    检测 LLM 凭记忆错位拼写"通用名↔商品名"的 critical 违规。

Iron Law: lookup 返回 None → 调用方必须 raise UnverifiedDrugError。
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from . import _cache
from ._known_drugs_fallback import (
    build_alias_to_generic_index,
    build_brand_to_generic_index,
    get_fallback_dict,
)


# --- Exceptions ---

class UnverifiedDrugError(Exception):
    """药品名 lookup 失败 → 调用方应 raise 此异常,拒绝写入报告。"""


# --- DrugRecord ---

@dataclass(frozen=True)
class DrugRecord:
    """中国药品权威记录。frozen=True 防止下游误改。"""

    generic_name_zh: str
    generic_name_en: str
    brand_names_zh: tuple[str, ...]
    brand_names_en: tuple[str, ...]
    nmpa_approval_no: str
    first_approval_date_cn: str
    indications_cn: tuple[str, ...]
    atc_code: str
    target: str
    drug_class: str
    sources: tuple[str, ...]

    @classmethod
    def from_dict(cls, d: dict) -> "DrugRecord":
        """从 dict 构造,自动把 list 转 tuple(frozen 兼容)。"""
        def _to_tuple(v: Any) -> tuple:
            if v is None:
                return ()
            if isinstance(v, (list, tuple)):
                return tuple(v)
            return (v,)

        return cls(
            generic_name_zh=d.get("generic_name_zh", ""),
            generic_name_en=d.get("generic_name_en", ""),
            brand_names_zh=_to_tuple(d.get("brand_names_zh", ())),
            brand_names_en=_to_tuple(d.get("brand_names_en", ())),
            nmpa_approval_no=d.get("nmpa_approval_no", ""),
            first_approval_date_cn=d.get("first_approval_date_cn", ""),
            indications_cn=_to_tuple(d.get("indications_cn", ())),
            atc_code=d.get("atc_code", ""),
            target=d.get("target", ""),
            drug_class=d.get("drug_class", ""),
            sources=_to_tuple(d.get("sources", ())),
        )

    def to_dict(self) -> dict:
        return {
            "generic_name_zh": self.generic_name_zh,
            "generic_name_en": self.generic_name_en,
            "brand_names_zh": list(self.brand_names_zh),
            "brand_names_en": list(self.brand_names_en),
            "nmpa_approval_no": self.nmpa_approval_no,
            "first_approval_date_cn": self.first_approval_date_cn,
            "indications_cn": list(self.indications_cn),
            "atc_code": self.atc_code,
            "target": self.target,
            "drug_class": self.drug_class,
            "sources": list(self.sources),
        }


# --- 公开函数 ---

def lookup_drug(
    name: str,
    market: str = "CN",
    cache_dir: Path | None = None,
) -> DrugRecord | None:
    """单药查询,返回完整记录 or None。

    匹配优先级:
    1. cache(若 cache_dir 给定且新鲜)
    2. _known_drugs_fallback 精确通用名命中
    3. _known_drugs_fallback 商品名/英文别名命中
    4. (未来) NMPA / CDE / DrugBank 在线抓取

    None = 该药不在权威数据库 → 调用方必须 raise UnverifiedDrugError。
    """
    if not name or not name.strip():
        return None

    name = name.strip()

    # 1. cache
    if cache_dir is not None:
        cache = _cache.load_cache(cache_dir)
        cached_dict = _cache.get_record(cache, name)
        if cached_dict:
            return DrugRecord.from_dict(cached_dict)

    # 2/3. fallback dict 命中(精确通用名 / 别名 / 商品名)
    fallback = get_fallback_dict()
    alias_idx = build_alias_to_generic_index()

    # 直接命中
    canonical_zh = alias_idx.get(name) or alias_idx.get(name.lower())
    if canonical_zh and canonical_zh in fallback:
        rec_dict = fallback[canonical_zh]
        record = DrugRecord.from_dict(rec_dict)
        if cache_dir is not None:
            _cache.save_record(cache_dir, name, record.to_dict())
        return record

    # 4. (在线抓取占位 — 默认 force_online=False,故跳过)
    # 可按需扩展:from . import _nmpa, _cde, _drugbank
    # 抓取失败时仍返回 None,调用方 raise UnverifiedDrugError

    return None


def lookup_drugs_batch(
    names: list[str],
    market: str = "CN",
    cache_dir: Path | None = None,
) -> dict[str, DrugRecord | None]:
    """批量查询。返回 {name: DrugRecord or None}。"""
    return {n: lookup_drug(n, market=market, cache_dir=cache_dir) for n in names}


def cross_check_drug_mentions(
    text: str,
    market: str = "CN",
    cache_dir: Path | None = None,
) -> dict:
    """扫描文本里所有疑似药品名,逐个 lookup,返回错误清单。

    检测两种 LLM 错误:
    1. 错位拼写: 文本说"X(商品名:Y)" 但 Y 实际是 Z 的商品名 → critical
    2. 未验证: 文本提到 Q,但 Q 不在权威数据库 → warning

    Returns:
        {
            "ok": bool,
            "verified_drugs": list[str],       # 命中权威数据库
            "unverified_drugs": list[str],     # 找不到 → 必须修
            "name_mismatches": list[dict],     # 错位
            "violation_severity": "none" | "warning" | "critical",
        }
    """
    if not text:
        return {
            "ok": True,
            "verified_drugs": [],
            "unverified_drugs": [],
            "name_mismatches": [],
            "violation_severity": "none",
        }

    fallback = get_fallback_dict()
    alias_idx = build_alias_to_generic_index()
    brand_idx = build_brand_to_generic_index()

    verified: list[str] = []
    unverified: list[str] = []
    mismatches: list[dict] = []

    # 第 1 步: 抓"通用名(商品名:XX)"或"通用名(商品名 XX)"模式
    # 中文括号 ( ) 和英文 () 都要支持
    paren_pattern = re.compile(
        r"([一-鿿]{2,8})\s*[\(（]\s*商品名[::]?\s*([一-鿿 A-Za-z]{2,30})"
    )
    for m in paren_pattern.finditer(text):
        claimed_generic = m.group(1).strip()
        claimed_brand = m.group(2).strip().split(",")[0].split(",")[0].strip()
        # 商品名 → 实际通用名
        actual_generic = brand_idx.get(claimed_brand) or brand_idx.get(claimed_brand.lower())
        if actual_generic and actual_generic != claimed_generic:
            mismatches.append({
                "text_uses": claimed_brand,
                "claimed_as": claimed_generic,
                "actual_generic": actual_generic,
                "evidence_source": "NMPA fallback dict",
            })

    # 第 2 步: 全文遍历所有 fallback dict 里出现的别名,统计 verified/unverified
    seen: set[str] = set()
    for alias, canonical in alias_idx.items():
        if alias in seen:
            continue
        if alias and alias in text:
            seen.add(alias)
            if canonical not in verified:
                verified.append(canonical)

    # 第 3 步: 抓文本中疑似药品名(中文 X 替尼/X 单抗/X 阿克 模式)
    # 简单启发式: 中文连续 2-6 字含"替尼"|"单抗"|"阿克"|"昔布"|"沙星"|"霉素" 的尾缀
    drug_suffix_pattern = re.compile(
        r"([一-鿿]{1,5}(?:替尼|单抗|阿克|昔布|沙星|霉素|拉唑|司他汀|沙坦))"
    )
    for m in drug_suffix_pattern.finditer(text):
        candidate = m.group(1)
        if candidate in alias_idx:
            continue  # 已 verified
        if candidate not in unverified:
            unverified.append(candidate)

    # 严重性
    if mismatches:
        severity = "critical"
        ok = False
    elif unverified:
        severity = "warning"
        ok = False
    else:
        severity = "none"
        ok = True

    return {
        "ok": ok,
        "verified_drugs": verified,
        "unverified_drugs": unverified,
        "name_mismatches": mismatches,
        "violation_severity": severity,
    }
