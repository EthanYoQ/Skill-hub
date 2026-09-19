# PPTX Mode · 把 Editorial 设计语言映射到 PowerPoint

> 本文件指导如何把 HTML 模式的设计 DNA(配色 / 字体 / 视觉表现形式)程序化迁移到 .pptx。复刻保真度目标 85-90%(视觉部分)。

## 核心原则

1. **用 python-pptx 程序化生成**——不要手动在 PowerPoint 里画。手动会丢一致性,程序化才能跨 deck 保持视觉统一。
2. **共享 design-tokens.md 和 typography.md** 的 RGB 值和字号 scale——PPT 是 token 的另一种渲染目标,DNA 不变。
3. **先读 `chart-selection.md` 再选组件**——PPTX 模式同样禁止把 KPI、时间窗、机制匹配、证据链默认画成 proof bars。
4. **降级清单要事先告诉用户**——不是所有 HTML 视觉都能 100% 复刻到 PPT,提前说明保真度。
5. **配合 anthropic-skills:pptx** — 那个 skill 已封装好 python-pptx 的常用操作,本 skill 提供"设计语言层",二者搭配。

## 工作流

### Step 1 · 安装依赖

```bash
pip install python-pptx Pillow
```

可选(嵌入字体场景):

```bash
pip install fonttools  # 字体子集化以减小 .pptx 体积
```

### Step 2 · 准备资产

`assets/` 目录需要:

- `Fraunces-VariableFont_SOFT,WONK,opsz,wght.ttf`(从 Google Fonts 下载)
- `Inter-VariableFont_opsz,wght.ttf`
- `JetBrainsMono-VariableFont_wght.ttf`
- `noise.png`(预渲染的 180×180 噪声图,用于 slide 背景叠层)
- `radial-glow-tl.png`(可选,左下径向光晕)
- `radial-glow-tr.png`(可选,右上径向光晕)

如果没有 noise.png,可以用 Python 生成:

```python
from PIL import Image, ImageFilter
import random
img = Image.new('RGB', (180, 180), (250, 249, 245))
pixels = img.load()
for y in range(180):
    for x in range(180):
        n = random.randint(-12, 12)
        r, g, b = pixels[x, y]
        pixels[x, y] = (max(0,min(255,r+n)), max(0,min(255,g+n)), max(0,min(255,b+n)))
img.filter(ImageFilter.SMOOTH).save('assets/noise.png')
```

### Step 3 · 用 EditorialDeck 类生成

完整生成器在 `assets/generate_pptx.py`。基础用法:

生成前必须读取:

- `references/design-tokens.md`
- `references/typography.md`
- `references/chart-selection.md`

组件选择硬规则:

- 独立 KPI → `add_hero_slide(stats=...)` 或 stat grid 思路,不画 proof bars。
- 时间先后 / 治疗窗口 → `add_relationship_slide(timeline=...)`。
- 机制 / 产品 / 触发条件匹配 → `add_relationship_slide(matrix=...)`。
- 证据引用 / 证据链 → `add_relationship_slide(evidence=...)` 或 `add_evidence_slide(pyramid=...)`。
- 同一指标横向比较、完成率、覆盖率、通过率 → 才用 `add_proof_slide(proof_bars=...)`。

