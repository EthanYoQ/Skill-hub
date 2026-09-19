<div align="center">

**English** | [中文](README.md)

</div>

# Skill-hub - AI Agent Skills for Codex & Claude Code

<p align="center">
  <img src="assets/README/skill-hub-hero.png" alt="A modular library of reusable AI agent skills" width="100%">
</p>

> Find, reuse, and maintain structured AI agent skills for Codex, Claude Code, Antigravity, and related AI coding tools.

**Start here:** [Browse every skill by name](./_meta/by-name.md) · [Explore by capability domain](./_meta/by-domain.md) · [Read the machine-readable index](./_meta/skills-lock.json) · [Check sources and maintenance boundaries](./_meta/skill-upstreams.json)

Skill-hub is a public Chinese-first AI Agent skill library for Codex, Claude Code, Antigravity, and related AI coding tools. It collects reusable `SKILL.md` automation practices, AI coding workflows, and prompt templates. The repository currently contains **60** reusable skills: **52** shared skills organized by capability domain and **8** project-specific skills archived by project for lookup, local sync, source tracking, and ongoing maintenance.

**Search intent:** Codex skills and Claude Code skills, Chinese AI Agent skill library, AI coding workflows, and prompt templates.

**Trust boundary:** this is a public open-source personal skill repository. It is not an official OpenAI, Anthropic, Claude Code, or Antigravity skill registry, and it is not a general-purpose prompt marketplace. Because the repository is public, use placeholders for credentials and do not commit real secrets, customer data, internal documents, or personal information.

**Start here:** [By Name](./_meta/by-name.md) | [By Domain](./_meta/by-domain.md) | [Machine-Readable Index](./_meta/skills-lock.json) | [Source Index](./_meta/skill-upstreams.json)

## <img src="assets/README/icons/map.svg" width="20" alt=""> Repository Positioning

Skill-hub is not just a prompt collection. It is a skill repository designed for agents. A skill usually contains trigger conditions, execution steps, constraints, references, or scripts so an AI coding assistant can reuse a stable workflow on similar tasks.

**Typical scenarios:** find reusable Agent skills, organize Codex / Claude Code workflows, turn project experience into `SKILL.md`, and maintain AI coding prompts and automation steps in one searchable repository.

| Position | What it means |
|---|---|
| <img src="assets/README/icons/overview.svg" width="20" alt=""> Personal knowledge base | Preserve workflows from Codex, Claude Code, Antigravity, and local projects as readable and syncable `SKILL.md` files. |
| <img src="assets/README/icons/categories.svg" width="20" alt=""> Skill directory | Organize skills by capability domain, technology stack, and project ownership so first-time readers can understand the coverage quickly. |
| <img src="assets/README/icons/index.svg" width="20" alt=""> Lookup entry points | Use the indexes under `_meta/` to find skills by name, domain, or technology stack. |
| <img src="assets/README/icons/source-index.svg" width="20" alt=""> Source tracking | Use `_meta/skill-upstreams.json` to record verified upstreams, avoiding name-based guesses during upgrades. |
| <img src="assets/README/icons/privacy.svg" width="20" alt=""> Public boundary | Every committed skill must be anonymized; real credentials and private data should stay in local environments only. |

## <img src="assets/README/icons/categories.svg" width="20" alt=""> Skill Categories

Shared skills live under `skills/`; project-specific skills live under `projects/`. The current categories come from `_meta/skills-lock.json` and `_meta/by-domain.md`.

| Category | Count | Directory | What to look for |
|---|---:|---|---|
| <img src="assets/README/icons/overview.svg" width="20" alt=""> Agent Engineering | 10 | `skills/01-agent-engineering/` | Agent building, debugging, autonomy loops, skill creation, GPT-6 Pro plan review, quality gates, skill lifecycle management, and Windows disk/project/memory maintenance. |
| <img src="assets/README/icons/format.svg" width="20" alt=""> Coding Languages | 1 | `skills/02-coding-languages/` | Language-level coding standards, design patterns, and testing conventions. |
| <img src="assets/README/icons/package.svg" width="20" alt=""> Frameworks and Stacks | 3 | `skills/03-frameworks/` | Frontend design, framework-level implementation patterns, and stack constraints. |
| <img src="assets/README/icons/index.svg" width="20" alt=""> Data and Search | 1 | `skills/06-data-search/` | Data scraping, search, deep research, PubMed, clinical trials, and report delivery. |
| <img src="assets/README/icons/format.svg" width="20" alt=""> Media and Content | 25 | `skills/07-media-content/` | PPT, PDF, DOCX, XLSX, images, video, GitHub README visuals, WeChat articles, and presentation content. |
| <img src="assets/README/icons/writing.svg" width="20" alt=""> Writing and Marketing | 5 | `skills/08-writing-marketing/` | Style imitation, marketing writing, GitHub SEO standards, and recurring evaluation. |
| <img src="assets/README/icons/source-index.svg" width="20" alt=""> Business and Industry | 7 | `skills/10-business-industry/` | Healthcare, legal, finance, market sizing, citation verification, pharma social listening, and industry report workflows. |
| <img src="assets/README/icons/directory.svg" width="20" alt=""> Project-Specific | 8 | `projects/` | Skills scoped to specific projects, such as email testing, Feishu, Alibaba Cloud, or invoice workflows. |

