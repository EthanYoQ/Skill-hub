# Failure playbook

先写下一个可证伪的假设，再选择一条最小证据路径。一次 cloud run 只回答一个问题；输入和失败现象未变时，重跑只会制造噪音。同一阶段连续失败两次后硬停止，不得第三次 dispatch，直到统一根因、替代假设、原始证据和本地 RED→GREEN replay 完整。

| 症状 | 先检查 | 安全动作 |
| --- | --- | --- |
| preflight 无法识别 stack 或 installer | 项目配置、lockfile、现有脚本 | 不套用模板；建立 adapter plan 并查官方文档 |
| Windows build 失败 | workflow 日志、runner image、冻结工具链、lockfile | 改一个可解释输入后再跑一次；保留 diagnostics artifact |
| native module 在 package 后或恢复后失败 | Electron/Node ABI、实际 rebuild/restore 命令、packaged smoke | 分开验证 package ABI 与开发 ABI，不扩大到无关依赖升级 |
| packaged helper 仅在 checkout 中成功 | bundle 中的开发 Electron 代码、未解析 runtime import、CJS/ESM warning、仓库 `node_modules` 污染 | 在隔离 package-like 目录运行 exact bundle；修复 protocol/bundle 后先跑 staged canary |
| installer 顶层退出 0 但有快退/残留进程 | armed record、capture handshake、PID/start time/path/parents、quiet evidence | 视为失败；先修监控或验收脚本，不加宽松豁免 |
| NSIS helper `exit 1` | 精确 image、command line、code、父链、TEMP canonical path | 仅为匹配的已知 probe 添加窄测试；未知事件保持失败 |
| Windows 短路径或目录别名导致路径断言失败 | 目标是否为同一 file identity、可信根 containment、对象替换竞态 | 比较稳定文件身份而非原始字符串；身份不可得时 fail closed |
| 慢 runner 上异步测试偶发超时 | 完成条件是否依赖短 polling/sleep、mock 是否能发出确定信号 | 用 deferred/event/fake time 同步；timeout 仅作外层保护，不任意加长 |
| ledger 命令顺序偶发倒退 | writer 是否跨进程比较 wall clock、是否有递增 sequence、runner clock rollback | sequence 作为权威顺序；按前值夹紧展示时间并记录 rollback，加入跨进程 fixture |
| qualification 与 promotion lockfile hash 不同 | hashMode、raw bytes、文本换行正规化 | 仅对明确文本 lockfile比较 LF-normalized hash；二进制始终 raw bytes |
| evidence JSON 被 verifier 拒绝 | BOM 位置/数量、严格 UTF-8、时间戳、版本、路径、签名/IP 表示 | 保存原字节，添加真实正例和独立负例；修正解码/归一化后完整本地回放，不盲目重建 |
| cross-run artifact 不匹配 | run ID、artifact ID、contract、manifest、checksum | 停止 promotion；不重新 build 或以同名 artifact 替换 |
| tag POST 201、随后 GET 404 | response、tag/SHA、重试预算 | 做有界只读重试；不再 POST、不删除现有状态 |
| draft/tag/assets 残留 | tag resolution、draft provenance、asset name/size/digest | 仅精确匹配可 resume；其他情况保留状态并请求人工决定 |

## 诊断顺序

1. 收集 workflow run URL/ID、commit、dispatch inputs、runner/toolchain、manifest 与最小日志片段。
2. 判断是在 qualification、promotion verify 还是 publish 状态；不要跨阶段猜测原因。
3. 写出单一假设及接受/拒绝它需要的证据。
4. 优先使用现有 logs、manifest 和 API metadata。只有证据不能回答问题时才下载 artifact 或申请一次新 run。
5. 将失败、未验证与临时缓解分别报告。未直接证实前，不称“已修复”或“已发布”。
6. 使用统一分类：`product`、`build`、`acceptance`、`gate-false-positive`、`promotion`。只有证据证明产品或构建输入改变时才默认重建。
7. 修复若改变 SHA，立即取消旧 SHA 的未完成 runs，并对尚未到达的 package smoke、evidence finalize、promotion preflight 做一次有界前向审计，再决定 staged canary 或 parallel matrix。

## 禁止的恢复捷径

- 不自动删除 draft、tag、assets 或 workflow artifacts；
- 不 force-push、force-update tag、覆盖 Release 或对同名 asset 重传；
- 不因安装器 helper 而忽略任意非零 exit；
- 不将 `draft 404` 在 read-only plan 中视为 draft 不存在；
- 不用新的构建替代已经 qualification 的 artifact；
- 不把一次失败变成无范围的代码审查、依赖升级或工作流重写。
- 不上传仓库日志 glob、workspace 或原始 secrets；failure diagnostics 只能上传显式 allowlist 中项目生成且已脱敏的 evidence。
