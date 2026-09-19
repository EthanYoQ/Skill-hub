# Typography System

> 这套设计的辨识度有 50% 来自字体——**Fraunces 衬线 + Inter 无衬线 + JetBrains Mono 等宽**三件套。每种字体只在特定场景使用,不要混用。

## 三字族分工

| 字族 | 角色 | 用在 | 不用在 |
|------|------|------|--------|
| **Fraunces** (serif) | 标题、数字、引言 | h1/h2/h3、stat 大数字、`.gradient-text`、引用斜体、CTA 时间数字、product-card h4 | 正文、按钮、metadata、技术文字 |
| **Inter** (sans) | 正文默认 | body、p、subtitle、descriptions、按钮文字、card body | 大数字、引用、技术 ID |
| **JetBrains Mono** (mono) | 数据 / 代码 / 技术 metadata | PMID、phase ID、时间戳、文件名、URL、size 标签、tag/chip 内文字、stage-pct 概率值 | 普通正文 |

## 大小 scale(完整 token)

### Projection scale(HTML deck 默认)

HTML 横向全屏 deck 的默认目标是投影演讲,字号必须接近 `guizang-ppt-skill` 的屏幕尺度,但继续使用本 skill 的 warm editorial 配色和 Fraunces / Inter / JetBrains Mono 字体。

已验证参考值(1920x1080):guizang 常规页主标题约 98-106px,lead 约 33-36px,卡片标题约 28-32px。生成本 skill 的 HTML deck 时,除非明确是 evidence/table/appendix compact 页,不要低于这组尺度太多。

```css
/* ===== HERO 层 ===== */
.hero-title       { font-family: var(--font-serif); font-size: clamp(110px, 7.6vw, 146px); font-weight: 600; line-height: 1.0; letter-spacing: -1.2px; }
.hero-sub         { font-family: var(--font-serif); font-size: clamp(28px, 1.9vw, 40px); line-height: 1.42; }

/* ===== Section 级 ===== */
.section-title    { font-family: var(--font-serif); font-size: clamp(78px, 5.2vw, 106px); font-weight: 600; line-height: 1.08; letter-spacing: -1px; }
.section-subtitle { font-family: var(--font-serif); font-size: clamp(25px, 1.75vw, 36px); line-height: 1.45; max-width: 1160px; }

/* ===== 大数字(stat / count-up) ===== */
.stat .num        { font-family: var(--font-serif); font-size: clamp(68px, 6vw, 124px); font-weight: 600; letter-spacing: -1px; line-height: 1; font-variant-numeric: tabular-nums; }
.bar-meta .pct    { font-family: var(--font-serif); font-size: clamp(28px, 2.1vw, 44px); font-weight: 700; }

/* ===== 卡片级标题 ===== */
.product-card h4  { font-family: var(--font-serif); font-size: clamp(24px, 1.55vw, 32px); font-weight: 700; }
.funnel-wrap h3   { font-family: var(--font-serif); font-size: clamp(24px, 1.55vw, 32px); font-weight: 600; }
.wf-phase-name    { font-family: var(--font-serif); font-size: clamp(24px, 1.55vw, 32px); font-weight: 600; }

/* ===== 正文 / 描述 ===== */
.product-card .insight { font-family: var(--font-sans); font-size: clamp(17px, 1.05vw, 22px); line-height: 1.58; }
.limit-item p          { font-family: var(--font-sans); font-size: clamp(17px, 1.05vw, 22px); line-height: 1.65; }
.section-subtitle      { font-size: clamp(25px, 1.75vw, 36px); line-height: 1.45; }

/* ===== Eyebrow / Tag(全大写小字) ===== */
.section-tag      { font-family: var(--font-mono); font-size: clamp(11px, .78vw, 15px); letter-spacing: 2px; text-transform: uppercase; font-weight: 600; }
.hero-eyebrow     { font-family: var(--font-mono); font-size: clamp(11px, .78vw, 15px); letter-spacing: 2px; font-weight: 600; }
.why-eyebrow      { font-family: var(--font-mono); font-size: clamp(11px, .78vw, 15px); letter-spacing: 2px; text-transform: uppercase; font-weight: 700; }

/* ===== 技术 metadata(等宽) ===== */
.jump-btn         { font-family: var(--font-mono); font-size: clamp(12px, .78vw, 15px); font-weight: 600; }
.product-chip     { font-family: var(--font-mono); font-size: clamp(10px, .68vw, 13px); font-weight: 700; letter-spacing: .3px; }
.wf-phase-output  { font-family: var(--font-mono); font-size: clamp(12px, .78vw, 15px); }
.phase-pill .ph-id { font-family: var(--font-mono); font-size: clamp(10px, .68vw, 13px); letter-spacing: 2px; font-weight: 800; }
.tech-stack-row span { font-family: var(--font-mono); font-size: clamp(10px, .72vw, 14px); font-weight: 600; }

/* ===== 极小辅助文字 ===== */
.bar-cell .stage-pct { font-family: var(--font-mono); font-size: clamp(10px, .68vw, 13px); }
.subpage-card .sp-tag { font-family: var(--font-mono); font-size: clamp(10px, .68vw, 13px); }
.aux-card .ax-meta { font-family: var(--font-mono); font-size: clamp(10px, .68vw, 13px); }
```

