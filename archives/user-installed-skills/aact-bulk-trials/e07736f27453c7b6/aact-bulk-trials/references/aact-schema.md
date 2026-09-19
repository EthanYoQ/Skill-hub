# AACT Schema 关系图与关键表

> 主 SKILL.md 第 4 节的展开。完整官方 schema：https://aact.ctti-clinicaltrials.org/schema

## 关系图（精简版）

```
                        ┌──────────────┐
                        │   studies    │  主表 nct_id 主键
                        │  (~500K 行)   │
                        └──────┬───────┘
                               │ nct_id (1-N)
        ┌─────────────┬────────┼────────┬──────────────┬───────────────┐
        │             │        │        │              │               │
   ┌────▼─────┐ ┌─────▼────┐ ┌─▼──────┐ ┌─▼───────┐ ┌──▼──────┐ ┌──────▼──────┐
   │conditions│ │interv-   │ │outcomes│ │sponsors │ │facilities│ │eligibilities│
   │(MeSH)    │ │entions   │ │        │ │         │ │(国家/址) │ │(入排标准)   │
   └──────────┘ └──────────┘ └────┬───┘ └─────────┘ └─────────┘ └─────────────┘
                                  │
                            ┌─────▼──────────┐
                            │outcome_analyses│  统计学结果
                            └────────────────┘

  Results-only 子树（仅有结果上传的试验）：
  studies → result_groups → results_baseline / outcome_measurements
```

## 关键表速查

| 表名 | 行级 | 关键列 | 用途 |
|------|------|--------|------|
| `studies` | ~500K | nct_id, brief_title, phase, study_type, overall_status, start_date, completion_date, enrollment, has_results | 主表，所有 NCT 元数据 |
| `conditions` | ~1.5M | nct_id, name, downcase_name | MeSH 适应症；用 `downcase_name` 做不区分大小写匹配 |
| `interventions` | ~900K | nct_id, name, intervention_type | 干预；type ∈ {Drug, Biological, Device, Procedure, Behavioral, Other} |
| `outcomes` | ~2M | nct_id, outcome_type, title, measure | 结局指标定义 |
| `outcome_analyses` | ~150K | nct_id, p_value, ci_lower_limit, ci_upper_limit, method | 统计分析结果 |
| `sponsors` | ~700K | nct_id, name, lead_or_collaborator, agency_class | agency_class ∈ {NIH, INDUSTRY, US_FED, OTHER} |
| `eligibilities` | ~500K | nct_id, gender, minimum_age, maximum_age, criteria | criteria 是入排全文（GIN 索引候选） |
| `facilities` | ~3M | nct_id, name, city, country, status | 站点级数据 |
| `result_groups` | ~400K | nct_id, ctgov_group_code, title | 结果分组（arm/group） |
| `results_baseline` | ~2M | nct_id, ctgov_group_code, title, param_value, param_type | baseline 人口学统计 |
| `outcome_measurements` | ~3M | nct_id, ctgov_group_code, param_value, dispersion_value | 主/次要终点测量 |

## 常见 JOIN 路径

```sql
-- 路径 1: 适应症 + 干预 + phase 过滤
studies s
  JOIN conditions c ON c.nct_id = s.nct_id
  JOIN interventions i ON i.nct_id = s.nct_id

-- 路径 2: 结果统计（仅 has_results = true）
studies s
  JOIN outcomes o ON o.nct_id = s.nct_id
  LEFT JOIN outcome_analyses oa ON oa.nct_id = s.nct_id

-- 路径 3: 地理 + 赞助商画像
studies s
  JOIN facilities f ON f.nct_id = s.nct_id
  JOIN sponsors sp ON sp.nct_id = s.nct_id AND sp.lead_or_collaborator = 'lead'
```

## 字段陷阱

- `phase` 自由文本：`Phase 1`, `Phase 1/Phase 2`, `Phase 2`, `Phase 3`, `Phase 4`, `N/A`, NULL
- `overall_status` 枚举：`Recruiting`, `Completed`, `Active, not recruiting`, `Terminated`, `Withdrawn`, `Suspended`, `Not yet recruiting`, `Unknown status`
- `start_date` / `completion_date` 可能仅精确到年月（day=1 占位）
- `enrollment` 可为 NULL；不要直接 SUM 不做 COALESCE
- `conditions.name` 大小写不一致；用 `downcase_name` 检索
- `intervention_type` 大小写敏感：`Drug` ≠ `drug`

## 推荐 GIN 索引（仅本地 dump 模式）

dump 默认无以下索引，建议建立加速文本检索：

```sql
CREATE EXTENSION IF NOT EXISTS pg_trgm;

CREATE INDEX IF NOT EXISTS idx_conditions_downcase_trgm
  ON conditions USING gin (downcase_name gin_trgm_ops);

CREATE INDEX IF NOT EXISTS idx_interventions_name_trgm
  ON interventions USING gin (LOWER(name) gin_trgm_ops);

CREATE INDEX IF NOT EXISTS idx_studies_start_date
  ON studies (start_date) WHERE start_date IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_eligibilities_criteria_trgm
  ON eligibilities USING gin (criteria gin_trgm_ops);
```

建索引后 `ILIKE '%term%'` 查询从全表扫描提速 10-100×。
