# AACT 5 个核心 SQL 模板

> 主 SKILL.md 第 5 节的展开。所有模板默认 `LIMIT 1000`，参数化（`:param`）防注入。生产环境调用前先 `EXPLAIN (ANALYZE, BUFFERS)`。

## 通用约定

- 所有参数用 `:param_name` 命名占位符（psycopg2 / asyncpg 均支持）
- 返回结构化结果 + meta（耗时、命中行数、来源 mode）
- 字符串匹配统一走 `LOWER(...)` 或 `downcase_name`，避免大小写陷阱
- 大于 50K 行的扫描自动切 server-side cursor

---

## 5.1 `query_trials_by_condition`

**签名**：`query_trials_by_condition(condition_term, year_from, year_to, phase, limit)`

```sql
-- 按适应症（支持 MeSH term 或自由文本，不区分大小写）检索试验
SELECT s.nct_id, s.brief_title, s.phase, s.overall_status,
       s.start_date, s.completion_date, s.enrollment,
       array_agg(DISTINCT c.downcase_name) AS conditions
FROM studies s
JOIN conditions c ON c.nct_id = s.nct_id
WHERE c.downcase_name ILIKE '%' || :condition_term || '%'
  AND (:year_from IS NULL OR s.start_date >= make_date(:year_from, 1, 1))
  AND (:year_to   IS NULL OR s.start_date <  make_date(:year_to + 1, 1, 1))
  AND (:phase     IS NULL OR s.phase = :phase)
GROUP BY s.nct_id
ORDER BY s.start_date DESC NULLS LAST
LIMIT :limit;
```

---

## 5.2 `query_trials_by_intervention`

**签名**：`query_trials_by_intervention(intervention_name, intervention_type, limit)`

```sql
-- 按干预名称（如 "voriconazole"）+ 类型（Drug/Biological/Device）检索
SELECT s.nct_id, s.brief_title, s.phase, s.overall_status,
       i.name AS intervention_name, i.intervention_type
FROM studies s
JOIN interventions i ON i.nct_id = s.nct_id
WHERE LOWER(i.name) LIKE LOWER('%' || :intervention_name || '%')
  AND (:intervention_type IS NULL OR i.intervention_type = :intervention_type)
ORDER BY s.start_date DESC NULLS LAST
LIMIT :limit;
```

---

## 5.3 `query_trials_results_summary`

**签名**：`query_trials_results_summary(nct_id_list)`

```sql
-- 仅查询已上传 results 的试验，返回 baseline + 主要终点统计
WITH have_results AS (
  SELECT nct_id FROM studies
  WHERE nct_id = ANY(:nct_id_list) AND has_results = true
)
SELECT s.nct_id, s.brief_title,
       rb.title AS baseline_title, rb.param_value, rb.param_type,
       oa.p_value, oa.ci_lower_limit, oa.ci_upper_limit, oa.method
FROM have_results h
JOIN studies s ON s.nct_id = h.nct_id
LEFT JOIN results_baseline rb ON rb.nct_id = s.nct_id
LEFT JOIN outcome_analyses oa ON oa.nct_id = s.nct_id
ORDER BY s.nct_id;
```

---

## 5.4 `bulk_disease_landscape` — 疾病全景

**签名**：`bulk_disease_landscape(disease_term, year_from, year_to)`

```sql
-- 按 phase / sponsor_class / status / 国家 四维聚合
WITH cohort AS (
  SELECT DISTINCT s.nct_id, s.phase, s.overall_status, s.start_date
  FROM studies s
  JOIN conditions c ON c.nct_id = s.nct_id
  WHERE c.downcase_name ILIKE '%' || :disease_term || '%'
    AND s.start_date BETWEEN make_date(:year_from, 1, 1)
                         AND make_date(:year_to, 12, 31)
)
SELECT 'phase' AS dim, COALESCE(phase, 'Unknown') AS bucket, COUNT(*) AS n
FROM cohort GROUP BY phase
UNION ALL
SELECT 'status', overall_status, COUNT(*) FROM cohort GROUP BY overall_status
UNION ALL
SELECT 'sponsor_class', sp.agency_class, COUNT(DISTINCT c.nct_id)
FROM cohort c
JOIN sponsors sp ON sp.nct_id = c.nct_id AND sp.lead_or_collaborator = 'lead'
GROUP BY sp.agency_class
UNION ALL
SELECT 'country', f.country, COUNT(DISTINCT c.nct_id)
FROM cohort c
JOIN facilities f ON f.nct_id = c.nct_id
GROUP BY f.country
ORDER BY dim, n DESC;
```

---

## 5.5 `find_similar_design_trials`

**签名**：`find_similar_design_trials(reference_nct_id, limit)`

```sql
-- 找设计相似试验：相同 condition + intervention_type + phase
WITH ref AS (
  SELECT s.phase,
         array_agg(DISTINCT c.downcase_name) AS conds,
         array_agg(DISTINCT i.intervention_type) AS itypes
  FROM studies s
  LEFT JOIN conditions c ON c.nct_id = s.nct_id
  LEFT JOIN interventions i ON i.nct_id = s.nct_id
  WHERE s.nct_id = :reference_nct_id
  GROUP BY s.phase
)
SELECT s.nct_id, s.brief_title, s.phase, s.overall_status,
       COUNT(DISTINCT c.downcase_name) FILTER (
         WHERE c.downcase_name = ANY((SELECT conds FROM ref))
       ) AS shared_conditions
FROM studies s
JOIN conditions c ON c.nct_id = s.nct_id
JOIN interventions i ON i.nct_id = s.nct_id
WHERE s.nct_id <> :reference_nct_id
  AND s.phase = (SELECT phase FROM ref)
  AND i.intervention_type = ANY((SELECT itypes FROM ref))
  AND c.downcase_name = ANY((SELECT conds FROM ref))
GROUP BY s.nct_id
HAVING COUNT(DISTINCT c.downcase_name) >= 1
ORDER BY shared_conditions DESC
LIMIT :limit;
```

---

## 性能优化习惯

- 始终先 `EXPLAIN (ANALYZE, BUFFERS)` 验证大查询
- JOIN 多表时按选择性最高的表先过滤（通常 `conditions`）
- 聚合大于 100K 行时用 `WITH cohort AS (...)` CTE 物化中间结果
- 不要 `SELECT *`，AACT 表通常 30+ 列
- 大于 50K 行扫描用 server-side cursor：
  ```python
  with conn.cursor(name='aact_stream') as cur:
      cur.itersize = 5000
      cur.execute(sql, params)
      for row in cur:
          ...
  ```

## 测试清单

新模板上线前验证：
- [ ] 在云端和本地两种模式下均可执行
- [ ] 参数化查询无 SQL 注入向量（用 `psql -e` 校验拼接后的真实 SQL）
- [ ] LIMIT 默认生效
- [ ] EXPLAIN 显示使用了预期索引（GIN trigram / btree on start_date）
- [ ] 极端输入（空字符串、超长 NCT 列表 > 1000、未来年份、SQL 元字符）不崩溃
- [ ] 无结果时返回空数组而非异常
- [ ] meta.elapsed_ms p95 < 5s（本地）/ < 30s（云端）