## <img src="assets/README/icons/directory.svg" width="20" alt=""> Directory Structure

```text
skills/                        # 52 shared skills, 7 capability domains
|-- 01-agent-engineering/      # Agent building, debugging, autonomy loops, harnesses
|-- 02-coding-languages/       # Programming languages
|-- 03-frameworks/             # Frameworks and technology stacks
|-- 06-data-search/            # Data scraping, search, deep research
|-- 07-media-content/          # PPT, video, PDF, documents, images
|-- 08-writing-marketing/      # Writing, style imitation, marketing
`-- 10-business-industry/      # Healthcare, legal, finance, market research, and other industry skills

projects/                      # 8 project-specific skills
_meta/                         # Chinese indexes, machine-readable mapping, source index
docs/                          # Directory conventions and privacy notes
scripts/                       # Junction setup, sync, and index rebuild scripts
assets/README/icons/           # Lucide SVG icons used by the README files
```

## <img src="assets/README/icons/index.svg" width="20" alt=""> Index Entry Points

If this is your first time reading the repository, start from the indexes instead of browsing every directory manually.

| Entry point | File | Best for |
|---|---|---|
| <img src="assets/README/icons/index.svg" width="20" alt=""> By Name | [`_meta/by-name.md`](./_meta/by-name.md) | You already know the skill name, such as `deep-research`, `gpt56-sol-pro-consult`, or `skill-creator`. |
| <img src="assets/README/icons/categories.svg" width="20" alt=""> By Domain | [`_meta/by-domain.md`](./_meta/by-domain.md) | You want to browse major categories such as agent engineering, data search, media content, or business workflows. |
| <img src="assets/README/icons/source-index.svg" width="20" alt=""> Machine-Readable Index | [`_meta/skills-lock.json`](./_meta/skills-lock.json) | Scripts, automation, and external tools that need skill names, paths, categories, and counts. |

## <img src="assets/README/icons/source-index.svg" width="20" alt=""> Source Index

[`_meta/skill-upstreams.json`](./_meta/skill-upstreams.json) is the source index for Skill-hub. It records verified open-source upstreams, candidate sources, local or project-specific provenance, upstream paths, last-check metadata, update policies, and status. For exact counts and classifications, treat the file's `verificationSummary`, `sources`, and related fields as the source of truth.

The source index answers three maintenance questions:

- Whether a skill is self-made, project-specific, an open-source mirror, or a locally mapped adaptation.
- Which skills can be compared with upstream automatically or semi-automatically when upstream changes.
- Which skills do not have enough evidence and must not be overwritten based only on a similar name.

Skills without an explicit source-index entry should not be treated as automatically replaceable upstream mirrors.

## <img src="assets/README/icons/format.svg" width="20" alt=""> Skill Format

Each skill is a directory whose core file is `SKILL.md`. Keep the frontmatter small so different agents can read it consistently.

```markdown
---
name: skill-name
description: One-line trigger condition: when should the agent use this skill.
---

# Body: instructions, references, examples
```

`description` should explain the trigger condition, not market the skill. See [`docs/directory-conventions.md`](./docs/directory-conventions.md) for naming rules.

## <img src="assets/README/icons/install.svg" width="20" alt=""> Installation and Local Setup

Regular users can clone the repository as a skill source, then point their local agent skill directories to the same source.

```powershell
git clone <this-repository-url> skill-hub
cd skill-hub
```

On Windows, Directory Junctions are commonly used so multiple agents can share one skill source instead of maintaining duplicate copies.

```powershell
# Preview
.\scripts\setup-junctions.ps1 -Source "D:\path\to\your\skills" -DryRun

