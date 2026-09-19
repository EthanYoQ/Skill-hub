# Stack adapters

Windows 目标先用 `scripts/preflight-windows-release.ps1` 的信号决定 stack 适配器；macOS 目标从冻结 profile、项目配置和 `references/macos-qualification.md` 选择包格式与架构。检测结果只是起点；构建命令、installer 类型、升级语义、签名与公证要求必须从项目配置和官方文档核对。

| 检测信号 | 适配器 | 共用的发布边界 | 不可假设的内容 |
| --- | --- | --- | --- |
| `electron` + `electron-builder` 依赖，或 build 配置含 `nsis` | Electron/NSIS | contract、Windows qualification、artifact bytes、promotion 状态机 | qualification tier、pnpm 版本、产物路径、NSIS 命令、native ABI、升级 fixture |
| `src-tauri/tauri.conf.*`、`Cargo.toml` 或 Tauri 依赖 | Tauri | contract、Windows qualification、artifact bytes、promotion 状态机 | installer 是 MSI 还是 NSIS、cargo/toolchain、bundler config、签名 |
| `.spec`、`PyInstaller`、Python build 配置 | PyInstaller | contract、Windows qualification、artifact bytes、promotion 状态机 | 是否有 installer、Python env、收集 hook、升级路径 |
| `.csproj`/`.sln`，并有 WiX `.wxs` 或 MSIX manifest | .NET/WiX/MSIX | contract、Windows qualification、artifact bytes、promotion 状态机 | WiX/MSIX 版本、Package Identity、证书、upgrade code、bootstrapper |
| profile 请求 macOS，项目产生 `.app`/DMG/ZIP/PKG | macOS package adapter | contract、same-SHA barrier、artifact bytes、promotion 状态机 | 架构、签名身份、公证、bundle ID、updater asset roles、mount/launch support |

## Electron/NSIS

读 [electron-nsis.md](electron-nsis.md)。适配器类型不决定 qualification tier：普通应用代码发布默认 Standard，只有该页列出的 installer、升级、runtime/native 或明确项目触发器才进入 Deep。共享 native module 时，Electron 打包 ABI 与开发 Node ABI 常不同；qualification 要验证打包应用，同时在必要时恢复并验证开发 ABI。只有明确从配置检测到 NSIS 时才应用 NSIS helper 规则。

## Tauri

先核对 Tauri 当前官方的 Windows bundling 文档与仓库配置。Tauri 可以产生 NSIS 或 MSI，但它不是 electron-builder：不要运行 `pnpm build:win`、Electron ABI restore、electron-builder artifact 路径或 NSIS helper whitelist，除非项目自己的实现和 installer 类型明确要求。未配置代码签名时记录签名缺失及平台分发影响；不要绕过 SmartScreen、篡改安全策略或伪造签名。

## PyInstaller

PyInstaller 先证明 Python environment、hidden imports/data files 和生成的 executable。它可能只有 portable EXE，也可能由 Inno Setup、NSIS 或企业部署器包装；后者需要独立的 installer adapter 和真实升级策略。不要把 portable EXE 当作已经测试过的 installer/uninstall/upgrade。

## .NET / WiX / MSIX

WiX 的 Product/Upgrade code 与 MSIX 的 Package Identity 直接影响升级和卸载。先从项目 manifest、签名策略和官方工具链文档提取这些值。MSIX、WiX bootstrapper 和传统 MSI 的安装/升级命令不同，必须由项目专属 acceptance script 处理，不能复制 Electron 模板。

## 新适配器

当 preflight 未能可靠分类时，保留 common contract/promotion 框架，建立一个小的 adapter plan：检测证据、官方文档版本、构建入口、精确产物、安装/升级模型和 acceptance 方案。先验证一个假设，不要为了“通用”扩展到无关的代码审查或工具链迁移。

## macOS

读 [macos-qualification.md](macos-qualification.md)。先冻结目标架构、包格式、bundle identity、签名/公证政策和 updater 角色；不把 Windows 的 installer lifecycle、PowerShell 或 NSIS helper 规则套到 macOS。

## 冻结适配器与签名边界

普通 `--win` 不是 NSIS 证据；只有配置或命令中明确出现 `nsis` target 才选 Electron/NSIS。普通 `.csproj` 也不是 installer adapter 证据；只在 WiX 或 MSIX manifest 等明确安装器信号存在时选择对应 adapter。

所有 stack 都必须在 contract、manifest、run ledger 与 promotion verifier 中引用 `acceptance/signing.json`。此 evidence 记录 signing status、验证结果和非空 unsigned distribution impact。未签名可由项目明确允许，但必须披露分发、SmartScreen、企业策略或用户信任影响；固定 promotion verifier Node 不能被表述为 app toolchain。
