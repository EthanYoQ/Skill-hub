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
4. **Compose-then-Audit** double-turn (≤ 3 turns) → `output/<slug>/report_raw.html` draft + `verification_report.json`
5. **Bundle + Design + TOC** → `output/<slug>/report_standalone.html` + `report_data.xlsx` + `delivery_manifest.json` (PDF only when explicitly requested)

## Production Non-Negotiables

- Production smoke must start from plugin-session bootstrap evidence: `.cache/<slug>/agent_run_context.json` with `mode=agent-plugin-bootstrap`, `agent_runtime=codex_or_claude_code_plugin_session`, and `requires_user_api_key=false`.
- Production smoke must continue through the reusable plugin continuation entrypoint and write `.cache/<slug>/plugin_session_invocation.json`; direct temporary callback scripts are not valid production-pass evidence.
- Disease-specific callbacks may adapt inputs or act as deterministic test doubles, but a production pass is invalid if a callback directly writes the final report or market model in place of reusable skills.
- Do not use one-off `scripts/generate_*smoke_report.py` generators or handwritten `skill_run_log.json` entries as production evidence.
- Every production run must write deliverables under a dedicated `output/<slug>/` directory; do not overwrite root-level or previous-run report files.
- The orchestrator must write `.cache/<slug>/orchestration_trace.json` with `entrypoint=disease-market-sizing-orchestration`, `agent_runtime=codex_or_claude_code_plugin_session`, a non-empty `run_id`, `status=ok`, and ok phases for `disease-stratifier`, `evidence-recall`, `cite-bound-content-generator`, `content-verification-layer`, `mermaid-renderer`, and `report-bundle-builder`.
- Downstream `skill_run_log.json` entries must be emitted by the same orchestrator run with `generated_by=disease-market-sizing-orchestration` and matching `run_id`; logs without this trace are invalid for production smoke.
- Evidence recall must use multiple retrieval channels and must not stop at the >50 literature hard floor when the disease area is source-rich; respiratory IFI-like topics should normally exceed 100 saved literature sources.
- Retrieval channel entries must carry provenance. `pubmed-search`, `europepmc-search`, `clinical-trials-search`, `bioc-fulltext-fetch`, `pubtator-entity-search`, `medical-evidence-grading`, and market recall entries in `skill_run_log.json` need `generated_by` / `run_id` plus a link to the orchestration run that consumed them.
- Fetched required channels must enter the body analysis. If ClinicalTrials.gov/AACT or PubTator/entity sources are saved under `.cache/<slug>/sources/`, production verification must require matching `[nct:...]` / `[aact:...]` / `[pubtator:...]` anchors or a recorded pre-verification exclusion reason.
- Evidence grading must affect source utilization. D-grade PubMed records may stay in background/reference appendices, but production smoke must block D-grade PMIDs used as analytical body anchors. Grading may use publication types and conservative study-design terms found in the saved PubMed title/abstract, but must not use external disease/drug dictionaries.
- Production compose must call `cite-bound-content-generator.compose(..., return_report=True)` and pass `ComposedReport.sub_pages` / `toc_anchors` to `report-bundle-builder`.
- Production compose must be agent-authored or reusable-skill-authored. The preferred plugin contract is `.cache/<slug>/agent_authored_compose.json` read by an adapter-only callback. `compose_authoring_provenance.json` must prove `authoring_mode=agent_authored_compose_artifact` and `generated_by=codex_or_claude_code_plugin_executor`; callback-authored HTML/formula/Mermaid is invalid.
- The agent-authored compose artifact must be a formal plugin phase, not an unexplained prewritten JSON. Pair it with `.cache/<slug>/agent_authored_compose_manifest.json` containing prompt digest, source tree digest, artifact checksum, current source slug, and validation time; production smoke must block missing or checksum-mismatched manifests.
- Production continuation accepts only final agent-authored compose artifacts: `provenance.phase=final`, current `source_run_slug`, `reader_layer.html`, `audit_layer.evidence_support_table`, `audit_layer.reader_to_audit_mapping`, substantive `claims`, current-run `source_usage`, `formula_dag_ref`, and `mermaid_sources`. Precompose artifacts are checkpoint evidence only and must block before smoke.
- Production verification must fail closed with semantic verification, source manifest provenance when available, and persisted `anchor_audit` metrics in `verification_report.json`.
- When semantic verification writes `.cache/<slug>/semantic_audit_log.jsonl`, `verification_report.json` must link that log and record matching non-empty entry counts. Otherwise the audit is not explainable and production smoke must fail.
- Production verification must block formula/model evidence citation dominance and evidence-digest-matrix body dominance. These are signs that the pipeline emitted a calculation dump or source-processing log instead of a V25-level report.
- Drug citation verification must scan the reader HTML plus audit-layer claims together. Audit claims alone are not enough because a reader-layer report can contain drug names that the audit layer omits; production smoke blocks zero drug mentions when antifungal drug names are visible.
- Production verification must require core evidence synthesis in the body when recall is broad. A V25-level report needs thematic literature digestion across cohorts/pathways/LP decisions plus growth drivers, payer/access impact, LP ranking methodology, and methods/sensitivity depth.
- Mermaid rendering must write `.cache/<slug>/mermaid_render_manifest.json`; decision-tree PNGs without this manifest are invalid. The extractor must match any `<div>` whose class list contains `mermaid`, including tags with attributes such as `data-chart`; HTML attributes cannot cause the renderer to skip flowchart blocks.
- Each Mermaid manifest block must self-describe graph quality with `edge_count`, `decision_node_count`, `numeric_evidence_count`, and `cross_point_count`. A manifest that only says render ok/path/source is insufficient for V25-level auditability.
- A compose artifact that fails verification is a failed draft only. It must not be treated as a latest deliverable candidate until `verification_report.verdict=ok`, rendered Mermaid assets exist, and bundle/smoke gates pass.
- Before production smoke audit, standalone HTML should embed the current source/citation/verification corpus as an audit package when the project provides `scripts/embed_source_corpus.py`; size parity must come from useful provenance, not fake padding images.
- Production smoke audit is mandatory before reporting a pass against V25. Count/size/image metrics are insufficient without sub-page depth, meaningful body source utilization, numeric evidence support, and Mermaid cross-point source checks.

## Functions

- `run(user_one_liner, project_root, callbacks, *, report_output_dir=None, v25_reference_html=None, require_production_smoke_audit=None) -> manifest dict`
