# Agent Skills Repository Design

## Goal

Create one private, team-maintained repository for reusable Agent Skills. Each
Skill is an independent top-level directory; no Skill receives its own
repository.

## Repository Architecture

- `README.md` is the repository entry point. It explains the shared directory
  contract and links to each available Skill.
- Each top-level Skill directory owns its content and evolves independently.
- `SKILL.md` is the only instruction file read by an Agent for that Skill.
- Human-oriented guides belong in the Skill's `README.md` and `docs/`.
- `examples/` contains prompt or sample-project material. `assets/` contains
  non-rule visual resources. Empty folders receive `.gitkeep` until populated.

## Initial Skill: `netlify-cli`

The initial directory is:

```text
netlify-cli/
├── README.md
├── SKILL.md
├── docs/
│   ├── beginner-guide.pdf
│   └── full-guide.pdf
├── examples/
├── assets/
└── CHANGELOG.md
```

`SKILL.md` is sourced from the existing Netlify CLI and Deploy Skill, so the
team starts with the established deployment workflow. The two supplied PDF
guides are retained as reference documents under `docs/` using stable English
filenames.

## Extension Model

Future Skills are added as peer directories, for example `github-cli/`,
`docker/`, `caddy/`, `ppt/`, and `design/`. Adding a Skill must not require
editing other Skill rule files; only the root index and the new Skill's own
directory need updates.

## Validation

The initial release will verify the required directories and files, confirm
that only `netlify-cli/SKILL.md` is an Agent rule file, verify both PDFs by
SHA-256 after copying, and check the published GitHub tree.
