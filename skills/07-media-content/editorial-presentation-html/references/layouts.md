# Layouts · Warm Editorial Fullscreen Deck

这些布局保留血液科 v5 的 warm editorial 设计语言,但输出形态是横向全屏 deck。每页固定 `100vw × 100vh`,通过 `#deck` 横向翻页,不是纵向滚动网页。

## 基础结构

```html
<section class="slide tone-paper">
  <div class="slide-chrome">
    <span>MODULE · TOPIC</span>
    <span>01 / 12</span>
  </div>
  <div class="wrap">
    <!-- 主内容 -->
  </div>
  <footer class="slide-foot">
    <span>Evidence / source note</span>
    <span>PFIZER HBU · INTERNAL</span>
  </footer>
</section>
```

## Guizang-scale 版面目标

本 skill 的 HTML deck 要复刻 `guizang-ppt-skill` 的演讲尺度,但保留 warm editorial 色板。已验证 guizang 输出在 1920x1080 下的结构:

- `.slide` 约 `6vh 6vw 10vh`,主 frame 宽度约 1690px(88vw),高度约 869px(80vh)。
- 常规主标题约 98-106px;hero 标题约 150px+;lead 约 33-36px。
- 主内容通过 `.frame` / `.wrap` 占住可用画布,不是缩在屏幕中心的网页容器。

因此本 skill 的 HTML 模板必须有两层尺度:

```css
.slide { padding: clamp(42px, 6vh, 68px) clamp(64px, 5.5vw, 116px) clamp(72px, 9vh, 108px); }
.wrap, .frame { width:100%; max-width:min(1690px, 88vw); margin:0 auto; flex:1; min-height:0; }
.frame { display:flex; flex-direction:column; overflow:hidden; }
```

医学证据密集页可以扩宽到 `min(1760px, 93vw)`,但不能通过缩小字号来伪装成可读。若 projection scale 下放不下,优先拆成更多页或使用 `.compact` 局部降级。

## 主题类

| 类 | 用途 |
|---|---|
| `tone-paper` | 默认米色底,最接近 v5 主体页 |
| `tone-warm` | 次级暖米底,用于章节切换和 evidence 页 |
| `tone-hero` | hero / cover,保留 v5 径向光晕和网格噪声 |
| `tone-soft` | 轻强调页,适合 timeline / matrix |

不要新增整页深蓝、深红、appendix 主题。品牌色只做局部语义高亮。

## 推荐页型

| 页型 | 用途 | 推荐组件 |
|---|---|---|
| Cover | 开场定位 | hero title + stat-strip |
| Why | 市场问题 / 背景 | market-bars / before-after |
| KPI | 多个独立数字 | stat-grid |
| Time Window | 时间先后 / 诊疗窗口 | decision-window / timeline |
| Workflow | 步骤流程 | pipeline / phase-pill |
| Mechanism | 机制匹配 | matrix / gene-drug-map |
| Evidence | 文献筛选与证据等级 | funnel + pyramid |
| Product Path | 产品路径 / 适应症边界 | product-path-card |
| Proof | 同一指标跨对象比较 | proof-bars |
| Close | 结论与行动 | CTA cards / question |

## 内容区尺寸

- 常规投影 deck 使用 `.wrap, .frame { max-width:min(1690px,88vw); }`,对应 guizang 的满幅演讲尺度。
- 内容密集、医学学术、表格/证据页可使用 `.wrap.wide, .frame.wide { max-width:min(1760px,93vw); }`。
- 横向全屏 deck 不应把主体压成屏幕中间的小块。1920×1080 下,主内容宽度通常应达到视口的 82%-90%;如果低于 80%,需要扩大 `.wrap/.frame` 或减少左右 padding。
- `.slide` 的左右 padding 建议 5vw-6vw。密集内容可用 3.2vw-4vw,但必须保持标题/lead 的 projection scale。

## 垂直定位

- `.wrap` 不要使用 `margin:auto auto 0`、`margin:auto` 或其他会在 flex column 中把内容推到底部的写法。
- 使用明确顶部节奏,例如 `.wrap { margin: clamp(24px, 3vh, 44px) auto 0; }`,并让 `.frame` / 主 grid 通过 `flex:1` 吃满可用高度。
- 如果要做开场 hero 的视觉居中,只对该页增加局部 class 或 inline 上边距,不要改全局 `.wrap`。
- 页脚使用 flex 流内 `margin-top:auto`,但主体 `.wrap` 不能也使用 auto margin;两者叠加容易产生偶发"内容沉底"。
- 常规内容页的主标题不应出现在页面下半部。1920x1080 下标题 top 通常在 120-220px 区间;超过 280px 要视为可疑。

## 全屏硬规则

- 每页必须能在 1920×1080 和 1440×900 下无纵向滚动。
- `.wrap` 内容高度要小于 `calc(100vh - chrome - foot - padding)`。
- 页脚使用 flex 流内 `margin-top:auto`,不要 absolute bottom。
- 标题超过 16 个中文字符时手工断行或降级字号。
- 常规页 `.section-title` 不能长期停留在 54-58px;这属于网页报告尺度。投影演讲页应接近 90-106px;长标题或 1440×900 下可降到 78px,但 1920 下 regular median 不能只有 78-85px。
- `.dense-slide` 不等于 `.compact`:dense 页可以用更宽容器、更紧组件间距,但非 compact dense 页标题仍要接近 projection scale。
- lead / subtitle 不能长期停留在 15-17px;投影演讲页应接近 28-36px,只有 `.compact` 页例外。
- 一个 deck 默认至少 3 类表达家族,除非素材只有一种数据关系。
