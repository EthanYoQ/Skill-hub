# 外部工作流包

Skill-hub 的 `skills/` 与 `projects/` 用于本仓库维护的独立技能；它们不适合承载有根级入口、固定分组、插件元数据或多技能协作关系的第三方工作流包。

完整包由 [`_meta/external-workflow-packs.json`](../_meta/external-workflow-packs.json) 统一登记。每个条目至少记录：原始上游、组织 fork、固定提交、许可证、安装入口、包完整性规则和更新策略。

## 已登记包

| 包 | 组织 fork | 适用场景 | 安装边界 |
|---|---|---|---|
| [Skills for Real Engineers](https://github.com/Singularity-AI-Gamer/skills) | [Singularity-AI-Gamer/skills](https://github.com/Singularity-AI-Gamer/skills) | 完整的软件工程工作流 | 整包安装；安装后在每个目标项目运行 `/setup-matt-pocock-skills`。 |

安装（由成员在目标项目中执行）：

```powershell
npx skills@latest add Singularity-AI-Gamer/skills
```

该命令已通过只读 `--list` 验证：组织 fork 可被 installer 克隆并发现 41 个 skill；本次验证没有把 skill 安装到任何本地运行时目录。

## 组织镜像部署

`Singularity-AI-Gamer/agent-skills` 在镜像生成时将该 fork 挂载为 [`external/mattpocock-skills`](https://github.com/Singularity-AI-Gamer/agent-skills/tree/main/external/mattpocock-skills) Git submodule，并固定到目录中记录的 commit。这样 GitHub 浏览、克隆与审查都能保留完整包边界和上游历史；`skills/`、`skills-lock.json`、`by-name.md`、`by-domain.md` 仍只表示 Skill-hub 自己维护的独立技能。

## 维护规则

1. 不将外部包的子技能逐个复制到 `skills/`，也不将它们写入 `skills-lock.json`、`by-name.md` 或 `by-domain.md`。
2. `sync-pull.ps1` 与 `sync-push.ps1` 仅管理本仓库的共享独立技能；不得用于外部包。
3. 需要组织可控分发时，优先保留 GitHub fork，而不是制作无历史、无根级文档的目录副本。
4. 同步上游前，审查完整仓库差异，并更新目录中的固定 commit；不要按子技能名称自动覆盖。
5. 组织专属规范应作为独立 overlay 或目标项目配置维护，避免直接污染上游工作流包。

## 新增包流程

1. 确认上游仓库、许可证、默认分支和一个不可变 commit。
2. 在组织下创建或确认 fork；保留上游结构与提交历史。
3. 在 `_meta/external-workflow-packs.json` 新增包级条目，而不是新增每个子 skill 的条目。
4. 在本文件添加人类可读说明与安装入口。
5. 验证 JSON、链接、安装说明和隐私边界；只有新增本仓库 `SKILL.md` 时才运行共享技能索引重建。
