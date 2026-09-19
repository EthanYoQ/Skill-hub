# Visual Grammar and Anti-Repetition Contract

This file owns visual-direction selection, deck planning, and repetition control for both HTML and PPTX. Read it before loading component snippets or calling page-template methods.

## 1. Separate invariant DNA from the selected profile

The invariant DNA is warm editorial materiality, evidence readability, fixed-stage behavior, role-based typography, accessible contrast, and disciplined semantic color. Beige, terracotta, Fraunces, rounded white cards, and one header/body/footer anatomy are not invariants.

Load `style-index.json`, shortlist profiles from purpose, audience, formality, density, mood, and requested scheme, then load only the selected profile. If the user explicitly locks the original Pfizer look, select `warm-paper-terracotta`. Otherwise do not default every unrelated brief to the first profile.

When visual latitude is high, present three genuinely different title-slide directions before full production: one safe, one bolder but suitable, and one wildcard. They must differ in palette family, contrast model, composition grammar, and typography treatment. Skip this preview round only when the user locks a profile or requests a fast deterministic conversion.

## 2. Declare density mode

- `speaker-led`: fewer claims per slide, large visual anchors, aggressive splitting.
- `balanced`: presentation-scale type with enough labels for later review.
- `reading-first`: denser grids, tables, citations, and annotations; never solve fit by globally shrinking type.

Density changes slide count, grid capacity, annotation burden, and candidate compositions. It is not a font-size switch.

## 3. Build a manifest before rendering

Use `assets/plan_deck.py` or produce the equivalent schema manually. The same manifest drives HTML and PPTX.

```json
{
  "deck_profile": "ink-cobalt-editorial",
  "density_mode": "reading-first",
  "seed": "brief-stable-id",
  "slides": [
    {
      "id": "s04",
      "narrative_role": "proof",
      "data_relation": "comparison",
      "cardinality": {"items": 5, "series": 2},
      "uncertainty": "mixed",
      "expression_family": "dot-plot",
      "composition_id": "chart-notes-asymmetric",
      "dominant_geometry": "split",
      "tone_id": "canvas",
      "continuation_of": null
    }
  ]
}
```

Required planning variables are narrative role, data relation, cardinality, series count, density, uncertainty, media availability, selected profile, and recent slide signatures. Use a stable brief-derived seed only to break equivalent ties. The same brief, profile, and seed must reproduce the same manifest.

## 4. Select expression and composition separately

First eliminate semantically invalid expressions. Then eliminate compositions that cannot fit the cardinality and density. Rank the survivors by profile compatibility and narrative role. Finally apply novelty penalties for recently used expression, composition, geometry, tone, and annotation anatomy.

Composition vocabulary:

| Composition | Best for | Typical geometry |
|---|---|---|
| `statement-full-bleed` | opener, tension, transition, closing | statement |
| `dominant-metric-marginalia` | one decisive number with context | asymmetric |
| `chart-notes-asymmetric` | trend/comparison with evidence notes | split |
| `comparison-split` | before/after or two alternatives | split |
| `ledger-takeaway-band` | reading-first facts, limits, or audit | ledger |
| `process-rail` | sequence or operating flow | process |
| `matrix-marginalia` | matching, portfolio, or decision boundary | matrix |
| `small-multiple-field` | repeated comparable series | chart-field |
| `image-text-offset` | product, place, person, or case evidence | image |
| `editorial-mosaic` | heterogeneous but related evidence | mosaic |

Four KPIs do not automatically imply four equal cards. Candidate structures include one dominant metric plus three annotations, a ledger, a split, or a small-multiple strip. A repeated expression family must change composition or annotation anatomy.

## 5. Plan palette cadence

Resolve colors through role tokens: `canvas`, `surface`, `contrast_surface`, `ink`, `muted`, `primary`, `secondary`, `signal`, `positive`, and `negative`. Preserve status meanings. Categorical colors must not accidentally imply positive, warning, or negative status.

Follow the selected profile's cadence. Do not randomize accents per slide. Use contrast surfaces for intentional beats and avoid three consecutive slides with the same tone unless the sequence is explicitly documented.

## 6. Hard anti-repetition gates

Before rendering:

- Adjacent non-continuation slides cannot share `composition_id`.
- No three consecutive slides may share dominant geometry or tone.
- Repeated expression families must change composition or annotation structure.
- Continuations declare `continuation_of`; they do not silently bypass the gate.
- For a 10-12 slide deck, use at least five composition IDs and four dominant geometries when content permits.
- Generic repeated-card-grid anatomy may cover at most 40% of non-title slides.
- Three consecutive identical header/body/footer signatures are a failure even if component names differ.

After rendering:

- Inspect the overview/contact sheet with text blurred or ignored. The deck should still show distinct beats.
- Compare major-region count and bounds; matching DOM or PPTX region signatures require review.
- Warn on high perceptual similarity between non-continuation screenshots.
- Check palette histograms and background runs.
- Keep all existing overflow, footer, viewport, package, and font checks.

Do not chase variety by adding decoration or random colors. Semantic validity, readability, and one coherent selected profile remain higher-priority gates.

## 7. HTML and PPTX parity

Both outputs use the same manifest, profile, and semantic expression decisions. They may use format-specific renderers, but PPTX must not collapse every unsupported composition into a card grid. If a composition is not feasible in PPTX, choose the next compatible composition during planning and record the substitution.

Legacy `add_*_slide()` methods remain compatibility wrappers. New work should plan the deck first and pass `style_profile` into `EditorialDeck`; a page-role method is not permission to skip the manifest or reuse its fixed anatomy across the deck.

Use `assets/render_manifest.py` as the default shared renderer. It must embed the same normalized manifest hash in the HTML metadata and PPTX core properties, preserve slide/composition order in `render-report.json`, and emit format-specific major-region signatures. Browser QA and PPTX package/shape inspection validate the rendered outputs; a manifest-only pass is not a release pass.
