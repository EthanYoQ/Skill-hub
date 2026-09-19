# Visual Components Library

> 这套设计语言的 12+ 个标志性视觉组件。每个都附 HTML + CSS、何时用、典型变体、色彩语义。直接复制粘贴使用。

## 目录

| 类别 | 组件 |
|------|------|
| 数据展示 | [Double Bar Chart 双柱图](#1-double-bar-chart-双柱图) · [Evidence Pyramid 5 级金字塔](#2-evidence-pyramid-5-级金字塔) · [Literature Funnel 文献漏斗](#3-literature-funnel-文献漏斗) · [Proof Bars 横向校验条](#4-proof-bars-横向校验条) · [Stat Bar 大数字行](#5-stat-bar-大数字行) |
| 流程类 | [Phase Pill 链式流水线](#6-phase-pill-链式流水线) · [Workflow Phase 详细 phase 卡](#7-workflow-phase-详细-phase-卡) · [TTET Step 编号步骤](#8-ttet-step-编号步骤) · [Architecture Overview 架构总览](#9-architecture-overview-架构总览) |
| 导航跳转 | [Jump Row 跳转行](#10-jump-row-跳转行) · [Subpage Card Grid 子页矩阵](#11-subpage-card-grid-子页矩阵) · [Aux Card 辅助卡](#12-aux-card-辅助卡) |
| CTA / Callout | [CTA Grid 行动召唤](#13-cta-grid-行动召唤) · [Data Pain 痛点高亮](#14-data-pain-痛点高亮) · [Iron Rule Band 铁律绑](#15-iron-rule-band-铁律绑) · [Anti-Pattern Callout 反例提示](#16-anti-pattern-callout-反例提示) |
| 品牌 | [Product Card 产品卡](#17-product-card-产品卡) · [Dual Products 双产品对照](#18-dual-products-双产品对照) · [Glass Eyebrow 玻璃态标签](#19-glass-eyebrow-玻璃态标签) · [Section Tag 章节标签](#20-section-tag-章节标签) |

---

## 图表选择总则

先读 `references/chart-selection.md`。本组件库不是让你把所有数据都画成同一种 bar,而是给不同关系提供不同表达。

| 关系 | 用 | 不用 |
|---|---|---|
| 单点关键数字 | stat-card / big-number | proof-bars |
| 多个独立 KPI | stat-grid / stat-strip | bar chart |
| 同一指标跨对象比较 | proof-bars / ranked bars | matrix |
| 患者旅程阶段覆盖 | market-bars | generic proof-bars |
| 时间先后 / 决策窗口 | timeline / decision-window | bar chart |
| 流程步骤 | phase-pill / wf-phase | proof-bars |
| 机制 / 基因 / 产品匹配 | matrix / gene-drug-map | bar chart |
| 文献筛选 | literature-funnel | proof-bars |
| 证据等级 | evidence-pyramid / evidence-ladder | bar chart |
| 旧模式 vs 新模式 | before-after / journey compare | proof-bars |

**硬约束**:
- 一个 deck 默认至少使用 3 类不同表达家族。
- 条形图只表达"同一指标的比较、完成率、覆盖率、通过率"。
- 不要把独立 KPI、时间窗口、机制匹配、证据链画成条。

**字号硬约束**:
- 组件 CSS 默认使用投影演讲尺度,不是网页报告尺度。
- 卡片标题 / 产品名 / 组件 h3 通常为 `clamp(24px,1.55vw,32px)`。
- 卡片正文 / matrix cell / timeline 描述通常为 `clamp(17px,1.05vw,22px)`。
- metadata / chip 可小,但不应低于 `clamp(10px,.68vw,13px)`。
- 只有 `.compact` 页可以局部降级,不要把整套组件复制成 10-15px 正文字号。

---

## 0. Non-Bar Core Components

### 0.1 Stat Grid / Stat Card

**何时用**:一个或多个互不相同的核心 KPI,例如市场规模、模块数、PMID 数、图表数。
**不何时用**:同一指标跨多个对象排名,那才用 proof-bars。

```html
<div class="stat-grid">
  <div class="stat-card">
    <div class="stat-k">Market</div>
    <div class="stat-v">38<span>亿</span></div>
    <div class="stat-d">血液 IFI 总市场</div>
  </div>
  <div class="stat-card">
    <div class="stat-k">Evidence</div>
    <div class="stat-v">43</div>
    <div class="stat-d">PMID refs</div>
  </div>
</div>
```

```css
.stat-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:24px;margin-top:3vh}
.stat-card{background:var(--bg-surface);border:1px solid var(--border-soft);border-radius:14px;padding:28px 30px;box-shadow:var(--shadow-card)}
.stat-card .stat-k{font-family:var(--font-mono);font-size:clamp(11px,.78vw,15px);letter-spacing:2px;text-transform:uppercase;color:var(--accent-deep);font-weight:700;margin-bottom:12px}
.stat-card .stat-v{font-family:var(--font-serif);font-size:clamp(68px,6vw,124px);font-weight:700;line-height:1;letter-spacing:-1.2px;color:var(--text-0)}
.stat-card .stat-v span{font-size:.48em;color:var(--accent);margin-left:3px}
.stat-card .stat-d{font-size:clamp(17px,1.05vw,22px);color:var(--text-2);line-height:1.55;margin-top:12px}
```

### 0.2 Decision Timeline / Clock Path

**何时用**:0h→24h→48h→72h 这类时间路径、诊疗窗口、等待成本。
**不何时用**:多个对象的完成率比较。

```html
<div class="decision-window">
  <div class="time-node active"><b>0-4h</b><span>识别高危患者</span></div>
  <div class="time-node"><b>4-12h</b><span>快速诊断回报</span></div>
  <div class="time-node risk"><b>24h+</b><span>窗口开始丢失</span></div>
  <div class="time-node late"><b>48-72h</b><span>传统药敏结果</span></div>
</div>
```

```css
.decision-window{display:grid;grid-template-columns:repeat(4,1fr);gap:18px;margin-top:3vh;position:relative}
.decision-window::before{content:"";position:absolute;left:8%;right:8%;top:44px;height:2px;background:linear-gradient(90deg,var(--brand-green),var(--brand-gold),var(--brand-red));z-index:0}
.time-node{position:relative;z-index:1;background:var(--bg-surface);border:1px solid var(--border-soft);border-radius:14px;padding:24px 22px;box-shadow:var(--shadow-card)}
.time-node b{display:block;font-family:var(--font-serif);font-size:clamp(30px,2.1vw,44px);line-height:1;color:var(--text-0);margin-bottom:10px}
.time-node span{font-size:clamp(17px,1.05vw,22px);color:var(--text-2);line-height:1.5}
.time-node.active{border-color:var(--brand-green)}.time-node.risk{border-color:var(--brand-gold)}.time-node.late{border-color:var(--brand-red)}
```

### 0.3 Gene Drug Matrix / Mechanism Map

**何时用**:病原体、耐药基因、作用机制、产品之间的匹配关系。
**不何时用**:同一指标数值排名。

```html
<div class="gene-drug-map">
  <div class="matrix-head">耐药机制</div><div class="matrix-head">触发信息</div><div class="matrix-head">产品路径</div>
  <div class="matrix-cell gene">KPC / OXA-48</div><div class="matrix-cell">CRE + 丝氨酸酶线索</div><div class="matrix-cell drug">思福妥</div>
  <div class="matrix-cell gene">NDM / VIM / IMP</div><div class="matrix-cell">金属酶阳性</div><div class="matrix-cell drug">思福诺</div>
  <div class="matrix-cell gene">CRAB / OXA</div><div class="matrix-cell">鲍曼不动杆菌 HABP/VABP</div><div class="matrix-cell drug">Xacduro</div>
</div>
```

```css
.gene-drug-map{display:grid;grid-template-columns:1fr 1.4fr 1fr;gap:6px;margin-top:28px}
.matrix-head{font-family:var(--font-mono);font-size:clamp(11px,.78vw,15px);letter-spacing:2px;text-transform:uppercase;color:var(--text-3);padding:10px 12px;border-bottom:2px solid var(--border-soft)}
.matrix-cell{background:var(--bg-surface);border:1px solid var(--border-soft);border-radius:8px;padding:18px 20px;font-size:clamp(17px,1.05vw,22px);color:var(--text-1);line-height:1.5}
.matrix-cell.gene{font-family:var(--font-mono);font-weight:700;color:var(--brand-purple)}
.matrix-cell.drug{font-family:var(--font-serif);font-weight:700;color:var(--accent-deep);font-size:clamp(24px,1.55vw,32px)}
```

### 0.4 Before / After Compare

**何时用**:旧模式 vs 新模式、传统路径 vs AI 路径、经验覆盖 vs 机制驱动。
**不何时用**:精确比例排名。

```html
<div class="before-after">
  <div class="ba-card muted">
    <div class="ba-k">Before</div>
    <h3>经验性覆盖</h3>
    <p>等待培养和药敏,治疗决策滞后。</p>
  </div>
  <div class="ba-card">
    <div class="ba-k">After</div>
    <h3>机制驱动 IAAT</h3>
    <p>用高危因素 + 快速诊断提前匹配产品路径。</p>
  </div>
</div>
```

```css
.before-after{display:grid;grid-template-columns:1fr 1fr;gap:22px;margin-top:28px}
.ba-card{background:var(--bg-surface);border:1px solid var(--border-soft);border-left:4px solid var(--accent);border-radius:14px;padding:24px 26px;box-shadow:var(--shadow-card)}
.ba-card.muted{opacity:.62;border-left-color:var(--border-strong)}
.ba-k{font-family:var(--font-mono);font-size:clamp(11px,.78vw,15px);letter-spacing:2px;text-transform:uppercase;color:var(--accent-deep);font-weight:700;margin-bottom:12px}
.ba-card h3{font-family:var(--font-serif);font-size:clamp(24px,1.55vw,32px);color:var(--text-0);margin-bottom:8px}
.ba-card p{font-size:clamp(17px,1.05vw,22px);color:var(--text-2);line-height:1.65}
```

---

## 1. Double Bar Chart 双柱图

**何时用**:对比两种"路径/旅程/状态"在多个阶段的覆盖差异。源页面用于对比"有预防"vs"无预防"两条患者旅程在 6 个治疗阶段的产品覆盖。
**不何时用**:多个独立 KPI、时间先后、机制匹配、证据筛选、完成率排名。完成率排名请用 proof-bars;时间请用 decision-window;机制请用 matrix。

**视觉特征**:6 列网格 · 每列代表一个阶段 · 每行一条路径 · cell 内嵌产品 chip · 不同阶段用不同 brand 色 · `.empty` cell 用条纹+虚线表示"该阶段无内容"。

```html
<div class="market-bars">
  <div class="bars-axis">
    <div class="axis-label">阶段 →</div>
    <div class="axis-label">阶段 1</div>
    <div class="axis-label event">关键事件</div>
    <div class="axis-label">阶段 3</div>
    <div class="axis-label">阶段 4</div>
    <div class="axis-label">阶段 5</div>
    <div class="axis-label">阶段 6</div>
  </div>

  <div class="bar-row">
    <div class="bar-meta">
      <span class="pct">~50%</span>
      <span class="label">LINE A · 主路径</span>
    </div>
    <div class="bar-track">
      <div class="bar-cell s-prevent">
        <span class="stage-icon">阶段 1</span>
        <span class="stage-pct">注释</span>
        <div class="product-row"><span class="product-chip wf">产品A</span></div>
      </div>
      <div class="bar-cell event">
        <span class="stage-icon">⚡关键</span>
        <span class="stage-pct">B = 1%-15%
          <span style="font-size:1.4em; color:var(--brand-red); font-weight:800;">?</span>
        </span>
      </div>
      <div class="bar-cell s-empiric"><span class="stage-icon">阶段 3</span></div>
      <div class="bar-cell s-dd">
        <span class="stage-icon">阶段 4</span>
        <div class="product-row">
          <span class="product-chip wf">产品A</span>
          <span class="product-chip kxb">产品B</span>
        </div>
      </div>
      <div class="bar-cell s-target">
        <span class="stage-icon">阶段 5</span>
        <div class="product-row">
          <span class="product-chip wf">产品A</span>
          <span class="product-chip kxb">产品B</span>
        </div>
      </div>
      <div class="bar-cell s-maint">
        <span class="stage-icon">阶段 6</span>
        <div class="product-row">
          <span class="product-chip wf">产品A</span>
          <span class="product-chip kxb">产品B</span>
        </div>
      </div>
    </div>
  </div>

  <div class="bar-row">
    <div class="bar-meta">
      <span class="pct">~50%</span>
      <span class="label">LINE B · 替代路径</span>
    </div>
    <div class="bar-track">
      <div class="bar-cell empty"><span class="stage-icon" style="color:var(--text-3);">—</span></div>
      <div class="bar-cell empty"><span class="stage-icon" style="color:var(--text-3);">—</span></div>
      <div class="bar-cell s-empiric"><span class="stage-icon">阶段 3</span></div>
      <div class="bar-cell s-dd"><span class="stage-icon">阶段 4</span></div>
      <div class="bar-cell s-target"><span class="stage-icon">阶段 5</span></div>
      <div class="bar-cell s-maint"><span class="stage-icon">阶段 6</span></div>
    </div>
  </div>
</div>
```

```css
.market-bars { margin-top: 30px; background: var(--bg-surface); border: 1px solid var(--border-soft); border-radius: 18px; padding: 36px 32px; box-shadow: var(--shadow-card); }
.bars-axis { display: grid; grid-template-columns: 140px repeat(6, 1fr); gap: 6px; margin-bottom: 10px; align-items: end; }
.bars-axis .axis-label { font-size: clamp(10px,.72vw,14px); color: var(--text-3); letter-spacing: 1px; font-weight: 700; text-transform: uppercase; padding: 4px 0; text-align: center; border-bottom: 2px solid var(--border-soft); }
.bars-axis .axis-label:first-child { text-align: left; border-bottom: none; color: transparent; }
.bars-axis .axis-label.event { color: var(--brand-red); }
.bar-row { display: grid; grid-template-columns: 140px 1fr; gap: 14px; align-items: center; margin: 14px 0; }
.bar-meta { font-size: clamp(12px,.8vw,15px); color: var(--text-2); text-align: right; padding-right: 6px; line-height: 1.3; }
.bar-meta .pct { font-family: var(--font-serif); font-size: clamp(28px,2.1vw,44px); font-weight: 700; color: var(--text-0); display: block; }
.bar-meta .label { font-size: clamp(10px,.72vw,14px); letter-spacing: .5px; color: var(--text-3); }
.bar-track { display: grid; grid-template-columns: repeat(6, 1fr); gap: 4px; height: 90px; }
.bar-cell { background: var(--bg-1); border: 1px solid var(--border-soft); border-radius: 6px; padding: 8px 6px; display: flex; flex-direction: column; gap: 4px; transition: all .3s; }
.bar-cell.empty { background: repeating-linear-gradient(45deg, transparent, transparent 4px, var(--bg-1) 4px, var(--bg-1) 8px); border-style: dashed; opacity: .35; }
.bar-cell.event { background: linear-gradient(135deg, rgba(194,89,74,.15), rgba(194,89,74,.05)); border-color: var(--brand-red); }
.bar-cell.s-prevent { background: linear-gradient(135deg, rgba(46,92,138,.18), rgba(46,92,138,.06)); border-color: rgba(46,92,138,.35); }
.bar-cell.s-empiric { background: linear-gradient(135deg, rgba(184,144,60,.16), rgba(184,144,60,.05)); border-color: rgba(184,144,60,.3); }
.bar-cell.s-dd { background: linear-gradient(135deg, rgba(184,144,60,.20), rgba(184,144,60,.07)); border-color: rgba(184,144,60,.35); }
.bar-cell.s-target { background: linear-gradient(135deg, rgba(204,120,92,.20), rgba(204,120,92,.06)); border-color: rgba(204,120,92,.4); }
.bar-cell.s-maint { background: linear-gradient(135deg, rgba(92,141,92,.16), rgba(92,141,92,.05)); border-color: rgba(92,141,92,.3); }
.bar-cell .stage-icon { font-size: clamp(13px,.9vw,17px); font-weight: 700; color: var(--text-0); letter-spacing: .3px; line-height: 1.2; }
.bar-cell .stage-pct { font-size: clamp(10px,.68vw,13px); color: var(--text-3); font-family: var(--font-mono); margin-top: auto; }
.bar-cell.event .stage-icon { color: var(--brand-red); font-size: clamp(13px,.9vw,17px); }
.product-row { display: flex; flex-wrap: wrap; gap: 3px; margin-top: 4px; }
.product-chip { display: inline-flex; padding: 2px 6px; border-radius: 4px; font-size: clamp(10px,.68vw,13px); font-weight: 700; letter-spacing: .3px; line-height: 1.2; font-family: var(--font-mono); }
.product-chip.wf { background: var(--pfizer-blue); color: #fff; }
.product-chip.kxb { background: var(--accent); color: #fff; }
```

**变体**:7 列(`grid-template-columns: 110px repeat(7, 1fr)`)、3 行(每行 `.bar-row` 重复)。

---

## 2. Evidence Pyramid 5 级金字塔

**何时用**:展示数据/证据的分级结构。源页面用于展示 5 级证据(最高级 → 估算级)。
**不何时用**:展示文献筛选数量递减(用 funnel),或展示通过率比较(用 proof-bars)。

**视觉特征**:5 行从上到下宽度递增(60% → 100%)· 颜色从绿(顶级)到深赭(估算级)递变 · 右侧数量计数 · hover 微缩放。

```html
<div class="pyramid-wrap">
  <h3>🏆 5 级证据金字塔</h3>
  <div class="pyramid-row t1">
    <span><span class="tier-icon">🟢</span>最高级<span class="tier-desc">多中心 ≥5 / n≥200</span></span>
    <span class="tier-count">18</span>
  </div>
  <div class="pyramid-row t2">
    <span><span class="tier-icon">🔵</span>重要级<span class="tier-desc">单中心 n≥50</span></span>
    <span class="tier-count">17</span>
  </div>
  <div class="pyramid-row t3">
    <span><span class="tier-icon">🟡</span>参考级<span class="tier-desc">n&lt;50</span></span>
    <span class="tier-count">7</span>
  </div>
  <div class="pyramid-row t4">
    <span><span class="tier-icon">⚪</span>国际级<span class="tier-desc">国际数据</span></span>
    <span class="tier-count">2</span>
  </div>
  <div class="pyramid-row t5">
    <span><span class="tier-icon">🟠</span>估算级<span class="tier-desc">必须标注推算</span></span>
    <span class="tier-count">按需</span>
  </div>
</div>
```

```css
.pyramid-wrap { background: var(--bg-surface); border: 1px solid var(--border-soft); border-radius: 16px; padding: 28px; box-shadow: var(--shadow-card); }
.pyramid-wrap h3 { font-family: var(--font-serif); font-size: clamp(24px,1.55vw,32px); color: var(--brand-green); margin-bottom: 22px; font-weight: 600; }
.pyramid-row { display: flex; justify-content: center; align-items: center; margin: 0 auto 8px; padding: 16px 18px; border-radius: 8px; font-size: clamp(17px,1.05vw,22px); font-weight: 600; transition: transform .2s; }
.pyramid-row:hover { transform: scale(1.02); }
.pyramid-row .tier-icon { font-size: clamp(20px,1.2vw,26px); margin-right: 8px; }
.pyramid-row .tier-desc { font-size: clamp(13px,.85vw,16px); opacity: .85; margin-left: 10px; font-weight: 400; }
.pyramid-row .tier-count { font-family: var(--font-serif); font-weight: 700; font-size: clamp(22px,1.45vw,30px); margin-left: auto; }
.pyramid-row.t1 { width: 60%; background: var(--brand-green); color: #fff; }
.pyramid-row.t2 { width: 72%; background: var(--brand-blue); color: #fff; }
.pyramid-row.t3 { width: 84%; background: var(--accent); color: #fff; }
.pyramid-row.t4 { width: 92%; background: var(--bg-2); color: var(--text-1); border: 1px solid var(--border); }
.pyramid-row.t5 { width: 100%; background: var(--accent-deep); color: #fff; }
```

---

## 3. Literature Funnel 文献漏斗

**何时用**:展示从初筛到精筛的多步过滤量级递减。源页面用于展示 PubMed 检索从"数千 → 500 → 120 → 47 → 43"的纳入路径。
**不何时用**:展示证据强弱等级(用 pyramid / evidence-ladder),或多个对象通过率(用 proof-bars)。

**视觉特征**:5 行从上到下宽度递减(100% → 65%)+ 居中 · clip-path 切角形成漏斗形 · 颜色从浅赭到深赭递变 · 数字右对齐用衬线大字。

```html
<div class="funnel-wrap">
  <h3>📚 文献检索漏斗</h3>
  <div class="funnel-stage"><span>初筛触达</span><span class="count">数千</span></div>
  <div class="funnel-stage"><span>标题/摘要筛</span><span class="count">~500</span></div>
  <div class="funnel-stage"><span>全文+时间窗</span><span class="count">~120</span></div>
  <div class="funnel-stage"><span>入库</span><span class="count">47</span></div>
  <div class="funnel-stage"><span>纳入 A/B/C 级</span><span class="count">43</span></div>
</div>
```

```css
.funnel-wrap { background: var(--bg-surface); border: 1px solid var(--border-soft); border-radius: 16px; padding: 28px; box-shadow: var(--shadow-card); }
.funnel-wrap h3 { font-family: var(--font-serif); font-size: clamp(24px,1.55vw,32px); color: var(--accent-deep); margin-bottom: 22px; font-weight: 600; }
.funnel-stage { margin-bottom: 4px; padding: 14px 18px; color: var(--text-0); font-weight: 600; display: flex; justify-content: space-between; align-items: center; background: linear-gradient(90deg, #F7EFE7, #FBF6EF); border-left: 3px solid var(--accent-hot); clip-path: polygon(0 0, 100% 0, calc(100% - 18px) 100%, 18px 100%); font-size: clamp(17px,1.05vw,22px); }
.funnel-stage:nth-child(2) { background: linear-gradient(90deg, #F2E2D3, #F7ECDE); border-color: #D99775; width: 95%; margin-left: 2.5%; }
.funnel-stage:nth-child(3) { background: linear-gradient(90deg, #ECCBB2, #F0D7BC); border-color: var(--accent); width: 85%; margin-left: 7.5%; }
.funnel-stage:nth-child(4) { background: linear-gradient(90deg, #D99975, #DFA987); border-color: var(--accent-deep); color: #fff; width: 75%; margin-left: 12.5%; }
.funnel-stage:nth-child(5) { background: linear-gradient(90deg, #A45946, #B86E5A); border-color: #7F3F30; color: #fff; width: 65%; margin-left: 17.5%; }
.funnel-stage .count { font-family: var(--font-serif); font-size: clamp(24px,1.55vw,32px); font-weight: 600; }
```

---

## 4. Proof Bars 横向校验条

**何时用**:展示多个项目/领域的某项指标对比(通过率、覆盖率、性能等)。源页面用于跨 5 治疗领域 stress test 的通过率对比。
**不何时用**:多个互不相干 KPI、时间窗口、机制匹配、文献筛选、流程步骤。proof-bars 只比较同一指标。

```html
<div class="proof-bars">
  <div class="proof-bar passed">
    <div class="pb-name">领域 A<span class="pb-domain">类别说明</span></div>
    <div class="pb-track"><div class="pb-fill" style="width:96.7%;">96.7%</div></div>
    <div class="pb-status">✓ 达标</div>
  </div>
  <div class="proof-bar iterating">
    <div class="pb-name">领域 B<span class="pb-domain">类别</span></div>
    <div class="pb-track"><div class="pb-fill" style="width:67.5%;">67.5%</div></div>
    <div class="pb-status">🟡 在验证</div>
  </div>
</div>
```

```css
.proof-bars { background: var(--bg-surface); border: 1px solid var(--border-soft); border-radius: 16px; padding: 28px 26px; box-shadow: var(--shadow-card); }
.proof-bar { display: grid; grid-template-columns: 180px 1fr 80px; align-items: center; gap: 16px; padding: 12px 0; border-bottom: 1px solid var(--border-soft); }
.proof-bar:last-child { border-bottom: none; }
.proof-bar .pb-name { font-family: var(--font-serif); font-size: clamp(20px,1.3vw,26px); font-weight: 600; color: var(--text-0); }
.proof-bar .pb-name .pb-domain { display: block; font-family: var(--font-sans); font-size: clamp(11px,.78vw,15px); color: var(--text-3); font-weight: 500; letter-spacing: .5px; margin-top: 2px; }
.proof-bar .pb-track { height: 26px; background: var(--bg-1); border-radius: 13px; position: relative; overflow: hidden; }
.proof-bar .pb-fill { height: 100%; border-radius: 13px; display: flex; align-items: center; padding: 0 12px; font-family: var(--font-serif); font-weight: 700; font-size: clamp(16px,1vw,20px); color: #fff; transition: width 1.4s cubic-bezier(.22,.8,.3,1); }
.proof-bar.passed .pb-fill { background: linear-gradient(90deg, var(--brand-green) 0%, #7AB07A 100%); }
.proof-bar.iterating .pb-fill { background: linear-gradient(90deg, var(--brand-gold) 0%, #D4B05E 100%); }
.proof-bar .pb-status { font-size: clamp(11px,.78vw,15px); text-align: right; font-weight: 700; letter-spacing: 1px; }
.proof-bar.passed .pb-status { color: var(--brand-green); }
.proof-bar.iterating .pb-status { color: var(--brand-gold); }
```

---

## 5. Stat Bar 大数字行

**何时用**:在 hero / 关键页展示 4-5 个核心指标。
**不何时用**:同一指标跨对象排序(用 proof-bars),或时间阶段变化(用 timeline)。

```html
<div class="stat-bar">
  <div class="stat">
    <div class="num"><span data-count="38">0</span><span class="unit">亿</span></div>
    <div class="label">市场规模</div>
    <div class="caption">7 维度 × 双路径</div>
  </div>
  <div class="stat">
    <div class="num"><span data-count="22">0</span></div>
    <div class="label">Skill 数</div>
  </div>
  <!-- 重复 4-5 个 -->
</div>
```

```css
.stat-bar { display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 28px; padding: 32px 0; border-top: 1px solid var(--border-soft); border-bottom: 1px solid var(--border-soft); }
.stat .num { font-family: var(--font-serif); font-size: clamp(68px, 6vw, 124px); font-weight: 600; letter-spacing: -1.2px; line-height: 1; margin-bottom: 8px; font-variant-numeric: tabular-nums; background: linear-gradient(135deg, #141413 0%, var(--accent-deep) 100%); -webkit-background-clip: text; background-clip: text; -webkit-text-fill-color: transparent; }
.stat .num .unit { font-size: .55em; color: var(--accent); -webkit-text-fill-color: var(--accent); margin-left: 4px; font-weight: 600; }
.stat .label { font-size: clamp(12px,.85vw,16px); color: var(--text-2); letter-spacing: .8px; text-transform: uppercase; font-weight: 600; }
.stat .caption { font-size: clamp(15px,.95vw,18px); color: var(--text-2); margin-top: 6px; }
```

---

## 6. Phase Pill 链式流水线

**何时用**:展示横向流程的 5-6 个阶段(短标签 + 描述)。
**不何时用**:数值大小比较;不要把 phase pill 当 bar chart 用。

```html
<div class="arch-row">
  <div class="phase-pill">
    <div class="ph-id">PHASE 0</div>
    <div class="ph-name">Contract</div>
    <div class="ph-name-zh">契约抽取</div>
    <div class="ph-skills-count">1 skill</div>
  </div>
  <div class="arch-arrow">→</div>
  <div class="phase-pill">
    <div class="ph-id">PHASE 1</div>
    <div class="ph-name">Stratify</div>
    <div class="ph-name-zh">动态分层</div>
    <div class="ph-skills-count">2 skills</div>
  </div>
  <div class="arch-arrow">→</div>
  <!-- ... -->
</div>
```

```css
.arch-row { display: flex; justify-content: center; align-items: stretch; gap: 14px; flex-wrap: wrap; margin: 22px 0; }
.phase-pill { background: var(--bg-surface); border: 1px solid var(--border); border-radius: 10px; padding: 18px 16px; min-width: 150px; text-align: center; box-shadow: var(--shadow-card); }
.phase-pill .ph-id { font-size: clamp(10px,.68vw,13px); color: var(--brand-purple); font-weight: 800; letter-spacing: 2px; margin-bottom: 6px; font-family: var(--font-mono); }
.phase-pill .ph-name { font-family: var(--font-serif); font-size: clamp(20px,1.25vw,26px); font-weight: 600; color: var(--text-0); margin-bottom: 2px; }
.phase-pill .ph-name-zh { font-size: clamp(13px,.85vw,16px); color: var(--accent-deep); font-weight: 600; margin-bottom: 4px; }
.phase-pill .ph-skills-count { font-size: clamp(10px,.68vw,13px); color: var(--text-3); font-family: var(--font-mono); }
.arch-arrow { color: var(--accent); font-size: 18px; align-self: center; font-weight: 700; }
```

---

## 7. Workflow Phase 详细 phase 卡

**何时用**:深入展开每个 phase 的工具/动作/输出。源页面用于 22 Skill 在 5 Phase 的完整编排。

```html
<div class="wf-phase p3">
  <div class="wf-phase-head">
    <div class="wf-phase-num">P3</div>
    <div>
      <div class="wf-phase-name">Compose <span class="zh">内容生成</span> <span class="en">CITE-BOUND CONTENT</span></div>
    </div>
    <span class="wf-phase-count">5 SKILLS</span>
    <span class="wf-phase-output">→ <b>output.json</b></span>
  </div>
  <div class="wf-skills-list">
    <span class="wf-skill-chip">skill-name-1</span>
    <span class="wf-skill-chip">skill-name-2</span>
  </div>
  <p style="font-size:clamp(15px,.95vw,19px); color:var(--text-3); margin-top:6px;">备注说明</p>
</div>
```

CSS(完整):见 desktop HTML 第 224-251 行,关键变体 `.p0/p1/p2/p3/p4/p5` 用不同 left-border 色对应紫/紫/金/赭/红/绿。

---

## 8-20. 其余组件简表(完整 HTML+CSS 见源 desktop HTML)

| # | 组件 | 源 HTML 行号 | 用途 |
|---|------|------------|------|
| 8 | TTET Step 编号步骤 | L341-345 | 编号 1-N 的流程步骤,每步带 step-num 圆 |
| 9 | Architecture Overview | L187-208 | 输入框 + phase pills + delivery box + iron rule band 总览 |
| 10 | Jump Row | L66-70 | 跳转按钮组 + label,放章节末尾 |
| 11 | Subpage Card Grid | L279-284 | 子页 hub 矩阵 · grid auto-fit |
| 12 | Aux Card | L286-290 | 辅助交付物卡(PDF/XLSX 等)|
| 13 | CTA Grid | L384-398 | 主钩 + 辅钩 + Q&A 加码三档 |
| 14 | Data Pain | L125-126 | 高亮痛点 callout · 左红边 |
| 15 | Iron Rule Band | L205-207 | 铁律横幅 · 宪法级提示 |
| 16 | Anti-Pattern Callout | L180-182 | 反例 callout · 左红边 + code 标签 |
| 17 | Product Card | L114-124 | 产品卡 with stage tags + insight |
| 18 | Dual Products | L350-355 | 双产品对照 · 左侧色边区分 |
| 19 | Glass Eyebrow (hero) | L140-141 | hero 顶部胶囊形玻璃态标签 |
| 20 | Section Tag | L59 | 小写英文 tag · uppercase letter-spacing |

完整 CSS 在源 `C:\Users\qiyon\Desktop\血液科市场调研_v5_desktop.html` 顶部 `<style>` 内,按需 grep 类名查找。

---

## 组件搭配建议

| Section 类型 | 推荐组件组合 |
|------------|-------------|
| WHY / 战略叙事 | Glass Eyebrow + Section Title + Double Bar Chart + Product Card + Data Pain + Jump Row |
| HERO | Glass Eyebrow + Hero Title + Stat Bar + Jump Row |
| EVIDENCE | Section Tag + Section Title + Funnel + Pyramid (并列) + Anti-Pattern Callout + Jump Row |
| ARCHITECTURE | Section Tag + Section Title + Architecture Overview + Iron Rule Band |
| WORKFLOW | Section Tag + Section Title + 5-6 Workflow Phase + Quality Gates + Stats Footer |
| COVERAGE | Section Tag + Section Title + Hub Center + Subpage Card Grid + Aux Card 行 |
| PROOF | Section Tag + Section Title + Proof Bars + Proof Key |
| LIMITATIONS | Section Tag + Section Title + Limit Grid (4 卡) + Roadmap (4 milestone) |
| BONUS | Section Tag + Section Title + Description + Embedded Video |
| CTA | Section Tag + Team Names + Tech Stack Row + CTA Grid (3 cards) + Team Meta |

每节**不要堆 5+ 组件** — 1-3 个核心组件 + 标题 + 跳转就够,留白比堆砌好看。