```python
from generate_pptx import EditorialDeck

# 初始化(行业垂直主色由 industry 决定)
deck = EditorialDeck(
    title="血液科 IFI · Case Sharing v5",
    industry="medical",          # "medical" | "tech" | "finance" | "education"
    embed_fonts=True,            # True 嵌入 Fraunces+Inter+Mono;False 用 Cambria/Calibri/Consolas
    aspect_ratio="16:9",         # "16:9" 1920×1080(默认)| "4:3" 1024×768
)

# 添加 slides — 每个对应 HTML 模式的一个 section
deck.add_why_slide(
    eyebrow="WHY · 项目源头 · 战略视角",
    title="血液真菌市场 = ",
    title_accent="两条平行患者旅程",
    bar_chart={
        "axis": ["阶段→", "预防", "突破", "经验性", "诊断驱动", "目标治疗", "维持"],
        "rows": [
            {"label": "LINE A · 有预防", "pct": "~50%", "cells": ["s-prevent", "event", "s-empiric", "s-dd", "s-target", "s-maint"]},
            {"label": "LINE B · 无预防", "pct": "~50%", "cells": ["empty", "empty", "s-empiric", "s-dd", "s-target", "s-maint"]},
        ]
    },
    data_pain="B 从 1% → 15% 不等(差 12 倍)· 必须用 AI 算清 P × B 真实分布"
)

deck.add_hero_slide(
    eyebrow="BLOOD ONCOLOGY · IFI · 2026",
    title_main="一句话起跑",
    title_accent="AI 编排 7 大血液疾病抗真菌药市场调研",
    sub="用户输入一句话疾病名 → 系统自动跑通 5 phase 流水线 → 输出 4 件交付物",
    stats=[
        ("38亿", "血液 IFI 总市场"),
        ("7", "Disease Modules"),
        ("22", "Engineered Charts"),
        ("43", "PMID Refs"),
    ]
)

deck.add_evidence_slide(
    funnel=[("PubMed 触达", "数千"), ("初筛", "~500"), ("纳入", "43")],
    pyramid=[("最高级", 18, "green"), ("重要级", 17, "blue"), ("参考级", 7, "gold")]
)

deck.add_relationship_slide(
    eyebrow="RELATIONSHIP GRAMMAR · 非条形图默认",
    title="时间窗、机制匹配、证据链 · 分开表达",
    timeline=[
        {"label": "Risk signal", "window": "0-6h", "message": "先识别治疗窗口", "tone": "gold"},
        {"label": "Decision", "window": "6-24h", "message": "明确是否升级", "tone": "accent"},
        {"label": "Target", "window": "24-48h", "message": "按证据校准路径", "tone": "green"},
    ],
    matrix=[
        {"mechanism": "耐药风险", "trigger": "高危病原线索 + 既往用药", "path": "产品路径 A", "tone": "medical"},
        {"mechanism": "治疗时机", "trigger": "ICU / 免疫抑制 / 失败信号", "path": "产品路径 B", "tone": "accent"},
    ],
    evidence=[
        {"grade": "A", "label": "指南锚点", "note": "定义临床边界", "tone": "green"},
        {"grade": "B", "label": "研究证据", "note": "支持机制路径", "tone": "blue"},
    ],
)

deck.add_architecture_slide(
    phases=[("P0", "Contract", "契约抽取"), ("P1", "Stratify", "动态分层"), ("P2", "Recall", "数据召回"), ("P3", "Compose", "内容生成"), ("P4", "Verify", "事实核验"), ("P5", "Bundle", "打包交付")],
    deliverables=[("HTML", "9MB"), ("PDF", "3 份口径"), ("Excel", "7 张证据表"), ("Manifest", "delivery.json")]
)

# ... 其他 slides ...

deck.add_cta_slide(
    team=["YongQi", "SimonSu", "VivienZhan", "RuiYu", "YingJi"],
    tech_stack=["Claude Code", "22 Skills", "Codex GPT-5.5", "Mermaid ELK", "Puppeteer"],
    ctas=[
        {"tag": "主钩 A", "time": "1 周", "title": "一句话疾病名 → demo", "desc": "..."},
        {"tag": "主钩 B", "time": "1 月", "title": "BU GPT 助手", "desc": "..."},
        {"tag": "Q&A 加码", "time": "3 月", "title": "5 治疗领域", "desc": "..."},
    ],
    contact="yong.qi.gpt@gmail.com"
)

deck.save("output/blood_oncology_v5.pptx")
```

## Design Token → PPT 映射

### 配色映射(直接 RGB 值)

```python
# 这些应该和 design-tokens.md 的 :root 完全对应
COLORS = {
    "bg_0":          (250, 249, 245),  # #FAF9F5
    "bg_1":          (243, 238, 227),  # #F3EEE3
    "bg_2":          (235, 229, 216),  # #EBE5D8
    "bg_surface":    (255, 255, 255),  # #FFFFFF
    "text_0":        (20, 20, 19),     # #141413
    "text_1":        (44, 42, 38),     # #2C2A26
    "text_2":        (91, 84, 74),     # #5B544A
    "text_3":        (98, 91, 79),     # #625B4F
    "accent":        (204, 120, 92),   # #CC785C 主赭石红
    "accent_hot":    (232, 168, 136),  # #E8A888
    "accent_deep":   (164, 89, 70),    # #A45946
    "brand_blue":    (46, 92, 138),    # #2E5C8A
    "brand_purple":  (107, 78, 143),   # #6B4E8F
    "brand_gold":    (184, 144, 60),   # #B8903C
    "brand_green":   (92, 141, 92),    # #5C8D5C
    "brand_red":     (194, 89, 74),    # #C2594A
    "brand_pink":    (199, 122, 154),  # #C77A9A
    "hema_crimson":  (140, 43, 58),    # #8C2B3A 医疗垂直
    "pfizer_blue":   (0, 149, 213),    # #0095D5
    "border_soft":   (227, 220, 204),  # #E3DCCC
    "border":        (208, 200, 181),  # #D0C8B5
}

# 行业垂直主色替换
INDUSTRY_VERTICAL = {
    "medical":   (140, 43, 58),    # #8C2B3A 深红血色
    "tech":      (26, 58, 110),    # #1A3A6E 深海军蓝
    "finance":   (45, 90, 58),     # #2D5A3A 深森林绿
    "education": (74, 45, 92),     # #4A2D5C 深紫罗兰
    "fashion":   (122, 41, 64),    # #7A2940 深酒红
}
```

