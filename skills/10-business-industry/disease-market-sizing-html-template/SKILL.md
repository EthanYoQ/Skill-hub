---
name: disease-market-sizing-html-template
description: >
  Use when generating multi-page HTML market research reports with main page +
  N disease sub-pages structure (e.g. hematology IFI, respiratory ICU fungal,
  oncology immunotherapy). Provides shared CSS design system, sticky topnav,
  hero gradients per market tier, disease-card grid, lp-callout boxes,
  cross-page link integrity, and (v1.2 · 2026-04-25) standalone single-file
  HTML-only 交付 pipeline (build_standalone.py base64 内嵌, v1.2 PDF 已停用,
  仅交付 HTML 单文件即终态交付物).
  Triggers on "生成 HTML 报告主页+子页", "市场调研 HTML 模板", "决策树跳转
  网格", "可分享交付物 / 双击可读 / 邮件附件", or any multi-page disease
  market sizing HTML output. Inherits from L0 market-sizing-mece-foundation §11
  visual specs (MRR alignment).
  After generating HTML pages, downstream skill is `report-bundle-builder` for single-file delivery.
---

# 疾病市场调研 HTML 模板 Skill (L2 · 复用组件)

> **L2 工具组件**:本 skill 提供"主页 + N 子页"HTML 报告的**模板库 + CSS 设计系统**。
> 设计目标:让任何疾病市场调研直接套用,得到一致美观、链接完整、tier 区分清晰的多页 HTML 报告。
> 上游依赖:`market-sizing-mece-foundation` (L0 §11 视觉规范) + `ifi-market-sizing-skill` (L1 §5.3 完整性清单)

## 一句话定义

**主页(总览 + 跳转网格)+ N 子页(疾病独立深挖)** 双重导航 HTML 模板,统一 CSS 设计系统(navy/blue/gold/red),tier-tag 视觉分级(⭐⭐⭐ 金 / ⭐⭐ 橙 / ⭐ 蓝),sticky topnav,disease-card grid,lp-callout 八色 box 系统。

---

## 何时调用本 skill

**调用时机**:
1. 市场调研项目即将生成 HTML 报告
2. 主报告章节数 ≥ 6 + 子市场数 ≥ 3 → 必须用主页 + 子页结构,否则单页过长
3. 已有手写 HTML 报告需要审计(检查是否符合本模板)

**不调用的场景**:
- 单一市场调研(无 N 子市场)→ 用单页咨询式 HTML
- 内部 brief / 快速摘要 → 用 markdown 即可

---

## 文件结构标准

```
output/
├── report_v??.html                  # 主页(总览 + N disease-card 跳转)
├── page_<sub1>.html                 # 子页 1(独立疾病决策树+测算+TOP 3 LP+证据)
├── page_<sub2>.html                 # 子页 2
├── ...
├── flowchart_main_v??.png           # 主图(疾病分流总览,主页 §3 嵌入)
├── flowchart_lp.png                 # LP 全景决策图(主页 §7.0 嵌入 · Iron Law)
├── flowchart_<sub1>_v??.png         # 子页 1 决策树
├── flowchart_<sub2>_v??.png         # 子页 2 决策树
└── flowchart_<sub*>_v??.mmd         # 决策树源码(配套 L2 skill `decision-tree-with-lp-embedding`)
```

---

## CSS 设计系统(共享模板 · 主页 + 子页通用)

