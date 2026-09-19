# Design Tokens

颜色值不是设计 DNA。先从 `style-index.json` 选择一个 profile，再把 profile 的角色色映射到组件兼容别名。只有用户明确锁定原始 Pfizer look 时，才使用下方 legacy block。

## 角色 token 合同（所有 profile 必须提供）

```css
:root {
  --canvas: #F7F6F2;
  --surface: #FFFFFF;
  --contrast-surface: #17243A;
  --ink: #152033;
  --muted: #566174;
  --primary: #2463A7;
  --secondary: #D06F52;
  --signal: #D6A53B;
  --positive: #397A62;
  --negative: #B94B55;

  /* Compatibility aliases for existing components. */
  --bg-0: var(--canvas);
  --bg-1: color-mix(in srgb, var(--canvas) 92%, var(--ink));
  --bg-2: color-mix(in srgb, var(--canvas) 84%, var(--ink));
  --bg-surface: var(--surface);
  --text-0: var(--ink);
  --text-1: color-mix(in srgb, var(--ink) 88%, var(--canvas));
  --text-2: var(--muted);
  --text-3: var(--muted);
  --accent: var(--primary);
  --brand-blue: var(--secondary);
  --brand-gold: var(--signal);
  --brand-green: var(--positive);
  --brand-red: var(--negative);
}
```

Do not hard-code profile RGB values inside components. Semantic status colors remain stable within one deck. Use the selected profile's typography metadata for display/body/data roles and provide system fallbacks.

## Legacy Pfizer profile block

```css
:root {
  /* ===== 米色底色系(温暖,不冷白) ===== */
  --bg-0: #FAF9F5;        /* 主底色 · 几乎所有 section 默认 */
  --bg-1: #F3EEE3;        /* 次底色 · 偶数 section / 强调区 */
  --bg-2: #EBE5D8;        /* 三档底色 · 内嵌卡片底 */
  --bg-surface: #FFFFFF;  /* 卡片白 · 提升层次感 */

  /* ===== 文本色(暖墨,不纯黑) ===== */
  --text-0: #141413;  /* 标题 · 最强对比 */
  --text-1: #2C2A26;  /* 正文 · 默认 */
  --text-2: #5B544A;  /* 次要文字 · 描述 / caption */
  --text-3: #625B4F;  /* 弱化文字 · meta / hint */

  /* ===== 主色:赭石红家族(Anthropic 主轴) ===== */
  --accent: #CC785C;       /* 主赭石 · CTA / 主链接 / 主流程 */
  --accent-hot: #E8A888;   /* 浅赭 · hover 高光 / 渐变端点 */
  --accent-deep: #A45946;  /* 深赭 · 强调正文 b / hover 文字 */
  --accent-wash: rgba(204,120,92,.08); /* 赭石淡洗 · 背景填充 */

  /* ===== 6 个品牌辅色(按语义分,不是凑色) ===== */
  --brand-blue:   #2E5C8A;  /* 信息 / 中性数据 / 第二条产品线 */
  --brand-purple: #6B4E8F;  /* 技术 / phase ID / metadata */
  --brand-gold:   #B8903C;  /* 经验性 / 局限提示 / 警示黄 */
  --brand-green:  #5C8D5C;  /* 通过状态 / 顶级证据 / 维持阶段 */
  --brand-red:    #C2594A;  /* 危险 / 突破事件 / 失败 */
  --brand-pink:   #C77A9A;  /* 罕见 / 辅助补色 */

  /* ===== 行业垂直主色(根据领域换) ===== */
  --hema-crimson: #8C2B3A;  /* 医疗/血液域;科技换 #1A3A6E,金融 #2D5A3A,教育 #4A2D5C */

  /* ===== 第三方品牌锁色(可选) ===== */
  --pfizer-blue: #0095D5;
  --pfizer-blue-deep: #00558C;

  /* ===== 边框系统(从软到硬 3 档) ===== */
  --border-soft:   #E3DCCC;  /* 默认卡片边 · 极轻 */
  --border:        #D0C8B5;  /* 标准边 · 按钮 / 输入 */
  --border-strong: #A69D88;  /* 强调边 · 选中态 */

  /* ===== 玻璃态(用于 nav / eyebrow) ===== */
  --glass-bg: rgba(255,255,255,.55);
  --glass-bd: rgba(20,20,19,.08);

  /* ===== 光晕 / 软阴影(分层叠加) ===== */
  --glow-accent: 0 0 40px rgba(204,120,92,.25);
  --glow-gold:   0 0 40px rgba(184,144,60,.22);
  --shadow-card:       0 1px 2px rgba(20,20,19,.04), 0 8px 24px rgba(20,20,19,.04);
  --shadow-card-hover: 0 2px 4px rgba(20,20,19,.06), 0 16px 40px rgba(204,120,92,.12);

  /* ===== 字体三件套 ===== */
  --font-sans: 'Inter', -apple-system, BlinkMacSystemFont, 'PingFang SC', 'Noto Sans SC', 'Microsoft YaHei', sans-serif;
  --font-serif: 'Fraunces', 'Source Han Serif SC', Georgia, serif;
  --font-mono: 'JetBrains Mono', Consolas, monospace;
}
```

