<div align="center">

**English** | [中文](README_zh.md)

</div>

# Skill-hub - AI 提示词与 Agent 技能库 / AI Agent Skill Library

Skill-hub 是一个公开的 AI 提示词、Agent 技能和 `SKILL.md` 工作流仓库，面向需要沉淀 Codex、Claude Code、Antigravity 等 AI 编程工具用法的个人开发者；当前包含 **59** 个可复用技能，按能力域、技术栈和项目私有技能组织，便于检索、本地同步与复用。

**Search intent:** for users searching for AI 提示词/提示词库, AI Agent 技能库, and Codex/Claude Code 自动化工作流.

English: a public AI Agent skill library with reusable `SKILL.md` workflows for Codex, Claude Code, Antigravity, agent engineering, AI coding, data search, media generation, writing, and business-domain automation.

**Start here:** [By Name](./_meta/by-name.md) · [By Domain](./_meta/by-domain.md) · [By Tech Stack](./_meta/by-platform.md) · [Machine-Readable Index](./_meta/skills-lock.json) · [Local Setup](#local-setup-user-configured)

**Boundary:** This is a personal showcase and learning repository, not an official OpenAI, Anthropic, Claude Code, or Antigravity skill registry. It is not a universal prompt marketplace. Because the repository is public, use placeholders for credentials and do not commit real secrets.

## Purpose

- **Backup and single source of truth**: Backed up online; if lost, you can pull it back from here.
- **Easy to find**: Three lookup entry points (alphabetical / domain / tech stack) to help you quickly determine whether a skill has already been captured or needs to be created.
- **Shared + project-specific coexistence**: General-purpose skills live in `skills/`; private skills scoped to a specific repository live in `projects/`.

## Directory Structure

```
skills/                        # 50 shared skills across 7 domains
├── 01-agent-engineering/      Agent engineering (building, debugging, autonomy loops, harness, etc.)
├── 02-coding-languages/       Programming languages (Swift + general)
├── 03-frameworks/             Framework stacks (frontend design, etc.)
├── 06-data-search/            Data scraping, retrieval, deep research
├── 07-media-content/          Multimedia (PPT, video, PDF, images)
├── 08-writing-marketing/      Writing, style imitation, and marketing
└── 10-business-industry/      Industry-specific (healthcare, legal, finance, etc.)

projects/                      # 9 project-specific skills
_meta/                         # Index entry points (Chinese)
docs/                          # Conventions documentation
scripts/                       # Sync and junction setup scripts
```

## How to Find Skills

Choose an entry point based on the dimension you care about:

| Entry Point | Best For |
|---|---|
| [By Name](./_meta/by-name.md) | You already know the skill name (e.g., `deep-research`) |
| [By Domain](./_meta/by-domain.md) | You want to browse categories like "Agent Engineering" / "Testing" / "Industry" |
| [By Tech Stack](./_meta/by-platform.md) | You want to find "Python-related" / "Browser Automation" skills |
| [Machine-Readable](./_meta/skills-lock.json) | Scripts, automation, external tool integration |

## Skill Format

Each skill is a directory containing a `SKILL.md` file with the following YAML frontmatter:

```markdown
---
name: skill-name
description: One-line trigger condition: when should the agent use this skill.
---

# Body: instructions, references, examples
```

The same frontmatter format works across multiple AI agents.

## Local Setup (User-Configured)

Different agents use different skills directory paths. On Windows, Directory Junctions are commonly used locally to point to a single source, avoiding duplicate copies.

Script: [`scripts/setup-junctions.ps1`](./scripts/setup-junctions.ps1)

```powershell
# Preview
.\scripts\setup-junctions.ps1 -Source "D:\path\to\your\skills" -DryRun

# Execute
.\scripts\setup-junctions.ps1 -Source "D:\path\to\your\skills"
```

## Sync Mechanism

Locally, a flat structure is preferred; the repository is organized by domain. Two scripts handle bidirectional sync:

- [`scripts/sync-push.ps1`](./scripts/sync-push.ps1): Local flat structure → Repository grouped structure
- [`scripts/sync-pull.ps1`](./scripts/sync-pull.ps1): Repository grouped structure → Local flat structure
- [`scripts/build-indexes.ps1`](./scripts/build-indexes.ps1): Rebuild indexes under `_meta/`

The mapping relationship comes from [`_meta/skills-lock.json`](./_meta/skills-lock.json).

## Naming and Directory Conventions

See [`docs/directory-conventions.md`](./docs/directory-conventions.md).

## Privacy and Anonymization

This repository is public. All skills undergo an anonymization scan before being added:

- Email addresses, phone numbers → Placeholders
- API keys / tokens / secrets → Placeholders
- Local user directories → `%USERPROFILE%` or `~`
- Private tools / service names → Generic descriptions

See [`docs/privacy-audit.md`](./docs/privacy-audit.md) for details.

**When using someone else's skill, fill in your own credentials using the `<YOUR_*>` / `<your-*>` placeholders; do not commit files with real credentials back to the repository.**

## License

For personal showcase and learning only. External PRs are not accepted by default.
