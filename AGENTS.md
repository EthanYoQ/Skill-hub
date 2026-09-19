# AGENTS.md — Agent 上传与维护规则

> 本文件写给 Agent 和人类贡献者。**上传或修改 skill 前，先读这份文档。**
> 它说明了仓库架构、命名规则、索引机制、上传 checklist 和脱敏要求。
> 读完你应该知道：skill 放哪个目录、SKILL.md 怎么写、上传后要更新哪些索引。

---

## 1. 仓库定位与双仓库关系

Skill-hub 是面向 Codex、Claude Code、Antigravity 等 Agent 的中文技能仓库。每个 skill 是一个目录，核心文件是 `SKILL.md`，让 AI 编程助手在相似任务中复用稳定流程。

本仓库（个人仓库）是单一事实源，组织仓库是**选择性镜像**（自动同步，但排除 `.github/org-exclude.txt` 列出的 skill）：

| 仓库 | 地址 | 角色 | 可见性 | 贡献方式 |
|---|---|---|---|---|
| 个人仓库 | `EthanYoQ/Skill-hub` | 单一事实源（全部 skill） | public | 直接编辑 |
| 组织仓库 | `Singularity-AI-Gamer/agent-skills` | 选择性镜像（排除列表之外的 skill） | private | 通过个人仓库 PR，合并后自动镜像 |

**镜像机制**：个人仓库 `push to mine` 时，GitHub Actions 自动把排除列表之外的 skill 同步到组织仓库。新增 skill 默认同步；不想同步的两种方式：

- **傻瓜式（推荐）**：在 SKILL.md frontmatter 加 `org-sync: false`，创建 skill 时加一行即可
- **批量排除**：加路径到 `.github/org-exclude.txt`（适合已有 skill 的批量管理）

朋友/团队成员通过个人仓库提 PR，合并后自动镜像到组织仓库。

---

## 2. 目录架构

```text
skills/                        # 共享技能，按能力域分组
|-- 01-agent-engineering/
|-- 02-coding-languages/
|-- 03-frameworks/
|-- 06-data-search/
|-- 07-media-content/
|-- 08-writing-marketing/
`-- 10-business-industry/

projects/                      # 项目私有技能（仅特定项目使用）
_meta/                         # 索引（机器可读 + 人类可读）
docs/                          # 约定文档（本文件、命名约定、隐私脱敏）
scripts/                       # 同步与索引重建脚本
assets/                        # README 使用的图标
.github/workflows/             # CI：镜像到组织仓库
```

---

## 3. 能力域编号

新增 skill 时先确定归属能力域。编号保证 GitHub 文件浏览器按字母序展示时也保持分组顺序。

| 编号 | 目录名 | 包含什么 |
|---|---|---|
| 01 | `01-agent-engineering` | Agent 构建、调试、自治循环、harness、提示工程、skill 生命周期 |
| 02 | `02-coding-languages` | 纯语言类（编码标准、patterns、testing），按语言分子目录 |
| 03 | `03-frameworks` | 具体框架 / 技术栈（Next.js、Flutter、Netlify 等） |
| 06 | `06-data-search` | 数据抓取、检索、搜索、深度研究 |
| 07 | `07-media-content` | PPT、视频、PDF、Excel、Word、图像、HTML 美化、设计 |
| 08 | `08-writing-marketing` | 写作、公众号、品牌、SEO |
| 10 | `10-business-industry` | 行业垂直（医疗、金融、法律、物流、能源） |

**分类判断优先级**：`xxx-patterns` / `xxx-testing` / `xxx-security` 这类名字，先看 `xxx` 是框架名（→ `03-frameworks/<框架>/`）还是语言名（→ `02-coding-languages/<语言>/`）。

---

## 4. 命名规则

- 所有目录名用 **kebab-case**（小写 + 连字符），例如 `deep-research`、`html-design-polish`
- 技能名保持与 `SKILL.md` frontmatter 里的 `name` 字段**完全一致**
- 项目目录也用 kebab-case（`ai-seed-project`，不是 `AI-Seed-Project`）
- 中文项目名翻译成英文（`素材` → `content-assets`）

---

## 5. SKILL.md frontmatter 规范

每个 skill 必须有 `SKILL.md`，开头是 YAML frontmatter：

```markdown
---
name: skill-name
description: 一句话触发条件：什么场景下 Agent 应该使用这个技能。
org-sync: false          # 可选。设为 false 则不同步到组织仓库（默认同步）
---

