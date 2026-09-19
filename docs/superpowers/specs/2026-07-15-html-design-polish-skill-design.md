# HTML Design Polish Skill Design

## Goal

Add the supplied HTML visual-polish Skill to the shared `agent-skills`
repository as an independently maintained package.

## Package Boundary

The package directory is `html-design-polish/`, matching the `name` declared
by the supplied Skill. Its `SKILL.md` is copied unchanged and remains the only
Agent rule file for this package.

## Contents

```text
html-design-polish/
├── README.md
├── SKILL.md
├── assets/
│   ├── clovernas-navigation-reference.png
│   ├── innovation-navigation-reference.png
│   └── xacduro-navigation-reference.png
├── examples/
└── CHANGELOG.md
```

The three supplied images are visual reference material only. They document
the intended use of hierarchy, card composition, contrast, and material; they
are not templates to copy pixel-for-pixel. `examples/` is retained with a
placeholder so future teams can add reusable prompts or before/after examples.

## Repository Integration

The root README gains one index row linking to the new package. The package
README explains the purpose, appropriate use cases, quick invocation, package
structure, and the role of the reference images. The changelog starts at
version `0.1.0`.

## Validation

Verify every required path exists, compare the package `SKILL.md` byte-for-byte
with the supplied source, verify the three asset files with SHA-256, confirm
there is exactly one `SKILL.md` beneath the package, and verify the published
GitHub tree.
