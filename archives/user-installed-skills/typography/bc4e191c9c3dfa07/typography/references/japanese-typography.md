# Typography Guidelines — Japanese Addendum
## Supplement to the main Typography Guidelines doc

---

## Foreword

Japanese typography does not bend to Latin rules. Many values in the main document require either replacement or significant adjustment when applied to Japanese text. Some rules flip entirely. This addendum is organized to mirror the main doc's structure so the two can be read in parallel.

The authoritative reference for Japanese typographic rules is **JIS X 4051** ("Formatting rules for Japanese documents"), codified for the web by the W3C's **Requirements for Japanese Text Layout (JLReq)**, produced by the W3C Japanese Layout Task Force. Where this document refers to JIS or JLReq, those are the primary sources.

---

## 1. The Writing System: What Makes It Different

Japanese uses three scripts simultaneously, often within the same sentence:

| Script | Characters | Purpose |
|---|---|---|
| 漢字 Kanji | ~2,000–3,000 in common use | Nouns, verb roots, concepts |
| ひらがな Hiragana | 46 base characters | Grammar particles, native words, inflections |
| カタカナ Katakana | 46 base characters | Foreign loanwords, emphasis, onomatopoeia |

Plus rōmaji (Latin script) and Arabic numerals, which frequently appear inline.

**Critical implication:** Every design decision that assumes a fixed character set, a proportional alphabet, word spaces, or uppercase/lowercase distinctions is incompatible with Japanese text by default.

---

## 2. Line Length (Characters Per Line)

**Target: 30–40 CPL for body text. WCAG hard limit: 40 CPL.**

This is approximately half the Latin target.

<br>

**Why the difference is so large:**

Japanese characters are square, full-width, and information-dense. A single kanji can carry the semantic weight of an English word or phrase. The eye's return sweep after a line is proportionally more cognitively demanding because each character requires more processing. The standard print convention in Japan reflects this: novels and newspapers typically run 35–45 characters per line in horizontal setting.

Sources:
- WCAG 1.4.8 explicitly specifies 40 CPL maximum for CJK languages
- W3C JLReq: body text in print uses the kihon-hanmen (基本版面) grid, where line length is specified as a multiple of the character size
- AQ Works (Tokyo/Paris design studio): "At this size 50 characters is too long, 10 is too short, but 30 is just right" (for standard body sizes)
- Medium article guidance: 40–55 characters for a sentence; paragraphs should not exceed 150 characters

**Practical range by context:**

| Context | CPL |
|---|---|
| Article / reading body text | 30–40 |
| Shorter columns, captions, multi-column | 20–30 |
| Long-form single column | up to 45 |
| Mobile portrait | natural (often 20–28) |
| WCAG hard maximum | 40 |

**CSS:**
```css
:lang(ja) .article-body {
  max-width: min(90vw, 38em);
  /* 38em ≈ 38 full-width characters for most Japanese fonts */
}
```

Note: the `ch` unit is unreliable for Japanese because it measures the width of `0` (a Latin/ASCII character), not a full-width CJK character. Use `em` instead — one `em` equals one full-width character in most Japanese fonts.

---

## 3. Line Height

**Target: 1.65–1.75 for body text. Minimum: 1.5.**

This is substantially higher than the Latin equivalent (1.5 at 65 CPL).

**Why:**
Japanese kanji are dense, high-stroke-count characters occupying a full square em-box. Without generous leading, lines appear to bleed into each other — the eye cannot cleanly distinguish the vertical channel between lines and loses its place during the return sweep. The square, evenly-massed profile of kanji means there are no descenders or ascenders to create natural visual separation between lines, as Latin script has.

Sources:
- Typotheque (CJK typesetting principles): leading of ~1.7 recommended for CJK, vs. 1.2 default
- CJK Typesetting 2025 (Asian Absolute): "around 170% of font size is recommended to avoid cramped appearance"
- LinkedIn guide (Hayataki): "line-height should be bigger than 1.2em; the average height is 1.5em"
- Medium (Pavel Laptev): "use 150% line height or even more"
- Xoxzo blog: "they need more space between lines to reduce rereading and damage on eye movement"

**Values by context:**

| Context | Line-height |
|---|---|
| Body text (30–40 CPL) | 1.65–1.75 |
| Captions, short text | 1.5 |
| Headings | 1.2–1.3 |
| Mixed Japanese/Latin body | 1.65 (use Japanese value; never compromise Japanese for Latin) |