### 字体映射

```python
# 嵌入模式(推荐 · 离线场景 · 95% 保真)
FONTS_EMBED = {
    "serif":      "Fraunces",
    "sans":       "Inter",
    "mono":       "JetBrains Mono",
}

# 降级模式(共享 · 在线场景 · 70% 保真)
FONTS_FALLBACK = {
    "serif":      "Cambria",        # Windows 自带衬线
    "sans":       "Calibri",        # Windows 自带无衬线
    "mono":       "Consolas",       # Windows 自带等宽
}
# Mac 等价:Cambria → Cochin · Calibri → Helvetica Neue · Consolas → Menlo
```

### 字号映射(HTML clamp → PPT 固定 pt)

PPT 是固定布局,不能 clamp,直接取 max 值除以 1.33(px → pt 换算):

| HTML | PPT(pt)| 用途 |
|------|--------|------|
| `clamp(40px, 5.5vw, 80px)` hero-title | **60pt** | hero h1 |
| `clamp(34px, 4.5vw, 58px)` section-title | **44pt** | section h2 |
| 22px `.bar-meta .pct` | **17pt** | 双柱图百分比 |
| `clamp(36px, 4vw, 64px)` stat .num | **48pt** | 大数字 |
| 17px section-subtitle | **14pt** | subtitle |
| 14px wf-phase-name | **11pt** | phase 名 |
| 13px proof-bar pb-name | **10pt** | bar 标签 |
| 12px button | **9pt** | 按钮 |
| 11px section-tag | **8pt** | eyebrow |
| 10px phase-pill ph-id | **8pt** | ID label |
| 8px product-chip | **6pt** | 微 chip(PPT 最小推荐 8pt,可 8pt 微调)|

## 视觉特性降级清单

### ✅ 100% 保真(原生支持)

- 所有 RGB 颜色
- 圆角矩形(shape with rounded corners)
- 软阴影(shape Outer Shadow + Blur)
- 渐变填充(linear / radial)
- 渐变文字(text fill gradient — Office 2016+)
- 等距网格布局
- 图表(虽然 PPT 自带不如 HTML 灵活)

### ⚠️ 降级实现(80-90% 保真)

| HTML | PPT 等价 |
|------|---------|
| 噪声纹理 `body::before` | slide background 用 noise.png 图片填充 + 30% 透明 |
| 径向渐变光晕 `radial-gradient` | shape 椭圆 + 渐变填充 + 模糊边缘 + 透明度 |
| 玻璃态 `backdrop-filter: blur(20px)` | 半透明白色填充(`rgba(255,255,255,.55)`)+ outer shadow |
| `clip-path: polygon()` 漏斗梯形 | shape Trapezoid 或自定义 freeform |
| `linear-gradient` 文字 | PowerPoint 文字 `solid_fill` + gradient (XML 直接写) |
| `letter-spacing` | python-pptx 的 `font.spacing`(以 100 单位 = 1 pt) |

### ❌ 不能复刻(放弃这些)

- IntersectionObserver reveal — PPT 没滚动,改用 entrance 动画
- count-up 数字插值 — PPT 动画不支持,改用静态显示
- `:hover` 状态 — PPT 没 hover
- `clamp()` 响应式 — PPT 固定布局
- 滚动 nav 浮动条 — PPT 用 slide-jump hyperlinks 替代
- font-feature-settings cv11 / ss01 — 浏览器特性

## EditorialDeck 类核心方法

完整实现见 `assets/generate_pptx.py`。关键方法:

