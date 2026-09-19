---
name: cn-clinical-guidelines-fetch
description: 抓中国权威医学指南正文（CSCO / NCCN 中文版 / NMPA / CDE / NHC）并返回结构化"治疗推荐表"。当用户做中国市场的疾病调研、需要 I 级证据来源、或需要交叉验证治疗方案推荐是否符合 CSCO 指南时使用。v2 (2026-04-26)：Cite-or-Block 升级 — 加 sources_dir 参数完整存档原文 + locate_section_in_guideline 函数，与 citation-anchor-resolver 联动。Iron Law：locale=zh-CN+geo=CN 时本 skill 在 PubMed 召回之前必跑，所有治疗方案推荐必须命中指南 I 级 ≥ 1 个。Fetches Chinese authoritative clinical guidelines (CSCO, NCCN-zh, NMPA, CDE, NHC) and returns structured "treatment recommendation tables". MUST run before PubMed recall when locale=zh-CN+geo=CN; all proposed treatment recs must hit at least one guideline Level-I drug.
keywords:
  - 中国指南
  - CSCO
  - NCCN 中文
  - NMPA
  - CDE
  - 国家卫健委
  - 治疗推荐
  - 临床路径
  - 一线治疗
  - I 级证据
  - chinese-clinical-guidelines
  - guideline-priority
  - treatment-table
license: MIT
---

# CN Clinical Guidelines Fetch

抓中国权威医学指南正文，转成结构化"治疗推荐表"。供 orchestration 流水线在召回阶段之前调用，作为 I 级证据来源。**只做指南抓取与 cross-check，不做检索、不做证据评分、不做 LP 嵌入。**

## Iron Law（违反此条 = 报告作废）

> **中国市场调研 (locale=zh-CN + market_geo=CN) 时本 skill 必跑，且必须在 PubMed 召回之前。**
>
> 报告里所有治疗方案推荐必须命中指南 I 级 ≥ 1 个药；
> 否则 cross_check_treatment_recommendations 返回 `severity=critical`，
> orchestration 必须强制重生成或把 §"治疗方案" 改为 placeholder + 红色警告。
>
> 指南证据等级：Practice Guideline = **I 级证据**，凌驾于 PubMed 任何 RCT / Meta / SR。
> 报告里所有治疗方案推荐必须以指南为锚，PubMed 文献只能补充"机制 / 真实世界数据 / 罕见亚群"。

## 1. 何时使用

触发场景：
- "做 ALK+ NSCLC 中国市场调研" / "侵袭性真菌中国市场" / "做血液科 IFI 报告" → 在召回之前先跑本 skill
- "查 CSCO 一线推荐 / 查指南 I 级 / 查 NCCN 中文" → 直接调用
- "我准备写治疗方案章节，先 cross-check 指南" → 调 cross_check_treatment_recommendations
- "查 NMPA 这药批了没 / 适应症什么"

不要使用本 skill：
- 全球市场（market_geo != CN）→ P2 task 加 NCCN 英文 + ESMO + WHO Essential Medicines fetcher
- 只要文献证据评分 → 用 medical-evidence-grading（其会把本 skill 的指南标 I 级）
- 只要药物的中文通用名↔商品名映射 → 用 nmpa-drug-registry-lookup（A5）

## 2. 跨 skill 协作（显式）

| 上游 / 下游 skill | 协作方式 |
|------------------|----------|
| `disease-market-sizing-orchestration` | **调用方**，市场调研 Step 0（在 Step 1 召回之前）调本 skill |
| `pubmed-eutils` | **下游**，本 skill 先跑，PubMed 召回作为补充证据 |
| `medical-evidence-grading` | **下游**，把本 skill 抓的指南打 I 级标签（最高） |
| `nmpa-drug-registry-lookup`（A5） | **同级 / 替换**，本 skill 的 `_nmpa.py` 当前是 minimal stub，A5 stable 后 refactor 复用 |

## 3. 公开函数

### 3.1 fetch_chinese_guidelines

```python
def fetch_chinese_guidelines(
    disease: str,                      # e.g. "ALK 融合阳性非小细胞肺癌"
    year_max: int | None = None,       # None = 最新版
    sources: list[str] | None = None,  # None = 全部 5 源
    cache_dir: Path | None = None,     # .cache/<slug>/guidelines/
    sources_dir: Path | None = None,   # v2: 原文存档目录，对接 A11
) -> dict:
    """返回结构化指南数据。

    Returns:
        {
            "csco":    {"version": "2024", "url": "...", "treatment_table": [...]},
            "nccn_zh": {...},
            "nmpa_drug_status": [{"drug":"阿来替尼","approval":"2018-08","indications":[...]}, ...],
            "cde":     {...},
            "nhc":     {...},
            "fetched_at":         "ISO 8601",
            "sources_attempted":  [...],
            "sources_succeeded":  [...],
            "source_errors":      {"csco": "..."},  # 仅在某源失败时
        }
    """
```

`sources` 可选项：`["csco", "nccn_zh", "nmpa", "cde", "nhc"]`。CSCO 默认最高优先级。

### 3.2 cross_check_treatment_recommendations

```python
def cross_check_treatment_recommendations(
    proposed_recs: list[dict],   # [{"line": "1L", "drugs": [...]}]
    guidelines: dict,            # fetch 返回的指南数据
) -> dict:
    """检查 proposed_recs 是否命中指南 I 级推荐。

    Returns:
        {
            "ok": bool,
            "guideline_hits":              [{"line":"1L","drug":"洛拉替尼"}, ...],
            "missing_guideline_drugs":     [...],   # 指南 I 级有 但 proposed 漏
            "extra_drugs_not_in_guideline":[...],   # proposed 写了但指南没有
            "violation_severity":          "none" | "warning" | "critical",
        }
    """
```

