---
name: editorial-presentation-html
description: YQ warm editorial 设计语言 · 用于 presentation / case sharing / 项目汇报 / 战略叙事 / 产品发布 / 给老板/director 看的演示页面。**支持双输出模式**:① HTML(横向全屏 deck,完整复刻 90%+ 视觉)② PPTX(复刻 85-90% 视觉,通过 python-pptx 程序化生成)。提供完整 design tokens(米色底 + 赭石红 #CC785C + 6 品牌色 + Fraunces 衬线 + Inter + JetBrains Mono)、多族谱视觉组件(stat / timeline / matrix / funnel / pyramid / phase pill / market-bars / proof-bars 等)、guizang-scale 投影字号、全屏横向版面骨架。**只要用户提到要做 presentation / slides / PPT / 幻灯片 / case sharing / 项目展示 / 战略汇报 / 给老板看的页面 / Pfizer 风格 / Anthropic 风格 / 编辑设计风格 / 类似血液科那套,就一定要用这个 skill,即使没明确说"用 editorial 风格"或没指定 HTML/PPT 格式**。源版本:`C:\Vibe Coding Project\AI Square\血液科市场调研\output\血液科市场调研_v5_desktop.html`。
---

# Editorial Presentation (HTML + PPTX 双模)

## 这个 skill 是什么

一套**视觉设计语言**的可复用 skill,源自 Pfizer 血液科 IFI 案例分享 v5 desktop 版的成熟设计系统。

**核心价值**:配色 + 字体 + 视觉表现形式 = 高识别度的"Anthropic warm editorial"风格,**不需要重新调色/选字/设计组件**,直接套用即可生成视觉一致的 presentation。

**双输出模式**:
- 🌐 **HTML 模式**(默认 · 100% 复刻):用于浏览器演示的**横向全屏 deck**。F11 下每页固定 100vw × 100vh,支持左右翻页、底部圆点、触屏/滚轮、ESC overview。视觉仍复刻血液科 v5 的 warm editorial,不是换主题。
- 📊 **PPTX 模式**(85-90% 复刻):用于必须交 .pptx 文件的场景(高管会、客户演示、传统企业)。通过 python-pptx 程序化生成,共享同一套配色/字体/组件视觉。

**两种模式共享的"设计 DNA"**:
1. 配色:米色底 #FAF9F5 + 赭石主色 #CC785C + 6 品牌辅色按语义分配
2. 字体:Fraunces 衬线大标题 + Inter 正文 + JetBrains Mono 数据
3. 视觉手段:软阴影卡片 + 圆角 + 渐变文字 + 微妙噪声纹理 + 多层背景径向渐变
4. 组件:stat / timeline / matrix / funnel / pyramid / market-bars / phase pill / proof-bars 等多族谱视觉模块
5. 版面节奏:eyebrow tag → 大标题 → subtitle → 主组件 → evidence / footer 的全屏 slide 结构
6. 投影尺度:页面布局和字号对齐 `guizang-ppt-skill` 的 fullscreen deck 尺度,但配色仍完全使用血液科 v5 warm editorial
7. 图表逻辑:先判断数据关系,再选组件;不要把所有数字都转成条形图

## 何时使用(**必须主动触发,不要等用户说风格名**)

任一信号出现立即调用:

- "做一个 presentation / slides / PPT / 幻灯片 / 演示文稿 / 汇报"
- "做 case sharing / 案例分享 / 项目展示 / 战略汇报"
- "给老板/director/VP 看 / 给客户演示"
- "类似血液科那套 / Pfizer 风格 / Anthropic 风格 / warm editorial / 编辑设计风格"
- "把 X 内容做成可演示的页面 / 做成 deck"
- 用户给一份内容(产品发布、市场调研、技术分享、案例复盘),需要做成展示

不要等用户明确说风格名——只要场景是 presentation 类输出,默认套这套设计语言。

## 第 0 步:**判断输出格式**

问自己 / 看用户表述:

| 用户说... | 用 |
|----------|-----|
| "做 HTML 页面 / 网页 / 浏览器演示 / F11 全屏 / 加跳转链接 / 嵌入视频" | **HTML 模式** |
| "做 PPT / .pptx / PowerPoint / 幻灯片文件 / 给传统企业用" | **PPTX 模式** |
| "做 presentation"(没说格式)| 默认 **HTML 模式**(更高保真),并主动问"要不要也出一份 PPT 版?" |
| "做一份给客户演示用的"(看上下文)| 客户是 IT/科技 → HTML;客户是医药/金融/政府 → PPTX |
| "做幻灯片样式"但没说文件类型 | HTML 模式(横向全屏 deck) |

如果不确定,**默认 HTML**(因为它复刻度最高,后续可再衍生 PPT)。

---

## HTML 模式工作流

### Step 1 · 读 references

按需读:

- **`references/design-tokens.md`** ⭐ 必读 — 完整 `:root` 变量(色板、字体、阴影)。**第一件事就是把这块原样塞进 `<style>`**。
- **`references/typography.md`** ⭐ 必读 — Fraunces / Inter / JetBrains Mono 应用规则、projection scale。HTML deck 字号要接近 guizang fullscreen 演讲尺度,不是网页报告尺度。
- **`references/chart-selection.md`** ⭐ 必读 — 图表选择规则。先判断数据关系,再选 stat / timeline / matrix / funnel / bar 等组件。**禁止把所有数字都画成条形图**。
- **`references/components.md`** — 视觉组件的 HTML+CSS 切片,包含每类组件的"何时用 / 不何时用"。
- **`references/layouts.md`** — 横向全屏 deck 的 slide 节奏、grid 布局、navigation。
- **`references/rewrite-existing-html.md`** — 改写已有 HTML deck 的专用流程。保留内容 section,只替换演示 shell / CSS / JS。
- **`references/qa.md`** — 生成后检查。重点查主内容宽度、垂直沉底、页脚遮挡、overview 和滚动条。

### Step 2 · 用 starter template 起手

`assets/starter-template.html` 是最小可运行骨架——包含 `<head>`(字体引入 + 全套 v5 design tokens + body 噪声纹理)+ 横向全屏 deck shell + 底部圆点 + 左右翻页 + ESC overview + 4 种非单一条形图示例。**不要从旧的纵向滚动 starter 开始**。

动手前先读 template 的 `<style>` 和 `<script>`。starter 是横向 deck shell 的唯一结构来源,不要自己从零发明 `#deck`、overview、dots、wheel/touch 逻辑。旧 HTML 改写也必须先对齐 starter 的 shell,再迁移原内容。

### Step 2.5 · 如果用户给的是已有 HTML

打开 `references/rewrite-existing-html.md`。这种任务的目标不是重写内容,而是把旧 deck 按本 skill 的 shell 重新渲染:

- 保留原始 `<section class="slide"...>...</section>` 的内容块,除非用户明确要求改文案。
- 替换纵向 scroll-snap / `scrollIntoView` / `IntersectionObserver` 为横向 fixed deck。
- 把旧整页深色主题降级为局部语义色,整体仍用 v5 warm editorial。
- 按 `references/qa.md` 跑检测,不通过就先修 skill / 模板规则,再重新生成。

### Step 3 · 按需嵌组件

`assets/component-snippets.html` 是组件粘贴库:

- 数据展示:stat-card / stat-grid / market-bars / evidence-pyramid / literature-funnel / proof-bars
- 时间与流程:timeline / clock-path / decision-window / phase-pill / wf-phase / ttet-step / arch-overview
- 匹配关系:matrix / gene-drug-map / product-path-card / before-after
- 导航跳转:jump-row / subpage-card / aux-card
- CTA / Callout:cta-grid / data-pain / iron-rule-band / anti-pattern-callout
- 品牌:product-card / dual-products

### Step 4 · 图表选择(先做,不要跳过)

打开 `references/chart-selection.md`,先把每页的"核心关系 → 组件"列出来:

| 数据关系 | 组件 |
|---|---|
| 一个数字很重要 | stat-card / big-number |
| 多个独立 KPI | stat-grid / stat-strip |
| 时间先后 / 诊疗窗口 | timeline / decision-window |
| 输入到输出 / 操作步骤 | pipeline / phase-pill |
| 病原体 / 基因型 / 机制 / 产品匹配 | matrix / gene-drug-map |
| 文献筛选数量递减 | funnel |
| 证据强弱分层 | pyramid / evidence-ladder |
| 同一指标跨对象比较 | proof-bars / ranked bars |
| 患者旅程阶段覆盖 | market-bars |

**硬规则**:
- 条形图只用于同一指标的横向比较、完成率、覆盖率、通过率。
- 多个互不相干 KPI 不得画成 proof-bars。
- 时间路径、机制匹配、证据链、决策流程不得画成普通 bar chart。
- 一个 deck 默认至少使用 3 类不同表达家族,除非素材本身只有一种数据关系。

### Step 5 · 颜色语义化分配

| 颜色 | 变量 | 用在 |
|------|------|------|
| 赭石红(主) | `--accent #CC785C` | 主 CTA / 关键链接 / 主流程线 |
| 朱红(危险) | `--brand-red #C2594A` | 突破事件 / 警告 / 失败 |
| 行业垂直 | `--hema-crimson #8C2B3A` | 严肃 callout(医疗/血液/科技按行业换) |
| 蓝(信息) | `--brand-blue #2E5C8A` | 中性数据 / 第二条线 |
| 紫(技术) | `--brand-purple #6B4E8F` | phase ID / metadata |
| 金(警示) | `--brand-gold #B8903C` | 经验性数据 / 局限提示 |
| 绿(通过) | `--brand-green #5C8D5C` | 通过状态 / 顶级证据 |

### Step 6 · 章节节奏(默认 11 页横向 deck 蓝图)

```
1. WHY        ← 项目背景 / 一张关键图把"为什么做"说清(常用 market-bars / before-after)
2. HERO       ← 大标题 + 一段定位 + stat-bar(4-5 个核心数字)
3. EVIDENCE   ← 数据/证据(漏斗 + 金字塔 / 信任链)
4. ARCHITECTURE ← 系统/方案总览
5. WORKFLOW   ← 详细流程深挖
6. COVERAGE   ← 交付物全貌
7. PROOF      ← 验证/复用证明(只有通过率/覆盖率才用 proof-bars)
8. LIMITATIONS ← 坦诚局限 + roadmap
9. BONUS      ← 衍生洞察(可选)
10. EXTRA     ← 个人项目或附加(可选)
11. CTA       ← 团队 + 3 个 CTA card + 联系
```

每个 slide 固定 `width:100vw;height:100vh`,内容区居中但必须吃满演讲画布。常规页面优先 `.wrap,.frame { max-width:min(1690px,88vw) }`;内容密集或投影演讲页面可用 `.wrap.wide,.frame.wide { max-width:min(1760px,93vw) }`,避免主体缩在屏幕中间太小。常规页标题应接近 90-106px,lead 应接近 28-36px;长标题或 1440×900 下可降到 78px,但 1920 下 regular title median 不能只有 78-85px。`dense-slide` 不等于 `compact`:dense 页可以更宽、更紧,但非 compact dense 页不能把标题封顶到 84px。只有 evidence/table/appendix `.compact` 页可以降级。页脚留在 slide flex 流里,但 `.wrap` 不要用 `margin:auto auto 0` / `margin:auto`,否则会和 footer 的 auto margin 叠加,导致偶发内容沉到底部。不要使用页面纵向滚动来展示下一页。

### HTML 验证清单

- [ ] `:root` 完整 80+ 变量
- [ ] Fraunces + Inter + JetBrains Mono 三字族都引入
- [ ] body 有噪声纹理叠层(`body::before`)
- [ ] `#deck` 横向 fixed flex,每个 `.slide` 是 100vw × 100vh
- [ ] 无页面纵向滚动条;F11 下页脚不遮挡正文
- [ ] 底部圆点、左右键、滚轮、触屏、ESC overview 可用
- [ ] 至少有一个 `.gradient-text` 锚点
- [ ] 至少 3 种 brand 色出现(不要单色到底)
- [ ] 数字用 Fraunces + tabular-nums
- [ ] 至少 3 类不同图表表达家族;不要全 deck 都是 bar / proof-bars
- [ ] 主内容区不能过小:1920×1080 下 `.wrap/.frame` 可视宽度通常不低于 80%,常规投影页接近 88%
- [ ] 字号不能过小:常规页主标题不低于 78px,hero 标题不低于 110px,lead/subtitle 不低于 24px;只有 `.compact` 页例外
- [ ] 1920×1080 下 regular title median 接近 90-106px;`.dense-slide:not(.compact)` 不能用 78-85px 作为常态
- [ ] `.wrap` 不使用 `margin:auto auto 0` / `margin:auto`;这会和 footer auto margin 叠加造成内容沉底
- [ ] 独立 KPI 没被画成 proof-bars
- [ ] 时间窗口没被画成普通 bar chart
- [ ] 机制匹配没被画成条形图
- [ ] 移动断点处理 720px / 900px

---

## PPTX 模式工作流

### Step 1 · 读 references

- **`references/pptx-mode.md`** ⭐ 必读 — PPT 输出模式的完整说明:design tokens 如何映射到 PPT 主题、组件如何用 shape 实现、哪些视觉特性降级、字体如何嵌入。
- **`references/chart-selection.md`** ⭐ 必读 — PPTX 也必须先判断数据关系,不要默认 proof-bars。
- **`references/design-tokens.md`** — 共享的色板/字号 scale(直接复用)
- **`references/typography.md`** — 共享的字体规则(直接复用)

### Step 2 · 用 generate_pptx.py 生成

`assets/generate_pptx.py` 是 python-pptx 程序化生成器,提供:

- `EditorialDeck` 类:封装好的 deck builder,自动应用色板/字体/版面
- 11 个 slide 模板函数:`add_why_slide()`, `add_hero_slide()`, `add_evidence_slide()`, ...,对应 HTML 11 节
- 组件函数:`draw_stat_grid()`, `draw_decision_timeline()`, `draw_gene_drug_matrix()`, `draw_evidence_list()`, `draw_double_bar_chart()`, `draw_evidence_pyramid()`, `draw_phase_pill_row()`,...
- 用法:

```python
from generate_pptx import EditorialDeck

deck = EditorialDeck(industry="medical")  # 或 "tech" / "finance" / "education"
deck.add_hero_slide(
    eyebrow="HEMATOLOGY · IFI MARKET INTELLIGENCE · 2026",
    title_main="一句话起跑",
    title_accent="AI 编排 7 大血液疾病抗真菌药市场调研",
    sub="用户输入一句话疾病名 → 系统跑通 5 phase 流水线 → 4 件交付物",
    stats=[("38亿", "血液 IFI 总市场"), ("7", "Disease Modules"), ("22", "Engineered Charts"), ("43", "PMID Refs")]
)
deck.add_evidence_slide(
    funnel_stages=[("PubMed 触达", "数千"), ("初筛", "~500"), ("纳入", "43")],
    pyramid_tiers=[("最高级", 18, "green"), ("重要级", 17, "blue"), ("参考级", 7, "gold")]
)
deck.save("output/blood_oncology_v5.pptx")
```

### Step 3 · 字体处理

PPT 不能像浏览器那样动态加载 web 字体。两条路:

**A. 字体嵌入(推荐 · 离线场景):**
```python
deck = EditorialDeck(embed_fonts=True)  # 把 .ttf/.otf 嵌入 .pptx
```
要求 `assets/fonts/` 目录含 Fraunces-VariableFont.ttf + Inter-VariableFont.ttf + JetBrainsMono.ttf,生成的 pptx 会带字体,任何机器打开都对。

**B. 字体降级(共享/在线场景):**
- Fraunces → "Cambria"(Windows 自带) / "Times New Roman" 或客户机器装的衬线
- Inter → "Calibri"(Windows 自带) / "Segoe UI"
- JetBrains Mono → "Consolas"(Windows 自带)

降级会损失一点辨识度,但配色/版面/组件仍然 ~85% 还原。

### Step 4 · 视觉特性降级地图

| HTML 特性 | PPT 实现 | 保真度 |
|----------|---------|-------|
| `--bg-0 #FAF9F5` 米色底 | slide background fill solid #FAF9F5 | 100% |
| 6 品牌色 | theme color scheme(可在 PPT View > Slide Master 编辑) | 100% |
| Fraunces / Inter / Mono | 嵌入字体或降级到 Cambria / Calibri / Consolas | 95% / 70% |
| 软阴影卡片 | shape 加 outer shadow + 圆角 12pt | 100% |
| 渐变文字 | text fill gradient 三色 stop | 100% |
| 噪声纹理 | slide background image fill 用 noise.png | 80% |
| 径向渐变光晕 | shape 径向渐变填充 alpha | 90% |
| 玻璃态 backdrop-filter | 半透明白色填充 + 软阴影 | 70% |
| Section navigation | PPT 没有滚动,改用 slide-jump hyperlinks | N/A |
| reveal 滚动动效 | 用 PPT 进入动画(渐入)等价 | 不同机制 |
| `clamp()` 响应式 | PPT 固定布局,16:9 1920×1080 设计 | N/A |

### PPTX 验证清单

- [ ] 主题色板覆盖 6 brand 色
- [ ] 标题用衬线字体(Fraunces 嵌入或 Cambria 降级)
- [ ] 数据用等宽字体(JetBrains Mono / Consolas)
- [ ] 至少 3 张 slide 用了不同 brand 色
- [ ] 至少 3 类不同图表表达,proof-bars 只用于同一指标比较
- [ ] 每张 slide 都有 eyebrow tag(顶部小字)+ 大标题 + 主组件
- [ ] CTA slide 用赭石主色实心按钮形 shape
- [ ] 16:9 1920×1080 分辨率
- [ ] 字体已嵌入(检查 .pptx 解压后 ppt/embeddings/fonts/)

---

## 关键设计原则(两模通用,不要破坏)

1. **不要全部正文用 Fraunces** — 衬线长篇阅读疲劳
2. **不要把所有色都换成主色** — 6 个品牌色按语义分,色彩多样性是辨识度
3. **不要把所有数字都画成条形图** — 图表先表达关系,再表达大小
4. **不要用纯黑文字** — 用 `#141413` 暖墨
5. **不要让每页/每屏背景一样** — 用 3 档底色 + 径向渐变交替,但保持同一套 v5 色板
6. **不要混用按钮风格** — 主 CTA 一种样式,辅 CTA 另一种,跳转第三种,不要乱
7. **不要把演讲 deck 做成网页报告** — 常规页必须采用 projection typography;放不下就拆页或 compact,不要全局缩字
8. **PPT 模式:不要在 PPT 里写 CSS** — 所有视觉走 python-pptx 的 shape API,不要嵌网页

## 常见任务模板

### 任务 A · "做一份 X 主题的 case sharing presentation"

→ HTML 模式 default → 读 design-tokens + chart-selection + components → 拷贝 starter → 11 slide 蓝图 → 删多余页

### 任务 B · "做一份 X 主题的 PPT 给客户演示"

→ PPTX 模式 → 读 pptx-mode.md → 用 generate_pptx.py(EditorialDeck 类)→ 11 个 add_*_slide 调用 → save .pptx

### 任务 C · "把这份 HTML presentation 转成 PPT 版"

→ 解析 HTML 11 sections → 每节调用对应 add_*_slide() → 字体降级 / 嵌入选一 → save

### 任务 D · "我要 HTML 和 PPT 都要,内容一致"

→ 同一份内容数据先抽成 JSON / dict → 一次 HTML 生成、一次 PPTX 生成 → 视觉一致

## 为什么这个 skill 重要

这套设计语言已经在 Pfizer 血液科 IFI 案例分享 v5(2026-04-27 交付)上验证有效,商业场景里被高规格客户/老板看过的设计。复用它意味着:

- 每次做 presentation 不用重调色/选字/设计组件
- HTML / PPT 双格式无缝切换,保持视觉一致
- 跨项目沉淀视觉资产 — 同一作者的多份 deck 看起来像一个系列
- 客户/老板第一眼会觉得"这是花了心思的",而不是"模板套出来的"

源版本参考:`C:\Users\qiyon\Desktop\血液科市场调研_v5_desktop.html`