```python
class EditorialDeck:
    def __init__(self, title, industry="medical", embed_fonts=True, aspect_ratio="16:9"):
        """初始化 deck,设置 master slide 的配色 + 字体 + 噪声背景。"""

    def add_why_slide(self, eyebrow, title, title_accent, bar_chart, data_pain):
        """Slide 1 WHY · 双柱图叙事"""

    def add_hero_slide(self, eyebrow, title_main, title_accent, sub, stats, jump_links=None):
        """Slide 2 HERO · 大标题 + stat-bar"""

    def add_evidence_slide(self, eyebrow, title, funnel, pyramid):
        """Slide 3 EVIDENCE · 漏斗 + 金字塔并排"""

    def add_relationship_slide(self, eyebrow, title, timeline=None, matrix=None, evidence=None, note=None):
        """Slide RELATIONSHIPS · 时间窗 + 机制矩阵 + 证据列表(非 bar 默认)"""

    def add_architecture_slide(self, phases, deliverables, iron_rule):
        """Slide 4 · phase pill 链 + delivery box"""

    def add_workflow_slide(self, phases_detail, quality_gates, stats_footer):
        """Slide 5 · 详细 workflow phases"""

    def add_coverage_slide(self, hub, subpages, aux_cards):
        """Slide 6 · hub 矩阵"""

    def add_proof_slide(self, proof_bars, key_message):
        """Slide 7 · 同一指标横向比较专用 proof bars"""

    def add_limitations_slide(self, limits, roadmap):
        """Slide 8 · 局限 + roadmap"""

    def add_bonus_slide(self, title, body, video_path=None, gh_link=None):
        """Slide 9 · 衍生洞察(可选)"""

    def add_cta_slide(self, team, tech_stack, ctas, contact):
        """Slide 11 · 团队 + CTA cards"""

    # 内部组件
    def _draw_double_bar_chart(self, slide, x, y, w, h, data): ...
    def _draw_evidence_pyramid(self, slide, x, y, w, h, tiers): ...
    def _draw_funnel(self, slide, x, y, w, h, stages): ...
    def _draw_decision_timeline(self, slide, x, y, w, h, items): ...
    def _draw_matrix(self, slide, x, y, w, h, rows): ...
    def _draw_evidence_list(self, slide, x, y, w, h, items): ...
    def _draw_phase_pill_row(self, slide, x, y, w, h, phases): ...
    def _draw_proof_bar(self, slide, x, y, w, h, name, pct, status): ...
    def _draw_stat_block(self, slide, x, y, num, label, caption=None): ...

    # 通用辅助
    def _add_section_tag(self, slide, x, y, text, color="accent_deep"): ...
    def _add_section_title(self, slide, x, y, w, main, accent=None): ...
    def _add_jump_row(self, slide, x, y, label, links): ...
    def _add_noise_overlay(self, slide): ...

    def save(self, path):
        """导出 .pptx"""
```

## 完整 EditorialDeck 实现

完整代码见 `assets/generate_pptx.py`(约 800 行 python-pptx 代码,封装好所有组件绘制)。本文件只展示 API。

## 验证 .pptx 输出

生成完后:

1. **用 PowerPoint 打开**(必须真实 PowerPoint,不是 LibreOffice/Keynote — 颜色/字体在不同 viewer 有偏差)
2. **检查字体是否生效**:菜单 File > Info > Embedded Fonts 应显示 Fraunces / Inter / JetBrains Mono
3. **配色检查**:View > Slide Master 看主题色板是否含 6 brand 色
4. **比对源 HTML**:同时打开 `血液科市场调研_v5_desktop.html` 和生成的 .pptx,Slide 1 / Slide 2 / Slide 3 看视觉一致度
5. **图表语法检查**:至少 3 类不同表达家族;独立 KPI 没被画成 proof bars;时间窗没被画成 bar;机制匹配没被画成 bar

如果某 slide 看起来"塑料化"或"不像源版本":

- 检查是否漏了噪声背景叠层(每页都要)
- 检查软阴影是否生效(shape outer shadow blur=24, distance=8)
- 检查圆角是否够大(卡片 12-14pt 圆角,小 chip 4-6pt)
- 检查衬线字体是否在标题用了 Fraunces(用了 Calibri 就降级了)

## 源页面参考

源 HTML:`C:\Users\qiyon\Desktop\血液科市场调研_v5_desktop.html`

每个 HTML section 在 EditorialDeck 中对应一个 `add_*_slide()` 方法,**section 内容数据保持一致 → 生成的 PPT 与 HTML 视觉同源**。
