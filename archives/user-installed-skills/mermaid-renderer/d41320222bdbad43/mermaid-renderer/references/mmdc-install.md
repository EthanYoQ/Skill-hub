# mmdc CLI 安装指引

`mmdc` = Mermaid CLI,通过 Node.js / npm 安装。Phase 4.5 hook 用它把 Mermaid 文本渲染为 PNG。

## macOS / Linux

```bash
# 1. 装 Node.js (>= 18.x)
brew install node                              # macOS
sudo apt install nodejs npm                    # Ubuntu/Debian

# 2. 全局装 mmdc
npm install -g @mermaid-js/mermaid-cli

# 3. 验证
mmdc --version    # 期望 11.x.x or later
```

## Windows

```powershell
# 1. 装 Node.js (https://nodejs.org/ 下载 LTS 安装包)

# 2. 装 mmdc
npm install -g @mermaid-js/mermaid-cli

# 3. 验证 (PowerShell 或 Git Bash)
mmdc --version
```

## 校验

mmdc 装好后,跑 mermaid-renderer 5 单测:

```bash
pytest tests/test_mermaid_renderer.py -v
# 期望 5 passed (含真实 mmdc 渲染 1 张测试图)
```

## 无 mmdc 也能跑

skill 自带 graceful fallback:无 mmdc 时返回 `ok=False, fallback_inline=mermaid_text`,orchestrator 保留 inline 不阻塞。但 5 疾病重跑要 ≥ 4 PNG 决策树达 IFI 80% 阈值,故强烈建议装 mmdc。

## 故障排查

- **`mmdc: command not found`** → npm 路径不在 $PATH,跑 `npm config get prefix` 找路径加 $PATH
- **`puppeteer chromium download failed`** → 国内网络问题,设环境变量 `PUPPETEER_DOWNLOAD_BASE_URL=https://npmmirror.com/mirrors/chromium-browser-snapshots/`
- **subprocess timeout** → 默认 30s,大图可在 `render_mermaid_to_png(..., timeout_sec=60)` 加长
