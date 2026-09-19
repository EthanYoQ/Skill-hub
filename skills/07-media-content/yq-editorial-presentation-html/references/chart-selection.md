# Chart Selection · 先判断数据关系,再选表达形式

这份 skill 的图表原则是：**表达家族服务于数据关系，页面构图服务于叙事角色与阅读密度。两者分开选择。** 不要把所有数字都画成条形图，也不要把语义正确的不同组件都塞进同一种白卡网格。

## P0 规则

- 先判断内容里的关系类型,再选择组件。
- 同时记录 cardinality、series count、ordinal/nominal、uncertainty、density mode、narrative role、media availability 和 annotation burden。
- 先排除语义无效表达，再排除容量不够的构图，然后按 profile compatibility 排名，最后应用 recent-use novelty penalty。
- 一个 deck 默认至少使用 3 类不同的表达家族,除非素材本身只有一种数据关系。
- 多个互不相干的 KPI 不得画成 proof bars。
- 时间先后、诊疗窗口、等待时间不得画成普通 bar chart。
- 病原体 / 基因型 / 机制 / 产品匹配不得画成条形图。
- 证据引用、证据质量、文献筛选不得画成 proof bars。
- 允许在同一表达家族里换变体,不要求每次同一种形态。
- 相同表达家族连续出现时，必须改变 composition 或 annotation anatomy；相邻非续页不得重复 composition。

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

## 第二层：从表达家族到构图

| 条件 | 候选构图 | 说明 |
|---|---|---|
| 1 个决定性数字 + 1-3 条解释 | `dominant-metric-marginalia` | 不要自动做四等分 KPI cards |
| 2-3 个可比较对象 | `comparison-split` / `chart-notes-asymmetric` | 方向、基线和不确定性必须可见 |
| 4-8 个相同结构系列 | `small-multiple-field` | 共享尺度；避免一张拥挤总图 |
| reading-first 证据/限制 | `ledger-takeaway-band` | 支持引用、状态和 takeaway |
| 时间或流程 | `process-rail` | 节点距离不暗示数值大小，除非确有量化 |
| 匹配/组合/边界 | `matrix-marginalia` | marginalia 用于规则、例外和证据等级 |
| 异质但相关的证据 | `editorial-mosaic` | 受 40% generic anatomy 上限约束 |
| 开场/转场/结论 | `statement-full-bleed` | 只保留一个核心命题和视觉锚点 |

`assets/plan_deck.py` 内置确定性候选排序和反重复验证。stable seed 只处理等价候选，不得用随机图表掩盖规划缺失。

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

生成 deck 前先写一张小表，或直接生成 manifest：

| 页面 | 叙事角色 | 核心关系 | 基数/密度 | 表达家族 | composition | tone |
|---|---|---|---|---|---|---|
| 01 | opener | statement | speaker-led | editorial narrative | statement-full-bleed | statement |
| 02 | tension | trend | 3 series / balanced | annotated chart | chart-notes-asymmetric | canvas |
| 03 | proof | evidence | 12 rows / reading-first | evidence ledger | ledger-takeaway-band | contrast |
| 04 | decision | matching | 4×3 / balanced | matrix | matrix-marginalia | canvas |

如果连续三页的 component name 不同，但 composition、主几何或 header/body/footer anatomy 相同，仍然必须重选。