```css
:root{
  /* 配色 (MRR 对齐 + 红/金 强调色) */
  --navy:#003366; --blue:#336699; --accent-blue:#0078D7;
  --red:#C62828; --red-bg:#FFEBEE;
  --green:#008060; --green-bg:#C8E6C9;
  --purple:#6A1B9A; --purple-bg:#F3E5F5;
  --gold:#F59E0B; --gold-dark:#78350F;
  --orange:#CA6F1E; --orange-light:#FFEEDA;
  --gray-100:#f3f4f6; --gray-200:#e5e7eb; --gray-300:#d1d5db;
  --gray-500:#6b7280; --gray-700:#374151; --gray-900:#1f2937;
  /* 字体 */
  --font-sans:'Source Han Sans CN','PingFang SC','Microsoft YaHei',sans-serif;
}
*{box-sizing:border-box}html{scroll-behavior:smooth}
body{font-family:var(--font-sans);color:var(--gray-900);line-height:1.65;margin:0;padding:0;font-size:11pt;background:#fff;font-feature-settings:"tnum" 1}
@page{size:A4;margin:2.2cm 2cm}
h1{color:var(--navy);font-size:22pt;margin:22pt 0 10pt;padding-bottom:6pt;border-bottom:2.5pt solid var(--navy);font-weight:700;scroll-margin-top:80px}
h2{color:var(--navy);font-size:15pt;margin:16pt 0 9pt;padding-left:10pt;border-left:4pt solid var(--blue);font-weight:700;scroll-margin-top:80px}
h3{color:var(--blue);font-size:12pt;margin:11pt 0 6pt;font-weight:600}
p{margin:6pt 0}ul,ol{margin:6pt 0;padding-left:22pt}li{margin:3pt 0}
```

### Tier 渐变 hero(子页头部 · 按市场分级)

```css
/* ⭐⭐⭐ 顶级(金色 — Crown Tier) */
.hero.t3{background:linear-gradient(135deg,var(--gold) 0%,var(--gold-dark) 100%)}
/* ⭐⭐ 中等(橙色) */
.hero.t2{background:linear-gradient(135deg,var(--orange) 0%,#7C3F00 100%)}
/* ⭐ 低(海军蓝) */
.hero.t1{background:linear-gradient(135deg,var(--blue) 0%,var(--navy) 100%)}
```

### 共享组件(必含)

| 组件 | 用途 | 关键 CSS |
|------|------|---------|
| `.hero` | 子页 / 主页头部渐变 | padding 28px 32px, color #fff, position relative |
| `.hero .back` | 子页返回主页 | position absolute top 14px right 32px, rgba(255,255,255,0.2) |
| `.hero .tier-tag` | tier 徽章 | background #fff, color tier 主色, padding 2pt 10pt, border-radius 10pt |
| `.topnav` | 章节快速跳转 | sticky top:0, z-index 50, display flex, gap 8px |
| `.disease-card` | 主页跳转网格(子页入口) | padding 16pt 18pt, border-left 5pt solid tier 主色 |
| `.lp-callout` | LP 高亮区块 | display flex, align-items flex-start, padding 12pt 16pt |
| `.lp-crown` | Crown LP | background #FEF3C7, border 3pt solid var(--gold) |
| `.lp-standard` | Standard LP | background #FEE2E2, border 2pt solid #DC2626 |
| `.callout` | 蓝色信息框 | border-left 4pt solid var(--accent-blue), background #E6F1FB |
| `.warning` | 红色警告框 | border-left 4pt solid var(--red), background var(--red-bg) |
| `.datahint` | 绿色数据洞察 | border-left 4pt solid var(--green), background var(--green-bg) |
| `.recommendation` | 紫色建议框 | border-left 4pt solid var(--purple), background var(--purple-bg) |
| `table.ds` | 数据表 | border-collapse, font-size 10pt, font-variant-numeric tabular-nums |
| `.figure` | 图片嵌入 | text-align center, page-break-inside avoid |
| `.anchor-badge` | PMID 文献徽章 | inline-block, font-size 9pt, background #e0f2fe, color #0369a1 |

---

## 主页结构(report_v??.html)

