# UI/UX Design Skills Import Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Import three pinned upstream UI/UX skills into the shared skill hub, record provenance, rebuild every index, and publish the change through the canonical repository.

**Architecture:** Vendor each complete upstream skill directory under `skills/07-media-content/`, copy its repository license into the vendored directory, and leave upstream content otherwise unchanged. Track repository URL, source path, ref, and commit in `_meta/skill-upstreams.json`; derive machine and human indexes with the repository scripts.

**Tech Stack:** Git/GitHub CLI, PowerShell, Python, Node.js, Markdown/YAML/JSON.

## Global Constraints

- `EthanYoQ/Skill-hub:mine` is the canonical source; `Singularity-AI-Gamer/agent-skills:main` is an automated mirror and must not be edited directly.
- Pin UI/UX Pro Max to `f8ac5e1266dba8354ea96e19994d9f4345e7ec31` (MIT).
- Pin Impeccable to `8259c28209b92792005cec14dad573df39f68eaf` (Apache-2.0).
- Pin Make Interfaces Feel Better to `366f0f86efcb2811c26e2cf386d09cf2ddc35fcb` (MIT).
- Preserve complete upstream skill directories and do not add the new paths to `.github/org-exclude.txt`.
- Do not commit secrets, temporary clones, generated caches, or unrelated changes.

---

### Task 1: Import UI/UX Pro Max

**Files:**
- Create: `skills/07-media-content/ui-ux-pro-max/**`
- Source: `.claude/skills/ui-ux-pro-max/**` from `nextlevelbuilder/ui-ux-pro-max-skill`

- [ ] Verify the target directory and index entry are absent; the baseline check must fail.
- [ ] Copy the complete pinned source directory and root `LICENSE` as `LICENSE.txt`.
- [ ] Run the repository skill validator.
- [ ] Run the bundled Python tests and data validator.
- [ ] Review only this skill before moving to Task 2.

### Task 2: Import Impeccable

**Files:**
- Create: `skills/07-media-content/impeccable/**`
- Source: `.agents/skills/impeccable/**` from `pbakaus/impeccable`

- [ ] Verify the target directory and index entry are absent; the baseline check must fail.
- [ ] Copy the complete Codex-oriented pinned source directory and root `LICENSE` as `LICENSE.txt`.
- [ ] Run the repository skill validator.
- [ ] Syntax-check all bundled JavaScript modules and run `scripts/context.mjs` from the repository root.
- [ ] Review only this skill before moving to Task 3.

### Task 3: Import Make Interfaces Feel Better

**Files:**
- Create: `skills/07-media-content/make-interfaces-feel-better/**`
- Source: `skills/make-interfaces-feel-better/**` from `jakubkrehel/make-interfaces-feel-better`

- [ ] Verify the target directory and index entry are absent; the baseline check must fail.
- [ ] Copy the complete pinned source directory and root `LICENSE` as `LICENSE.txt`.
- [ ] Run the repository skill validator.
- [ ] Verify every local Markdown reference resolves to a copied file.
- [ ] Review only this skill before moving to metadata.

### Task 4: Record Provenance and Rebuild Indexes

**Files:**
- Modify: `_meta/skill-upstreams.json`
- Modify: `_meta/skills-lock.json`
- Modify: `_meta/by-name.md`
- Modify: `_meta/by-domain.md`
- Modify: `README.md`
- Modify: `README_EN.md`
- Modify: `README.en.md`
- Modify: `_meta/README.md`

- [ ] Add open-source mirror entries with exact repository, path, ref, commit, license, and verification evidence.
- [ ] Run `scripts/build-indexes.ps1 -DryRun`, then rebuild indexes.
- [ ] Replace generated placeholder descriptions with concise Chinese descriptions and remove `_todo` markers.
- [ ] Rebuild again to prove the manual descriptions are preserved.
- [ ] Run `scripts/update-readme-counts.py` and confirm counts are consistent.

### Task 5: Verify and Publish

**Files:**
- Review: all changed files

- [ ] Confirm all three directories contain `SKILL.md`, support files, and `LICENSE.txt`.
- [ ] Scan changed files for secrets, local user paths, and temporary artifacts.
- [ ] Run full index regeneration and verify a clean second run.
- [ ] Inspect `git diff`, stage only intended files, and commit tersely.
- [ ] Push the feature branch to `lubiny0601-spec/Skill-hub`.
- [ ] Open a draft PR against `EthanYoQ/Skill-hub:mine`; after merge, verify the mirror workflow updates `Singularity-AI-Gamer/agent-skills:main`.