**CSS:**
```css
:lang(ja) {
  line-height: 1.7;
}

:lang(ja) h1,
:lang(ja) h2,
:lang(ja) h3 {
  line-height: 1.25;
}
```

---

## 4. Font Size

**Target: same as Latin baseline (16px minimum), but Japanese may appear visually larger.**

**The size perception problem:**

Japanese characters have no lowercase — all characters are sized approximately like Latin capital letters. At the same CSS `font-size`, Japanese text appears approximately 10–15% larger than Latin text visually, due to the larger perceived cap-height and the full square em-box. This creates layout tension in mixed-language interfaces.

Sources:
- AQ Works: "In this image you can see Japanese (Hiragino Mincho Pro) looks too big next to English (Times New Roman) of the same font size"
- Xoxzo blog: "by decreasing the type size by 10–15% for Japanese texts, you can balance them with the Latin"

**Recommended approach for mixed-language interfaces:**

Option A — use CSS to target Japanese content specifically:
```css
:lang(ja) {
  font-size: 0.9em; /* Reduces Japanese relative to parent Latin size */
}
```

Option B — design around Japanese as the primary scale, and let Latin inherit it. This is preferable when Japanese is the dominant language of the interface.

For pure Japanese pages, standard body sizes apply:

| Context | Size |
|---|---|
| Minimum body text | 12px (lower than Latin 16px minimum is permissible for Japanese in dense UI contexts, per JLReq) |
| Standard body text | 14–16px |
| Comfortable reading | 16–18px |
| Older audience target | 16px minimum recommended |

---

## 5. Letter Spacing (字間 Jikan)

**Target: 0.05em–0.1em for body text. 0 for headings.**

Latin body text should never have letter-spacing added (see main doc, rule 6). Japanese is different. Because kanji are complex, densely-stroked characters sharing similar structural patterns, a small amount of additional spacing reduces visual crowding and aids character discrimination.

Sources:
- Hayataki: "set letter-spacing at 0.1em or 0.2em to ensure legibility"
- Lapteev: "you could set letter-spacing at 0.05em or 0.15em"
- Minimum guide: 0.05em for body paragraphs

**Values:**

| Context | Letter-spacing |
|---|---|
| Body text | 0.05em |
| Dense UI, small sizes | 0.05em–0.1em |
| Headings | 0 (or slightly negative: –0.02em for large display headings) |
| Stylistic display text (slogans, etc.) | 0.1em–0.2em (deliberately spaced for elegance) |

**CSS:**
```css
:lang(ja) p,
:lang(ja) li,
:lang(ja) td {
  letter-spacing: 0.05em;
}

:lang(ja) h1,
:lang(ja) h2 {
  letter-spacing: 0;
}
```

---

## 6. Text Alignment: Justified is Standard

**Use `text-align: justify` for Japanese body text.** This is the opposite of the Latin rule.

In the main document, justified text is on the "never do" list for Latin. For Japanese, it is the typographic default — in print and on the web.

**Why justification works for Japanese but not Latin:**

Latin justification creates visual "rivers" of whitespace because word spacing is variable and words are different lengths. Japanese has no word spaces (the language uses no spaces to separate words) and all characters are the same width (full-width em-box). Justification therefore adjusts glyph-level spacing uniformly, producing clean rectangular text blocks without rivers. This is aesthetically and functionally correct.

**CSS:**
```css
:lang(ja) p {
  text-align: justify;
}
```

Note: In some short-column or multi-column contexts, a line with few characters (particularly a final line) can look strangely stretched. Use `text-align-last: left` to handle the last line of a paragraph.

```css
:lang(ja) p {
  text-align: justify;
  text-align-last: left;
}
```

---

## 7. Kinsoku Shori (禁則処理) — Line Break Rules

Kinsoku Shori ("prohibition rules") are JIS X 4051-mandated constraints on which characters are permitted at the start or end of a line. This is the Japanese equivalent of widows/orphans handling in Latin, but more extensive and more strictly defined.

**Characters that cannot start a line:**
```
。、！？）」』】〕〗…‥
（small kana: っゃゅょぁぃぅぇぉァィゥェォッャュョ）
```

