---
name: disease-market-sizing-orchestration
description: Cross-disease market sizing entry skill. Triggered by user one-liner like "做 X 市场调研" or "Run market sizing for X". Auto-runs 5 phase pipeline: contract → stratify → recall → compose-audit → bundle. Hard-gates on Cite-or-Block: every fact claim must carry citation anchor verifiable against sources/. Resumable mid-run.
license: Cite-or-Block strict (P0 iron law, see ../../CLAUDE.md)
---

# Disease Market Sizing Orchestration

## Phase Sequence

1. **contract-elicitor** → `.cache/<slug>/contract.json`
2. **disease-stratifier** → `.cache/<slug>/staging.json`
3. **Evidence Recall** (inline 7 retrieval + A1' guidelines) → `.cache/<slug>/sources/`
4. **Compose-then-Audit** double-turn (≤ 3 turns) → `output/report_raw.html` + `verification_report.json`
5. **Bundle + Design + TOC** → `output/report_standalone.html/pdf/xlsx` + `delivery_manifest.json`

## Functions

- `run(user_one_liner, project_root, callbacks) -> manifest dict`
