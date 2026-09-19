# Evidence contract

优先使用 GitHub API metadata、workflow 日志、manifest 和小型 evidence 文件。只有真实平台验收、完整 bundle 复核或 hash 复核需要时才下载大型安装包。缺少旧 run 的完整 bundle bytes 时不得用重建产物伪造回放结论。

## Qualification artifact 内容

建议把以下内容放在一个有明确名称和有限 retention 的 artifact 中：

```text
release-evidence/
  release-contract.json
  run-ledger.json
  manifest.json
  SHA256SUMS.txt
  acceptance/
    install.json
    launch.json
    quiet-window.json
    error-dialogs.json
    uninstall.json
    upgrade-data.json
    native-abi.json
    packaged-smoke.json
    signing.json
  release-bundle/
    <exact release assets>
```

macOS 或其他 profile-defined 平台使用自己的精确 receipt set；不要复制 Windows 的九项列表后把不适用项写成空成功。每个平台仍必须包含 signing evidence；需要公证时另含 notarization evidence。

Producer 必须直接读取 `profile.platforms.<platform>.acceptanceReceipts`，不得用模板硬编码列表静默替代。进入 manifest finalize 前，递归枚举 `acceptance/` 下实际 JSON，要求其规范相对路径集合与 profile 完全一致：缺一项、额外一项、大小写碰撞、symlink/reparse point 或不安全路径都 fail closed。项目 adapter 只能生成这些平台事实，不能改写通用集合门禁。

该目录树是 promotion consumer 的精确输入，不是建议性的示意：`manifest.json` 必须是 `schemaVersion: 2`，顶层包含 `commit`、`releaseCreated: false`、`contractRawBytesSha256`、`profileRawBytesSha256`、`artifacts`、`evidence` 和 `signing`。`artifacts` 只索引 `release-bundle/` 下将发布的原始字节；`evidence` 至少精确索引 `release-contract.json`、`run-ledger.json` 和 profile 要求的全部 receipt。`signing.evidencePath` 必须指向 manifest 已绑定的 signing receipt。

除 `manifest.json` 和 `SHA256SUMS.txt` 外，解包后的每个文件都必须恰好出现一次在 `artifacts` 或 `evidence` 中；checksum 表的键集合必须恰好等于全部 manifest record 加 `manifest.json`。不得夹带构建目录、诊断日志或未索引文件。

`run-ledger.json` 只记录上传前可知的 repository、workflow、run ID、attempt、actor、dispatch inputs、head SHA、runner image、开始/结束时间、命令结果，以及 `contractRawBytesSha256` / `profileRawBytesSha256`。这两个 hash 必须与 manifest 及 promotion 当前读取的 profile 原始字节一致。ledger 的 `signing` 必须与 manifest `signing` 使用同一四字段 envelope：`status`、`validationResult`、`unsignedDistributionImpact`、`evidencePath`；该路径必须是 profile 声明、已存在且已被 manifest raw hash 绑定的 signing receipt。artifact ID、digest、URL 只能在上传后由 job outputs、step summary 或独立外层 attestation 记录；不要回写已上传 evidence artifact 或 ledger。避免记录 token、证书、私钥或用户数据。

跨进程 ledger 不能假设 runner wall clock 单调。每个事件记录递增 `sequence` 作为权威顺序；时间戳用于观察和持续时间。若既有 schema 要求时间戳非递减，writer 将新时间夹紧到前一已提交时间并另记 `clockRollbackObserved` 与原始观察值，而不是重排或拒绝真实命令。用跨进程时钟回拨 fixture 覆盖 writer、finalizer 和 verifier；不要通过放宽命令顺序门禁掩盖回拨。

## Hash 语义

| 对象 | 规则 |
| --- | --- |
| `.exe`、`.msi`、`.msix`、`.zip`、`.blockmap` 及所有二进制资产 | 直接读取原始字节计算 SHA-256 |
| manifest、ledger、contract、updater metadata | 原始字节 SHA-256，同时保留 UTF-8 JSON 的明确编码 |
| `pnpm-lock.yaml`、`package-lock.json`、`yarn.lock`、`Cargo.lock` 等明确文本 lockfile | 可额外记录 `text-newlines-crlf-to-lf` hash，仅将 CRLF/LF 规范为 LF；不要用于二进制资产 |
| platform evidence JSON | 原始字节 SHA-256；解析时仅允许 byte 0 的单个 UTF-8 BOM，并执行严格 UTF-8/JSON 解码；语义归一化不得改变原字节记录 |

