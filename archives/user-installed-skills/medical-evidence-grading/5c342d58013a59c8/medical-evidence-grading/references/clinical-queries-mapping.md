# Clinical Queries 8 类问题映射

> 本文档由 `medical-evidence-grading/SKILL.md` 引用。`recommend_search_strategy(question_type)` 函数返回的查询模板基于此表。

## 问题分类决策树

输入用户原始 query 后,先用关键词匹配确定 question_type:

```
"疗效" / "治疗" / "efficacy" / "effective" / "vs"      → therapy
"诊断" / "敏感度" / "diagnosis" / "sensitivity"        → diagnosis
"危险因素" / "风险" / "etiology" / "risk factor"       → etiology
"预后" / "生存" / "prognosis" / "survival"             → prognosis
"不良反应" / "副作用" / "adverse" / "harm" / "safety"  → harm
"预测模型" / "评分" / "decision rule" / "score"        → prediction
"指南" / "guideline" / "consensus"                     → guideline
"系统综述" / "Meta" / "systematic review"              → sr
```

## 完整映射表

| question_type | Clinical Queries filter | PubMed query 模板 | EuropePMC query 模板 | 优先 grade | 推荐主调 skill |
|--------------|------------------------|-------------------|---------------------|-----------|---------------|
| therapy | `therapy/narrow` | `({q}) AND randomized controlled trial[pt]` | `({q}) AND PUB_TYPE:"Randomized Controlled Trial"` | A-B | pubmed-eutils |
| diagnosis | `diagnosis/narrow` | `({q}) AND (sensitivity[ti] OR specificity[ti] OR diagnostic accuracy[ti])` | `({q}) AND (sensitivity OR specificity)` | A-C | pubmed-eutils + europepmc-search |
| etiology | `etiology/narrow` | `({q}) AND (cohort studies[mh] OR risk[ti])` | `({q}) AND PUB_TYPE:"Cohort Studies"` | B-C | pubmed-eutils |
| prognosis | `prognosis/narrow` | `({q}) AND (prognosis[mh] OR survival analysis[mh])` | `({q}) AND prognosis` | B-C | pubmed-eutils |
| harm | `etiology/broad` | `({q}) AND (adverse effects[sh] OR toxicity[sh])` | `({q}) AND adverse effects` | A-C | pubmed-eutils + clinical-trials-v2 (AE 表) |
| prediction | `clinical_prediction_guides/narrow` | `({q}) AND (decision rule[tw] OR prediction model[ti])` | `({q}) AND prediction model` | A-B | pubmed-eutils |
| guideline | n/a | `({q}) AND (practice guideline[pt] OR consensus[ti])` | `({q}) AND PUB_TYPE:"Practice Guideline"` | A only | pubmed-eutils.pubmed_clinical_queries(scope='guidelines') |
| sr | n/a (Cochrane) | `({q}) AND (systematic[sb] OR meta-analysis[pt])` | `({q}) AND PUB_TYPE:"Meta-Analysis"` | A only | pubmed-eutils + europepmc-search |

## 多类型并行(harm + therapy 联合检索)

不良反应类问题常需同时调 therapy filter (RCT 中的 AE 章节) 和 harm filter (专门安全性研究):

```python
# evidence_search 内部并行
asyncio.gather(
    search_one_type("therapy", q),      # RCT 主结局含 AE
    search_one_type("harm", q),         # 专门安全性 cohort
    search_one_type("guideline", q),    # 指南中的安全性章节
)
```

## 罕见病 / 超罕见病调整

罕见病(发病率 < 1/2000)定义参考 EMA/FDA orphan disease 列表。检索策略调整:

| 调整项 | 常见病 | 罕见病 |
|-------|-------|-------|
| 优先 grade | A only(若可用) | A-C(放宽) |
| 是否纳入 case series | 否 | 是 |
| 是否纳入 patient registry | 否 | 是(单独标记) |
| RCT 大型阈值 | n>=1000 | n>=200 |
| date_range 默认 | 5years | 15years |
| 推荐补充 skill | - | aact-bulk-trials.bulk_disease_landscape() 拿全部历史试验 |

## 中国本土证据补充策略

PubMed 不索引部分中文期刊。当 query 涉及"中国"/"汉族"/"中医"等本土场景:

1. 先按上表正常检索国际证据
2. 提示用户用 CNKI / 万方 / VIP / 中华医学期刊网 补充
3. 本 skill 不直接调中文数据库(独立工具集)
4. 国际指南若有中国版(如 NCCN 中国版),通过 `europepmc-search.search_articles(query="...China version")` 召回
