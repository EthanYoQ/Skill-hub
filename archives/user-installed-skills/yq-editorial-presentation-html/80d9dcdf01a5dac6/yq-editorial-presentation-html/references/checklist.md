# Checklist · Warm Editorial Deck QA

## P0 · Planning and semantics

- [ ] Purpose, audience, formality, density mode, output format, and selected profile are explicit.
- [ ] The profile supports the requested output format; a locked profile is never silently substituted.
- [ ] A slide manifest exists and `assets/plan_deck.py --validate-only` passes.
- [ ] Every expression matches its data relation, cardinality, series count, uncertainty, and annotation burden.
- [ ] Independent KPIs are not proof bars; timelines are not generic bars; matching relations are not bars.
- [ ] Adjacent non-continuation slides do not share `composition_id`.
- [ ] No three-slide run shares dominant geometry or tone.
- [ ] Repeated expression families change composition or annotation anatomy.
- [ ] For 10-12 slides, content permits at least five composition IDs and four dominant geometries.
- [ ] Generic repeated-card or mosaic anatomy is at most 40% of non-title slides.

## P0 · HTML behavior and readability

- [ ] HTML is a horizontal fullscreen deck: fixed `#deck`; each `.slide` is `100vw × 100vh`.
- [ ] No vertical page scroll; F11 does not crop the current slide.
- [ ] Main content is normally at least 80% of viewport width at 1920×1080.
- [ ] Regular titles are at least 78px, hero titles at least 110px, and lead/subtitle at least 24px, except declared compact pages.
- [ ] Navigation dots, arrows, wheel, touch, and ESC overview work.
- [ ] Footers stay in flow and do not cover content; `.wrap` does not use flex auto margins that sink content.
- [ ] Chinese titles do not leave a single character on a line.

## P1 · Profile coherence

- [ ] All colors resolve through selected profile role tokens.
- [ ] Display/body/data typography follows the selected profile with usable fallbacks.
- [ ] Status colors remain semantically consistent; categorical colors do not imply status accidentally.
- [ ] Palette cadence creates deliberate contrast beats without random per-slide color changes.
- [ ] Corner, border, depth, decorative vocabulary, and annotation style remain coherent inside the profile.

## P2 · Rendered diversity

- [ ] An overview/contact sheet still shows different beats when text is ignored or blurred.
- [ ] No three consecutive slides share the same header/body/footer anatomy.
- [ ] Major-region bounds and counts do not repeat mechanically across unrelated slides.
- [ ] High screenshot similarity between non-continuation slides is reviewed and justified.
- [ ] Visual variety comes from semantic composition, not decorative noise or random colors.

## P3 · PPTX

- [ ] PPTX is 16:9 and reopens successfully.
- [ ] `style_profile` and manifest profile match; the profile declares PPTX support.
- [ ] Unsupported HTML compositions have explicit PPTX substitutions, not a universal card-grid fallback.
- [ ] Font embedding or fallback path is verified; WPS is not reported as Microsoft PowerPoint.
- [ ] Package checks cover requested fonts, `ppt/fonts/`, and `embeddedFontLst` when embedding is requested.