# Execute
.\scripts\setup-junctions.ps1 -Source "D:\path\to\your\skills"
```

Different tools use different real skill directories. The script only creates local directory links; it does not configure remote accounts, secrets, or private services for you.

## <img src="assets/README/icons/sync.svg" width="20" alt=""> Sync Workflow

Local usage can keep skills in a flat directory, while the repository stores them by capability domain. The sync scripts translate between the two layouts.

| Operation | Script | Purpose |
|---|---|---|
| <img src="assets/README/icons/push.svg" width="20" alt=""> Push to repository | [`scripts/sync-push.ps1`](./scripts/sync-push.ps1) | Sync a local flat skill directory into the repository's grouped layout. |
| <img src="assets/README/icons/install.svg" width="20" alt=""> Pull to local | [`scripts/sync-pull.ps1`](./scripts/sync-pull.ps1) | Sync the repository's grouped layout back into a local flat skill directory. |
| <img src="assets/README/icons/index.svg" width="20" alt=""> Rebuild indexes | [`scripts/build-indexes.ps1`](./scripts/build-indexes.ps1) | Rebuild `_meta/` indexes from the repository's `SKILL.md` files. |
| <img src="assets/README/icons/upgrade.svg" width="20" alt=""> Audit upstreams | [`scripts/refresh-upstream-skills.ps1`](./scripts/refresh-upstream-skills.ps1) | Check every registered upstream, update only `mirror` entries, and report `mapped` drift for human merging. |

Before syncing, review `git status` and `git diff` so real credentials, temporary outputs, and private drafts do not enter the public repository.

## <img src="assets/README/icons/upgrade.svg" width="20" alt=""> Upgrade and Maintenance Workflow

When maintaining Skill-hub, upgrade from evidence rather than name matching.

1. Read [`_meta/skill-upstreams.json`](./_meta/skill-upstreams.json) and confirm whether the skill has a verified upstream.
2. Only compare upstreams automatically for entries with `classification=open-source` and `updatePolicy=mirror` or `updatePolicy=mapped`.
3. For `candidate`, `unknown`, self-made, and project-specific skills, gather evidence or do a manual review before changing content.
4. After upgrading, run [`scripts/build-indexes.ps1`](./scripts/build-indexes.ps1) so `_meta/` reflects the latest counts, paths, and descriptions.
5. Review skill content, index changes, and anonymization with `git diff` before committing.

The repository includes [`skills/01-agent-engineering/skill-lifecycle-manager/`](./skills/01-agent-engineering/skill-lifecycle-manager/), a cross-runtime workflow for skill search, installation, upgrades, sync, source verification, and quality audits across Codex, Claude Code, Skill Hub, personal/project installs, and managed Claude Code plugin caches.

The cloud [`refresh-upstream-skills.yml`](./.github/workflows/refresh-upstream-skills.yml) runs every Monday and can also be dispatched manually. It opens or refreshes a pull request only for verified `classification=open-source`, `updatePolicy=mirror` full-tree changes. `mapped`, `candidate`, `self`, and `local` entries are never overwritten automatically, preserving a human review gate for external Skill instructions.

## <img src="assets/README/icons/maintenance.svg" width="20" alt=""> Maintenance Conventions

- Add shared skills under the right `skills/<domain>/` directory and keep directory names in kebab-case.
- Add project-specific skills under `projects/<project-name>/`, not under shared skill domains.
- After editing skill descriptions, rebuild indexes so `by-name`, `by-domain`, and the machine-readable index stay aligned.
- When changing upstream source judgments, require evidence; do not write an unverified similar repository as a confirmed source.
- Do not revert other people's worktree changes; before committing, keep the scope to README files, icons, or explicitly authorized files.
- Boundary with private repository: Maintain a clear separation with [Skill-hub-private](https://github.com/EthanYoQ/Skill-hub-private). Published shared skills (including `media-use`, `skill-lifecycle-manager`, `xhs-pharma-social-listening`, `yq-article-style-imitation`, and `yq-editorial-presentation-html`) are authoritatively maintained in this public repository; corresponding duplicate archives in the private backup repository have been synchronized and purged to avoid drift.

## <img src="assets/README/icons/privacy.svg" width="20" alt=""> Privacy Boundary

This repository is public. Every skill should be anonymized before being committed. See [`docs/privacy-audit.md`](./docs/privacy-audit.md) for the detailed rules.

| Content type | Repository requirement |
|---|---|
| <img src="assets/README/icons/privacy.svg" width="20" alt=""> API keys, tokens, secrets, authorization codes | Replace with placeholders such as `<YOUR_*_TOKEN>` or `<YOUR_*_KEY>`. |
| <img src="assets/README/icons/privacy.svg" width="20" alt=""> Email addresses, phone numbers, personal names | Replace with example emails, `<your-phone>`, `用户`, or `Anon`. |
| <img src="assets/README/icons/privacy.svg" width="20" alt=""> Local user directories | Rewrite as `%USERPROFILE%` or `~`. |
| <img src="assets/README/icons/privacy.svg" width="20" alt=""> Internal tool names, customer names, project code names | Rewrite as generic descriptions unless the names are already public. |
| <img src="assets/README/icons/privacy.svg" width="20" alt=""> Signed URLs, real logs, production data | Do not commit them; if leaked, rotate credentials first, then clean the worktree and history. |

When using skills from this repository, fill in your credentials locally. Do not commit files containing real credentials back to the public repository.

## <img src="assets/README/icons/overview.svg" width="20" alt=""> License

This repository is fully open source under the [MIT License](./LICENSE). Third-party open-source skills keep their original upstream license terms when a source license or notice is present.