# 正文：指令、参考、示例
```

### `org-sync` 字段（可选）

- 不写或写 `true`：skill 会同步到组织仓库（默认）
- 写 `false`：skill 只保留在个人仓库，不镜像到组织仓库

创建 skill 时加一行 `org-sync: false` 即可，无需编辑其他文件。

### `description` 写法（关键）

- **格式**：一句话，15–30 字（中文）
- **视角**：第二人称或动词开头，回答"什么时候用这个技能"
- **保留术语**：`Agent`、`MCP`、`TDD`、`SKU`、`CDSS` 等技术名词不翻译
- **避免**：营销用语、主观评价、"高质量" / "最佳实践"之类无信息量的词

示例：

| | 写法 |
|---|---|
| 正确 | 用 gh CLI 做仓库运营：Issue 分诊、PR 管理、CI、发布、贡献者、陈旧项。 |
| 错误 | 一个高质量的、完整的 GitHub 工作流工具，帮你极大地提升效率。 |
| 正确 | 网页需要产品清晰度、信息层级、响应式或视觉系统美化、重设计或设计审计时使用。 |
| 错误 | Use when a webpage needs product-clarity, information-hierarchy, redesign...（英文长句） |

---

## 6. skill 文件构成

| 文件 | 必需 | 用途 |
|---|---|---|
| `SKILL.md` | 是 | Agent 唯一规则文件，frontmatter + 指令正文 |
| `README.md` | 否 | 面向人类的说明与快速开始（skill 复杂时建议补） |
| `CHANGELOG.md` | 否 | skill 演进记录 |
| `docs/` | 否 | 说明文档与参考资料（PDF、长文档等） |
| `examples/` | 否 | 示例项目、命令或提示词 |
| `assets/` | 否 | 流程图、截图及其他资源 |

简单 skill 只需 `SKILL.md`。复杂 skill 鼓励补 `README.md` 和 `examples/`，但 **只有 `SKILL.md` 是 Agent 规则文件**，其余是人类参考。

---

## 7. 索引机制

`_meta/` 下四个文件构成索引层，`build-indexes.ps1` 会自动重建其中三个：

| 文件 | 用途 | 重建方式 |
|---|---|---|
| `skills-lock.json` | 机器可读映射（name/domain/path/descriptionZh） | 脚本自动重建，保留手工 `descriptionZh` |
| `by-name.md` | A-Z 全量索引 | 脚本自动重建 |
| `by-domain.md` | 按能力域分组 | 脚本自动重建 |
| `skill-upstreams.json` | 来源追踪（自制/开源镜像/项目私有） | 人工维护 |

**新增 skill 后，必须运行索引重建脚本**，否则 `by-name` / `by-domain` / `skills-lock.json` 不会包含新 skill。

---

## 8. 上传 skill 完整 checklist

Agent 上传一个新 skill 时，按顺序执行：

1. **确定能力域** — 对照第 3 节能力域编号表，选最匹配的 `skills/<domain>/`
2. **创建目录** — 在 `skills/<domain>/` 下建 kebab-case 目录，目录名 = 技能名
3. **写 SKILL.md** — frontmatter 的 `name` 与目录名一致，`description` 按第 5 节规范写
4. **补可选文件** — 复杂 skill 补 `README.md` / `examples/` / `docs/` / `assets/`
5. **脱敏扫描** — 按第 9 节规则，把凭据、邮箱、手机号、用户目录替换为占位符
6. **重建索引** — 运行 `.\scripts\build-indexes.ps1`（先 `-DryRun` 预览）
7. **检查 lock** — 确认 `_meta/skills-lock.json` 已包含新 skill，`descriptionZh` 已填
8. **git diff 审查** — 确认无敏感信息、无临时输出、分类正确
9. **提交** — 提交到个人仓库 mine 分支，组织仓库自动镜像（排除列表中的 skill 不会同步）

---

## 9. 脱敏规则（入库前必做）

仓库是 public。发布到仓库的任何文件，都不得包含以下内容：

| 类别 | 处理方式 |
|---|---|
| API Key / Token / Secret / 授权码 | 用 `<YOUR_*_TOKEN>` / `<YOUR_*_KEY>` 占位 |
| Access Key ID / Secret | 用 `<YOUR_ACCESS_KEY>` 占位 |
| 邮箱地址 | 用 `<your-email>@example.com` 占位 |
| 手机号 / 联系方式 | 用 `<your-phone>` 占位 |
| 个人昵称 / 真名 | 替换为 `用户` 或 `Anon` |
| 本地用户目录（`C:\Users\<name>\...`） | 改写为 `%USERPROFILE%` 或 `~` |
| 公司内部工具名 / 产品代号 | 改写为通用描述 |
| 已签名 URL（含 AKID、签名） | 禁止入库 |

`.gitignore` 已配置常见密钥文件模式（`.env`、`*.key`、`*.pem`、`*_token*`）。GitHub 启用 Push Protection，提交含明文密钥时会被自动拦截。

详细规则见 [`docs/privacy-audit.md`](./docs/privacy-audit.md)。

---

## 10. 来源追踪

`_meta/skill-upstreams.json` 记录每个 skill 的来源，回答三个维护问题：

- 这个 skill 是自制、项目私有、开源镜像，还是经过本地映射改造
- 如果上游更新，哪些 skill 允许自动或半自动比对升级
- 哪些 skill 证据不足，不能仅凭名称覆盖本地版本

**升级规则**：
1. 只对 `classification=open-source` 且 `updatePolicy=mirror` 或 `mapped` 的条目执行上游比对
2. 对 `candidate`、`unknown`、自制技能和项目私有技能，先补证据或人工审查，不直接覆盖
3. **不要凭技能名猜测来源**，必须有证据

---

## 11. 本地 ↔ 仓库同步

本地使用扁平结构（多个 Agent 共享），仓库内按能力域分组。同步脚本在两种结构间转换：

| 操作 | 脚本 | 作用 |
|---|---|---|
| 本地 → 仓库 | `scripts/sync-push.ps1` | 把本地扁平技能目录同步到仓库分组目录 |
| 仓库 → 本地 | `scripts/sync-pull.ps1` | 把仓库分组目录同步回本地扁平目录 |
| 重建索引 | `scripts/build-indexes.ps1` | 根据 SKILL.md 重建 `_meta/` 索引 |
| 建 Junction | `scripts/setup-junctions.ps1` | Windows 上让多个 Agent 共享同一份技能目录 |

`sync-push.ps1` 读取 `_meta/skills-lock.json` 建立 `{name → repoPath}` 映射，本地 skill 在 lock 中查不到时会报"未映射列表"，**不自动归类**，避免错误分类。

---

## 12. 维护约定

- 新增共享 skill → 放入 `skills/<domain>/`，目录名 kebab-case
- 新增项目私有 skill → 放入 `projects/<project-name>/`，不混入通用技能目录
- 修改 skill 描述后 → 运行索引重建脚本，确保 `by-name`、`by-domain`、`skills-lock.json` 一致
- 修改上游来源判断 → 必须有证据，不要把未证实的相似仓库写成确定来源
- 提交前 → 只整理自己本次触碰的文件，`git diff` 审查脱敏情况

---

## 13. 相关文档

- [`docs/directory-conventions.md`](./docs/directory-conventions.md) — 目录与命名约定（详细版）
- [`docs/privacy-audit.md`](./docs/privacy-audit.md) — 隐私与脱敏说明
- [`_meta/README.md`](./_meta/README.md) — 索引入口说明
- [`README.md`](./README.md) — 仓库总览（面向人类读者）