normalised lockfile hash 用于 Windows / Linux 之间的来源比较，不能替代 installer 的 raw-byte hash。manifest 应清楚标示 `hashMode`，避免把二者混为一谈。

所有 required platform 必须读取同一路径、同一提交中的 profile 原始字节，并用相同输入生成逐字节一致的公共 `release-contract.json`；promotion 会要求各平台的 contract/profile raw-byte hash 完全相同。平台 runner、toolchain、source path 等差异写入平台 verification 或 qualification plan，不得污染公共 contract。

## Evidence 生成顺序

1. 建立 contract，写出 run ledger 的开始记录。
2. 运行构建和真实 acceptance；保留每一步结构化结果及最少必要日志摘录。
3. 枚举 contract 的精确 artifact set，写入每个文件的相对路径、大小、raw SHA-256 和 role。
4. 写 manifest，再计算并写 `SHA256SUMS.txt`。checksum 表可以包含 manifest 本身，但不把 checksum 文件自身加入自己的清单。
5. 上传 evidence artifact；在上传后的 job outputs、step summary 或独立外层 attestation 记录 artifact ID、digest、URL，不回写 artifact 内的 ledger。

验证命令顺序时优先使用 `sequence` 与明确的 stage transition；不能用两个独立进程采集到的 wall-clock 大小关系代替顺序证据。

模板 artifact 名是 profile 的固定身份：Windows 为 `qualified-windows`，macOS 为 `qualified-macos`。禁止拼接 SHA、run ID 或 attempt 形成动态 artifact 名；不可变身份由 workflow/run/attempt/artifact ID 共同提供。

## 验收表达

事实与结论分开记录。例如 `launch.json` 可写 `processIdentityCaptured: true`、`newProductErrorDialogCount: 0`、`quietWindowCompleted: true`，再由 gate 推导 `accepted: true`。出现未捕获进程、超时或新错误对话框时，`accepted` 必须为 false/blocked，不能用空字段表示成功。

## Promotion 时的复核

在 publish job 取得写权限前，读回所有 required platform 的 contract、ledger、manifest、receipt 和每个 asset bytes，证明它们绑定同一 source SHA。远端 Release asset 必须逐项核验 name、state、size 与平台提供的 SHA-256 digest；只有聚合后的 exact set 全部匹配才可将 draft 切换为正式 Release。

## 冻结 v2 不可放宽项

- 在 install、build 和 acceptance 前生成并 hash 冻结 contract；运行前直接核验 dispatch inputs、checkout、runner image、app toolchain。promotion 的固定 verifier runtime 不等同于 app toolchain。
- 每个独立 acceptance JSON（包括 `acceptance/signing.json`）都要有 `accepted: true`、非空 `observations` 和至少一个直接观察字段。将每个文件的 raw-byte SHA-256 写入 manifest，并列入 `SHA256SUMS.txt`。
- signing evidence 对所有 stack 都是必需项：记录 `status`（`signed` 或 `unsigned`）、`validationResult` 与非空 `unsignedDistributionImpact`。未签名可以被接受，但必须披露实际分发影响，绝不伪称已验证签名。
- 每个明确文本 lockfile 始终记录 raw-byte SHA-256；仅对严格 UTF-8（允许 UTF-8 BOM）再记录 newline-canonical hash。canonicalization 只能把 CRLF/CR 改为 LF，其他字节不变；非 UTF-8 或不允许编码必须 fail closed。
- artifact path 必须先 canonicalize 为 checkout-relative 路径，拒绝越界、ADS、尾点/尾空格和不区分大小写碰撞；上传 action 的 artifact ID、digest、URL 写入 job output 或外层 step summary，不能回写到已上传 artifact。
- failure diagnostics 只从项目生成的已脱敏 allowlist 复制到单独目录；禁止上传仓库日志 glob、workspace 或未审计的原始日志。
