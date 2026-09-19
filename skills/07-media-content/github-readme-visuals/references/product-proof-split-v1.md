# Product-proof Split v1

Use this profile as the default first image for GUI software repositories. It preserves the visual grammar established by the approved README hero: verified brand and product copy on the left, complete real software screenshots on the right, with identical geometry across repositories and languages.

## Output contract

- Canvas: `2560 x 1280`, 2:1.
- Left evidence-and-copy region: `1060 px` wide, with `180 px` left padding.
- Right screenshot collage: four to six distinct real application states; six is the default.
- Every screenshot frame: `800 x 600`, 4:3, `8deg` clockwise rotation, `object-fit: contain`.
- Primary screenshot: the application's first/default screen, placed in the main overview slot.
- Logo: original transparent product logo directly on the canvas background. Do not invent a dark tile or frame.
- Author/byline: derive from verified repository ownership or README facts. Never guess a person or organization.
- Locales: use one shared composition source. Localize copy and in-product screenshot UI together.
- Final GUI hero: deterministic HTML/CSS render. Do not use image generation for the final composition.

## Fixed screenshot geometry

Do not estimate these values independently. The bundled template is the geometry source of truth.

| Slot | CSS left | CSS top | Z | Approximate rotated corners: TL / TR / BR / BL |
| --- | ---: | ---: | ---: | --- |
| Top center | 1400 | -230 | 2 | `1446,-283 / 2238,-171 / 2154,423 / 1362,311` |
| Top right | 2170 | -75 | 3 | `2216,-128 / 3008,-16 / 2924,578 / 2132,466` |
| Main overview | 1198 | 335 | 9 | `1244,282 / 2036,394 / 1952,988 / 1160,876` |
| Middle right | 1944 | 533 | 7 | `1990,480 / 2782,592 / 2698,1186 / 1906,1074` |
| Bottom left | 1102 | 841 | 5 | `1148,788 / 1940,900 / 1856,1494 / 1064,1382` |
| Bottom right | 1937 | 1007 | 6 | `1983,954 / 2775,1066 / 2691,1660 / 1899,1548` |

The two decorative triangles remain at the left edge and point down-left using the template's fixed rotations. Do not flip, mirror, or relocate them.

## Slot selection

Map screenshot entries in `hero-data.js` by importance, not filename order:

1. Main overview: first/default product screen.
2. Top center: next most important workflow.
3. Middle right: next distinct workflow or state.
4. Bottom left: settings, review, output, or another supporting state.
5. Top right: optional supporting state.
6. Bottom right: optional supporting state.

When only four or five distinct states exist, leave the unused optional slots hidden. Do not duplicate a screen, show a near-identical crop, or fabricate UI to make the collage look fuller.

## Left-side hierarchy

Keep the following order:

1. Original product logo, product name, and verified author or organization.
2. Two short headline bars that make the product category and primary interaction clear.
3. A compact proof card containing only supported product, workflow, or implementation facts. Provider logos are optional and require repository evidence.
4. Three or four concise, supported feature statements.

Avoid API-key, pricing, privacy, offline, provider, or deployment claims unless the repository or user directly confirms them.

## Required production package

Copy the template without editing its bytes:

```text
docs/readme-visuals/product-proof-split-v1.html
```

Copy and customize the data example:

```text
docs/readme-visuals/hero-data.js
```

Create the manifest:

```text
docs/readme-visuals/visual-manifest.json
```

Render the shared source once per locale, normally to:

```text
docs/images/<product>-hero-zh.png
docs/images/<product>-hero-en.png
```

The copied HTML template must remain byte-identical to `assets/product-proof-split-v1.html`. All repository-specific paths, copy, colors, and locale content belong in `hero-data.js`.

## Manifest schema

Use this structure. Paths are repository-relative and must remain inside the repository.

```json
{
  "schema_version": 1,
  "profile": "product-proof-split-v1",
  "composition_source": "docs/readme-visuals/product-proof-split-v1.html",
  "data_source": "docs/readme-visuals/hero-data.js",
  "heroes": {
    "zh": {
      "readme": "README.md",
      "output": "docs/images/product-hero-zh.png",
      "ui_locale": "zh-CN",
      "screenshots": [
        {
          "path": "docs/images/screens/overview-zh.png",
          "role": "primary",
          "capture_provenance": "computer-use-capture",
          "complete_window": true,
          "ui_locale": "zh-CN"
        }
      ]
    }
  }
}
```

Allowed `capture_provenance` values are `computer-use-capture`, `playwright-capture`, `provided-real-screenshot`, and `project-authored-screenshot`. Image generation is never valid screenshot provenance.

## Bilingual rules

- Keep both locale heroes at `2560 x 1280`.
- Keep screenshot count, order, slots, geometry, logo treatment, and hierarchy identical.
- Capture separate UI-language screenshots when the application supports the locale.
- Use semantically equivalent claims; typography may adjust to prevent overflow.
- If the application does not support a README locale, disclose that limitation instead of presenting localized overlay copy as localized product UI.

## Blocking failures

Do not deliver when any of these is true:

- The GUI hero is illustration-only or omits real target-product screenshots.
- A screenshot is generated, cropped, incomplete, duplicated, near-duplicated, or in the wrong supported UI language.
- The first screenshot is not the intended primary screen.
- The logo has an invented tile or container.
- Decorations overlap the logo or screenshot bounds.
- The template geometry changed without an explicit user-selected reference override.
- The manifest is missing, inconsistent with README paths, or fails the verifier.
- Only Markdown paths, tests, or file existence were checked without visually inspecting both exported hero images.
