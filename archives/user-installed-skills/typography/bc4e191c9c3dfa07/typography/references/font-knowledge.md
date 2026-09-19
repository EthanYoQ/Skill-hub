# Font Knowledge Reference

Comprehensive font selection, pairing, personality, and loading guidance for the Typography skill. Read this when making font choices, advising on typeface selection, or auditing font implementation.

---

## Table of Contents

1. [Font Personality Taxonomy](#1-font-personality-taxonomy)
2. [Recommended Fonts by Category](#2-recommended-fonts-by-category)
3. [Font Pairing](#3-font-pairing)
4. [Font Loading Strategy](#4-font-loading-strategy)
5. [Font Licensing](#5-font-licensing)
6. [Anti-Patterns](#6-anti-patterns)
7. [Quick Picks](#7-quick-picks)

---

## 1. Font Personality Taxonomy

Font choice is a voice decision, not a decoration decision. The typeface sets the register of the communication before a single word is read.

### Sans-Serif Categories

| Category | Character | Signals | Examples |
|----------|-----------|---------|----------|
| **Humanist sans** | Warm, organic, calligraphic roots. Open apertures, varied stroke widths. | Approachable, readable, "we're human beings talking to you" | Frutiger, Source Sans, Lato, Open Sans |
| **Geometric sans** | Cold, precise, constructed from circles and lines. Monolinear strokes. | Modern, designed, minimalist, "we thought about this" | Futura, Avenir, Montserrat, Poppins, DM Sans, Plus Jakarta Sans |
| **Neo-grotesque sans** | Neutral, invisible. Minimal stroke contrast, tight apertures. | Professional neutrality, "the container should not distract" | Helvetica, Arial, Roboto, Inter, SF Pro |
| **Grotesque sans** | Predecessors to neo-grotesques. Slightly irregular, more character. | Editorial credibility, journalistic, "serious but not corporate" | Franklin Gothic, News Gothic, IBM Plex Sans |

### Serif Categories

| Category | Character | Signals | Examples |
|----------|-----------|---------|----------|
| **Old-style (Humanist)** | Renaissance forms. Diagonal stress, bracketed serifs, low contrast. | Tradition, scholarship, literary credibility | Garamond, Palatino, EB Garamond |
| **Transitional** | Enlightenment era. More vertical stress, higher contrast, sharper serifs. | Authority, establishment, refined but not flashy | Baskerville, Georgia, Charter, Libre Baskerville |
| **Modern / Didone** | Extreme thick-thin contrast. Unbracketed hairline serifs. | Luxury, fashion, editorial drama. Almost never for body text on screen. | Bodoni, Didot, Playfair Display |
| **Slab serif** | Thick block-like serifs, often monolinear. | Sturdy, confident, industrial | Rockwell, Clarendon, Roboto Slab, Zilla Slab |

### Extended Personality Map

| Category | Archetype | What it says |
|----------|-----------|-------------|
| Humanist sans | The teacher | "Let me explain this clearly" |
| Geometric sans | The architect | "I designed this from first principles" |
| Neo-grotesque sans | The consultant | "I'm here to deliver information, not personality" |
| Grotesque sans | The journalist | "I report the facts with credibility" |
| Old-style serif | The professor | "I've read the primary sources" |
| Transitional serif | The lawyer | "This is authoritative and precise" |
| Modern/Didone serif | The fashion editor | "Aesthetics are substance, not decoration" |
| Slab serif | The engineer | "I built this to last" |
| Monospace | The programmer | "Here is the raw material; parse it yourself" |
| Display/script | The performer | "Look at me" (use sparingly) |

---

## 2. Recommended Fonts by Category

### Sans-Serif for UI

**Inter** — Rasmus Andersson. OFL / Google Fonts. Variable font.
Designed specifically for computer screens. Tall x-height, tabular numbers, extensive OpenType features. The de facto modern web UI font. Includes "Inter Display" optical size for larger text. Best for: general-purpose UI, dashboards, data-heavy interfaces.

**Source Sans 3** — Paul D. Hunt / Adobe. OFL / Google Fonts. Variable font.
Humanist sans, clean and warm. Part of Adobe's Source superfamily (pairs perfectly with Source Serif and Source Code Pro). Best for: interfaces needing a softer feel than geometric options. Government, institutional.

**DM Sans** — Colophon Foundry (for Google). OFL / Google Fonts. Variable font.
Low-contrast geometric sans with slightly rounded terminals. Modern but neutral. Best for: marketing sites, SaaS products, startup landing pages.

**Plus Jakarta Sans** — Tokotype. OFL / Google Fonts. Variable font.
Geometric sans with friendly, rounded quality. Wider letterforms. Emerged as a popular Inter alternative in 2023-2025. Best for: modern SaaS, fintech, approachable dashboards.

**IBM Plex Sans** — Mike Abbink / Bold Monday. OFL / Google Fonts. Variable font.
Grotesque sans with subtle humanist touches. Distinctive slotted counters. Part of the Plex superfamily. Best for: enterprise/corporate interfaces, design systems needing gravitas.

### Serif for Reading

**Literata** — TypeTogether (for Google Play Books). OFL / Google Fonts. Variable font with optical size axis.
Designed explicitly for long-form screen reading. The optical size axis adjusts proportions for body vs display automatically. Best for: e-readers, editorial sites, sustained reading. The top pick for screen reading.

**Charter** — Matthew Carter / Bitstream (1987). Permissive Bitstream license. Not on Google Fonts; widely available as system font, self-hostable.
Designed for low-resolution output. Sturdy, low-contrast, survives poor rendering. Compact proportions. The typographer's recommendation for "if you only pick one serif." Best for: long-form reading, text-heavy sites.

**Source Serif 4** — Frank Griesshammer / Adobe. OFL / Google Fonts. Variable font with optical size axis.
Transitional serif, clean modern proportions. Pairs seamlessly with Source Sans and Source Code. Best for: editorial content, documentation, mixed serif/sans interfaces.

**Lora** — Cyreal. OFL / Google Fonts. Variable font.
Contemporary serif with moderate contrast, slightly calligraphic curves. True italic companion. Best for: blogs, editorial sites, body text needing more personality than a transitional.

**Newsreader** — Production Type (for Google). OFL / Google Fonts. Variable font with optical size axis.
High-contrast newspaper serif. Sharp, precise, editorial. Best for: news sites, publications, magazine-style layouts.

**Merriweather** — Sorkin Type. OFL / Google Fonts.
Large x-height, slightly condensed, sturdy serifs. Optimized for 16px body on screen. The long-standing workhorse. Best for: content-heavy sites, WordPress blogs.

### Monospace for Code

**JetBrains Mono** — JetBrains. OFL / Google Fonts. Variable font.
138 code-specific ligatures, increased x-height, wider letterforms. Arguably the default code font for 2024-2025. Best for: code editors, code blocks, terminal.

**Fira Code** — Nikita Prokopov. OFL / Google Fonts. Variable font.
Pioneered code ligatures. Comprehensive ligature set. Slightly narrower than JetBrains Mono. Based on Mozilla's Fira. Best for: code blocks, developer documentation.

**Source Code Pro** — Paul D. Hunt / Adobe. OFL / Google Fonts. Variable font.
Clean, no ligatures (some developers prefer this). Excellent character disambiguation. Part of Source superfamily. Best for: code display where ligatures are unwanted.

### Display / Heading Fonts

**Fraunces** — Undercase Type. OFL / Google Fonts. Variable font with weight, optical size, "wonk", and softness axes.
Old-style soft serif with adjustable quirkiness via the "wonk" axis. Extremely expressive range from a single file. Best for: hero text, editorial headers, branding with personality.

**Playfair Display** — Claus Eggers Sorensen. OFL / Google Fonts. Variable font.
High-contrast transitional serif. Very thin hairlines. Pure display face — not for body text. Best for: fashion, luxury, editorial headers.

**Sora** — Jonathan Barnbrook. OFL / Google Fonts. Variable font.
Geometric sans with futuristic quality. Wide weight range. Best for: tech headers, modern branding.

**Space Grotesk** — Florian Karsten. OFL / Google Fonts. Variable font.
Proportional counterpart to Space Mono. Angular terminals, retro-futuristic. Best for: tech brands, developer marketing.

### Japanese Web Fonts

**Noto Sans JP / Noto Serif JP** — Google/Adobe. OFL / Google Fonts. Variable (Sans).
The baseline. Comprehensive coverage, clean, neutral. Google Fonts serves with unicode-range subsetting. The safe default.

**M PLUS 1 / M PLUS Rounded 1c** — Coji Morishita. OFL / Google Fonts. Variable (M PLUS 1).
Clean modern gothic. The rounded variant is popular for friendly consumer apps. One of few Japanese families with a rounded variant on Google Fonts.

**Zen family** (Zen Kaku Gothic, Zen Maru Gothic, Zen Old Mincho, Zen Antique) — Yoshimichi Ohira. OFL / Google Fonts.
Stylistic range rare in free Japanese fonts. Zen Old Mincho is a quality free alternative to commercial mincho faces.

**Shippori Mincho** — FONTDASU. OFL / Google Fonts.
Elegant high-contrast mincho. More refined than Noto Serif JP. Multiple weights including heavy display weights. Best for: Japanese editorial, literary content.

**Commercial Japanese options:**
- **MORISAWA TypeSquare** and **FONTPLUS**: subscription services for premium Japanese typefaces (Ryumin, Shin Go, etc.). The professional standard.
- **Adobe Fonts**: includes Kozuka Gothic/Mincho and Source Han variants via Creative Cloud.

---

## 3. Font Pairing

### Core Principle

Contrast in structure, harmony in proportion. Pair fonts that differ in category (serif + sans) but share structural DNA (similar x-height, proportions, aperture).

### Structural Compatibility Markers

1. **x-height** — the single most important pairing metric. Two fonts with similar x-heights feel cohesive even if their styles differ.
2. **Proportions** — wide vs narrow letterforms; circular vs oval 'o'. Match these.
3. **Stroke contrast** — the thick/thin ratio. Pairing extreme contrast with monolinear creates tension.
4. **Aperture** — open (Frutiger) pairs with open; closed (Helvetica) pairs with closed.

### The Two-Font Rule

Two typefaces is almost always enough. One for headings, one for body. Vary weight and size for hierarchy.

- **Two is right for:** marketing sites, blogs, most web apps, documentation.
- **Three works when:** you need a distinct register for code, data, or captions.
- **More than three:** almost never on the web.

The real rule: you need as many typefaces as you have distinct communicative registers, and no more.

### Reliable Pairings

#### Superfamily pairings (safest — designed to work together)
- **Source Sans 3 + Source Serif 4 + Source Code Pro** — Adobe's superfamily
- **IBM Plex Sans + IBM Plex Serif + IBM Plex Mono** — more distinctive than Source
- **Noto Sans + Noto Serif + Noto Sans Mono** — universal, every script including CJK

#### Sans UI + Serif body (editorial pattern)
- **Inter + Literata** — the modern default. Inter for chrome, Literata for articles.
- **Inter + Charter** — precision UI meets sturdy reading face.
- **DM Sans + Lora** — warmer pairing. Geometric headings with calligraphic body.
- **Plus Jakarta Sans + Newsreader** — contemporary geometric + editorial serif.

#### Sans heading + sans body
- **Sora or Space Grotesk (headings) + Inter or Source Sans (body)** — distinctive display + neutral workhorse.

#### Display serif + sans body
- **Playfair Display + Source Sans 3** — classic editorial. High-contrast display + humanist sans.
- **Fraunces + Inter or DM Sans** — expressive serif + neutral sans. Wonk axis controls personality.

#### Monospace in context
- **JetBrains Mono + Inter** — the standard for developer tools and documentation.

### Category Pairing Compatibility

| Heading category | Good body pairings |
|---|---|
| Humanist sans | Old-style serif, transitional serif |
| Geometric sans | Modern/Didone serif, neo-grotesque sans (if different family) |
| Neo-grotesque sans | Transitional serif (the "serious publication" combo) |
| Slab serif | Humanist sans |
| Modern/Didone serif | Geometric sans |
| Display/script | Almost any neutral body font (keep display to headlines only) |

---

## 4. Font Loading Strategy

### Defaults for 2025

1. **Self-host fonts.** Cache partitioning (Chrome 86+, 2020) killed the CDN advantage. Self-hosting eliminates a third-party connection (100-300ms saved), gives full control, and avoids GDPR issues with Google Fonts CDN.

2. **woff2 only.** Browser support >97%. Drop woff, ttf, eot, svg.

3. **`font-display: optional` as default.** The font is used if already cached; otherwise the system font renders and the web font is cached for the next navigation. Eliminates FOUT and FOIT. Use `swap` only for icon fonts or brand-critical display text.

4. **Preload at most 1-2 critical font files**, and only with `swap` or `fallback`. With `optional`, skip preloading — the whole point is to not block on the font.

5. **Variable fonts when using 2+ weights.** Breakeven is ~2 weights. At 3+ weights, variable is always smaller. Example: Inter static Regular + Bold + Medium = ~54KB. Inter variable = ~32KB for all weights.

6. **Subset to characters actually used.** Tools: `glyphhanger` (crawls your site), `pyftsubset`. Google Fonts does this automatically via `unicode-range`.

7. **Fallback font metric overrides** when using `swap` or `fallback`:
```css
@font-face {
  font-family: 'Adjusted Arial';
  src: local('Arial');
  size-adjust: 105%;
  ascent-override: 90%;
  descent-override: 22%;
  line-gap-override: 0%;
}
```
Tools to calculate values: `fontaine` (npm), Next.js `@next/font`, Malte Ubl's Fallback Font Generator.

8. **Cache headers:** `Cache-Control: max-age=31536000, immutable` on self-hosted font files.

### Font Performance Budget

| Per-file | Assessment |
|----------|-----------|
| < 15 KB woff2 | Excellent |
| 15-30 KB | Normal for full Latin |
| 30-50 KB | Investigate subsetting or variable consolidation |
| 50+ KB | Actively causing problems on slow connections |

| Per-page total | Target |
|----------------|--------|
| < 50 KB | High-performance / mobile-first |
| < 100 KB | Standard target (Google recommendation) |
| > 200 KB | Too many fonts or not subsetting |

A typical well-optimized site uses 2-4 font files.

### How to Self-Host Google Fonts

Use `google-webfonts-helper` (web tool), `fontsource` (npm packages), or download woff2 files directly. Set long cache headers.

```css
@font-face {
  font-family: 'Inter';
  src: url('/fonts/inter-variable.woff2') format('woff2');
  font-weight: 100 900;
  font-display: optional;
}
```

---

## 5. Font Licensing

### Google Fonts (SIL Open Font License)
- **Cost:** Free.
- **Rights:** Use, modify, redistribute freely. Cannot sell as standalone font.
- **Catalog:** ~1,500+ families. Top 20 are good to excellent; long tail includes amateur work. Curate carefully.
- **When to use:** any budget-constrained project; open-source projects; when client needs to own fonts outright.

### Adobe Fonts
- **Cost:** Included with Creative Cloud (~$55/month all apps).
- **Rights:** Tied to active subscription. Fonts stop working if subscription lapses.
- **Catalog:** ~25,000+ families from professional foundries.
- **When to use:** when you already pay for CC; agency work.
- **Caveat:** fonts are rented, not owned. Matters for client handoffs.

### Commercial Foundries

| Foundry | Known for | Aesthetic |
|---------|-----------|-----------|
| **Klim** (NZ) | Calibre, Untitled Sans, Tiempos | Clean, considered, "if you know, you know" |
| **Commercial Type** (NYC) | Graphik, Atlas Grotesk, Lyon | Editorial/fashion standard |
| **Grilli Type** (CH) | GT America, GT Walsheim, GT Sectra | Swiss precision with personality |
| **Hoefler&Co** (NYC) | Gotham, Mercury, Sentinel | American editorial and political branding |
| **Lineto** (CH) | Akkurat, Circular | Minimalist tech aesthetic |
| **Colophon** (London) | Apercu, Reader | Distinctive, slightly quirky editorial |
| **Dinamo** (CH/DE) | ABC Diatype, ABC Favorit | "Cool design studio" fonts |

**When to pay:** when brand identity demands a specific voice free fonts can't provide; exclusive or semi-exclusive use; when typographic quality is a competitive differentiator.

### System Fonts by Platform

| Platform | System sans | System serif | System mono |
|----------|------------|-------------|-------------|
| macOS / iOS | SF Pro | New York | SF Mono, Menlo |
| Windows | Segoe UI | Cambria | Consolas |
| Android | Roboto | Noto Serif | Droid Sans Mono |
| Linux | varies (DejaVu, Noto, Liberation) | varies | varies |

**When system fonts are right:** performance-critical apps, native-feeling UIs, internal tools, admin panels. Zero loading latency.

**When system fonts are wrong:** brand-driven marketing, editorial sites, any project where "looking like every other app on this OS" is a problem.

---

## 6. Anti-Patterns

### Generic / Lazy Font Choices

1. **Montserrat + Roboto for everything.** Sorting Google Fonts by popularity and picking the top two is not a font strategy.
2. **Playfair Display + Open Sans on every project.** Fresh in 2015. A cliche by 2020.
3. **Using a display face for body text.** Lobster, Pacifico, Abril Fatface at 16px in paragraphs. Display faces are for large sizes only.
4. **Too many weights loaded.** Loading 6 weights when you use 2. Performance cost with no typographic benefit.
5. **Faux italic.** Using a font with no true italic and relying on browser slanting. Looks cheap.
6. **Mixing fonts from the same category.** Two geometric sans together (Futura + Poppins) creates a "close but wrong" feeling — looks like a mistake, not a choice.
7. **Platform default presented as intentional.** System-ui or browser default serif is fine IF deliberate. It's an anti-pattern when accidental.

### "AI Generated This" Tells

- Over-polished generic combinations — perfectly formatted but typographically anonymous.
- Inconsistent typographic voice — mixing registers within a piece in a way that suggests no single aesthetic was in charge.
- Perfect adherence to "best practices" with zero personality — correct hierarchy, correct spacing, but nothing that suggests a specific human made a specific choice.

The antidote: make choices that reflect a specific opinion. Use a font because you have a reason, not because it was the first result.

---

## 7. Quick Picks

### By Use Case

| Use case | Top pick | Runner-up | Budget option |
|----------|----------|-----------|---------------|
| General web UI | Inter | Source Sans 3 | System font stack |
| Long-form reading | Literata | Charter | Georgia |
| Code blocks | JetBrains Mono | Fira Code | Source Code Pro |
| Hero / display (serif) | Fraunces | Playfair Display | — |
| Hero / display (sans) | Space Grotesk | Sora | — |
| Japanese sans | Noto Sans JP | M PLUS 1 | System Gothic stack |
| Japanese serif | Shippori Mincho | Zen Old Mincho | Noto Serif JP |
| "Just give me a system" | Source superfamily | IBM Plex superfamily | System fonts |

### By Project Type

| Project type | Recommended approach |
|---|---|
| SaaS / dashboard | Inter or Source Sans. System monospace for data. `optional` loading. |
| Editorial / blog | Literata or Charter body + Inter UI. `swap` for body font. |
| Marketing / landing | Plus Jakarta Sans or DM Sans + display heading. 2 fonts max. |
| Developer docs | Inter + JetBrains Mono. |
| E-commerce | Source Sans (neutral) or IBM Plex (authoritative). Avoid personality. |
| Japanese-primary | Noto Sans JP (UI) + Shippori Mincho (reading). Always subset. |
| Portfolio / creative | Commercial foundry font or distinctive Google Fonts option (Fraunces, Space Grotesk). This is where personality matters most. |

### Font Selection Decision Tree

1. **Do you need Japanese support?** → Start with Noto Sans/Serif JP as baseline. Add Latin font that pairs well at a similar x-height.
2. **Is this a reading surface?** → Use a serif with an optical size axis (Literata, Source Serif 4, Newsreader). Pair with a neutral sans for UI chrome.
3. **Is this a data/UI surface?** → Inter, Source Sans, or IBM Plex Sans. One family, multiple weights. Skip the serif.
4. **Is this brand/marketing?** → Pick one distinctive font for display/headings, one neutral font for body. Two fonts maximum.
5. **Is this developer-facing?** → Inter for UI, JetBrains Mono for code. Done.
6. **Is performance the top priority?** → System font stack. Zero loading cost.
7. **Unsure?** → Source superfamily (Sans + Serif + Code). It covers every register and the fonts were designed to work together.
