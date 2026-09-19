# QA · Fullscreen Deck Checks

生成或改写 HTML deck 后必须做检查。优先用浏览器自动检测,再人工看关键截图。

## 必查断言

在 1920×1080 和 1440×900 两个视口下检查:

- slide 数量符合预期。
- `document.documentElement.scrollHeight <= clientHeight + 1`,没有页面纵向滚动条。
- 每个 `.slide` 没有内容/页脚重叠。
- `.wrap` / `.frame` 可视宽度不小于视口 80%;常规投影页建议接近 88%,密集医学页建议达到 90% 以上。
- `.wrap` 顶部不低于页面中部;常规页 `wrapTop` 不应超过视口高度的 26%。
- 常规页主标题 computed font-size 不低于 78px;hero 页不低于 110px;只有 `.compact` 页可低于此值。
- 1920×1080 下常规页主标题 median 应接近 90-106px;如果 regular median 只有 78-85px,说明 dense 页被错误降级,需要检查 `.dense-slide:not(.compact)` 的标题规则。
- 常规页 lead / subtitle computed font-size 不低于 24px;只有 `.compact` 页可低于此值。
- 卡片标题不低于 22px;卡片正文不低于 16px。若大量正文只有 11-15px,判定为网页报告尺度残留。
- ESC overview 展示所有 slide 缩略图。
- overview 不应需要纵向滚动,除非 slide 超过 24 页且用户接受多屏索引。

## 静态检查

必须 grep:

- 不应出现 `scrollIntoView`。
- 不应出现旧纵向 `scroll-snap-type:y` 生效规则。
- 不应出现 `IntersectionObserver` 作为翻页状态依赖。
- 不应出现 `.wrap { margin:auto` 或 `margin:auto auto 0`。
- 必须出现 `#deck`, `#overview`, `Escape`, `touchstart`, `wheel`。

## 截图抽查

至少截图:

- 第 1 页:确认开场尺度和整体色彩。
- 一个常规标题页:确认主标题接近 guizang 的投影尺度,不是 54-58px。
- 内容最密的一页:确认文字可读、页脚不遮挡。
- 结论/CTA 页:确认没有沉底。
- ESC overview:确认缩略图数量和布局。

## Creator-style 结果记录

用下面格式记录结果:

```json
{
  "assertions": [
    {"text": "keeps all slides", "passed": true, "evidence": "19/19"},
    {"text": "no vertical scrollbar", "passed": true, "evidence": "1920=false,1440=false"},
    {"text": "main content not too narrow", "passed": true, "evidence": "min width ratio 0.88"},
    {"text": "projection typography", "passed": true, "evidence": "regular title median 96px at 1920, lead median 31px"},
    {"text": "no sunk slide", "passed": true, "evidence": "max wrapTop ratio 0.18"},
    {"text": "overview shows all slides", "passed": true, "evidence": "19 cards"}
  ]
}
```

如果任何 P0 断言失败,不要只修产物。先判断是否需要更新 skill 的 `layouts.md` / `checklist.md` / starter template。
