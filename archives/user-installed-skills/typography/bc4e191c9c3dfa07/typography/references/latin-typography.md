# Typography Guidelines
## Research-grounded decisions for reading, UI, dark mode, and mobile

---

## Philosophy

> "Websites aren't broken by default, they are functional, high-performing, and accessible. You break them."
> — motherfuckingwebsite.com

> "Responsive means that it responds to whatever motherfucking screensize it's viewed on."
> — bettermotherfuckingwebsite.com

The browser renders semantic HTML correctly. Every typographic decision made on top of that is a bet. This document records the bets worth making — each grounded in research — and the ones to skip.

The iA Writer principle applies: **fewer decisions, made well, applied consistently.** iA Writer supports a maximum of 64–80 characters per line, couples line-height to column width automatically, and ships three font variants all serving the same underlying measure. Every rule in this document follows the same logic: a defensible number, a cited reason, and a specific CSS implementation.

---

## 1. Reading / Article Layout

These rules govern long-form content: articles, documentation, blog posts, reader views.

### 1.1 Characters Per Line (CPL)

**Target: 60–70 CPL. Hard limits: 45 min, 80 max.**

| Source | Recommendation |
|---|---|
| Bringhurst, *Elements of Typographic Style* | 45–75 CPL |
| Baymard Institute (2012) | 50–75 CPL, sweet spot ~65 |
| Emil Ruder, *Typographie* (1967) | 50–60 CPL for maximum reading speed |
| iA Writer implementation | 64–80 CPL depending on font |
| Dyson & Haselgrove (2001) | Longer lines read faster; shorter lines better comprehension |

The Dyson/Haselgrove finding is the key tension: speed peaks wider, comprehension peaks narrower. For a reader app where retention matters, bias toward the narrower end of the range (60–65 CPL).

**Why it fails outside the range:**
- Too wide (>80): eye struggles to find line start/end; return sweep errors increase
- Too narrow (<45): rhythm breaks; reader begins next line before finishing current one; word skipping increases

**CSS:**
```css
.article-body {
  max-width: min(90vw, 65ch);
  margin-inline: auto;
}
```

The `ch` unit scales with font size, so this remains valid when users zoom or change their system font size. `min()` ensures it never overflows on small viewports.

### 1.2 Body Font Size

**Target: 18px desktop, 16px mobile minimum.**

iA Writer's "100% Easy-to-Read Standard" (2006) established Georgia 16px as a baseline that was controversial at the time and is now consensus. With higher-DPI screens, the floor has moved up. Text-heavy designs (articles) should use 18–24px; interaction-heavy designs can use 14–20px.

**CSS:**
```css
:root {
  --font-size-body: clamp(16px, 1.1vw + 14px, 18px);
}
body {
  font-size: var(--font-size-body);
}
```

### 1.3 Line Height

**Target: 1.45–1.55 for body text. Coupled to column width.**

iA Writer's explicit rule: **wider columns require more line-height.** The eye needs more vertical separation to execute the return sweep accurately on long lines. At the 65 CPL target, 1.5 is the right value.

| Context | Line-height |
|---|---|
| Body text (65 CPL) | 1.5 |
| Body text (80 CPL) | 1.6 |
| Body text (45 CPL) | 1.4 |
| H1–H2 headings | 1.1–1.2 |
| H3–H4 subheadings | 1.2–1.3 |
| Captions / labels | 1.3 |

**CSS:**
```css
.article-body {
  line-height: 1.5;
}
```

### 1.4 Contrast

**Target: #1a1a1a on #f5f5f5. Not pure black on white.**

iA Writer's values: text `#424242`, background `#f5f6f6`. The principle: the eye rarely encounters pure black-on-white contrast in the physical world. Softening both values reduces perceived harshness without sacrificing legibility. WCAG AA requires 4.5:1 for body text; `#424242` on `#f5f6f6` is approximately 8:1 — comfortable without being aggressive.

For reading contexts, target 7:1 to 9:1. Below 4.5:1 fails WCAG. Above 12:1 starts to introduce harshness.

**CSS:**
```css
:root {
  --color-text: #1a1a1a;
  --color-bg: #f5f5f5;
}
```

### 1.5 Paragraph Spacing and Margins

Paragraph spacing should be generous enough to separate thoughts without creating the appearance of disconnected fragments. A safe value is `1em` top margin on paragraphs (`margin-block-start`). Do not use both indentation and spacing — choose one.

**CSS:**
```css
.article-body p + p {
  margin-block-start: 1.1em;
}
```

---

## 2. UI Typography: Headings, Labels, Navigation

These rules govern interface elements: page titles, section headings, navigation labels, button text, form labels, captions.

### 2.1 Type Scale

