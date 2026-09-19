# Rewrite Existing HTML Deck

用于把已有 HTML presentation 改成本 skill 的横向全屏 deck。目标是**格式迁移**,不是内容重写。

## 原则

- 保留原始 slide 内容。默认不改医学声明、引用、证据边界、产品描述和页内正文。
- 只替换演示外壳、CSS token、布局 shell、导航和 JS。
- `deck-shell.html` 是行为 shell 的结构来源。先对齐 shell，再迁移旧内容；视觉构图由 manifest 和 profile 决定。
- 如果发现某页显示异常,先判断是通用 skill 规则缺陷还是该页特殊内容密度。通用缺陷要写回 skill。

## 推荐流程

1. 读取原 HTML 的基本结构:
   - `<title>` / `<meta>`
   - 原 `<style>`
   - 原 `<section class="slide"...>` 数量
   - 原 `<script>` 导航逻辑
2. 抽取所有原始 slide section,作为不可改写内容块。
3. 用 behavior-only deck shell 重建页面:
   - `html, body { width:100%; height:100%; overflow:hidden; }`
   - `#deck { position:fixed; inset:0; display:flex; height:100vh; }`
   - `.slide { flex:0 0 100vw; width:100vw; height:100vh; overflow:hidden; }`
   - 底部 dots、左右键、滚轮、触屏、ESC overview
4. 追加选定 style profile 的角色 token:
   - 从 `style-index.json` 读取 palette、typography、composition grammar 和 cadence
   - 状态色保留语义，分类色不冒充状态
   - 原内容的深浅节拍映射到 profile tone，不强制改回米色
5. 控制内容区:
   - 常规页: `.wrap, .frame { max-width:min(1690px,88vw); }`
   - 医学密集页/产品页/证据表页: `.wrap.wide, .frame.wide { max-width:min(1760px,93vw); }`
   - `.slide` 左右 padding 默认 5vw-6vw;密集页可使用 3.2vw-4vw
   - 不要把所有内容继续套进旧网页报告的 `1320px` 中栏
6. 控制垂直层级:
   - `.wrap` 用明确顶部间距,例如 `margin:clamp(24px,3vh,44px) auto 0`
   - `.wrap` 或 `.frame` 应有 `flex:1; min-height:0`,主 grid 用 `align-content:center` 或 `align-items:center`
   - 不要用 `margin:auto auto 0` 或 `margin:auto`
   - footer 可以 `margin-top:auto`,但 wrap 不能同时 auto
7. 删除旧导航逻辑:
   - 不要保留 `scrollIntoView`
   - 不要保留纵向 scroll-snap
   - 不要依赖 `IntersectionObserver` 更新页码
8. 生成后按 `qa.md` 检查。

## Legacy inline size 覆盖

旧 HTML 经常带有网页报告尺度的 inline 字号,例如 `font-size:15px`、`clamp(26px,3.8vw,50px)`、卡片正文 `12px`。迁移时必须用统一覆盖层接管这些尺寸:

```css
.slide-title,
.section-title { font-size:clamp(78px,5.2vw,106px) !important; line-height:1.08; }
.slide-action,
.subtitle,
.lead { font-size:clamp(25px,1.75vw,36px) !important; line-height:1.45; }
.ic-title,
.card-title,
.product-card h4,
.path-card h3 { font-size:clamp(24px,1.55vw,32px) !important; }
.ic-body,
.card-body,
.product-card p,
.path-card p,
.matrix-cell { font-size:clamp(17px,1.05vw,22px) !important; line-height:1.58; }
.compact .slide-title,
.compact .section-title { font-size:clamp(46px,3.8vw,76px) !important; }
.compact .slide-action,
.compact p,
.compact li,
.compact .matrix-cell { font-size:clamp(15px,.95vw,19px) !important; }
```

注意:这些 `!important` 只用于改写已有 HTML,目的是压过原文件 inline size。新建 deck 不应依赖大量 inline style。

### Dense 不是 Compact

`dense-slide` 只能表示"内容较多,需要更宽的容器和更紧的组件间距",不能作为全局缩字理由。已验证失败模式:把普通内容页设为 `.dense-slide` 后写入 `.dense-slide .slide-title{font-size:clamp(78px,4.1vw,84px)}`,导致 1920 下标题只有约 78.7px,比 guizang-scale 常规页低一档。

改写旧 HTML 时必须遵守:

```css
.dense-slide:not(.compact) .slide-title {
  font-size:clamp(78px,4.9vw,96px) !important;
}
.dense-slide:not(.compact) .slide-action,
.dense-slide:not(.compact) .subtitle,
.dense-slide:not(.compact) .lead {
  font-size:clamp(24px,1.55vw,32px) !important;
}
.dense-slide:not(.compact) .ic-title,
.dense-slide:not(.compact) .card-title,
.dense-slide:not(.compact) h3,
.dense-slide:not(.compact) h4 {
  font-size:clamp(22px,1.45vw,30px) !important;
}
.dense-slide:not(.compact) .ic-body,
.dense-slide:not(.compact) .card-body,
.dense-slide:not(.compact) p,
.dense-slide:not(.compact) li {
  font-size:clamp(16px,1vw,20px) !important;
}
```

只有 `.compact`、`.appendix-slide`、证据表格和法规声明页可以进入更小字号。产品机制页、普通证据页、结论页即使内容密集,也应优先用宽容器、减少装饰、拆页或重排,不要把普通页缩成报告页。

## 内容保留检查

改写后必须确认:

- 原 slide 数 = 新 slide 数。
- 每个原 `<section class="slide"...>...</section>` 的正文内容仍在。
- 如果只是 shell/CSS/JS 迁移,section hash 应保持一致。
- 产品名、合规说明、引用文献、Claim-Evidence Log 不得丢失。

## 常见失败

### 主体缩太小

症状:投影时中间只有一小块内容。

修复:扩大 `.wrap/.frame` 到 `min(1690px,88vw)` 或密集页 `min(1760px,93vw)`,并检查标题是否达到 86-106px、lead 是否达到 28-36px。不要只扩大卡片宽度而保留 15px 正文。

### 内容沉到底部

症状:某一页顶部大片空白,内容贴近底部。

常见原因:`.wrap { margin:auto auto 0; }` 与 footer 的 `margin-top:auto` 同时存在。

修复:全局 `.wrap` 使用明确 top margin;只对 hero 页单独视觉居中。

### 页脚遮挡正文

症状:引用或免责声明压在图表上。

修复:footer 必须在 flex 流内,不用 absolute bottom。检查 `.wrap` 高度和 footer 高度是否超出可用高度。
