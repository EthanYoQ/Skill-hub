<div align="center">

[English](README.md) | **中文**

</div>

# YQ Editorial Presentation Skill

> 一套用于浏览器全屏演示和 PPTX 交付的 warm editorial presentation skill。

这个 skill 会把 presentation 需求生成成横向全屏 HTML deck：保留 Pfizer 血液科 v5 的 warm editorial 配色，使用接近 guizang deck 的投影字号，并按数据关系选择图表表达，而不是默认把所有数字都画成条形图。

---

## 效果预览

### 投影尺度封面
![投影尺度封面](screenshots/01_projection_hero.png)

### 机制匹配矩阵
![机制匹配矩阵](screenshots/02_mechanism_matrix.png)

### 结论卡片页
![结论卡片页](screenshots/03_conclusion_cards.png)

### ESC 全局索引
![ESC 全局索引](screenshots/04_esc_overview.png)

---

## 这一版更新

- skill 名称改为 **YQ Editorial Presentation Skill**。
- HTML 模式改为真正的 `100vw x 100vh` 横向全屏 deck。
- 字体尺度对齐 guizang 风格的演讲投影尺度：
  - hero 标题目标 110px+
  - 常规标题在 1920x1080 下目标 90-106px
  - lead 正文目标 28-36px
- 保留原 warm editorial 视觉 DNA：
  - 米色底 `#FAF9F5`
  - 赭石主色 `#CC785C`
  - 医疗深红 `#8C2B3A`
  - Pfizer 蓝 `#0095D5`
  - Fraunces / Inter / JetBrains Mono
- 图表生成改为先判断数据关系，再选择表达形式。
- 改写已有 HTML 时增加 fullscreen、overview、页脚遮挡、内容沉底、投影字号的 QA 规则。

---

## 设计 DNA

| 层级 | 规则 |
|---|---|
| 背景 | 暖米色、细噪声、编辑感径向光 |
| 主色 | 赭石红 + 医疗深红、Pfizer 蓝、绿、金、紫 |
| 标题 | Fraunces 衬线，建立演讲气场和编辑感 |
| 正文 | Inter，适合医学 / 商业叙事的高密度阅读 |
| 数据 | JetBrains Mono + tabular numerals |
| 版式 | eyebrow tag -> 大标题 -> lead -> 关系组件 -> footer |
| 演示壳 | 横向全屏 slide，支持键盘 / 滚轮 / 触屏 / 底部圆点 / ESC overview |

---

## 图表选择规则

这一版不再把所有数字都转成条形图。

| 数据关系 | 使用 |
|---|---|
| 一个重要数字 | `stat-card` / big number |
| 多个独立 KPI | `stat-grid` / `stat-strip` |
| 时间窗口或先后顺序 | `timeline` / `decision-window` |
| 步骤到步骤 | `pipeline` / `phase-pill` |
| 机制 / 基因型 / 产品匹配 | `matrix` / `gene-drug-map` |
| 文献筛选数量递减 | `funnel` |
| 证据强弱分层 | `pyramid` / `evidence-ladder` |
| 同一指标跨对象比较 | `proof-bars` / ranked bars |
| 患者旅程阶段覆盖 | `market-bars` |

硬规则：独立 KPI、时间窗口、机制匹配、证据链、决策流程都不能强行画成 generic bar chart。

---

## 输出模式

| | HTML 模式 | PPTX 模式 |
|---|---|---|
| 保真度 | 最高 | 85-90% |
| 格式 | 单文件 `.html` | 由 python-pptx 生成 `.pptx` |
| 导航 | 左右键、滚轮、触屏、圆点、ESC overview | PowerPoint 原生翻页 |
| 画布 | `100vw x 100vh`，无页面纵向滚动 | 16:9 |
| 适合 | 浏览器演示、教学、策略路径讲解 | 客户交付、高管会、传统 PPT 场景 |

---

## 仓库结构

```text
editorial-presentation-skill/
├── SKILL.md
├── README.md
├── README_zh.md
├── assets/
│   ├── starter-template.html
│   └── generate_pptx.py
├── references/
│   ├── design-tokens.md
│   ├── typography.md
│   ├── chart-selection.md
│   ├── components.md
│   ├── layouts.md
│   ├── rewrite-existing-html.md
│   ├── qa.md
│   └── pptx-mode.md
├── evals/
│   └── evals.json
└── screenshots/
```

---

## 安装

克隆到你的 skills 目录：

```bash
git clone https://github.com/EthanYoQ/editorial-presentation-skill.git \
  ~/.claude/skills/yq-editorial-presentation-skill
```

PPTX 模式需要：

```bash
pip install python-pptx
```

---

## 使用方式

HTML 模式默认启用：

```text
帮我做一个关于 [主题] 的 presentation，给 [受众] 看。
要求能浏览器全屏演示，适合现场讲课。
```

改写已有 HTML deck：

```text
使用 YQ Editorial Presentation Skill 改写这份 HTML deck。
保留全部内容，只更新演示 shell、版式、字号和图表表达。
```

PPTX 模式：

```text
用同一套 warm editorial 设计语言生成一份 PPTX 版本。
```

---

## QA 标准

生成的 HTML deck 应通过：

- 改写任务中 slide 数量保持一致
- `1920x1080` 和 `1440x900` 下无页面纵向滚动条
- ESC overview 能显示所有 slide
- 1920 下常规标题中位数接近 90-106px
- lead 正文保持投影可读
- 页脚不遮挡图表或证据文字
- `dense-slide` 不能被当作 `compact`
- 除非内容只有一种数据关系，否则至少使用 3 类图表表达家族

---

## License

可用于并改造到你自己的 presentation 工作流中。
