"""cn-clinical-guidelines-fetch — 顶层 fetcher。

公开 3 个函数：
- fetch_chinese_guidelines(disease, year_max, sources, cache_dir, sources_dir) -> dict
- cross_check_treatment_recommendations(proposed_recs, guidelines) -> dict
- locate_section_in_guideline(source_id, section, sources_dir) -> dict

Iron Law（中国市场调研 locale=zh-CN+geo=CN 时必跑，在 PubMed 召回之前）：
报告里所有治疗方案推荐必须命中指南 I 级 ≥ 1。

A1' v2 (Cite-or-Block 升级)：
新增 sources_dir 参数把抓到的原文存档供 A11 citation-anchor-resolver 锚点解析。
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# 本 skill 内部模块
import _csco
import _nccn
import _nmpa
import _cde
import _nhc
import _provenance  # Stage 3.1b 强约束级 (architect af265bdc 修订 2)

DEFAULT_SOURCES = ["csco", "nccn_zh", "nmpa", "cde", "nhc"]


def fetch_chinese_guidelines(
    disease: str,
    year_max: int | None = None,
    sources: list[str] | None = None,
    cache_dir: Path | None = None,
    sources_dir: Path | None = None,
) -> dict[str, Any]:
    """抓中国权威医学指南正文，返回结构化 "治疗推荐表"。

    Args:
        disease: 中文病种名（如 "ALK 融合阳性非小细胞肺癌"）。
        year_max: 最大年份，None = 最新版。
        sources: 来源列表，None = 全部 5 源（csco/nccn_zh/nmpa/cde/nhc）。
        cache_dir: 缓存目录，None = 不读写缓存。
        sources_dir: 若非 None，把抓到的原文存档到 sources_dir/guidelines/
            供 citation-anchor-resolver 解析 [guideline:<source_id>:§X.X.X]。

    Returns:
        {
            "csco": {"version": "2024", "source_id": "...", "raw_text": "...",
                     "treatment_table": [...]},
            "nccn_zh": {...},
            "nmpa_drug_status": [...],
            "cde": {...},
            "nhc": {...},
            "fetched_at": "ISO 8601",
            "sources_attempted": [...],
            "sources_succeeded": [...],
        }
    """
    if sources is None:
        sources = list(DEFAULT_SOURCES)
    if cache_dir is not None:
        cache_dir = Path(cache_dir)
        cache_dir.mkdir(parents=True, exist_ok=True)
    if sources_dir is not None:
        sources_dir = Path(sources_dir)
        (sources_dir / "guidelines").mkdir(parents=True, exist_ok=True)

    result: dict[str, Any] = {
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "sources_attempted": list(sources),
        "sources_succeeded": [],
    }

    fetchers = {
        "csco": _csco.fetch_csco,
        "nccn_zh": _nccn.fetch_nccn_zh,
        "nmpa": _nmpa.fetch_nmpa_drug_status,
        "cde": _cde.fetch_cde,
        "nhc": _nhc.fetch_nhc,
    }

    for src in sources:
        fn = fetchers.get(src)
        if fn is None:
            continue
        try:
            data = fn(
                disease=disease,
                year_max=year_max,
                cache_dir=cache_dir,
                sources_dir=sources_dir,
            )
            if data is None:
                continue
            # NMPA 用专门的键
            if src == "nmpa":
                result["nmpa_drug_status"] = data
            else:
                # Stage 3.1b 强约束: 给每个有 raw_text + source_id 的源加 provenance
                # (architect af565bdc 修订 2 — 真改 fetcher.py + _raw/ + checksum)
                if (
                    sources_dir is not None
                    and isinstance(data, dict)
                    and data.get("raw_text")
                    and data.get("source_id")
                ):
                    endpoint = data.get("source_url") or _DEFAULT_ENDPOINTS.get(src, "<unknown-endpoint>")
                    data = _provenance.attach_provenance_to_guideline(
                        guideline_data=data,
                        raw_text=data["raw_text"],
                        sources_dir=sources_dir,
                        source_id=data["source_id"],
                        endpoint=endpoint,
                    )
                result[src] = data
            result["sources_succeeded"].append(src)
        except Exception as exc:  # noqa: BLE001
            # 单源失败不阻塞其它源
            result.setdefault("source_errors", {})[src] = str(exc)

    return result


# Stage 3.1b: 默认 endpoint 表 (用于 fetcher 没回传 source_url 时的 provenance.endpoint)
# 真实抓取实现 (_csco.py 等) 应在结果 dict 里返回 source_url, 此表是 fallback。
_DEFAULT_ENDPOINTS: dict[str, str] = {
    "csco": "https://www.csco.org.cn/guidelines/",
    "nccn_zh": "https://www.nccn.org/guidelines/category_chinese",
    "cde": "https://www.cde.org.cn/main/news/listpage/",
    "nhc": "http://www.nhc.gov.cn/wjw/",
}


def locate_section_in_guideline(
    source_id: str,
    section: str,
    sources_dir: Path | str,
) -> dict[str, Any]:
    """从已存档指南原文中切出指定章节。

    Args:
        source_id: 指南 source_id（如 "CSCO-2024-NSCLC"）
        section: 章节标记（如 "§5.5.2"）
        sources_dir: 原文存档目录（含 guidelines/ 子目录）

    Returns:
        {
            "source_id": ...,
            "section": ...,
            "text": "章节正文",
            "start_line": int,
            "end_line": int,
            "anchor_str": "[guideline:<source_id>:<section>]",
        }

    P0 守护：
    - 文件 / toc 不存在 → 抛 FileNotFoundError，不 fallback 到内置答案
    - 章节在 toc 里找不到 → 抛 KeyError
    """
    g_dir = Path(sources_dir) / "guidelines"
    txt_path = g_dir / f"{source_id}.txt"
    toc_path = g_dir / f"{source_id}.toc.json"

    if not txt_path.is_file():
        raise FileNotFoundError(
            f"Guideline source not archived: {txt_path}"
        )
    if not toc_path.is_file():
        raise FileNotFoundError(
            f"Guideline toc not archived: {toc_path}"
        )

    raw_text = txt_path.read_text(encoding="utf-8")
    toc = json.loads(toc_path.read_text(encoding="utf-8"))

    if section not in toc:
        raise KeyError(
            f"Section {section} not in {source_id} toc "
            f"(available: {sorted(toc.keys())})"
        )

    entry = toc[section]
    start_line = int(entry["start_line"])
    end_line = int(entry["end_line"])
    lines = raw_text.splitlines()
    section_text = "\n".join(lines[start_line - 1 : end_line])

    return {
        "source_id": source_id,
        "section": section,
        "text": section_text,
        "start_line": start_line,
        "end_line": end_line,
        "anchor_str": f"[guideline:{source_id}:{section}]",
    }


def cross_check_treatment_recommendations(
    proposed_recs: list[dict[str, Any]],
    guidelines: dict[str, Any],
) -> dict[str, Any]:
    """检查 proposed_recs 是否命中指南 I 级推荐。

    Args:
        proposed_recs: 报告里准备写的治疗方案,
            形如 [{"line": "1L", "drugs": ["<药名 A>", "<药名 B>"]}, ...]。
        guidelines: fetch_chinese_guidelines 返回的指南数据。

    Returns:
        {
            "ok": bool,
            "guideline_hits": [...],
            "missing_guideline_drugs": [...],
            "extra_drugs_not_in_guideline": [...],
            "violation_severity": "none" | "warning" | "critical",
        }
    """
    # 收集指南所有 I 级药物（按 line 分组）
    guideline_i_by_line: dict[str, set[str]] = {}
    for src_key in ("csco", "nccn_zh"):
        src_data = guidelines.get(src_key)
        if not src_data:
            continue
        table = src_data.get("treatment_table", [])
        for item in table:
            if item.get("level") != "I":
                continue
            line = str(item.get("line", "")).strip()
            drug = str(item.get("drug", "")).strip()
            if not line or not drug:
                continue
            guideline_i_by_line.setdefault(line, set()).add(drug)

    # 收集 proposed 提到的药物（按 line 分组）
    proposed_by_line: dict[str, set[str]] = {}
    for rec in proposed_recs:
        line = str(rec.get("line", "")).strip()
        drugs = rec.get("drugs", []) or []
        proposed_by_line.setdefault(line, set()).update(
            str(d).strip() for d in drugs
        )

    hits: list[dict[str, str]] = []
    missing: list[str] = []
    extra: list[str] = []

    # 在 guideline 涉及的每个 line 上做命中分析
    for line, gl_drugs in guideline_i_by_line.items():
        proposed_drugs = proposed_by_line.get(line, set())
        # 命中：guideline I 级药物里在 proposed 中（substring 也算）
        hit_set: set[str] = set()
        for gd in gl_drugs:
            if any(gd in pd or pd in gd for pd in proposed_drugs):
                hit_set.add(gd)
                hits.append({"line": line, "drug": gd})
        # 缺失：指南 I 级有但 proposed 没有
        for gd in gl_drugs - hit_set:
            missing.append(gd)

    # extra：proposed 提了但任何 line 的指南 I 级都不在
    all_guideline_drugs: set[str] = set()
    for s in guideline_i_by_line.values():
        all_guideline_drugs.update(s)
    for line, proposed_drugs in proposed_by_line.items():
        for pd in proposed_drugs:
            in_guideline = any(
                pd in gd or gd in pd for gd in all_guideline_drugs
            )
            if not in_guideline:
                extra.append(pd)

    # 严重性判定
    severity = _severity(
        guideline_i_by_line, proposed_by_line, hits
    )

    ok = severity in ("none",)
    return {
        "ok": ok,
        "guideline_hits": hits,
        "missing_guideline_drugs": missing,
        "extra_drugs_not_in_guideline": extra,
        "violation_severity": severity,
    }


def _severity(
    guideline_i_by_line: dict[str, set[str]],
    proposed_by_line: dict[str, set[str]],
    hits: list[dict[str, str]],
) -> str:
    """决定 violation_severity。

    规则：
    - 任意 line 的指南 I 级药物 → proposed 完全没命中 → critical
    - 部分命中（>= 1 个但不全）→ warning
    - 全部命中 → none
    - 指南没数据 → none
    """
    if not guideline_i_by_line:
        return "none"

    any_critical = False
    any_partial = False
    any_full = False

    for line, gl_drugs in guideline_i_by_line.items():
        if not gl_drugs:
            continue
        proposed_drugs = proposed_by_line.get(line, set())
        # 计算 line 上的命中数
        line_hits = sum(
            1
            for gd in gl_drugs
            if any(gd in pd or pd in gd for pd in proposed_drugs)
        )
        if line_hits == 0:
            any_critical = True
        elif line_hits < len(gl_drugs):
            any_partial = True
        else:
            any_full = True

    if any_critical:
        return "critical"
    if any_partial:
        return "warning"
    if any_full:
        return "none"
    return "none"