Use a **modular scale** — a consistent ratio applied to the base font size. Do not pick sizes arbitrarily.

| Scale name | Ratio | Use case |
|---|---|---|
| Major second | 1.125 | Dense UIs, dashboards, data-heavy |
| Major third | 1.25 | Standard web UI, most projects |
| Perfect fourth | 1.333 | Editorial, document-style interfaces |

Starting from a 16px base with a 1.25 ratio:

| Level | Size | Usage |
|---|---|---|
| xs | 12px | Captions, footnotes, fine print (never below 12px) |
| sm | 14px | Labels, metadata, timestamps |
| base | 16px | Body text, form inputs, navigation |
| md | 20px | Lead paragraphs, section intros |
| lg | 25px | H3, card titles |
| xl | 31px | H2, page section headings |
| 2xl | 39px | H1, page titles |
| 3xl | 49px | Hero headings, display text |

**CSS:**
```css
:root {
  --scale: 1.25;
  --size-xs:   0.75rem;   /* 12px */
  --size-sm:   0.875rem;  /* 14px */
  --size-base: 1rem;      /* 16px */
  --size-md:   1.25rem;   /* 20px */
  --size-lg:   1.5625rem; /* 25px */
  --size-xl:   1.953rem;  /* 31px */
  --size-2xl:  2.441rem;  /* 39px */
  --size-3xl:  3.052rem;  /* 49px */
}
```

### 2.2 Font Weight as Hierarchy Signal

Weight is a more precise hierarchy signal than size alone in dense UIs. The principle: **use size to signal category, weight to signal state or emphasis within a category.**

| Weight | Value | Usage |
|---|---|---|
| Regular | 400 | Body text, most UI text — never increase for readability |
| Medium | 500 | Active navigation states, subtle emphasis |
| Semi-bold | 600 | Navigation labels, button text, subheadings, card titles |
| Bold | 700 | H1–H2, critical alerts, primary headings only |
| Heavy | 800+ | Hero text, display use only |

Reserve bold for the top of the hierarchy. Using bold throughout flattens the signal and forces readers to infer hierarchy from context alone.

### 2.3 Heading Line Length

Headings operate on different rules than body text:

| Heading level | Max CPL |
|---|---|
| Hero / H1 | 30–40 characters |
| H2 section headings | 40–60 characters |
| H3 subheadings | 50–65 characters |
| Microcopy (buttons, CTAs) | 20–35 characters |

Long H1s dilute the message. Cap hero text at ~35 characters and let it breathe vertically.

### 2.4 Navigation and Labels

- Use semi-bold (600) for active nav items; regular (400) for inactive
- Minimum size: 14px for labels; 16px for primary navigation
- Uppercase labels: acceptable for short ALL-CAPS navigation items (under 4 words); avoid for body or long labels — all-caps removes ascender/descender shape cues that aid word recognition
- Letter-spacing: `0.05em` on uppercase labels only; never add tracking to mixed-case body text

### 2.5 Limit Font Sizes

Even complex UIs rarely need more than 5–6 distinct sizes. Text-heavy pages: up to 6. Interaction-heavy pages: 4 is usually enough. More than 6 sizes creates visual noise and signals a missing design system rather than hierarchy.

### 2.6 Spacing as Hierarchy

More space above a heading than below it binds the heading visually to its following content. Standard ratio: space above ≈ 2× space below.

```css
h2 {
  margin-block-start: 2em;
  margin-block-end: 0.5em;
}
```

---

## 3. Dark Mode

### 3.1 The Evidence

The research verdict is clear but nuanced:

- **Light mode wins on visual acuity and proofreading accuracy** for users with normal vision (Piepenbrock et al., University of Düsseldorf — the most rigorous study available)
- **Dark mode preferred subjectively** — 68.4% survey preference; users perceive it as more comfortable even when performance metrics favor light
- **Dark mode is better for low-light environments** and for users with specific visual conditions (cloudy ocular media, certain low-vision conditions)
- **Dark mode reduces OLED battery draw by 11–38%** at 50% brightness (Dash & Hu, 2021)

**Practical conclusion:** Ship both. Default to system preference (`prefers-color-scheme`). Do not force either.

### 3.2 Dark Mode Color Rules

