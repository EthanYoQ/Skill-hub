---
name: content-verification-layer
description: Phase 4 Turn 2 of disease-market-sizing-orchestration (A6' upgrade). Audits compose output via Cite-or-Block strict — every anchor must reverse-resolve to an actual file in sources/, every fact claim must have an anchor. Returns verdict (ok/blocked) + violations list. Use AFTER cite-bound-content-generator (Turn 1), BEFORE report-bundle-builder (phase 5).
license: Cite-or-Block strict (P0 iron law, see ../../CLAUDE.md)
---

# Content Verification Layer (Phase 4 Turn 2)

## Strict Audits

1. `enforce_citations_in_text(html)` — flag fact-bearing claims without anchors
2. anchor existence reverse-lookup — every anchor source_id must have a backing file in sources/
3. (Future T13: route drug claims to A5' verifier; route treatment claims to A1' locate_section)

## Functions

- `verify_section(section_html, sources_dir) -> Verdict`
- `verify_full_report(html, sources_dir) -> Verdict`
- `enforce_citations_in_text(html) -> list[Violation]`

## P0 守门

Tests grep skill source for hardcoded drug names / disease names — CI blocks on hit.