In plain terms: closing punctuation (periods, commas, closing brackets, question marks) must never begin a line. Small kana (the small forms like っ used for glottal stops) must not begin a line.

**Characters that cannot end a line:**
```
「『【〔（
```

Opening brackets and quotation marks must not end a line.

**CSS implementation:**
```css
:lang(ja) {
  line-break: strict;         /* Enforces JIS X 4051 kinsoku rules */
  word-break: keep-all;       /* Do not break mid-word (used with line-break) */
  overflow-wrap: break-word;  /* Prevent layout overflow on long strings/URLs */
}
```

**Warning:** `word-break: break-all` is catastrophic for Japanese — it forces breaks at arbitrary character positions, disregarding all kinsoku rules. Never use it on Japanese text.

**For headings specifically** — use `word-break: auto-phrase` (Chrome 119+) to break at natural phrase boundaries (文節 bunsetsu) rather than arbitrary character positions:

```css
:lang(ja) h1,
:lang(ja) h2,
:lang(ja) h3 {
  word-break: auto-phrase; /* Requires lang="ja" on the element or ancestor */
}
```

This requires `lang="ja"` on the `<html>` tag or element. Without the language attribute, the browser cannot apply Japanese-specific breaking rules.

---

## 8. Punctuation Spacing (text-spacing-trim)

Japanese full-width punctuation characters (、。「」（）etc.) contain internal glyph spacing on one side by design — they fit within a full em-box. When two punctuation characters appear adjacent, this creates excessive visual gaps.

The CSS `text-spacing-trim` property (Chrome 118+, in progress elsewhere) removes this double-spacing between adjacent CJK punctuation:

```css
:lang(ja) {
  text-spacing-trim: trim-start; /* Removes opening space on first punctuation of a line */
}
```

For broader compatibility, consider the **Yaku Han JP** library, which replaces full-width punctuation with half-width variants automatically:

```html
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/yakuhanjp/dist/css/yakuhanjp.min.css">
```

```css
:lang(ja) {
  font-family: 'YakuHanJP', /* Japanese punctuation half-width fix */
    'Hiragino Kaku Gothic ProN',
    'ヒラギノ角ゴ ProN',
    sans-serif;
}
```

---

## 9. Typefaces: Mincho and Gothic

The Latin serif/sans-serif distinction maps to Japanese as follows:

| Japanese term | Equivalent | Characteristics |
|---|---|---|
| 明朝 Mincho | Serif | Triangular stroke-end decorations (like serifs), variable stroke width. Originated in Ming Dynasty China. Traditional, authoritative, literary. |
| ゴシック Gothic | Sans-serif | Uniform stroke width, minimal decoration. Associated with modern design, UI, technical content. |

The iA Writer principle applies: Mincho ≈ the priest (authoritative, traditional); Gothic ≈ the hacker (democratic, functional). Neither is better — they signal different registers.

**Font stacks:**

Gothic (UI, digital-first, modern):
```css
font-family:
  'Hiragino Kaku Gothic ProN',  /* macOS/iOS */
  'ヒラギノ角ゴ ProN',
  'Yu Gothic',                   /* Windows */
  '游ゴシック体',
  YuGothic,
  'Meiryo',                      /* Windows fallback */
  'メイリオ',
  'Noto Sans JP',                /* Cross-platform */
  sans-serif;
```

Mincho (reading, editorial, traditional):
```css
font-family:
  'Hiragino Mincho ProN',        /* macOS/iOS */
  'ヒラギノ明朝 ProN',
  'Yu Mincho',                   /* Windows */
  '游明朝体',
  YuMincho,
  'Noto Serif JP',               /* Cross-platform */
  serif;
```

**Warning:** When no Japanese font is specified in CSS, many browsers default to **MS Mincho** (Windows) — an outdated, low-quality system font that renders poorly on screen at body sizes. Always explicitly set a font-family for Japanese content.

**Cross-platform recommendation:**

For new projects where web font loading is acceptable: **Noto Sans CJK JP** (Gothic, 7 weights) or **Noto Serif CJK JP** (Mincho) from Google Fonts. These are the most neutral, broadly compatible, and weight-flexible options available.

**Font file size warning:**

Japanese font files are large. A complete Japanese font with kanji can be 2MB+ (vs. under 500KB for a Latin font). Use the `unicode-range` CSS property or Google Fonts' subsetting parameters to load only what is needed. Failure to do this is a significant page load issue.

