"""NMPA 适应症 / 上市状态 fetcher（minimal）。

策略:
- 真实抓取 nmpa.gov.cn 公开数据库的工作 (P2 task) 留待将来实现。
- 当前对已抓到的 ALK+ NSCLC 8 种 ALK-TKI 上市快照,从
  references/<source_id>.json 在运行时读取,而非硬编码在 .py 源文件内
  (refactor cleanup 2 — 让 P0 watchdog 不必豁免本 skill)。
- 其他病种 fallback null,让流水线在缺数据时标 warning。
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


_REFERENCES_DIR = Path(__file__).resolve().parent.parent / "references"


def _load_drug_status(source_id: str) -> dict[str, Any] | None:
    """从 references/<source_id>.json 读取 NMPA 药物上市快照。"""
    path = _REFERENCES_DIR / f"{source_id}.json"
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _matches_filter(disease: str, payload: dict[str, Any]) -> bool:
    """根据 references json 的 disease_filter 字段判断病种命中。"""
    filt = payload.get("disease_filter", {}) or {}
    any_of = filt.get("any_of") or []
    all_of = filt.get("all_of") or []
    if all_of and not all(token in disease for token in all_of):
        return False
    if any_of and not any(token in disease for token in any_of):
        return False
    if not any_of and not all_of:
        return False
    return True


def fetch_nmpa_drug_status(
    disease: str,
    year_max: int | None = None,
    cache_dir: Path | None = None,
    sources_dir: Path | None = None,
) -> list[dict[str, Any]] | None:
    """NMPA 药物上市状态查询。

    返回 list[{"drug","approval","indications"}]，上层 fetcher 合并到
    result["nmpa_drug_status"]。

    病种映射逻辑:
    1. ALK + (NSCLC 或 肺癌) 关键词命中 → 读 NMPA-ALK-TKI-status.json 快照
    2. 其它病种 fallback None,让流水线标 warning(避免凭空伪造数据)
    """
    if "ALK" in disease and ("NSCLC" in disease or "肺癌" in disease):
        payload = _load_drug_status("NMPA-ALK-TKI-status")
        if payload is None:
            return None
        if not _matches_filter(disease, payload):
            return None
        return [dict(d) for d in payload.get("drug_status", [])]
    return None
