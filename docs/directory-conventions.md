# 目录与命名约定

## 目标

让仓库在 **GitHub 侧便于查找**，同时保留本地扁平结构供三个 Agent 使用。

## 顶层结构

| 目录 | 含义 | 是否发布 |
|---|---|---|
| `skills/` | 共享技能（三 Agent 通用） | 是 |
| `projects/` | 项目私有技能（仅在特定仓库生效） | 是 |
| `_meta/` | 中文索引 + 机器可读映射 | 是 |
| `docs/` | 约定文档（本文件等） | 是 |
| `scripts/` | 本地同步脚本 / Junction 建立脚本 | 是 |

## 能力域编号

| 编号 | 名称 | 包含什么 |
|---|---|---|
| 01 | agent-engineering | Agent 构建、调试、自治循环、harness、council、提示工程 |
| 02 | coding-languages | 纯语言类（编码标准、patterns、testing）。按语言分子目录。 |
| 03 | frameworks | 具体框架 / 技术栈（Django、Laravel、Spring Boot、Next.js、Flutter 等） |
| 06 | data-search | 数据抓取、检索、搜索、研究 |
| 07 | media-content | PPT、视频、PDF、Excel、Word、图像、设计 |
| 08 | writing-marketing | 写作、公众号、品牌、SEO、投资材料 |
| 10 | business-industry | 行业垂直（医疗、金融、物流、供应链、采购、法律、能源） |

编号保证在 GitHub 文件浏览器里按字母序展示时也保持能力域分组顺序。

## 命名规则

- 所有目录名使用 **kebab-case**（小写 + 连字符）
- 技能名保持原名（与 `SKILL.md` 里的 `name` 一致）
- 项目目录也是 kebab-case（如 `ai-seed-project`，不是 `AI-Seed-Project`）
- 中文项目目录翻译为英文（`素材` → `content-assets`）

## 分类的判断优先级

`xxx-patterns` / `xxx-testing` / `xxx-security` / `xxx-tdd` / `xxx-verification` 决定：

1. `xxx` 是**框架名**（`django`、`laravel`、`springboot`、`nextjs`、`flutter`、`nestjs`、`vercel-react` 等） → 归入 `03-frameworks/<框架>/`
2. `xxx` 是**语言名**（`python`、`golang`、`rust`、`cpp`、`java`、`kotlin`、`swift`、`csharp`、`dotnet`、`perl`） → 归入 `02-coding-languages/<语言>/`

## 一句话描述写作规范

每个技能 `SKILL.md` 的 `description` 字段：

- **格式**：一句话，15–30 字（中文）
- **视角**：第二人称或动词开头，回答"什么时候用这个技能"
- **保留术语**：`Agent`、`MCP`、`TDD`、`SKU`、`CDSS` 等技术名词不要翻译
- **避免**：营销用语、主观评价、"高质量" / "最佳实践"之类无信息量的词

示例：

- 正确：用 gh CLI 做仓库运营：Issue 分诊、PR 管理、CI、发布、贡献者、陈旧项。
- 错误：一个高质量的、完整的 GitHub 工作流工具，帮你极大地提升效率。

## 添加新技能

1. 在本地扁平结构（约定路径见 `scripts/setup-junctions.ps1` 的 `-Source` 参数）新建一个 `<skill-name>/SKILL.md`
2. 用 `scripts/sync-push.ps1` 推送到仓库（脚本会根据 `_meta/skills-lock.json` 查目标能力域）
3. 若是新命名无法归类，先在本地放着，手动在仓库里确定归类后更新 `_meta/skills-lock.json`

## 已归档的决策

当前分类结果见 [_meta/by-domain.md](../_meta/by-domain.md)，机器可读映射见 [_meta/skills-lock.json](../_meta/skills-lock.json)。