```css
@font-face {
  font-family: 'Noto Sans JP';
  src: url('...') format('woff2');
  unicode-range: U+3000-9FFF, U+F900-FAFF, U+FF00-FFEF;
  /* Load only CJK range; Latin falls through to next font in stack */
}
```

---

## 10. Italics: Never Use

**Never apply CSS `font-style: italic` to Japanese text.**

Japanese has no italic letterforms. Browsers that encounter an italic rule on Japanese text will either:
a) Force an oblique (synthesized slant) on an inherently non-slanted typeface — unreadable and typographically incorrect, or
b) Do nothing and leave the text unaffected

Both outcomes are worse than not using italic at all.

**How to express emphasis in Japanese:**

| Latin technique | Japanese equivalent |
|---|---|
| *Italics* | 傍点 bōten (emphasis dots placed above/beside characters) — CSS `text-emphasis` |
| **Bold** | Heavier weight variant — `font-weight: 700` |
| Inline quotation/reference | 「Japanese corner brackets」 |
| Foreign word/term | Katakana rendering |

**CSS for bōten (emphasis dots):**
```css
.emphasis-ja {
  text-emphasis: filled circle;
  text-emphasis-position: over right; /* Above characters in horizontal text */
}
```

---

## 11. Vertical Text (縦書き Tategaki)

Japanese can be set vertically (top to bottom, right to left columns) — the traditional direction for literary and formal texts. On the web this is achieved with `writing-mode: vertical-rl`.

**When to use:**

Vertical text is appropriate for: traditional literary content, poetry, formal documents, some decorative headings in appropriate contexts. It is generally not appropriate for UI, apps, articles, or documentation.

**Key behavior changes in vertical mode:**
- Line length becomes column height
- `width` and `height` semantics swap
- Latin characters and Arabic numerals render rotated 90° by default (use `text-orientation: mixed` or `text-combine-upright` for inline numbers)
- Scrolling direction should match vertical reading: horizontal scrolling, or paginated

**CSS:**
```css
.vertical-text {
  writing-mode: vertical-rl;
  text-orientation: mixed;      /* Rotates Latin, keeps CJK upright */
}

/* For numbers inline in vertical text */
.tate-chuu-yoko {
  text-combine-upright: all;    /* Sets numbers horizontally within vertical line */
}
```

For most web projects: **do not use vertical text unless the content specifically requires it.** The implementation complexity and browser inconsistencies are substantial.

---

## 12. Mixed Japanese and Latin Text

Many Japanese pages contain mixed content — product names in Latin, numbers, brand names, URLs. The rules for mixed text are nuanced.

**Font pairing:**

Latin characters will render from the first Latin-compatible font in the stack. Japanese characters will render from the first CJK font. They will not use the same font unless that font explicitly contains both scripts (Noto does; most others do not).

A well-constructed stack explicitly pairs both:
```css
font-family:
  'Inter',                       /* Latin — explicit choice */
  'Hiragino Kaku Gothic ProN',   /* Japanese — system gothic */
  'Noto Sans JP',                /* Japanese — cross-platform fallback */
  sans-serif;
```

**Size adjustment for mixed content:**

Because Japanese characters appear larger than Latin at the same `font-size`, use `font-size-adjust` or scoped CSS to compensate:

```css
/* If Latin is the primary language and Japanese is inline */
:lang(ja) span.japanese-inline {
  font-size: 0.9em;
}

/* If Japanese is primary and Latin is inline */
span.latin-inline {
  font-size: 1.1em;
}
```

**Inter-script spacing:**

When switching from Japanese to Latin or numerals inline, a small space typically improves readability. Modern browsers are beginning to add this automatically (Chrome inter-script spacing feature), but it is not yet universal. The W3C JLReq specifies this spacing as standard. Until `text-autospace` has broad support, add it manually:

```css
/* Approximate manual spacing between CJK and Latin/numbers */
/* Advanced: use CSS text-autospace when available */
@supports (text-autospace: ideograph-alpha) {
  :lang(ja) {
    text-autospace: ideograph-alpha ideograph-numeric;
  }
}
```

---

## 13. The `lang` Attribute: Non-Negotiable

