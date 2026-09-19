<div align="center">

[English](README.md) | **中文**

</div>

# Skill-hub - AI 提示词与 Agent 技能库

Skill-hub 是一个公开的 AI 提示词、Agent 技能和 `SKILL.md` 工作流仓库，面向需要沉淀 Codex、Claude Code、Antigravity 等 AI 编程工具用法的个人开发者；当前包含 **59** 个可复用技能，按能力域、技术栈和项目私有技能组织，便于检索、本地同步与复用。

**搜索意图：** 适合正在找 AI 提示词/提示词库、AI Agent 技能库、Codex/Claude Code 自动化工作流的人。

**快速入口：** [按名字查](./_meta/by-name.md) · [按能力域查](./_meta/by-domain.md) · [按技术栈查](./_meta/by-platform.md) · [机器可读索引](./_meta/skills-lock.json) · [本地设置](#本地设置使用者自配)

**边界说明：** 这是个人展示与学习仓库，不是 OpenAI、Anthropic、Claude Code 或 Antigravity 官方技能库，也不是通用提示词市场。仓库公开，请只使用占位符填写凭据，不要提交真实密钥或隐私数据。

## 仓库定位

- **备份与单一源**：线上备份，丢失时可从这里拉回。
- **便于查找**：提供三种检索入口（字母 / 能力域 / 技术栈），帮你快速确认某个技能是否已经沉淀，还是需要新建。
- **共享 + 项目私有并存**：通用技能位于 `skills/`；仅对某个具体仓库生效的私有技能位于 `projects/`。

## 目录结构

```
skills/                        # 50 个共享技能，分 7 个能力域
├── 01-agent-engineering/      Agent 工程（构建、调试、自治循环、harness 等）
├── 02-coding-languages/       编程语言（Swift + 通用）
├── 03-frameworks/             框架栈（前端设计等）
├── 06-data-search/            数据抓取、检索、深度研究
├── 07-media-content/          多媒体（PPT、视频、PDF、图像）
├── 08-writing-marketing/      写作、风格仿写与营销
└── 10-business-industry/      行业业务（医疗、法律、金融等）

projects/                      # 9 个项目私有技能
_meta/                         # 中文索引入口
docs/                          # 约定文档
scripts/                       # 同步与 Junction 建立脚本
```

## 如何查找技能

按你关心的维度选一个入口：

| 入口 | 适合场景 |
|---|---|
| [按名字查](./_meta/by-name.md) | 已经知道技能名（如 `deep-research`） |
| [按能力域查](./_meta/by-domain.md) | 想找 "Agent 工程" / "测试" / "行业业务" 一类 |
| [按技术栈查](./_meta/by-platform.md) | 想找 "Python 相关" / "浏览器自动化" 一类 |
| [机器可读](./_meta/skills-lock.json) | 脚本、自动化、外部工具集成 |

## 技能格式

每个技能是一个目录 + 内含 `SKILL.md`，YAML frontmatter 如下：

```markdown
---
name: skill-name
description: 一句话触发条件：什么场景下 Agent 应该使用这个技能。
---

# 正文：指令、参考、示例
```

同一套 frontmatter 可被多个 AI Agent 通用。

## 本地设置（使用者自配）

多个 Agent 的 skills 目录路径各不相同，本地常用 Windows Directory Junction 指向同一份源，避免多份副本。

脚本：[`scripts/setup-junctions.ps1`](./scripts/setup-junctions.ps1)

```powershell
# 预览
.\scripts\setup-junctions.ps1 -Source "D:\path\to\your\skills" -DryRun

# 执行
.\scripts\setup-junctions.ps1 -Source "D:\path\to\your\skills"
```

## 同步机制

本地习惯扁平结构，仓库按能力域分层。两个脚本双向同步：

- [`scripts/sync-push.ps1`](./scripts/sync-push.ps1)：本地扁平 → 仓库分组
- [`scripts/sync-pull.ps1`](./scripts/sync-pull.ps1)：仓库分组 → 本地扁平
- [`scripts/build-indexes.ps1`](./scripts/build-indexes.ps1)：重建 `_meta/` 下的索引

映射关系来自 [`_meta/skills-lock.json`](./_meta/skills-lock.json)。

## 分类与命名约定

见 [`docs/directory-conventions.md`](./docs/directory-conventions.md)。

## 隐私与脱敏

仓库公开，所有技能在纳入仓库前都做过脱敏扫描：

- 邮箱、手机号 → 占位符
- API Key / Token / Secret → 占位符
- 本地用户目录 → `%USERPROFILE%` 或 `~`
- 私有工具 / 服务名 → 通用描述

详见 [`docs/privacy-audit.md`](./docs/privacy-audit.md)。

**使用他人技能时，请按 `<YOUR_*>` / `<your-*>` 占位符填入自己的凭据；请勿将填入真实凭据的文件再提交回仓库。**

## 许可

仅用于个人展示与学习，默认不接受外部 PR。