```
[hero · 顶部 navy 背景]
  - 标题 + 立场 + 版本日期 + 署名
  - 分母总市场 + 数据基准

[topnav sticky]
  - 8-12 个章节锚点

[main]
  ① 执行摘要(8-12 条结论)
  ② 研究方法概要
  ③ 主图 flowchart_main_v??.png(完整渲染嵌入)
  ④ N 张 disease-card 跳转网格(子页入口)
     - 每张 disease-card 含: tier-tag, 疾病名, market 占比, 链接
  ⑤ 市场规模(总览表 + TAM/SAM/SOM)
  ⑥ 结论与策略
  ⑦ LP 决策图
     - §7.0 LP 全景决策图 PNG 嵌入(Iron Law · 失败模式 #28)
     - §7.1 8 LP 总览(lp-callout × 8)
     - §7.2 LP 排序表
     - §7.3 LP 量化方法
  附录 A:研究方法论
  附录 B:子页索引(再次列表所有子页 + PNG)
  附录 C:参考文献

[footer]
  - 子页快速跳转链(N 个)
  - 署名
```

## 子页结构(page_<sub>.html)

```
[hero · tier 渐变 (t1/t2/t3)]
  - back 链(返回主页)
  - tier-tag(⭐⭐⭐ 顶级 / ⭐⭐ 中 / ⭐ 低)
  - 疾病名 + market 总额 + 占比
  - 双分支结构提示(预防 X% / 非预防 X%)

[topnav sticky]
  - 主页 / ①决策树 / ②测算 / ③TOP 3 LP / ④证据

[main]
  ① 决策树 PNG 嵌入(flowchart_<sub>_v??.png)
     · 含本 skill `decision-tree-with-lp-embedding` 的 LP 节点级标注
  ② 测算依据
     - 表 1 双分支患者流量
     - 表 2 阶段 × 主药构成
     - datahint 核心洞察
  ③ TOP 3 LP(lp-callout × 3)
     - 1 个 lp-crown(本子页 Crown)
     - 2 个 lp-standard
     - recommendation 区块解释 LP 选择逻辑 + 链回主页 §7
  ④ 关键证据 PMID 表(≥4 行)

[footer]
  - 返回主页链
  - 署名
```

---

## Iron Law(本 skill 强制清单)

