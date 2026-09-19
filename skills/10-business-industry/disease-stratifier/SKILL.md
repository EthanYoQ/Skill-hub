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

CI watchdog (scripts/p0_watchdog.py) scans this skill's source for disease names + staging templates and blocks merge on hit.

## Functions

- `stratify(slug_dir, ask_llm) -> staging.json path`

## Schema

`schemas/staging.schema.json` — every dimension MUST have name + citation_anchor + sub_cohorts (≥1).
