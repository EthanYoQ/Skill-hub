



# Skill-hub - Codex / Claude Code 中文 Agent 技能库

<p align="center">
  <img src="assets/README/skill-hub-hero.png" alt="由模块化技能卡片构成的 AI Agent 技能库视觉图" width="100%">
</p>


<div align="center">
  
[English](README_EN.md) | **中文**

</div>

> 为 Codex、Claude Code、Antigravity 等 AI 编程工具查找、复用与维护结构化 Agent 技能。

**从这里开始：** [按名字浏览全部技能](./_meta/by-name.md) · [按能力域探索](./_meta/by-domain.md) · [查看机器可读索引](./_meta/skills-lock.json) · [了解来源与维护边界](./_meta/skill-upstreams.json) · [浏览完整外部工作流包](./docs/external-workflow-packs.md)

Skill-hub 是一个面向 Codex、Claude Code、Antigravity 等 AI 编程工具的中文 Agent 技能库，收集可复用的 `SKILL.md` 自动化实践、AI 编程工作流和提示词模板。仓库当前包含 **60** 个可复用技能，其中 **52** 个共享技能按能力域组织，**8** 个项目私有技能按项目归档，便于检索、本地同步、来源追踪和持续维护。

**适合搜索：** Codex 技能与 Claude Code 技能、中文 Agent 技能库、AI 编程工作流与提示词模板。

**信任边界：** 这是公开开源的个人 Skill 仓库，不是 OpenAI、Anthropic、Claude Code 或 Antigravity 官方技能库，也不是通用提示词市场。仓库公开，请只使用占位符填写凭据，不要提交真实密钥、客户数据、内部资料或个人隐私。

**快速入口：** [按名字查](./_meta/by-name.md) | [按能力域查](./_meta/by-domain.md) | [机器可读索引](./_meta/skills-lock.json) | [来源索引](./_meta/skill-upstreams.json) | [完整外部工作流包](./docs/external-workflow-packs.md)

## <img src="assets/README/icons/map.svg" width="20" alt=""> 仓库定位

Skill-hub 不是单一提示词合集，而是面向 Agent 使用的技能仓库。每个技能通常包含触发条件、执行步骤、约束、参考资料或脚本，让 AI 编程助手能在相似任务中复用稳定流程。

**典型场景：** 查找可复用的 Agent 技能，整理自己的 Codex / Claude Code 工作流，把项目经验沉淀成 `SKILL.md`，为 AI 编程任务建立可复用的提示词和自动化步骤。

| 定位 | 说明 |
|---|---|
| <img src="assets/README/icons/overview.svg" width="20" alt=""> 个人知识库 | 把分散在 Codex、Claude Code、Antigravity 和本地项目里的工作流沉淀成可读、可同步的 `SKILL.md`。 |
| <img src="assets/README/icons/categories.svg" width="20" alt=""> 技能目录 | 用能力域、技术栈和项目归属组织技能，方便第一次读到的人快速判断仓库覆盖范围。 |
| <img src="assets/README/icons/index.svg" width="20" alt=""> 检索入口 | 通过 `_meta/` 下的索引按名称、能力域或技术栈查找技能。 |
| <img src="assets/README/icons/source-index.svg" width="20" alt=""> 来源追踪 | 用 `_meta/skill-upstreams.json` 记录已验证上游，避免升级时只凭技能名猜测来源。 |
| <img src="assets/README/icons/privacy.svg" width="20" alt=""> 公开边界 | 所有入库技能必须脱敏；真实凭据和私有数据只应保留在本地环境。 |

## <img src="assets/README/icons/categories.svg" width="20" alt=""> 技能种类

共享技能位于 `skills/`，项目私有技能位于 `projects/`。当前分类来自 `_meta/skills-lock.json` 和 `_meta/by-domain.md`。