**Never use pure black (#000000) as background.** Material Design specifies `#121212`; the reason is depth perception — pure black eliminates all shadow and elevation cues, making the UI appear flat and increasing glare contrast. Use dark grey.

| Surface level | Value | Usage |
|---|---|---|
| Base background | #121212 | Page/app background |
| Surface +1 | #1e1e1e | Cards, panels |
| Surface +2 | #252525 | Elevated modals, dropdowns |
| Surface +3 | #2c2c2c | Tooltips, highest elevation |

For text on dark backgrounds, use off-white rather than pure white:

| Text role | Light mode | Dark mode |
|---|---|---|
| Primary text | #1a1a1a | #e8e8e8 |
| Secondary text | #595959 | #a0a0a0 |
| Disabled / metadata | #8a8a8a | #606060 |

### 3.3 Contrast Ratios in Dark Mode

WCAG AA minimums apply in both modes. Targets:

| Text type | WCAG AA min | Target |
|---|---|---|
| Body text (< 18px) | 4.5:1 | 7:1–10:1 |
| Large text (≥ 18px or bold ≥ 14px) | 3:1 | 5:1–8:1 |
| UI components, focus indicators | 3:1 | 4.5:1 |

In dark mode, achieving high contrast is easier — but **avoid going too high**. White text (#ffffff) on dark grey (#121212) is approximately 18:1, which can feel harsh. `#e8e8e8` on `#121212` gives approximately 14:1 — high enough to be clearly readable, reduced enough to avoid glare.

### 3.4 Accent and Brand Colors in Dark Mode

Do not simply invert light-mode accent colors. A bright brand blue that reads well on white may be harsh or garish on dark backgrounds.

Rules:
- Desaturate bright colors by 20–40% for dark backgrounds
- Increase lightness of dark colors that need to remain visible
- Test every color independently against the dark surface it sits on
- Create a dark-specific color token set, not a mechanical inversion

### 3.5 Implementation

```css
:root {
  color-scheme: light dark;

  /* Light defaults */
  --color-bg: #f5f5f5;
  --color-surface: #ffffff;
  --color-text: #1a1a1a;
  --color-text-secondary: #595959;
}

@media (prefers-color-scheme: dark) {
  :root {
    --color-bg: #121212;
    --color-surface: #1e1e1e;
    --color-text: #e8e8e8;
    --color-text-secondary: #a0a0a0;
  }
}
```

---

## 4. Mobile

### 4.1 Line Length on Mobile

Portrait viewport naturally constrains CPL — it is rarely an issue. Landscape is where it breaks.

| Mode | Target CPL |
|---|---|
| Portrait (article) | 35–45 CPL (natural from viewport) |
| Landscape (article) | Cap at 80 CPL maximum — Baymard finding |
| UI labels, mobile | 20–35 CPL |

Do not set a fixed `max-width` that ignores portrait/landscape switching. Use:

```css
.article-body {
  max-width: min(90vw, 65ch);
}
```

This lets portrait behave naturally (90vw will be narrower than 65ch) while capping landscape at 65ch.

### 4.2 Font Size on Mobile

**16px is the absolute minimum for body text.** Apple's iOS Human Interface Guidelines recommend 17pt for body content in most contexts (approximately 22.7px at standard density). The 16px figure comes from usability research and platform conventions, not WCAG (which only requires 200% zoom support).

| Element | Desktop | Mobile |
|---|---|---|
| Body text | 18px | 16px minimum |
| Subheadings (H3) | 20–25px | 18–20px |
| Section headings (H2) | 28–32px | 22–26px |
| Page title (H1) | 36–48px | 28–36px |
| Captions / labels | 14px | 14px |
| Fine print | 12px | 13px (slightly larger on mobile) |

Implement with `clamp()` for fluid scaling:

```css
:root {
  --size-body: clamp(16px, 1vw + 14px, 18px);
  --size-h1:   clamp(28px, 4vw + 16px, 48px);
  --size-h2:   clamp(22px, 2.5vw + 16px, 32px);
  --size-h3:   clamp(18px, 1.5vw + 14px, 25px);
}
```

### 4.3 Line Height on Mobile

Mobile needs slightly more line-height than desktop — smaller screens are typically held closer, and text is read in more varied conditions (movement, outdoor light).

| Context | Desktop | Mobile |
|---|---|---|
| Body text | 1.5 | 1.55–1.6 |
| Headings | 1.1–1.2 | 1.2–1.3 |
| Labels / nav | 1.3 | 1.4 |

### 4.4 Touch Targets

Typography interacts with touch target sizing. Any interactive text (links, nav items, buttons) must meet minimum touch target requirements:

- Apple HIG: 44×44 pt minimum
- Material Design: 48×48 dp minimum
- WCAG 2.5.5 (AAA): 44×44 CSS pixels

For inline text links, this means adding padding rather than relying on the text height alone:

```css
a {
  padding-block: 0.25em;
  /* Expands touch target without affecting visual layout */
}
```

### 4.5 Viewport and Scaling

Always include:
```html
<meta name="viewport" content="width=device-width, initial-scale=1">
```

Without this, mobile browsers scale down the desktop layout, making all font-size decisions irrelevant.

Use `rem` for font sizes (scales with user's system font preference), `em` for component-level spacing (scales with local font size), and `px` only for borders and fine details that should not scale.

---

## 5. Typeface Decisions

### 5.1 Serif vs. Sans-Serif

iA's framing: the serif is a priest; the sans is a hacker. Neither is better — they signal different tonal registers.

For reading/article contexts: serif typefaces (Georgia, Charter, Libre Baskerville, iA Writer fonts) are defensible and traditional. They do not measurably outperform sans-serif above 12px, but they carry authority and reading comfort associations built from print history.

For UI typography: sans-serif performs better at small sizes, in labels, in navigation, and in data-dense contexts. Mixing serif body with sans-serif UI is a standard and effective pairing.

### 5.2 System Font Stack

When using system fonts (zero-load, platform-native rendering):

```css
font-family:
  -apple-system,       /* SF Pro on macOS/iOS */
  BlinkMacSystemFont,  /* SF Pro on Chrome/macOS */
  "Segoe UI",          /* Windows */
  "Noto Sans",         /* Android/Linux */
  sans-serif;
```

For serif reading content:
```css
font-family:
  Georgia,
  "Times New Roman",
  serif;
```

### 5.3 Variable Fonts

iA Writer uses variable fonts in recent versions to adjust optical weight based on size, device, and background color — a technique borrowed from print's graded typefaces. Where a variable font is available, use the `font-variation-settings` or the `font-optical-sizing: auto` property to let the browser do this work automatically.

```css
body {
  font-optical-sizing: auto;
}
```

---

## 6. What to Never Do

These are categorical rules, not guidelines with exceptions:

1. **Never justify text on the web.** Variable word spacing creates rivers of whitespace that interrupt reading flow. Left-align always.
2. **Never use `font-size` below 12px** anywhere a user is expected to read.
3. **Never use pure black (#000) on white (#fff)** for body text. Soften both.
4. **Never use pure black (#000) as dark mode background.** Use #121212 or darker grey.
5. **Never use more than 6 distinct font sizes** in a single interface without strong justification.
6. **Never add letter-spacing to mixed-case body text.** Only to ALL-CAPS labels, and then sparingly (`0.05em` maximum).
7. **Never use a liquid (100% width) layout for long-form reading text.** Column width is a readability control, not an aesthetic preference.
8. **Never invert light mode colors mechanically to produce dark mode.** Create dark-specific tokens.
9. **Never use ALL-CAPS for text longer than 4–5 words.** Removes word-shape recognition cues.
10. **Never omit the viewport meta tag on any page serving mobile users.**

---

## 7. Quick Reference

| Decision | Value |
|---|---|
| Body CPL (desktop, article) | 60–65 ch |
| Body CPL (mobile, portrait) | Natural (35–45) |
| Body CPL (mobile, landscape cap) | 80 max |
| Body font size (desktop) | 18px |
| Body font size (mobile min) | 16px |
| Line-height (body, 65ch) | 1.5 |
| Line-height (mobile body) | 1.55–1.6 |
| Line-height (headings) | 1.1–1.2 |
| Text color (light) | #1a1a1a |
| Background color (light) | #f5f5f5 |
| Text color (dark) | #e8e8e8 |
| Background color (dark) | #121212 |
| Contrast ratio target (body) | 7:1–10:1 |
| Contrast ratio WCAG AA (body) | 4.5:1 minimum |
| Type scale ratio (standard) | 1.25 |
| Heading spacing above:below | 2:1 |
| Touch target minimum | 44×44px |
| Paragraph spacing | 1.1em |
| Max distinct font sizes (UI) | 5–6 |

---

## Sources

- Bringhurst, R. *The Elements of Typographic Style* (1992)
- Ruder, E. *Typographie* (1967) — 50–60 CPL for optimal reading speed
- Baymard Institute — *Readability: The Optimal Line Length* (2012)
- Dyson, M. C. & Haselgrove, M. — *The influence of reading speed and line length on the effectiveness of reading from screen* (2001, British Journal of Educational Technology)
- Shaikh, A. D. — *The Effects of Line Length on Reading Online News* (2005)
- Piepenbrock, C. et al. — Institut für Experimentelle Psychologie, Düsseldorf — contrast polarity and visual acuity studies
- Nielsen Norman Group — *Dark Mode vs. Light Mode: Which Is Better?*
- iA — *Responsive Typography: The Basics* (2012); *A Typographic Christmas* (2018)
- iA — *The 100% Easy-to-Read Standard* (2006)
- Material Design 3 — Surface and elevation guidelines
- WCAG 2.1 — Success Criteria 1.4.3 (contrast), 1.4.4 (resize text), 2.5.5 (target size)
- Apple Human Interface Guidelines — Typography, Touch Targets
- motherfuckingwebsite.com / bettermotherfuckingwebsite.com — The prior art