### 主页必含
- [ ] §3 嵌入 `flowchart_main_v??.png`(主图)
- [ ] §4 N 张 disease-card 跳转网格(每张含 tier-tag + market 数字 + 链接)
- [ ] **§7.0 嵌入 `flowchart_lp.png` LP 全景决策图(Iron Law · L1 失败模式 #28 历史复现)**
- [ ] §7.1 全部 LP 的 lp-callout
- [ ] footer 含全部 N 个子页快速跳转链

### 子页必含
- [ ] hero 渐变按 tier 分级(t1/t2/t3)
- [ ] sticky topnav 4 个锚点(决策树 / 测算 / TOP 3 LP / 证据)
- [ ] §1 嵌入 `flowchart_<sub>_v??.png`
- [ ] §3 TOP 3 lp-callout(1 个 lp-crown + 2 个 lp-standard)
- [ ] §3 末尾 recommendation 链回主页 §7
- [ ] footer 含返回主页链 + 署名
- [ ] 每子页至少 4 个反向链接(hero back / topnav home / recommendation / footer)

### 链接互联
- [ ] 主页 → 子页:每张 disease-card / 跳转表 / footer 链接全部就位
- [ ] 子页 → 主页:每子页 ≥4 个反向链接
- [ ] 子页 → PNG:每子页正确引用其专属 flowchart_<sub>_v??.png
- [ ] 主页 → flowchart_lp.png + flowchart_main_v??.png 全部就位

### 视觉一致性
- [ ] 全部页面共用同一套 CSS 变量(--navy / --gold / etc)
- [ ] 全部页面字体堆栈一致(Source Han Sans CN → PingFang SC → Microsoft YaHei)
- [ ] tier-tag 配色与 hero 渐变 tier 主色保持一致
- [ ] lp-crown 仅 Crown LP 使用,其他 LP 一律用 lp-standard

---

## 跨疾病移植清单(下次"呼吸科 ICU 真菌"项目)

| 模板部分 | 移植方式 |
|---------|---------|
| CSS :root 变量 | ✅ 直接复用 |
| .hero / .topnav / .disease-card / .lp-callout | ✅ 直接复用 |
| Tier 渐变(t1/t2/t3) | ✅ 直接复用 — Crown/中/低 视觉规范一致 |
| 主页 7 章 + 3 附录骨架 | ✅ 直接复用 — 改章节内容 |
| 子页 4 节(决策树+测算+TOP 3 LP+证据) | ✅ 直接复用 |
| 子页文件名 | 🟡 改名 — 例 `page_RICU_CAPA.html` / `page_PCCM_CPA.html` |
| 主图文件名 | 🟡 改名 — 例 `flowchart_main_resp_v??.png` |
| LP 全景图文件名 | ✅ 保持 `flowchart_lp.png` |
| 配色三档(t3 金/t2 橙/t1 蓝) | ✅ 直接复用 |

---

## 失败模式速查

| # | 失败模式 | 根因 | 修复 |
|---|--------|------|-----|
| 1 | 主页缺 LP 决策图 PNG | skill 无强约束清单 | 本 skill Iron Law §7.0 |
| 2 | 子页 hero 全部用同色 | 无 tier 视觉分级 | 强制 t1/t2/t3 三档渐变 |
| 3 | 子页缺 sticky topnav | 长子页用户找不到锚 | 强制 4 锚点 sticky topnav |
| 4 | disease-card 缺 tier-tag | 主页跳转视觉无层级 | 强制 tier-tag + 颜色对应 hero 渐变 |
| 5 | lp-callout 全部红色 | Crown 与普通无区分 | 强制 1 个 lp-crown(金)+ 其他 lp-standard(红) |
| 6 | 子页 footer 缺返回主页链 | 用户卡死子页 | 强制 footer back 链 |
| 7 | 跨页面 CSS 不一致 | 子页独立写 CSS | 强制全部页用同一套 :root 变量 |
| 8 | LP 排序表用普通 td 不分级 | 视觉重点缺失 | Crown LP 用 background:#FEF3C7;font-weight:600 |
| 9 | 缺 footer 子页快速跳转 | 主页用户在 §7 后无法直接进子页 | 强制 footer 含全部 N 个子页链 |
| 10 | 跨文件交付的链接断裂 | HTML/PNG 跨文件相对路径,收件人解压时漏文件 / 路径不对 / 无 AI 软件无法浏览 | **Iron Law(阶段 6):必须用 build_standalone.py 合并成单文件 HTML 交付,禁止直接交付 7 HTML + 8 PNG 散文件**(v1.2:PDF 已停用,单 HTML 即终态)|
| 11 | PDF 决策树压缩失真 / 重复劳动 | Chrome headless PDF 把 base64 PNG 二次压缩,且 PDF 与单 HTML 内容完全冗余,维护成本翻倍 | **v1.2 决策(2026-04-25)**:PDF 不再交付。单 HTML(零依赖+决策树原画质+锚点跳转)即终态交付物,涵盖屏幕浏览、邮件附件、即时通讯、网盘分享所有场景 |

---

## 阶段 6:可分享交付物生成(单文件 HTML · v1.2 仅 HTML 交付)

> **场景定义**:多页 HTML 报告完成后,需要交付给最终读者(同事 / 客户 / 高管)的"零依赖"形态。
> v2.5.3 实战经验:用户电脑可能没有任何 AI 软件,要"双击就能读 / 邮件附件直接发 / 网盘/即时通讯一键分享"。
>
> ⚠️ **v1.2 重大决策(2026-04-25 用户最终明确)**:**以后交付全部交付 HTML,不再交付 PDF**。
> 单 HTML 已是终态交付物 — 决策树原画质 base64、锚点跳转、零依赖、双击可读、邮件附件可发,**完全覆盖 PDF 所有场景**。PDF 反而引入二次压缩失真、内容冗余、维护翻倍问题。
> 如读者明确要打印,可在浏览器中 Ctrl+P 自行另存为 PDF — **生成方不再主动产出 PDF**。

### 6.1 何时触发

用户出现以下任一意图,立即进入阶段 6:
- "生成可分享的交付物 / 分享给同事 / 邮件附件 / 网盘分享"
- "目标用户电脑可能没有任何 AI 软件 / 双击就能阅读"
- "打包发出去 / 一键交付 / 给客户最终版"
- 项目临近收尾、所有主页+子页已就绪、所有 PNG 已渲染

### 6.2 交付物形态(v1.2 仅 HTML 交付)

| 交付物形态 | 文件 | 大小 | 用户体验 | 推荐 |
|----------|------|------|---------|------|
| **单 HTML(base64 内嵌)** | report_v??_standalone.html | ~9 MB | 双击浏览器打开 · 锚点跳转 · 零依赖 · 决策树原画质 | ✅ **唯一交付物** |
| ~~配套 PDF~~ | ~~report_v??_standalone.pdf~~ | — | — | ❌ **v1.2 停止交付**(失败模式 #11)|
| **ZIP 打包(原生 7 HTML + 8 PNG)** | report.zip | ~10 MB | 解压后打开主页 · 跨文件链接易断 | ❌ **不推荐**(失败模式 #10) |

**为什么单 HTML 即终态**:
- 决策树原画质保留(PDF 会二次压缩)
- 锚点跳转 / 平滑滚动 / 浏览器搜索全部支持(PDF 弱化)
- 邮件附件 9 MB 完全可发(PDF 同体积无优势)
- 读者若需打印 → 在浏览器中 Ctrl+P 自行另存为 PDF(分发方零成本)
- 维护成本砍半:只跑 build_standalone.py,无需 Chrome headless 二次渲染

### 6.3 核心技术规范

#### A) PNG → base64 内嵌
```python
# 正则匹配 <img src="*.png">,替换为 data: URI
data_uri = f"data:image/png;base64,{base64.b64encode(png_bytes).decode('ascii')}"
```
- 8 张 PNG 全部内嵌(主图 1 + LP 全景图 1 + 子页决策树 N)
- 单文件目标 < 25 MB(主流邮箱附件上限)

#### B) 跨文件链接 → 锚点跳转
- 主页 `href="page_<key>.html"` → `href="#page-<key>"`
- 主页 `href="page_<key>.html#decision"` → `href="#page-<key>"`(子页 hash 重写时同步处理)
- 子页 `href="report_v??.html"` → `href="#top"`
- 子页 `href="report_v??.html#§N"` → `href="#§N"`
- 子页内部 `href="#decision|calc|lp|evidence"` → `href="#page-<key>-decision"`(防止多子页锚点冲突)

#### C) 子页 body 包裹成 section
```html
<section class="standalone-subpage" id="page-<key>">
  <div class="standalone-divider">
    <span class="standalone-divider-label">子页 · <key></span>
    <a href="#top" class="standalone-back">↑ 回到主页顶部</a>
  </div>
  <!-- 原子页 body 内容 -->
</section>
```

#### D) 顶部三件套
```html
<a id="top"></a>                                       <!-- 锚点 -->
<div class="standalone-banner">                        <!-- 横幅说明 -->
  <strong>📦 单一独立 HTML 版</strong> · 已合并主页 + 全部 N 个子页 + 全部 M 张 PNG · 零外部依赖 · 双击浏览器即可阅读
</div>
```
每个子页 section 内置"↑ 回到主页顶部"返回链。

#### E.5) 悬浮目录导航(Floating TOC · v1.3 · 2026-04-25 强制)

> **Iron Law**:单文件 HTML 必须含全量悬浮 TOC(主页 + 全部 N 子页所有 h1/h2),不只是主页章节。

**用户体验目标**:
- 右上角圆形目录按钮(40-44px · 始终可见 · 不打扰内容)
- 点击展开右侧悬浮面板(420px · 主报告 + N 子页全量 h1/h2 节点)
- 点击面板外区域 / Esc 键 / 收起按钮 → 关闭
- 点击任意 anchor → 平滑滚动 + 自动收起
- 打印时(@media print) 自动隐藏

**HTML 结构**:
```html
<button id="ftoc-button" type="button" aria-label="打开目录导航">
  <svg viewBox="0 0 24 24">...</svg>
</button>
<div id="ftoc-overlay" hidden>
  <aside id="ftoc-panel" role="dialog">
    <header class="ftoc-header">
      <span class="ftoc-title">目录导航</span>
      <button id="ftoc-close">收起</button>
    </header>
    <div class="ftoc-body">
      <div class="floating-toc-section">
        <div class="floating-toc-section-title">📋 主报告</div>
        <ul>
          <li class="ftoc-l1"><a href="#ch1" data-ftoc-link>一、执行摘要</a></li>
          <li class="ftoc-l2"><a href="#ch1-1" data-ftoc-link>1.1 ...</a></li>
          ...
        </ul>
      </div>
      <div class="floating-toc-section">
        <div class="floating-toc-section-title">
          📑 子页 · <a href="#page-{key}" data-ftoc-link>{key}</a>
        </div>
        <ul>...</ul>
      </div>
      ... (N 子页)
    </div>
  </aside>
</div>
```

**CSS 关键规则**:
- `#ftoc-button { position: fixed; top: 18px; right: 22px; z-index: 9998; }`
- `#ftoc-overlay { position: fixed; inset: 0; z-index: 9999; backdrop-filter: blur(2px); }`
- `#ftoc-panel { width: min(420px, calc(100vw - 28px)); max-height: calc(100vh - 28px); }`
- `body.ftoc-open { overflow: hidden; }`(打开时锁定背景滚动)
- `@media print { #ftoc-button, #ftoc-overlay { display: none !important; } }`

**JS 行为**(vanilla,零依赖):
- 点击按钮 → toggle 显示
- 点击 `#ftoc-overlay`(但非 `#ftoc-panel` 子元素)→ 关闭
- 按 `Esc` 键 → 关闭
- 点击任意 `[data-ftoc-link]` → 50ms 后自动关闭(让锚点跳转先生效)
- 按 `T` 键(键焦点在 body)→ 快速打开

**自动构建**:
- `build_standalone.py` 中的 `extract_headings(html, prefix_id)` + `build_floating_toc(main_html, sub_pages)` 自动从合并后的 HTML 提取所有 `<h1 id>` / `<h2 id>` / `<h3 id>` 并构建树
- 子页 anchor 通过 `prefix_id="page-{key}-"` 自动加前缀,不会与主页冲突

**Iron Law(v1.3.1 修复 · 2026-04-25 用户反馈)**:
1. **主报告分组必须过滤 `page-*` 前缀 anchor**:`extract_headings(main_html)` 在合并后的 HTML 上调用会同时抓到主页和已合并的子页 h1/h2(id 已带 `page-{key}-` 前缀)→ 必须 `if anchor.startswith("page-"): continue` 过滤,否则主报告分组会出现 N 套重复且无归属(图中症状:连续 6 套"双分支决策树/Market 测算/TOP 3 LP/关键证据"无子页归属)
2. **禁用 backdrop-filter: blur**:9 MB+ 大文档下 `backdrop-filter: blur(2px)` 会让浏览器对整个 viewport 强制重排重绘 → 鼠标延迟高、卡顿。改用 `background: rgba(15,23,42,0.35)` 半透明纯遮罩(GPU 友好)
3. **过渡时长 ≤ 150ms · 动画用 `@keyframes` 而非 `transition`**:opacity transition 130ms · panel 用 `animation: ftoc-pop 0.14s ease-out`,加 `will-change: opacity/transform` 提示合成层
4. **打开用 `requestAnimationFrame` 而非 `setTimeout(10)`**:确保 hidden 切换后下一帧才加 .show class(避免动画跳过)

**血液科 v2.5.3 实测**:92 个目录条目自动提取(主页 30+ + 6 子页各 ~10),HTML 体积 +0.02 MB(可忽略)。

#### E.6) 子页 sticky topnav 在合并版隐藏
```css
.standalone-subpage .topnav { display: none !important; }
.standalone-subpage { margin-top: 60pt; padding-top: 30pt; border-top: 4pt double var(--navy); page-break-before: always; }
.standalone-divider { display: flex; justify-content: space-between; background: linear-gradient(90deg, var(--navy) 0%, var(--blue) 100%); color: #fff; padding: 12pt 18pt; border-radius: 6pt; }
```
原因:合并后所有锚点都在同一文档,子页 topnav 失去意义且会污染滚动。

### 6.4 复用脚本骨架(从 build_standalone.py 抽取)

**完整参考实现**:`<output_dir>/build_standalone.py`(血液科 v2.5.3 验证可用)

```python
from pathlib import Path
import base64, re
from dataclasses import dataclass

# ===== 配置常量(跨疾病移植仅改这里)=====
OUT = Path(__file__).parent
MAIN_HTML = OUT / "report_v??.html"
SUB_PAGES: list[tuple[str, Path]] = [
    ("<key1>", OUT / "page_<key1>.html"),
    ("<key2>", OUT / "page_<key2>.html"),
    # ... N 个子页
]
OUTPUT_HTML = OUT / "report_v??_standalone.html"

@dataclass(frozen=True)
class SubPage:
    key: str; title: str; body_html: str; head_style: str

# ===== 核心五函数 =====
def extract_subpage(path, key) -> SubPage: ...      # 提取子页 body + 重写主页链接
def png_to_base64(path) -> str: ...                  # PNG → data: URI
def inline_all_png(html, base_dir): ...              # 批量替换 <img src="*.png">
def rewrite_subpage_links(html) -> str: ...          # 主页 page_*.html → #page-*
def build_section_for_subpage(sub) -> str: ...       # 子页 body → <section>

def merge():
    # 1) 读主页 + N 子页
    # 2) 注入 extra CSS(.standalone-* 系列)
    # 3) 重写主页跨文件链接
    # 4) <body> 后注入 <a id="top"> + banner
    # 5) </main> 前插入 N 个子页 section
    # 6) inline_all_png 全文 PNG 内嵌
    # 7) 写出 + 验证
```

### 6.5 ~~配套 PDF 生成~~(v1.2 已停用 · 2026-04-25)

> ❌ **本节已停用**:用户最终明确"以后交付全部交付 HTML,不再交付 PDF"。
> 单 HTML 是终态交付物 — 决策树原画质 base64 内嵌、锚点跳转、零依赖,完全覆盖 PDF 所有场景。
> 读者若需打印,在浏览器中按 `Ctrl+P` 自行另存为 PDF — **生成方不再主动产出 PDF**。
> Chrome headless / playwright 命令仅作历史归档保留(失败模式 #11)。

### 6.6 验证清单(交付前必过)

- [ ] **文件大小** < 25 MB(邮件附件可发)
- [ ] **锚点跳转**:点击主页任一 disease-card → 平滑滚到对应子页 section
- [ ] **回退链**:每个子页内 "↑ 回到主页顶部" 工作正常
- [ ] **PNG 内嵌**:N+1 张 PNG 全部用 `data:image/png;base64,...` 内嵌(grep 计数)
- [ ] **零外部依赖**:断网双击打开,所有图、所有跳转、所有样式都正常
- [ ] **banner 提示**:文件顶部"📦 单一独立 HTML 版"横幅可见
- [ ] **悬浮目录导航**(v1.3 Iron Law):右上角目录按钮可见,点击展开主报告 + 全部 N 子页全量目录(h1/h2 全提取),点击外部/Esc 关闭,@media print 隐藏
- [ ] ~~PDF 验证~~ — v1.2 不再交付 PDF,本项删除

### 6.7 跨疾病移植清单

| 配置项 | 改动 | 示例(呼吸科 ICU 真菌) |
|-------|------|----------------------|
| `MAIN_HTML` | 🟡 改 | `report_resp_v??.html` |
| `SUB_PAGES` | 🟡 改 | `[("RICU_CAPA", ...), ("PCCM_CPA", ...), ...]` |
| `OUTPUT_HTML` | 🟡 改 | `report_resp_v??_standalone.html` |
| `extract_subpage()` 中主页文件名正则 | 🟡 改 | `r'href="report_resp_v??\.html"'` |
| 五个核心函数(extract / inline / rewrite / build / merge)| ✅ 直接复用 | — |
| extra CSS(.standalone-* 系列)| ✅ 直接复用 | — |
| banner 文案 | 🟡 改版本号即可 | — |
| ~~Chrome headless PDF 命令~~ | ❌ v1.2 已停用 | 不再交付 PDF |

### 6.8 Iron Law(本阶段强制条款)

**报告交付前必须生成单文件 HTML 版本(v1.2 更新 · 仅 HTML 交付)**:
- 跨文件链接的"N HTML + M PNG"形态**禁止**直接交付给最终读者
- 必须用 `build_standalone.py` 合并成单一 HTML(零外部依赖)
- ❌ **不再生成 PDF**(失败模式 #11 · 用户最终决策 2026-04-25)
- 合并失败或 §6.6 验证清单未全过 → **不可声明"已交付"**
- **历史复现证据**:
  - v2.5.3 初版双交付 HTML + PDF — 用户立即指出"以后交付全部交付 HTML,不再交付 PDF"
  - 单 HTML 已涵盖屏幕浏览/邮件附件/即时通讯/网盘分享/打印(浏览器 Ctrl+P)所有场景

---

## 版本历史

- **v1.3 (2026-04-25)** · **新增悬浮目录导航 Iron Law**(阶段 6.3 §E.5)— 单文件 HTML 必须含全量 TOC(主页 + 全部 N 子页 h1/h2),右上角圆形按钮 + 悬浮面板,点击外部/Esc 关闭,@media print 隐藏。`build_standalone.py` 新增 `extract_headings()` + `build_floating_toc()` 自动构建,血液科 v2.5.3 实测 92 条目自动提取。
- **v1.2 (2026-04-25)** · **PDF 永久停用**(用户最终决策"以后交付全部交付 HTML,不再交付 PDF")。新增失败模式 #11(PDF 二次压缩失真 + 内容冗余)。Iron Law 简化为"必须生成单文件 HTML 版本"。读者打印需求 → 浏览器 Ctrl+P 自助。
- **v1.1 (2026-04-25)** · 追加阶段 6:可分享交付物生成(原方案 单文件 HTML + 配套 PDF · 已被 v1.2 收敛为 HTML-only)。新增失败模式 #10。证据来源:
  - 血液科 v2.5.3 [build_standalone.py](D:/Vibe Coding Project/AI Square/血液科市场调研/output/build_standalone.py)
  - 交付物 [report_v25_standalone.html](D:/Vibe Coding Project/AI Square/血液科市场调研/output/report_v25_standalone.html) (9 MB)
- **v1.0 (2026-04-25)** · 从血液科 v2.5 第 6 次迭代抽出。证据来源:
  - 主页 [report_v25.html](D:/Vibe Coding Project/AI Square/血液科市场调研/output/report_v25.html)
  - 6 子页 [page_alloHSCT.html](D:/Vibe Coding Project/AI Square/血液科市场调研/output/page_alloHSCT.html) 等
  - L1 ifi-market-sizing-skill v1.5 §5.3 HTML 报告完整性清单

---

## Skill Presented by:YongQi, SimonSu, RuiYu, YingJi