| 类别 | 数量 | 目录 | 适合查什么 |
|---|---:|---|---|
| <img src="assets/README/icons/overview.svg" width="20" alt=""> Agent 工程 | 10 | `skills/01-agent-engineering/` | Agent 构建、调试、自治循环、技能创建、GPT-6 Pro 方案审查、质量门、skill 生命周期，以及 Windows 磁盘/项目垃圾与内存健康维护。 |
| <img src="assets/README/icons/format.svg" width="20" alt=""> 编程语言 | 1 | `skills/02-coding-languages/` | 语言级编码标准、设计模式和测试规范。 |
| <img src="assets/README/icons/package.svg" width="20" alt=""> 框架与技术栈 | 3 | `skills/03-frameworks/` | 前端设计、框架级实现模式和技术栈约束。 |
| <img src="assets/README/icons/index.svg" width="20" alt=""> 数据与检索 | 1 | `skills/06-data-search/` | 数据抓取、搜索、深度研究、PubMed、临床试验和报告交付。 |
| <img src="assets/README/icons/format.svg" width="20" alt=""> 媒体与内容制作 | 25 | `skills/07-media-content/` | PPT、PDF、DOCX、XLSX、图像、视频、GitHub README 视觉、公众号文章和演示内容。 |
| <img src="assets/README/icons/writing.svg" width="20" alt=""> 写作与营销 | 5 | `skills/08-writing-marketing/` | 风格仿写、营销写作、GitHub SEO 标准与周期评估。 |
| <img src="assets/README/icons/source-index.svg" width="20" alt=""> 行业与业务 | 7 | `skills/10-business-industry/` | 医疗、法律、金融、市场规模、引用校验、药企舆情研究和行业报告流程。 |
| <img src="assets/README/icons/directory.svg" width="20" alt=""> 项目私有 | 8 | `projects/` | 只对特定项目生效的技能，例如邮箱测试、飞书、阿里云或发票项目流程。 |

## <img src="assets/README/icons/directory.svg" width="20" alt=""> 目录结构

```text
skills/                        # 52 个共享技能，分 7 个能力域
|-- 01-agent-engineering/      # Agent 构建、调试、自治循环、harness
|-- 02-coding-languages/       # 编程语言
|-- 03-frameworks/             # 框架与技术栈
|-- 06-data-search/            # 数据抓取、检索、深度研究
|-- 07-media-content/          # PPT、视频、PDF、文档、图像
|-- 08-writing-marketing/      # 写作、风格仿写、营销
`-- 10-business-industry/      # 医疗、法律、金融、市场研究等行业技能

projects/                      # 8 个项目私有技能
_meta/                         # 中文索引、机器可读映射、来源索引
docs/                          # 目录约定与隐私脱敏说明
scripts/                       # Junction 建立、同步、索引重建脚本
assets/README/icons/           # README 使用的 Lucide SVG 图标
```

## <img src="assets/README/icons/index.svg" width="20" alt=""> 索引入口

第一次阅读时，建议先从索引入口开始，而不是直接浏览所有目录。

| 入口 | 文件 | 适合场景 |
|---|---|---|
| <img src="assets/README/icons/index.svg" width="20" alt=""> 按名字查 | [`_meta/by-name.md`](./_meta/by-name.md) | 已经知道技能名，例如 `deep-research`、`gpt56-sol-pro-consult` 或 `skill-creator`。 |
| <img src="assets/README/icons/categories.svg" width="20" alt=""> 按能力域查 | [`_meta/by-domain.md`](./_meta/by-domain.md) | 想浏览 Agent 工程、数据检索、媒体内容、行业业务等大类。 |
| <img src="assets/README/icons/source-index.svg" width="20" alt=""> 机器可读索引 | [`_meta/skills-lock.json`](./_meta/skills-lock.json) | 给脚本、自动化、外部工具读取技能清单、路径、分类和数量。 |
| <img src="assets/README/icons/package.svg" width="20" alt=""> 完整外部工作流包 | [`docs/external-workflow-packs.md`](./docs/external-workflow-packs.md) | 使用保留原始结构和入口的第三方工作流包；不将其拆入本仓库技能索引。 |

## <img src="assets/README/icons/source-index.svg" width="20" alt=""> 来源索引

[`_meta/skill-upstreams.json`](./_meta/skill-upstreams.json) 是 Skill-hub 的来源索引。它记录已验证的开源上游、候选来源、本地或项目私有来源、上游路径、最近检查信息、升级策略和状态。具体数量和分类摘要以该文件中的 `verificationSummary`、`sources` 和相关字段为准。

来源索引用来回答三个维护问题：

- 这个技能是自制、项目私有、开源镜像，还是经过本地映射改造。
- 如果上游更新，哪些技能允许自动或半自动比对升级。
- 哪些技能证据不足，不能仅凭名称覆盖本地版本。

未在来源索引中明确标注的技能，不应被当作可自动覆盖的上游镜像。

## <img src="assets/README/icons/package.svg" width="20" alt=""> 完整外部工作流包

有些第三方仓库不是独立技能的松散集合，而是有根级入口、配置步骤、分组顺序或插件定义的完整工作流包。它们保留在独立的组织 fork 中，并在 [`_meta/external-workflow-packs.json`](./_meta/external-workflow-packs.json) 中以包级来源、固定版本和安装方式登记；不会被拆分写入 `skills-lock.json` 或共享技能同步流程。

首个登记包是 [mattpocock/skills 的组织 fork](https://github.com/Singularity-AI-Gamer/skills)。详情与维护规则见 [`docs/external-workflow-packs.md`](./docs/external-workflow-packs.md)。

## <img src="assets/README/icons/format.svg" width="20" alt=""> 技能格式

每个技能是一个目录，核心文件是 `SKILL.md`。推荐 frontmatter 保持简洁，便于不同 Agent 读取。

```markdown
---
name: skill-name
description: 一句话触发条件：什么场景下 Agent 应该使用这个技能。
---

