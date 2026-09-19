# Chrome Headless 配置(PDF 渲染依赖)

## 自动检测路径

`build_pdf._detect_chrome()` 按平台尝试以下路径:

```python
# Windows
C:\Program Files\Google\Chrome\Application\chrome.exe
C:\Program Files (x86)\Google\Chrome\Application\chrome.exe
C:\Program Files\Microsoft\Edge\Application\msedge.exe

# Linux
/usr/bin/google-chrome
/usr/bin/chromium
/usr/bin/chromium-browser

# macOS
/Applications/Google Chrome.app/Contents/MacOS/Google Chrome
```

第一个存在的路径被选用。`build_pdf` 也接受 `chrome_path=` 参数显式指定。

## 找不到时

`build_pdf` 会抛 `RuntimeError`,带详细安装指引:

```
No Chrome/Edge/Chromium found. Set chrome_path explicitly or install one of:
  Windows: C:\Program Files\Google\Chrome\Application\chrome.exe
  Linux:   /usr/bin/google-chrome (or chromium)
  macOS:   /Applications/Google Chrome.app
```

## 安装命令

| 平台 | 命令 |
|-----|------|
| Ubuntu/Debian | `sudo apt-get install -y google-chrome-stable` 或 `sudo apt-get install -y chromium-browser` |
| macOS | `brew install --cask google-chrome` |
| Windows | 从 https://www.google.com/chrome/ 下载安装包,默认路径已被检测覆盖 |

## CI 环境

- **GitHub Actions**:`browser-actions/setup-chrome@v1`
- **Docker**:用 `selenoid/chrome:latest` 或 `mcr.microsoft.com/playwright/python`(自带)
- **GitLab CI**:`image: zenika/alpine-chrome`

## 头部参数解释

`build_pdf` 调用 Chrome 时使用以下参数:

| 参数 | 用途 |
|-----|-----|
| `--headless=new` | 新版 headless 模式(2022+),性能与新功能优于 `--headless=old` |
| `--disable-gpu` | 关 GPU,Windows 下避免 driver 异常 |
| `--no-sandbox` | 容器/CI 环境兼容,本地无害 |
| `--no-pdf-header-footer` | 不生成默认页眉页脚(我们的 HTML 自己控制 TOC) |
| `--print-to-pdf=<path>` | 输出 PDF 路径(Chrome 直接写文件,无需 stdout 转写) |

## 渲染失败排查

| 症状 | 原因 | 修复 |
|------|------|------|
| `Chrome headless failed: ... timeout` | HTML 太大或 JS 阻塞 | 检查 `<script>` 是否内嵌大量 base64,考虑分页 |
| `PDF not generated` | Chrome 启动成功但写文件失败 | 检查 `out_path.parent` 是否可写,磁盘空间 |
| 输出 PDF 字体异常 | 系统缺中文字体 | Windows 默认有 Microsoft YaHei;Linux 装 `fonts-noto-cjk` |
| 页码不准 | pypdf 未安装 → `_measure_pages` 返回全 None | `pip install pypdf` |
