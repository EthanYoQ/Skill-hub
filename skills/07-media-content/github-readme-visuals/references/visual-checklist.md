# README Visual Checklist

## Source and content

- Confirm the resolved Skill path is a canonical install or source copy, not a `-workspace/skill-snapshot` evaluation baseline.
- For a GUI application without an explicit user-selected alternative, confirm Product-proof split v1 is the selected profile.
- Confirm the supplied reference was directly inspected before production.
- Record the reference's canvas ratio, left/right allocation, dominant visual, screenshot count, overlap, rotation, off-canvas clipping, shadows, and text hierarchy.
- For one-to-one requests, record a pixel geometry table with every screenshot's four corners, size, angle, off-canvas clipping, z-order, neighbor gaps, and every asymmetric decoration's direction.
- Confirm no supplied reference UI, logo, copy, or branded asset was reused; layout grammar may be matched when the user explicitly requests it.
- Label generated artwork as visual treatment internally; do not imply that it is an exact product screenshot.
- Confirm every real screenshot comes from the target product and reflects a supported capability.
- Confirm every visible product claim is source-backed or user-confirmed; pay special attention to API keys, pricing, privacy, offline operation, providers, and deployment.
- Confirm the dominant screenshot is the application's first/default screen unless the brief specifies another primary workflow.
- Confirm every collage screenshot is unique in page and state; exclude near-duplicate settings screens and repeated crops.
- Confirm screenshots show the complete application window. Do not crop product UI to force the reference aspect ratio; recapture at the target ratio instead.
- Check for API keys, tokens, email addresses, account identifiers, local file paths, personal data, and customer information.

## Asset handling

- For Product-proof split v1, confirm the repository contains the byte-identical bundled HTML template, a repository-specific `hero-data.js`, and `visual-manifest.json`.
- Confirm the first manifest screenshot is the primary/default interface and all screenshot entries use allowed real-capture provenance.
- Confirm every screenshot is 4:3, preferably 1200x900, and every Product-proof split hero is 2560x1280.
- Store README-bound assets in a repository-tracked directory such as `docs/images/`.
- Use stable, descriptive filenames and relative Markdown image paths.
- Check that each asset exists, is nonempty, and renders locally.
- Use concise, descriptive alt text that explains the screen or visual purpose.
- For multilingual repositories, use language-qualified hero filenames and verify that each README references the matching asset.
- When the product supports the locale, capture a separate full screenshot set in each README language; do not reuse another locale's UI captures under localized overlay copy.

## README integrity

- Confirm that only additions were made unless the user explicitly approved deletions or rewrites.
- Keep existing heading order, links, examples, tables, and diagrams intact.
- Keep language variants factually equivalent.
- Keep localized hero geometry and screenshot order identical unless the user explicitly requests culturally distinct art direction.
- Put the hero close to the download or install call to action and screenshots close to the workflow they substantiate.

## Final checks

- Confirm a GUI hero contains real target-product screenshots inside the hero itself; a separate screenshot section below an illustration is not a substitute.
- Inspect the hero and every screenshot at README display size for contrast, crop, distortion, and unreadable text.
- For an explicit reference match, compare left/right allocation, dominant screenshot position, screenshot count, overlap/rotation pattern, and text-block hierarchy.
- Confirm that a screenshot-led reference resulted in a screenshot-led final image with real target-product captures, not generated substitute UI.
- Confirm decorative shapes do not overlap screenshots, logos, labels, controls, or other content-sensitive regions.
- Confirm the original logo is used without an invented tile or frame unless that container is part of the existing brand system.
- If the reference uses equal-size screenshot frames, confirm one canonical rendered width and aspect ratio is applied to all frames; hierarchy must come from placement, overlap, off-canvas clipping, rotation, and z-order.
- Confirm no `object-fit: cover`, clip, mask, or manual crop removes interface content. If the source ratio differed, verify a new full-window capture was made at the target ratio.
- Inspect every language export separately for missing assets, black render blocks, overflow, unexpected wrapping, and layout drift.
- Confirm both the hero copy and the screenshot UI language match the destination README, including navigation, tabs, buttons, and settings labels.
- For one-to-one work, compare a 50% opacity or edge overlay at the reference's exact pixel dimensions.
- Confirm measured screenshot corners are within 8 px and rotations within 0.5 degrees of the geometry table unless a user-approved deviation is documented.
- Confirm asymmetric decorations point in the same direction as the reference; color and position alone do not pass.
- Run the Product-proof split manifest verifier and treat any canonical-template, provenance, completeness, uniqueness, dimension, locale, or README-mapping error as blocking.
- Run `git diff --check`.
- Review `git diff -- README*.md docs/images` and `git status --short` so unrelated files are not staged or reported as part of the deliverable.