# 正文：指令、参考、示例
```

`description` 应该描述触发条件，而不是营销话术。详细命名规则见 [`docs/directory-conventions.md`](./docs/directory-conventions.md)。

## <img src="assets/README/icons/install.svg" width="20" alt=""> 安装与本地接入

普通使用者可以把仓库作为技能源克隆到本地，再把自己的 Agent 技能目录指向同一份源。

```powershell
git clone <this-repository-url> skill-hub
cd skill-hub
```

Windows 上常用 Directory Junction 让多个 Agent 共享同一份技能目录，避免维护多份副本。

```powershell
# 预览
.\scripts\setup-junctions.ps1 -Source "D:\path\to\your\skills" -DryRun

# 执行
.\scripts\setup-junctions.ps1 -Source "D:\path\to\your\skills"
```

不同工具的实际技能目录不同，脚本只负责建立本地目录连接；不会替你配置远程账号、密钥或私有服务。

## <img src="assets/README/icons/sync.svg" width="20" alt=""> 同步流程

本地使用时可以保持扁平技能目录，仓库内则按能力域分组。同步脚本负责在两种结构之间转换。

| 操作 | 脚本 | 作用 |
|---|---|---|
| <img src="assets/README/icons/push.svg" width="20" alt=""> 推送到仓库 | [`scripts/sync-push.ps1`](./scripts/sync-push.ps1) | 把本地扁平技能目录同步到仓库分组目录。 |
| <img src="assets/README/icons/install.svg" width="20" alt=""> 拉回本地 | [`scripts/sync-pull.ps1`](./scripts/sync-pull.ps1) | 把仓库分组目录同步回本地扁平目录。 |
| <img src="assets/README/icons/index.svg" width="20" alt=""> 重建索引 | [`scripts/build-indexes.ps1`](./scripts/build-indexes.ps1) | 根据仓库中的 `SKILL.md` 重建 `_meta/` 下的索引文件。 |
| <img src="assets/README/icons/upgrade.svg" width="20" alt=""> 审计上游 | [`scripts/refresh-upstream-skills.ps1`](./scripts/refresh-upstream-skills.ps1) | 检查全部已登记上游；只自动更新 `mirror`，并把 `mapped` 差异列为人工合并项。 |

同步前建议先查看 `git status` 和 `git diff`，确认没有把真实凭据、临时输出或项目私有草稿带入公开仓库。

## <img src="assets/README/icons/upgrade.svg" width="20" alt=""> 升级与维护流程

维护 Skill-hub 时，优先按证据升级，而不是按技能名猜测。

1. 查看 [`_meta/skill-upstreams.json`](./_meta/skill-upstreams.json)，确认技能是否有已验证上游。
2. 只对 `classification=open-source` 且 `updatePolicy=mirror` 或 `updatePolicy=mapped` 的条目执行上游比对。
3. 对 `candidate`、`unknown`、自制技能和项目私有技能，先补证据或人工审查，不直接覆盖。
4. 升级后运行 [`scripts/build-indexes.ps1`](./scripts/build-indexes.ps1)，让 `_meta/` 索引反映最新技能数量、路径和描述。
5. 用 `git diff` 审查技能内容、索引变化和脱敏情况，再提交。

仓库内的 [`skills/01-agent-engineering/skill-lifecycle-manager/`](./skills/01-agent-engineering/skill-lifecycle-manager/) 提供跨 Codex 与 Claude Code 的 skill 搜索、安装、升级、同步、来源校验和质量审计流程，可维护 Skill-hub 来源索引，识别个人/项目级安装，并安全处理 Claude Code 插件缓存。

云端的 [`refresh-upstream-skills.yml`](./.github/workflows/refresh-upstream-skills.yml) 每周一自动执行，也支持手动触发。它只把来源索引中 `classification=open-source`、`updatePolicy=mirror` 且全树比对有变化的 Skill 更新到固定自动化分支并创建或刷新 PR；`mapped`、`candidate`、`self` 和 `local` 不会被云端直接覆盖。这样无需重复提出更新请求，同时保留对外部 Skill 指令变更的人工审查门。

## <img src="assets/README/icons/maintenance.svg" width="20" alt=""> 维护约定

- 新增共享技能时，先放入合适的 `skills/<domain>/` 子目录，并保持目录名为 kebab-case。
- 新增项目私有技能时，放入 `projects/<project-name>/`，避免混入通用技能目录。
- 修改技能描述后，运行索引重建脚本，确保 `by-name`、`by-domain` 和机器索引一致。
- 修改上游来源判断时，必须有证据；不要把未证实的相似仓库写成确定来源。
- 不修改别人的工作区改动；提交前只整理自己本次触碰的 README、图标或明确授权文件。
- 与私人仓库边界：与私人仓库 ([Skill-hub-private](https://github.com/EthanYoQ/Skill-hub-private)) 保持严格职责划分。已进入公开库维护的共享技能（包括 `media-use`、`skill-lifecycle-manager`、`xhs-pharma-social-listening`、`yq-article-style-imitation`、`yq-editorial-presentation-html`）以本公开仓库为唯一权威源，私人备份库中对应的重复快照已同步清理，避免多头维护。

## <img src="assets/README/icons/privacy.svg" width="20" alt=""> 隐私边界

仓库是公开的。所有技能在纳入仓库前都应做脱敏扫描，规则见 [`docs/privacy-audit.md`](./docs/privacy-audit.md)。

| 内容类型 | 入库要求 |
|---|---|
| <img src="assets/README/icons/privacy.svg" width="20" alt=""> API Key、Token、Secret、授权码 | 用 `<YOUR_*_TOKEN>` 或 `<YOUR_*_KEY>` 等占位符替代。 |
| <img src="assets/README/icons/privacy.svg" width="20" alt=""> 邮箱、手机号、个人姓名 | 用示例邮箱、`<your-phone>`、`用户` 或 `Anon` 替代。 |
| <img src="assets/README/icons/privacy.svg" width="20" alt=""> 本地用户目录 | 改写为 `%USERPROFILE%` 或 `~`。 |
| <img src="assets/README/icons/privacy.svg" width="20" alt=""> 公司内部工具名、客户名、项目代号 | 改写为通用描述，除非这些名称本来就是公开信息。 |
| <img src="assets/README/icons/privacy.svg" width="20" alt=""> 已签名 URL、真实日志、生产数据 | 不入库；如已泄漏，先轮换凭据，再清理工作区和历史。 |

使用本仓库技能时，请在本地填入自己的凭据；不要把填入真实凭据的文件提交回公开仓库。

## 用户安装版本归档

[用户 Skill 归档目录](./archives/user-installed-skills/README.md) 保存本机清理前尚未入库的完整文件版本；同名但内容不同的版本以 SHA-256 分开保存。[机器索引](./_meta/user-installed-skill-archives.json) 记录版本位置和目录校验值。归档不计入共享技能数量，也不参与默认安装或上游自动覆盖。

## <img src="assets/README/icons/overview.svg" width="20" alt=""> 许可

本仓库采用 [MIT License](./LICENSE) 完全开源。第三方开源 skill 如保留原始许可证或来源说明，以其上游许可证为准。