**严重性规则**：
- `critical` = 任意 line 上指南 I 级药物 → proposed 完全没命中
- `warning`  = 部分命中（>= 1 个但不全）
- `none`     = 全部命中 / 指南没数据

### 3.3 locate_section_in_guideline (v2)

```python
def locate_section_in_guideline(
    source_id: str,                  # e.g. "CSCO-2024-NSCLC"
    section: str,                    # e.g. "§5.5.2"
    sources_dir: Path | str,         # 原文存档目录
) -> dict:
    """
    Returns:
        {
          "source_id":   ...,
          "section":     ...,
          "text":        "章节正文",
          "start_line":  int,
          "end_line":    int,
          "anchor_str":  "[guideline:CSCO-2024-NSCLC:§5.5.2]",
        }
    """
```

P0 守护：文件 / toc 不存在 → `FileNotFoundError`；章节在 toc 里找不到 → `KeyError`；
**绝不**回退到内置答案。

## 4. Cite-or-Block 原文存档 (v2)

当调用 `fetch_chinese_guidelines(..., sources_dir=Path(".cache/<slug>/sources"))` 时，
本 skill 把抓到的指南原文写到：

```
sources_dir/
└── guidelines/
    ├── CSCO-2024-NSCLC.txt        ← 原文（UTF-8）
    ├── CSCO-2024-NSCLC.toc.json   ← {"§5.5.2": {"start_line": 18, "end_line": 28}, ...}
    └── CSCO-2024-NSCLC.meta.json  ← {"version", "url", "disease", "archived_at", ...}
```

下游 `citation-anchor-resolver.resolve_citation(anchor, sources_dir)` 即可解析
`[guideline:CSCO-2024-NSCLC:§5.5.2]` → 章节正文，配合关键词核对实现 Cite-or-Block。

`locate_section_in_guideline` 是同一存档结构的更高层 API，多返一份行号 + anchor_str。

## 5. 数据源（按优先级）

| 来源 | 用途 | 抓取方式 |
|-----|------|---------|
| **CSCO**（中国临床肿瘤学会） | 肿瘤精准医疗首选 | 公开 PDF / HTML，WebFetch + PDF 解析 |
| **NCCN 中文版** | 全球指南本地化 | 公开 HTML，WebFetch（P2 stub） |
| **NMPA**（国家药监局） | 药物上市状态 + 适应症 | nmpa.gov.cn 数据库（minimal，TODO refactor to A5） |
| **CDE**（药品审评中心） | 临床试验技术审评 | cde.org.cn（P2 stub） |
| **NHC**（国家卫健委） | 诊疗规范（部分病种） | nhc.gov.cn（P2 stub） |

详见 `references/source-priority.md`。

## 6. 失败容错

| 场景 | 处置 |
|-----|------|
| CSCO 网站当下不可达 | fall back 到 `cache_dir/csco_<slug>.json`（若 < 7 天） |
| `cache_dir is None` 且远程抓不到 | 回退 hardcoded fixture（仅 ALK+ NSCLC 等少数 ground-truth 病种） |
| `cache_dir` 提供但 cache miss + 远程 fail | 抛 `RuntimeError`，调用方在 `sources_succeeded` 不写 csco |
| 指南 PDF 解析失败 | 用 HTML 版本，失败再用文件名拼接的章节标题 |
| 全部指南来源都失败 | manifest 标 `guideline_fetch_failed: True`，报告 §0 红色警告 + 不阻塞流水线但产物视为 draft |
| cross-check critical violation | 重生成 1 次，仍违规 → 强制把 §"治疗方案" 改为 placeholder + warning |

详见 `references/failure-modes.md`。

## 7. Schema

`treatment_table` item 结构：

```python
{
    "line":     "1L" | "2L" | "3L" | "Maintenance" | "Adjuvant",
    "level":    "I" | "II" | "III",            # CSCO 推荐等级
    "drug":     "洛拉替尼",                    # 中文通用名
    "drug_en":  "Lorlatinib",                  # 可选 英文通用名
    "category": "三代 ALK-TKI",                # 可选 药物类别
    "regimen":  "..." ,                        # 可选 联合方案（非单药时）
}
```

详见 `references/treatment-table-schema.md`。

## 8. 已知限制 / TODO

- `_nmpa.py` 当前是 minimal hardcoded（仅 ALK+ NSCLC 八种 ALK-TKI），TODO：A5（nmpa-drug-registry-lookup）stable 后 refactor 复用
- `_nccn.py` / `_cde.py` / `_nhc.py` 当前是 stub，返回 None
- CSCO 反爬严重，当前依赖 hardcoded fixture（基于 CSCO 2024 公开发布版的 ALK+ NSCLC §5.5.2 表格）。P2 task：完整 PDF 章节解析

## 9. 依赖

- Python 3.10+
- `httpx` —— HTTP 请求
- `beautifulsoup4` —— HTML 解析（P2）
- `pypdf` —— PDF 章节解析
- `pyyaml` —— 配置（可选）

## 10. 测试

- `tests/test_cn_clinical_guidelines.py` 含 4 个核心测试：
  1. ALK+ NSCLC CSCO 一线 I 级 8 药全命中
  2. cross_check 漏掉所有 I 级一线药 → critical
  3. cross_check 部分命中 → warning / none
  4. CSCO 不可达 + 无缓存 → 不进 sources_succeeded