**Always declare `lang="ja"` on Japanese content.** Without it, none of the browser-level typography improvements — `word-break: auto-phrase`, kinsoku handling, `text-autospace`, font subsetting, `text-spacing-trim` — activate correctly.

```html
<html lang="ja">        <!-- Pure Japanese page -->

<html lang="ja-JP">     <!-- Japanese as spoken in Japan (regional variant) -->

<!-- Mixed content: use inline lang attribute -->
<p lang="ja">日本語のテキスト <span lang="en">English inline</span> 続きの日本語</p>
```

For mixed-language pages, apply `lang` at the most granular level possible. This is also a WCAG 3.1.2 requirement (Language of Parts).

---

## 14. Quick Reference: Japanese vs. Latin

| Property | Latin (main doc) | Japanese |
|---|---|---|
| CPL (body) | 60–65 ch | 30–40 em |
| CPL unit | `ch` | `em` |
| WCAG CPL maximum | 80 | 40 |
| Line-height (body) | 1.5 | 1.65–1.75 |
| Line-height (headings) | 1.1–1.2 | 1.2–1.3 |
| Letter-spacing (body) | 0 | 0.05em |
| Text alignment | left (never justify) | justify (standard) |
| Italics | ✓ Use for emphasis | ✗ Never — use font-weight or text-emphasis |
| Font size vs. Latin | baseline | appears 10–15% larger — reduce if mixed |
| Body size minimum | 16px | 12px (UI), 14–16px (reading) |
| Line break control | not usually needed | `line-break: strict` required |
| Word break | default | `word-break: keep-all` |
| Serif term | Serif | 明朝 Mincho |
| Sans-serif term | Sans-serif | ゴシック Gothic |
| Default browser font | (varies, usually readable) | MS Mincho — override always |
| Font file size | <500KB | 2MB+ — subset aggressively |
| `lang` attribute | good practice | mandatory for correct rendering |

---

## 15. What to Never Do (Japanese-specific)

1. **Never use `word-break: break-all` on Japanese text.** Catastrophic — breaks mid-character-group, violates all kinsoku rules.
2. **Never apply `font-style: italic` to Japanese.** Produces synthesized oblique or no effect — both wrong.
3. **Never justify Latin text, never left-align Japanese body text without reason.** Each language has its correct default.
4. **Never set Japanese font sizes without testing.** What appears legible to a non-Japanese reader at 12px may be illegible to a native reader parsing complex kanji.
5. **Never omit the `lang="ja"` attribute.** It is required for correct rendering, kinsoku rules, and phrase-boundary breaking.
6. **Never load a full Japanese font file without subsetting.** A 2MB+ font file on every page load is unacceptable.
7. **Never rely on default browser font for Japanese.** MS Mincho (Windows) is the common default and is poor for screen reading.
8. **Never use `ch` units for Japanese column width.** `ch` measures a Latin `0`; use `em` for CJK.
9. **Never use `text-align: justify` without `text-align-last: left`.** The last line of a paragraph should not stretch.
10. **Never ignore punctuation spacing.** Full-width Japanese punctuation stacks badly without `text-spacing-trim` or Yaku Han JP.

---

## Sources

- W3C Japanese Layout Task Force — *Requirements for Japanese Text Layout (JLReq)* (W3C Working Group Note, 2009; updated 2020)
- JIS X 4051 — *Formatting rules for Japanese documents* (Japanese Industrial Standard)
- AQ Works — *Seven rules for perfect Japanese typography*
- Hayataki Masaharu — *The Most Comprehensive Guide to Web Typography in Japanese* (LinkedIn)
- Typotheque — *Typesetting principles of Chinese, Japanese, and Korean (CJK) text*
- Asian Absolute — *CJK Typesetting in 2025: Challenges, Workflows, and Best Practices*
- Xoxzo blog — *Basic Japanese typography tips for web design*
- Pavel Laptev (Medium) — *Japanese typography on the web — tips and tricks*
- Chrome Developers blog — *Introducing four new international features in CSS* (2023)
- MDN Web Docs — `line-break`, `text-spacing-trim`, `text-emphasis`, `writing-mode`
- kilianmuster.com — *Japanese — The Typography*
- ryelle.codes — *Typography troubles: Balancing lines in Japanese & Korean*
- WCAG 2.1 — Success Criterion 1.4.8 (Visual Presentation), 3.1.2 (Language of Parts)
