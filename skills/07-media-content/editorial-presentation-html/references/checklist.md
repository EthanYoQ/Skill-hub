# Checklist · Warm Editorial Deck QA

## P0 · 必须通过

- [ ] 仍使用血液科 v5 色板: `#FAF9F5`, `#F3EEE3`, `#EBE5D8`, `#CC785C`, `#8C2B3A`, `#0095D5`。
- [ ] 没有引入靛蓝 / 冷纸白等其他主题 token。
- [ ] HTML 是横向全屏 deck:`#deck` fixed flex,`.slide` 为 `100vw × 100vh`。
- [ ] 页面没有纵向滚动条,F11 下当前 slide 不被裁底。
- [ ] 主内容区不是缩在屏幕中间的小块:1920×1080 下 `.wrap/.frame` 可视宽度通常不低于视口 80%,常规投影页优先 `max-width:min(1690px,88vw)`,密集学术页优先 `max-width:min(1760px,93vw)`。
- [ ] 字号达到投影尺度:常规页主标题不低于 78px,hero 标题不低于 110px,lead/subtitle 不低于 24px;只有 `.compact` 页例外。
- [ ] 1920×1080 下常规页标题中位数接近 90-106px;如果只有 78-85px,说明普通页被 `.dense-slide` 错误降级。
- [ ] 卡片标题不低于 22px,卡片正文不低于 16px;大量 11-15px 正文属于旧网页报告尺度残留。
- [ ] 底部圆点、左右键、滚轮、触屏、ESC overview 都存在。
- [ ] 页脚在 slide 文档流内,不使用 absolute bottom 压住正文。
- [ ] `.wrap` 不使用 `margin:auto auto 0` / `margin:auto`;主体内容不能被 flex auto margin 推到底部。
- [ ] 中文标题没有单字落行。
- [ ] 没有把多个独立 KPI 画成 proof-bars。
- [ ] 没有把时间窗口画成普通 bar chart。
- [ ] 没有把机制匹配画成条形图。
- [ ] 一个 deck 至少 3 类表达家族,除非素材只有一种数据关系。

## P1 · 视觉一致性

- [ ] 标题用 Fraunces / Source Han Serif SC 或同等衬线。
- [ ] 正文用 Inter / Noto Sans SC。
- [ ] 数据和页眉页脚用 JetBrains Mono。
- [ ] 卡片圆角、软阴影、噪声纹理、径向光晕保持 v5 质感。
- [ ] 品牌色按语义使用,不是随意换整页背景。

## P2 · 图表多样性

- [ ] KPI 用 stat-grid / stat-strip。
- [ ] 时间关系用 timeline / decision-window。
- [ ] 机制/产品匹配用 matrix。
- [ ] 文献筛选用 funnel。
- [ ] 证据等级用 pyramid / evidence-ladder。
- [ ] 只有同一指标跨对象比较时才用 proof-bars。

## P3 · PPTX

- [ ] PPTX 仍为 16:9。
- [ ] PPTX 使用同一套 v5 RGB token。
- [ ] PPTX 示例不只包含 bar / proof-bars。
- [ ] 字体嵌入或降级路径可用。
