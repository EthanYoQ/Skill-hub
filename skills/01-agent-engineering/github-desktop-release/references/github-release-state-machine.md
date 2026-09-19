# GitHub Release promotion state machine

promotion 的目标是把同一 qualification artifact 的原始字节发布出去，不是再运行构建。所有远端状态先读后写，失败残留是恢复线索而不是自动清理对象。

## 状态

```text
UNQUALIFIED
  -> QUALIFIED_ARTIFACT
  -> READ_ONLY_PLAN
  -> VERIFIED_PROMOTION_PACKAGE
  -> TAG_AND_DRAFT
  -> DRAFT_ASSETS_VERIFIED
  -> PUBLISHED
```

`READ_ONLY_PLAN` 不得写 tag 或 Release。它验证 workflow run、head SHA、默认分支祖先、artifact ID/name、contract、ledger、manifest、checksum 和 existing remote state。

进入 `READ_ONLY_PLAN` 前先完成 [promotion-preflight.md](promotion-preflight.md)。本地缺少解压工具、磁盘不足、账号选择错误或 output/cache 计划无效时，在下载大 artifact 前停止；修复这些本地条件后沿用同一 immutable run identities，不重新 qualification。

不要让每个项目重写这套状态机。将 Skill 的 `scripts/github-desktop-promotion.mjs` 与 `scripts/validate-release-profile.mjs` 原样复制到项目的 `.release/scripts/`，保留文件名，并复制 promotion workflow 模板。项目只维护 release profile 与 qualification acceptance adapters。

## 最小权限分层

- workflow 顶层 `permissions: {}`；
- qualification 使用 `contents: read`，不拥有 Release 写权限；
- promotion verify job 使用 `actions: read` 与 `contents: read`，仅下载指定 cross-run artifact；
- publish job 才使用 `contents: write`，同时保留 `actions: read`（若需要读取 promotion artifact）；
- checkout 使用冻结 ref 且 `persist-credentials: false`。不要把 PAT 写入日志、contract 或 artifact。

## 只读计划

1. 输入必须含 qualification run ID、完整 expected SHA、tag 和人类确认字符串。
2. 验证 run 成功、workflow 身份及 `head_sha == expected_sha`；验证 SHA 是默认分支祖先。
3. 对每个 required platform 按 workflow、run ID、attempt 和 artifact ID 选择唯一、未过期 artifact；名字相同但来自别的 run 不够。所有 run 的 `head_sha` 必须等于同一个 expected SHA。
4. 读取 tag、Release 和 assets。若只读 token 对 draft Release 的 tag endpoint 返回 404，记录 `draftState: unknown`；权限不足或可见性延迟不能被解释为“可创建”。
5. 下载全部 required platform artifact 后逐字节复核 evidence，聚合 exact release asset set，再创建仅本次 promotion 可用的 verified package artifact。

下载前先用 API metadata 确认 artifact 大小、未过期状态和 immutable identity。qualification 已绿而本地下载、解压或 verifier runtime 失败属于 promotion 环境故障；只要 source、bytes 与 acceptance meaning 未变，就修复本地环境并从只读计划恢复。

每个平台的 schema-v2 manifest 和 run ledger 都必须记录同一个 `contractRawBytesSha256` 与 `profileRawBytesSha256`。`release-contract.json` 必须属于 manifest/checksum exact set，且其 raw SHA-256 等于前者；promotion 当下读取的 profile 原始字节 SHA-256 必须等于后者。所有 required platform 的两个 hash 必须完全一致。`signing.evidencePath` 也必须指向 manifest evidence 中已经 raw-hash 绑定的文件。

promotion verifier 还必须读取 signing evidence，核验 status、验证结果与 unsigned distribution impact 已被 qualification manifest/ledger 一致记录。固定 verifier runtime 只运行 promotion verifier，不证明或替代 qualified app toolchain。

`signing.evidencePath` receipt 使用与 replay 相同的严格 UTF-8 JSON 解析规则：只允许 byte 0 位置的一个 UTF-8 BOM；重复或错位 BOM 失败。receipt 必须 `accepted: true`、含非空字符串 `observations`，且 `status`、`validationResult`、`unsignedDistributionImpact` 与 manifest signing 三字段逐字一致。

## 原子 claim 与可见性

创建 `refs/tags/<tag>` 前先确认 tag 为空。创建 API 返回 201 后，立即 GET 仍 404 可能是短暂可见性延迟；对同一个 tag/SHA 做固定 5 次 read-after-write（间隔 250、500、1000、2000 ms）。draft create、每个 asset upload、release PATCH 和最终 authoritative readback 使用同一边界。重试只读，不重 POST、不改 SHA、不删除 tag。耗尽后明确失败、保留已知状态并转人工恢复。

## Draft、上传与发布

1. tag 已精确指向 qualified SHA 后，创建 target commit、name、body/provenance 都与 plan 匹配的 draft Release。
2. 上传 exact release asset set，且每个文件在上传前再核对大小和 raw SHA-256。
3. GET draft，逐项验证 `draft: true`、asset name、`uploaded` state、size 和 GitHub `sha256:` digest；拒绝额外或重复资产。
4. 仅全部匹配后按 profile 的 draft/prerelease/latest channel policy PATCH Release，再读回 tag、Release、channel flags 和 assets 证实最终状态。

发布 PATCH 或发布后验证失败时，若可能只恢复 draft 标志；不删除 tag、draft 或 assets。恢复也失败时保留全部标识并报告人工介入。

## Safe resume

只有同时满足以下条件才可 resume：现有 tag 精确解析到 expected SHA，draft 尚未发布且 tag/name/body/provenance 相同，且每个现有远端 asset 都是 verified manifest 的精确子集，name、`uploaded` state、size 和 GitHub `sha256:` digest 全部匹配。此时只上传缺少的 assets，再验证完整集合后发布。未知 draft 状态、不同 SHA、额外或重复资产、digest 缺失或不匹配都需要停止；不要覆盖、删除、重传或 force-update。

已经发布的 Release 只能执行只读 authoritative readback；若 channel policy 或完整资产集合不匹配，不得 PATCH 成另一个状态。`expectedLatest` 必须通过 `/releases/latest` 的 Release ID 独立核验，不能从 workflow success 或创建顺序推断。