## Compact mode(只给密集页)

只有下列页面可以进入 compact mode:证据引用列表、合规声明、dense matrix、需要完整保留原 HTML 内容的迁移页。compact mode 也不能回到网页报告尺度:

```css
.compact .section-title { font-size: clamp(46px, 3.8vw, 76px); }
.compact .section-subtitle,
.compact .subtitle      { font-size: clamp(18px, 1.25vw, 24px); }
.compact .card-title,
.compact h3,
.compact h4             { font-size: clamp(18px, 1.25vw, 24px); }
.compact .card-body,
.compact p,
.compact li             { font-size: clamp(15px, .95vw, 19px); }
```

不要用全局 scale transform 把整页缩到能塞下为止。内容超高时,优先拆页、删减重复视觉装饰,或把该页标记为 compact;不要让所有页面都继承 12-15px 正文字号。

## 字重使用规则

Fraunces 用 3 个字重(500/600/700),按场景:

- **500**:很少用,仅在 Fraunces 大字号下需要更轻盈感时
- **600**:**默认**——所有标题、subtitle、stat 数字都用 600
- **700**:强调标题(product-card h4、`.bar-meta .pct`、CTA `.cta-time`)、`.gradient-text` 默认 600 但你想让它更醒目可上 700

Inter 用 5 个字重(400/500/600/700/800),按场景:

- **400**:正文默认(其实通常不显式写,继承 body 即可)
- **500**:轻微强调(`caption`、`team-meta`、链接)
- **600**:**最常用强调**——subtitle 的 strong、按钮文字、tag、card 副标题、所有 letter-spacing 的全大写小字
- **700**:重点强调(eyebrow、stat label 、`.proof-bar .pb-status`)
- **800**:极致强调(phase-num 圆圈数字、wf-stat 数值)——用得很省

JetBrains Mono 用 3 个字重(400/500/700):

- **400**:`.bar-cell .stage-pct` 这种最小数据
- **500**:`.tech-stack-row` chip
- **700**:`.product-chip`、`.phase-pill .ph-id`、强调技术 metadata

## letter-spacing(字距)调整

衬线 Fraunces 在大字号时**收紧字距**(负值):

```css
.hero-title    { letter-spacing: -2px; }   /* 80px 大标题 */
.section-title { letter-spacing: -1.5px; } /* 58px h2 */
.team-names    { letter-spacing: -1px; }
.stat .num     { letter-spacing: -2px; }
.cta-time      { letter-spacing: -.5px; }
.invoice-info h4 { letter-spacing: -.3px; }
.limit-item h4 { letter-spacing: -.2px; }
```

**为什么**:大字号衬线天然字距偏宽,负 letter-spacing 让标题"紧凑而有力";小字号(< 18px)不要负值。

无衬线 Inter 在**全大写 + 小字号**时**放宽字距**(正值):

