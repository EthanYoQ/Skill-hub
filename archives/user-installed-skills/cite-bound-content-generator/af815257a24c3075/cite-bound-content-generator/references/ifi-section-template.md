# IFI 章节强制结构(每次 compose 必读)

> R1 by Phase-2-Quality-Fix sprint(2026-04-26).
> 本文档 = LLM 生成报告时必须遵循的章节框架基线。
> composer.py `_assert_ifi_structure(html)` 强制硬约束(opt-in via `enforce_ifi=True`),违者抛 `ComposeError` 含**所有缺失项**(architect 修订 2 collect-all-violations once),触发 orchestrator retry loop 重写。

---

## 7 章必含 + data-section marker

输出 html 必须含以下 7 个 `<section data-section="...">` 包裹:

### 1. 执行摘要
```html
<section data-section="exec-summary">
  ≥ 200 字概述,含 3 关键 P0 数字(发病率 / 患者池 / 市场规模)+ citation 锚点.
</section>
```

### 2. 流行病学
```html
<section data-section="epidemiology">
  中国 + 国际数据,带 PMID / guideline 锚点 ≥ 5 条.
</section>
```

### 3. 治疗格局(含决策树 ≥ 4 张)
```html
<section data-section="treatment-landscape">
  指南推荐线序 + 试验证据.
  <div class="mermaid">
  graph TD
    A[确诊] --> B{ALK 阳性?}
    B -->|是| C[1L 二代 TKI]
    B -->|否| D[标准化疗]
  </div>
  ...(共 ≥ 4 张 Mermaid block)
</section>
```

### 4. 市场规模(三层 TAM/SAM/SOM)
```html
<section data-section="market-sizing">
  <section data-subsection="tam">
    Total Addressable Market — 全部潜在患者池.
    年新发 X 例 [PMID:xxx],累计 Y 例 [guideline:CSCO-...],数字带锚点.
  </section>
  <section data-subsection="sam">
    Serviceable Addressable Market — 当前药品准入下覆盖.
  </section>
  <section data-subsection="som">
    Serviceable Obtainable Market — 现实可获份额.
  </section>
</section>
```

每子段 ≥ 1 数字带 citation 锚点。MECE 计算公式见 `~/.claude/skills/market-sizing-mece-foundation/SKILL.md`。

### 5. 竞争格局
```html
<section data-section="competitive-dynamics">
  竞品矩阵 + 上市 / 在研管线 + NMPA 批准状态.
</section>
```

### 6. LP 框架(8+ leverage points,LP 提及 ≥ 50)
```html
<section data-section="lp-framework">
  ≥ 8 个 LP(Leverage Point,策略干预点)+ 排序方法 + 每 LP 独立段.
  全文(主报告 + 子页累计)LP 提及次数 ≥ 50.
</section>
```

### 7. 附录(方法学 + 引用)
```html
<section data-section="appendix">
  数据来源、检索策略、PMID / NCT / guideline 完整 reference list.
</section>
```

---

## 子页(每 cohort 独立 .html,R3b sub-page schema)

主报告每 cohort(基于 `staging.dimensions` 的 sub_cohorts)产一个独立子页:

```html
<sub-page slug="1l-treatment">
  <section class="cohort-page" data-cohort="1l-treatment">
    <h1>1L 治疗 cohort 深度分析</h1>
    ...
  </section>
</sub-page>
```

composer 解析 `<sub-page slug="...">...</sub-page>` 包裹,落盘成 `output/<disease-slug>/page_<cohort-slug>.html`。

---

## 字数 / 数量硬约束

| 项 | 阈值 | 检查方式 |
|----|----|----|
| 主报告 text 长度 | ≥ 4000 字(去 html tag) | `len(re.sub(r'<[^>]+>', '', html))` |
| 决策树 Mermaid block | ≥ 4 | `html.count('<div class="mermaid">')` |
| LP 提及次数 | ≥ 50 | `len(re.findall(r'\b(?:LP\|策略干预点\|leverage point)\b', html))` |
| `data-section` markers | 7 个全 | regex search 每个 marker |
| TAM/SAM/SOM subsection | 三个全 | 在 market-sizing 内查 |

任一不达 → `ComposeError` 含**所有缺失项**(architect 修订 2 collect-all-violations once),orchestrator retry loop 反馈给 LLM 一次性补齐。

---

## 引用强制(P0 铁律)

每数字 + 每事实声明带 citation 锚点:

```html
<a href="#pmid:38819031">[PMID:38819031]</a>
<a href="#nct:NCT03052608">[NCT03052608]</a>
<a href="#guideline:CSCO-2024-NSCLC-§5.5.2">[CSCO-2024]</a>
```

或文本内嵌:`年新发 X 例 [pmid:38819031]`、`PFS Y 月 [nct:NCT03052608]`。

P0 铁律:**无锚点 = 凭记忆 = 阻断**。
