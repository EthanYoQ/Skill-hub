# GRADE 自动评级完整规则表

> 本文档由 `medical-evidence-grading/SKILL.md` 引用。所有 GRADE 评级逻辑细节在此。

## Iron Law (不可违反)

**GRADE 评级前必须调用 `pubmed-eutils.efetch_pubmed()` 拿真实 publication_type；不可仅凭 title 推断。**

理由：title 含"randomized"未必是 RCT(可能是综述讨论 RCT);title 不含"meta"未必不是 Meta(可能简称 SR)。MeSH publication_type 由 NLM 索引员人工标注,是唯一权威来源。

---

## 评级输入

```
{
  "publication_types": [...],   # MeSH 标签数组,来自 efetch
  "abstract": str,               # 摘要全文
  "sample_size": int | None,     # 可选,来自 bioc-fulltext-fetch 抽取
  "journal": str,
  "year": int,
  "is_preprint": bool
}
```

---

## 评级表(完整)

### Grade A (最高质量,优先纳入)
- `Practice Guideline` / `Guideline`
- `Consensus Development Conference` / `Consensus Development Conference, NIH`
- `Meta-Analysis`
- `Systematic Review` (含 Cochrane Database Syst Rev)
- `Randomized Controlled Trial` AND n >= 1000
- `Clinical Trial, Phase III` AND multicenter AND n >= 500

### Grade B (高质量)
- `Randomized Controlled Trial` AND n < 1000
- `Clinical Trial, Phase III` (单中心或 n<500)
- `Multicenter Study` AND prospective AND n >= 200
- `Cohort Studies` AND n >= 500 AND prospective
- `Pragmatic Clinical Trial`

### Grade C (中等质量)
- `Cohort Studies` AND (n < 500 OR retrospective)
- `Case-Control Studies`
- `Cross-Sectional Studies`
- `Clinical Trial, Phase II`
- `Observational Study`
- `Comparative Study`(无随机化)

### Grade D (低质量,谨慎引用)
- `Case Reports`
- `Review` (非 systematic) / `Narrative Review`
- `Clinical Trial, Phase I`
- `Pilot Projects`
- Preprint (medRxiv / bioRxiv) → 标记 `Grade D-`(发表后升级至原本对应等级)

### EXCLUDED (自动剔除,不进入排序)
- `Editorial`
- `Letter`
- `Comment`
- `News`
- `Biography` / `Historical Article`
- `Retracted Publication` (除非用户在 query 中明确 `include_retracted=True`)
- `Published Erratum` (合并到原文)

---

## 降权信号(Grade 降一级)

每命中一条降权信号,grade 下移一级(A→B, B→C, C→D)。最多降两级。

1. 单中心研究(无 `Multicenter Study` tag)且 n < 500
2. 样本量 < 100 且非罕见病(罕见病定义见 `clinical-queries-mapping.md`)
3. 期刊 IF < 2.0(可选,需 NLM Catalog API,默认不启用)
4. 发表 > 10 年前 AND 该领域近 5 年有更新指南
5. 利益冲突未声明 OR 制药公司全资助且无独立 DSMB
6. 撤稿期刊(如 Surgery News 等被列入 watchlist)
7. 二次发表(`secondary publication` flag)

## 升权信号(Grade 升一级,极少使用)

仅当满足以下任一条件:
1. n > 10000 大型登记/真实世界研究
2. 期刊为 NEJM / Lancet / JAMA / BMJ / Nature Medicine 且为原创研究
3. 入选当年某主流指南的 key reference

---

## publication_type 缺失启发式(fallback)

当 efetch 返回 publication_types 为空(常见于发表 < 6 个月的新文献尚未 MeSH 索引):

```python
def infer_pub_type_from_text(title: str, abstract: str) -> tuple[list[str], str]:
    """
    返回 (推断的 publication_types, 置信度标签)
    grade 加 _inferred 后缀,提示用户人工复核。
    """
    text = (title + " " + abstract).lower()
    types = []
    if "meta-analysis" in text or "meta analysis" in text:
        types.append("Meta-Analysis")
    if "systematic review" in text or "prisma" in text:
        types.append("Systematic Review")
    if "randomized" in text and ("trial" in text or "study" in text):
        types.append("Randomized Controlled Trial")
    if "cohort" in text:
        types.append("Cohort Studies")
    if "case-control" in text or "case control" in text:
        types.append("Case-Control Studies")
    if "case report" in text:
        types.append("Case Reports")
    if "guideline" in text or "consensus" in text:
        types.append("Practice Guideline")
    return types, "inferred_low_confidence"
```

启发式规则只在 publication_types 为空时启用,grade 输出 `B_inferred`、`A_inferred` 等,提示用户。

---

## 样本量提取规则

`bioc-fulltext-fetch` 抽样本量优先级:

1. abstract 中正则 `n\s*=\s*(\d+)` 或 `(\d+)\s*patients enrolled`
2. fulltext Methods 段的 sample size paragraph
3. CONSORT flow diagram 描述(若可解析)
4. ClinicalTrials.gov 注册的 enrollment 数(via `clinical-trials-v2.search_studies`)

提取失败 → `sample_size = None` → GRADE 按 publication_type 默认值,不应用 n 阈值降权。

---

## 跨疾病阈值调整

| 场景 | RCT 大型阈值 | Cohort 大型阈值 |
|------|-------------|----------------|
| 常见病(肿瘤/心血管/感染) | 1000 / 500 | 500 |
| 罕见病(发病率 < 1/2000) | 200 / 100 | 100 |
| 超罕见病(发病率 < 1/50000) | 50 / 30 | 30 |
| 外科术式比较 | 300 / 150 | 200 |

阈值通过 `evidence_search(rare_disease_mode=True)` 切换。