```css
.section-tag    { letter-spacing: 2px; }    /* eyebrow tag */
.hero-eyebrow   { letter-spacing: 2px; }
.why-eyebrow    { letter-spacing: 2.5px; }  /* 强调 */
.stat .label    { letter-spacing: .8px; }
.team-credit    { letter-spacing: 1px; }
.phase-pill .ph-id { letter-spacing: 2px; }
.wf-stat .l     { letter-spacing: 1.5px; }
.cta-tag        { letter-spacing: 1.5px; }
```

**为什么**:全大写小字距太挤,放宽字距让它呼吸——这是编辑设计的经典手法。

## line-height(行高)

| 场景 | line-height |
|------|------------|
| 大标题(40px+) | 1.0 - 1.08 |
| 小标题(17-22px) | 1.2 - 1.3 |
| 正文(13-17px) | 1.55 - 1.7 |
| body 默认 | 1.6 |
| stat 数字 | 1 |

**原则**:字号越大行高越紧,字号越小行高越松——这是为了视觉密度均衡。

## tabular-nums(数字等宽)

凡是涉及数字对齐的地方,加 `font-variant-numeric: tabular-nums`:

- `.stat .num`(stat-bar 大数字)
- 任何用 count-up 的数字
- 表格里的数字列

body 默认已经在 `font-feature-settings: "cv11", "ss01", "tnum"` 里全局启用了 tnum。但某些 Fraunces 场景需要显式声明。

## 字体引入(必须放 `<head>`,不可懒加载)

```html
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500;9..144,600;9..144,700&family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;700&display=swap" rel="stylesheet">
```

**关键参数**:
- `Fraunces:opsz,wght@9..144,500;9..144,600;9..144,700`:
  - `opsz` 是光学尺寸轴(9-144),让浏览器在不同字号自动选最合适的字形——**这是 Fraunces 高级感的来源**,不要简化为 `Fraunces:wght@500`
  - `9..144` 是支持 9px 到 144px 的全字号范围
- `display=swap`:字体加载中先用 fallback,加载完替换——避免 FOIT(白屏)

## 中文回退栈

中文字符不在 Fraunces/Inter 里,会回退到系统字体。栈顺序:

```css
--font-sans: 'Inter', -apple-system, BlinkMacSystemFont, 'PingFang SC', 'Noto Sans SC', 'Microsoft YaHei', sans-serif;
--font-serif: 'Fraunces', 'Source Han Serif SC', Georgia, serif;
```

- macOS:中文走 PingFang SC,英文走 Inter/Fraunces
- Windows:中文走 Microsoft YaHei(微软雅黑) / Source Han Serif SC(思源宋体),英文走 Inter/Fraunces
- 这种 mix 是有意的——英文衬线 + 中文宋体的对照,产生编辑设计的对话感

如果想要中文也用 Fraunces 风格的衬线,加载思源宋体或方正书宋:

```css
--font-serif: 'Fraunces', 'Source Han Serif SC', 'Songti SC', '方正书宋', serif;
```

## 反模式(禁止使用)

❌ 全部正文用 Fraunces——衬线长篇阅读疲劳
❌ 用 Playfair Display / Cormorant 替换 Fraunces——失去光学尺寸特性
❌ 用 SF Pro / system-ui 替换 Inter——Inter 的字符特征(替代 a/g、tnum)是这套设计的细节质感
❌ 用 Courier / Monaco 替换 JetBrains Mono——JetBrains Mono 字怀更宽,在 8px chip 里仍清晰
❌ Fraunces 字重用到 800——会变得"塑料化",这套设计的衬线最重 700
❌ 全大写正文不加 letter-spacing——小字全大写挤成一团
❌ 大标题行高超过 1.2——大字号行高紧凑才有标题感

## 字体加载性能

- `<link rel="preconnect">` 提前建立 fonts.googleapis.com 连接
- 三字族总下载量 ~150KB(woff2),首屏可接受
- 如果做离线/桌面交付,把字体下载本地放 `assets/fonts/` 用 `@font-face` 引入,不依赖 Google Fonts 联网