## 字体引入(放到 `<head>`)

```html
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500;9..144,600;9..144,700&family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;700&display=swap" rel="stylesheet">
```

**原始 profile 的关键参数解释**:
- `Fraunces` 用 `opsz` 可变光学尺寸(9..144),让 60px 大标题和 14px 小标题都最优。其他 profile 按 `style-index.json` 选择自己的 display 字体。
- `Inter` 加载 5 个字重(400/500/600/700/800),覆盖正文到强调
- `JetBrains Mono` 用于数据/代码/PMID/技术 metadata,不要换成 Courier

## body 基础样式(温暖底 + 噪声 + 径向光晕)

```css
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

html { scroll-behavior: smooth; scroll-snap-type: y proximity; }

body {
  font-family: var(--font-sans);
  background:
    radial-gradient(1200px 600px at 85% 15%, rgba(204,120,92,0.08), transparent 55%),
    radial-gradient(900px 500px at 10% 80%, rgba(140,43,58,0.05), transparent 60%),
    var(--bg-0);
  color: var(--text-1);
  line-height: 1.6;
  overflow-x: hidden;
  font-feature-settings: "cv11", "ss01", "tnum";  /* Inter 替代字符 + tabular nums */
  -webkit-font-smoothing: antialiased;
}

/* 噪声纹理叠层；按 profile materiality 调整，不能压低可读性。 */
body::before {
  content: '';
  position: fixed;
  inset: 0;
  pointer-events: none;
  z-index: 0;
  opacity: .35;
  mix-blend-mode: multiply;
  background-image: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='180' height='180'><filter id='n'><feTurbulence type='fractalNoise' baseFrequency='0.85' numOctaves='2' stitchTiles='stitch'/><feColorMatrix values='0 0 0 0 0.08  0 0 0 0 0.07  0 0 0 0 0.05  0 0 0 0.06 0'/></filter><rect width='100%25' height='100%25' filter='url(%23n)'/></svg>");
}
```

**为什么这样写**:
- 两个 `radial-gradient` 在右上角和左下角制造柔光,让屏幕"有光线",不是平板
- `mix-blend-mode: multiply` 让噪声跟底色相乘,纹理不会显得突兀
- `feTurbulence` 的 `baseFrequency='0.85'` 是细密颗粒,粗了像电视雪花,细了看不出来——0.85 是甜点
- `font-feature-settings` 开启 Inter 的替代字符 + tabular numerals(数字等宽),让 stat-bar 数字对齐

## 字号 scale(clamp 响应式)

```css
.section-title  { font-size: clamp(34px, 4.5vw, 58px); }   /* h2 大标题 */
.hero-title     { font-size: clamp(40px, 5.5vw, 80px); }   /* hero h1 */
.hero-sub       { font-size: clamp(15px, 1.3vw, 19px); }   /* hero 副标题 */
.team-names     { font-size: clamp(26px, 3.6vw, 44px); }   /* CTA 团队名 */
.stat .num      { font-size: clamp(36px, 4vw, 64px); }     /* 大数字 */

/* 固定字号 */
.section-subtitle { font-size: 17px; }
.product-card h4  { font-size: 17px; }
.bar-cell .stage-icon { font-size: 11px; }
.product-chip { font-size: 8px; }
```

**clamp 三参数语义**:`clamp(min, ideal-vw, max)` — 移动端最小、桌面端最大、中间按视口宽度自动插值。不要换成固定 px 或 rem,这套设计的优雅在响应式自适应。

## 间距系统(隐式,不用 spacing token)

这套设计没有用 `--space-1/2/3` 之类的间距 token,而是直接用具体 px:

- 卡片内边距:18-26px(小卡)/ 28-40px(大卡)
- section 上下:`100px 48px 60px` 桌面 / `90px 18px 50px` 移动
- 组件间距:`margin-top: 22px / 28px / 36px`(按层级递增)
- 元素间距:`gap: 4-6px`(密集网格) / `12-18px`(中等) / `24-32px`(舒朗)

**原则**:**不要全部统一**——每个组件按它自己的视觉密度调间距,反而比统一更舒服。

## 圆角 scale

| 用法 | 圆角 |
|------|------|
| 小 chip / tag / badge | 4-6px |
| 按钮 / 输入 | 8-10px |
| 卡片 | 12-14px |
| 大容器 / 报告框 | 16-20px |
| 胶囊形(eyebrow / phase-count) | 100px |

## 应用到不同领域

不要只替换一个行业色。用 purpose、audience、formality、density、mood 和 scheme 从 `style-index.json` 选择 profile；再保持该 profile 的 palette、type roles、materiality、composition grammar 和 cadence。用户锁定原始 Pfizer look 时才使用米色 + 赭石 legacy profile。
