# Chart Selection · 先判断数据关系,再选表达形式

这份 skill 的图表原则是: **图表服务于关系,不是服务于组件复用**。不要把所有数字都画成条形图。条形图保留,但只用于适合条形图的数据关系。

## P0 规则

- 先判断内容里的关系类型,再选择组件。
- 一个 deck 默认至少使用 3 类不同的表达家族,除非素材本身只有一种数据关系。
- 多个互不相干的 KPI 不得画成 proof bars。
- 时间先后、诊疗窗口、等待时间不得画成普通 bar chart。
- 病原体 / 基因型 / 机制 / 产品匹配不得画成条形图。
- 证据引用、证据质量、文献筛选不得画成 proof bars。
- 允许在同一表达家族里换变体,不要求每次同一种形态。

## 决策表

| 数据关系 | 首选表达 | 可选变体 | 不要用 |
|---|---|---|---|
| 一个数字很重要 | `stat-card` | `stat-hero` / `big-number` | bar / proof-bars |
| 多个独立 KPI | `stat-grid` | `stat-strip` | bar / proof-bars |
| 同一指标跨对象比较 | `proof-bars` | `ranked-bars` / compact table | matrix / funnel |
| 阶段覆盖或患者旅程 | `market-bars` | journey map | generic bar |
| 时间先后 / 诊疗窗口 | `timeline` | `clock-path` / `decision-window` | proof-bars |
| 输入到输出 / 操作步骤 | `pipeline` | `phase-pill` / `workflow-phase` | proof-bars |
| 病原体 / 基因型 / 机制 / 产品匹配 | `matrix` | `gene-drug-map` / decision table | bar |
| 文献筛选数量递减 | `funnel` | evidence flow | proof-bars |
| 证据强弱分层 | `pyramid` | `evidence-ladder` | bar |
| 旧模式 vs 新模式 | `before-after` | journey compare | proof-bars |
| 产品定位 / 适应症 / 限制 | `product-path-card` | product matrix | bar |

## 反例

### 坏例: 4 个 KPI 全部画成 bar

素材:
- 38 亿市场规模
- 7 个疾病模块
- 22 张图
- 43 条 PMID

正确做法: `stat-grid` 或 `stat-strip`。它们是互不相干的指标,不是同一指标的横向比较。

### 坏例: 0h / 24h / 48h / 72h 画成 bar

正确做法: `timeline` 或 `decision-window`。这是时间顺序和决策窗口,不是大小比较。

### 坏例: KPC / NDM / CRAB 对应药物画成 bar

正确做法: `matrix` 或 `gene-drug-map`。这是机制匹配关系,不是数值大小。

### 坏例: PubMed 初筛到纳入画成 proof bars

正确做法: `funnel`。这是筛选递减过程。

## 生成前自检

生成 deck 前先写一张小表:

| 页面 | 核心关系 | 组件 |
|---|---|---|
| 01 | 核心定位 + 独立 KPI | cover + stat-strip |
| 02 | 患者旅程阶段覆盖 | market-bars |
| 03 | 时间窗口 | decision-window |
| 04 | 机制匹配 | matrix |
| 05 | 证据筛选和分级 | funnel + pyramid |

如果这张表里连续 3 页都是 bar / proof-bars,必须重选组件。
