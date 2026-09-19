---
name: cite-bound-content-generator
description: Phase 4 Turn 1 of disease-market-sizing-orchestration. Generates report HTML with mandatory citation anchors per fact claim. Reads contract + staging + sources/. Every drug/treatment/stat/recommendation MUST carry [pmid:.../guideline:.../nct:...] anchor that resolves to an actual file in sources/. NEVER hardcode drug names or numerical claims. Use AFTER evidence recall (phase 3), BEFORE content-verification-layer (Turn 2).
license: Cite-or-Block strict (P0 iron law, see ../../CLAUDE.md)
---

# Cite-Bound Content Generator (Phase 4 Turn 1)

## LLM Prompt Constraints (enforced inside ask_llm callback)

> "You write report HTML for the disease/region described in the contract. Every fact claim
> (drug name, brand name, dosage, number, recommendation grade, epidemiology, mechanism)
> MUST carry a citation anchor in one of these forms:
> `[guideline:<source_id>:<locator>]` / `[pmid:<id>:<locator>]` / `[nct:<id>:<locator>]`.
> The source_id of every anchor MUST appear in the provided sources_summary.
> Sentences without an anchor for a fact claim are forbidden — your report will be rejected."

## IFI 章节强制结构(每次 compose 必读 — R1 by Phase-2-Quality-Fix)

参考完整模板:[`references/ifi-section-template.md`](references/ifi-section-template.md).

输出 html 必须含以下结构 (composer.py `_assert_ifi_structure` 在 `enforce_ifi=True` 时强制,违者抛 `ComposeError` 含**所有缺失项** + orchestrator retry loop 反馈给 LLM 一次性补齐):

- 7 个 `<section data-section="...">` marker:`exec-summary` / `epidemiology` / `treatment-landscape` / `market-sizing` / `competitive-dynamics` / `lp-framework` / `appendix`
- `market-sizing` 内三 `<section data-subsection="tam|sam|som">` 子段
- `<div class="mermaid">...</div>` 决策树 block ≥ 4 张
- LP 提及次数 ≥ 50(全文 `\b(?:LP|策略干预点|leverage point)\b`)
- 主报告 text 长度 ≥ 4000 字(去 html tag)
- 每数字 + 每事实声明带 citation 锚点(P0 铁律,无锚点 = 凭记忆 = 阻断)

## sub-page 输出指令(R3b by Phase-2-Quality-Fix · 每 cohort 独立 .html)

每 cohort(基于 `staging.dimensions` 的 sub_cohorts)用 `<sub-page slug="cohort-slug">...</sub-page>` 包裹独立段:

```html
<sub-page slug="1l-treatment">
  <section class="cohort-page" data-cohort="1l-treatment">
    <h1>1L 治疗 cohort 深度分析</h1>
    ...
  </section>
</sub-page>
```

`composer._parse_sub_pages` 解析后, `ComposedReport.sub_pages: list[dict {slug, html}]` 经 `_persist_sub_pages` 落盘成 `output/<disease-slug>/page_<cohort-slug>.html`,主报告通过 `<a href="page_<slug>.html">` 链接。

## Functions

- `compose(slug_dir, ask_llm, previous_violations=None, *, enforce_ifi=False) -> (html_path, idx_path)`
  - `enforce_ifi=True` (production) → 强制 IFI 结构,违者 ComposeError
  - `enforce_ifi=False` (default, fake-LLM tests) → 只查 anchor 解析,不查结构

- `_parse_sub_pages(raw_html) -> (main_html, sub_pages)` — 抽 `<sub-page slug="...">` 包裹的子页

- `_extract_toc_anchors(html) -> list[str]` — 从 main_html H2/H3 id 抽 TOC 浮动锚点

- `ComposedReport(main_html, sub_pages, toc_anchors, claims, raw_html)` — 升级输出 schema dataclass

## P0 Watchdog

`tests/test_cite_bound_content_generator.py::test_compose_p0_watchdog` —
grep skill source for forbidden hardcoded patterns. CI blocks on hit.
