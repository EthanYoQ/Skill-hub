---
name: disease-stratifier
description: Phase 2 of disease-market-sizing-orchestration. Discovers disease-specific stratification dimensions by citing guideline sections from sources/guidelines/. ALWAYS uses cite-based discovery — NEVER built-in stratification templates. Output: .cache/<slug>/staging.json. Use AFTER contract-elicitor and AFTER A1' guidelines fetch.
license: Cite-or-Block strict (P0 iron law, see ../../CLAUDE.md)
---

# Disease Stratifier (Phase 2)

## P0 守门 — strict prohibitions

- 禁止内置 `KNOWN_STAGING_TEMPLATES` dict
- 禁止 `if disease == "X": stratify_by("Y")` 类硬编码
- 禁止凭 LLM 训练记忆生成"标准分期"
- 所有分层维度必须从 sources/guidelines/ 实际抓回的原文 cite
- 可选 `branch_scorecard` 必须保留到 `staging.json`，并用于后续 `branch_actionability_gate` / `medical_plausibility_gate`
- `CORE_SUBPAGE` 只能用于真实 `patient_pool` 分支，并且必须具备独立患者池、药物类别策略、药企可行动性、药物类别相关性、市场测算可行性与 strong 科室归属
- `SECONDARY_SUBPAGE` 也必须是真实 `patient_pool` 分支；非 patient-pool 分支不能伪装成任何 disease-market 子页
- 诊断基础设施、风险因子、证据雷达、横切 workflow 不能默认占用 disease-market 子页槽位；BAL/诊断 infrastructure 默认是横切 LP，不是独立疾病市场子页
- 正确降级为 `CROSS_CUTTING_LP` / `EVIDENCE_RADAR` / `REJECTED` 的非子页分支只需要基础元数据，并且不得出现在 `delivery_manifest.sub_pages`

CI watchdog (scripts/p0_watchdog.py) scans this skill's source for disease names + staging templates and blocks merge on hit.

## Functions

- `stratify(slug_dir, ask_llm) -> staging.json path`

## Schema

`schemas/staging.schema.json` — every dimension MUST have name + citation_anchor + sub_cohorts (≥1). Optional `branch_scorecard` MUST use structured branch metadata. `CORE_SUBPAGE` / `SECONDARY_SUBPAGE` branches require full patient-pool proof, drug-class strategy, `pharma_actionability`, `drug_class_relevance`, `market_sizing_feasibility`, `respiratory_ownership_strength`, and actions with trigger/owner/output/KPI. Non-subpage dispositions may carry only `slug`, `title`, `branch_type`, and `disposition` so P0 quality gates can audit that they were downgraded and did not consume disease-market subpage slots.
