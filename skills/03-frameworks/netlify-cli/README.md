# Netlify CLI Skill

用于指导 Agent 和团队成员通过 Netlify CLI 安装工具、完成登录与站点关联、运行本地开发环境、管理环境变量，以及执行预览或生产部署。

## 适用场景

- 新项目或本地项目需要连接到 Netlify。
- 使用 `netlify dev` 在本地模拟 Netlify 环境。
- 通过 Git 持续部署，或直接上传构建产物进行手动部署。
- 配置、导入、导出或按部署环境管理 Netlify 环境变量。
- 需要确认当前 CLI 登录状态或已关联站点。

## 快速开始

前提：Node.js 18.14.0 或更高版本。

```bash
npm install -g netlify-cli
netlify login
netlify status
netlify deploy --dir=dist      # 创建预览部署
netlify deploy --prod --dir=dist  # 发布到生产环境
```

部署前请阅读 [SKILL.md](SKILL.md) 中的完整规则；在 Git 仓库中执行 `netlify init` 或 `netlify link` 前，先确认目标站点与部署模式。

## 目录结构

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

## 文档

- [新手简明指南](docs/beginner-guide.pdf)：适合首次使用 Skill 和 Netlify CLI 的成员。
- [CLI 全流程部署指南](docs/full-guide.pdf)：涵盖更完整的部署流程与操作说明。

## 内容边界

- `SKILL.md` 是此 Skill 唯一的 Agent 规则文件。
- `docs/` 存放解释性和参考性文档。
- `examples/` 用于存放可复现示例项目、命令片段或提示词。
- `assets/` 用于存放流程图、截图和其他非规则资源。
