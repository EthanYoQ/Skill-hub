# Netlify CLI Skill Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Publish a private, extensible `agent-skills` repository containing the first team-managed Netlify CLI Skill.

**Architecture:** The repository root is a discovery index. `netlify-cli/` is a self-contained Skill package whose `SKILL.md` is the sole Agent rule file; human documentation and binary references are separated into its README and `docs/` directory. Future Skills are peer directories and do not depend on the Netlify package.

**Tech Stack:** Git, GitHub CLI, Markdown, PDF reference documents.

## Global Constraints

- Repository: `Singularity-AI-Gamer/agent-skills`, private, branch `main`.
- Preserve the existing Netlify rule content in `netlify-cli/SKILL.md` without adding another Agent instruction file.
- Copy the supplied PDFs byte-for-byte to `netlify-cli/docs/beginner-guide.pdf` and `netlify-cli/docs/full-guide.pdf`.
- Keep `examples/` and `assets/` in Git with `.gitkeep` until they contain real assets.
- Do not add credentials, tokens, or deployment state to the repository.

---

### Task 1: Scaffold the Skill package and root index

**Files:**
- Create: `README.md`
- Create: `netlify-cli/README.md`
- Create: `netlify-cli/CHANGELOG.md`
- Create: `netlify-cli/examples/.gitkeep`
- Create: `netlify-cli/assets/.gitkeep`

**Interfaces:**
- Consumes: the approved repository design at `docs/superpowers/specs/2026-07-15-agent-skills-design.md`.
- Produces: a discoverable root index and a self-contained Netlify CLI package.

- [ ] **Step 1: Create the required directories and placeholder files**

Run:

```bash
mkdir -p netlify-cli/{docs,examples,assets}
touch netlify-cli/examples/.gitkeep netlify-cli/assets/.gitkeep
```

- [ ] **Step 2: Create the root README**

Write `README.md` with: repository purpose; the rule that every Skill is a top-level directory; a table indexing `netlify-cli`; and an extension checklist requiring `README.md`, `SKILL.md`, `docs/`, `examples/`, `assets/`, and `CHANGELOG.md` for every future Skill.

- [ ] **Step 3: Create the Netlify CLI README and changelog**

Write `netlify-cli/README.md` with purpose, applicable scenarios, a fast-start sequence (`netlify login`, `netlify status`, `netlify deploy --dir=dist`, `netlify deploy --prod`), its directory tree, and the two-document index. Write `netlify-cli/CHANGELOG.md` with `## [0.1.0] - 2026-07-15` and the initial package contents.

- [ ] **Step 4: Validate the human-facing package files**

Run:

```bash
test -f README.md
test -f netlify-cli/README.md
test -f netlify-cli/CHANGELOG.md
test -f netlify-cli/examples/.gitkeep
test -f netlify-cli/assets/.gitkeep
```

Expected: all commands exit `0`.

- [ ] **Step 5: Commit the package scaffolding**

```bash
git add README.md netlify-cli
git commit -m "docs: scaffold netlify cli skill"
```

### Task 2: Add the Agent rule and PDF references

**Files:**
- Create: `netlify-cli/SKILL.md`
- Create: `netlify-cli/docs/beginner-guide.pdf`
- Create: `netlify-cli/docs/full-guide.pdf`

**Interfaces:**
- Consumes: `/Users/clover/.codex/plugins/cache/openai-curated-remote/netlify/1.0.0/skills/netlify-cli-and-deploy/SKILL.md` and the two supplied PDFs.
- Produces: the Agent rule and stable documentation references used by `netlify-cli/README.md`.

- [ ] **Step 1: Copy the current rule and PDFs**

Run:

```bash
cp /Users/clover/.codex/plugins/cache/openai-curated-remote/netlify/1.0.0/skills/netlify-cli-and-deploy/SKILL.md netlify-cli/SKILL.md
cp /Users/clover/Downloads/用SKILL让Agent发布HTML到Netlify_新手简明版_Clover陈.pdf netlify-cli/docs/beginner-guide.pdf
cp /Users/clover/Downloads/Netlify\ CLI全流程部署指南_Clover陈.pdf netlify-cli/docs/full-guide.pdf
```

- [ ] **Step 2: Verify file identity and the rule-file boundary**

Run:

```bash
shasum -a 256 netlify-cli/docs/beginner-guide.pdf netlify-cli/docs/full-guide.pdf
find netlify-cli -name 'SKILL.md' -type f | wc -l
```

Expected: the PDF hashes are `5e946525f762777d78b1c3802cd1738a8cb756cf9a465712f20d97125ac22222` and `f4058d81b77c4c2f43cd93473ead3161f48539adfa0a8c19f11ab0d0fbe205b1`; the rule-file count is `1`.

- [ ] **Step 3: Commit the source material**

```bash
git add netlify-cli/SKILL.md netlify-cli/docs
git commit -m "feat: add netlify cli skill resources"
```

### Task 3: Validate and publish the initial release

**Files:**
- Verify: `README.md`
- Verify: `netlify-cli/`

**Interfaces:**
- Consumes: the commits from Tasks 1 and 2.
- Produces: a verified `main` branch and GitHub tree for the team.

- [ ] **Step 1: Run the repository contract check**

Run:

```bash
for path in README.md netlify-cli/README.md netlify-cli/SKILL.md netlify-cli/docs/beginner-guide.pdf netlify-cli/docs/full-guide.pdf netlify-cli/examples/.gitkeep netlify-cli/assets/.gitkeep netlify-cli/CHANGELOG.md; do test -e "$path" || exit 1; done
test "$(find netlify-cli -name SKILL.md -type f | wc -l | tr -d ' ')" = 1
git status --short
```

Expected: every required path exists, exactly one `SKILL.md` is found under `netlify-cli`, and the working tree is clean after commits.

- [ ] **Step 2: Push `main`**

```bash
git push origin main
```

Expected: the remote advances successfully.

- [ ] **Step 3: Verify the published GitHub contents**

Run:

```bash
gh api repos/Singularity-AI-Gamer/agent-skills/contents --jq '.[].name'
gh api repos/Singularity-AI-Gamer/agent-skills/contents/netlify-cli --jq '.[].name'
```

Expected: the root includes `README.md` and `netlify-cli`; the Skill directory includes `README.md`, `SKILL.md`, `docs`, `examples`, `assets`, and `CHANGELOG.md`.

- [ ] **Step 4: Commit the plan**

```bash
git add docs/superpowers/plans/2026-07-15-netlify-cli-skill.md
git commit -m "docs: add netlify cli skill implementation plan"
git push origin main
```
