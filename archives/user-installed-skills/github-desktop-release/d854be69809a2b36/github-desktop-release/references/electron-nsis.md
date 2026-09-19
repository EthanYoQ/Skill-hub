# Electron / electron-builder / NSIS adapter

只在 preflight 和项目配置同时证明 Electron、electron-builder 与 NSIS 时使用本页。先核对当前 electron-builder、Electron、Node、包管理器与 NSIS 配置的官方文档；这些版本与命令不是跨项目常量。

## Qualification tiers

Use a small non-promotable target preflight before a formal installer run: resolve the current runner label, perform the locked install, load release-critical native bindings for the actual Windows architecture, and resolve the intended assets. It is an early compatibility check, not an installer qualification.

The selected profile must name the exact receipt set. Keep two committed profiles when both modes are needed:

- **Standard**: one frozen installer build; real install, launch/packaged smoke, bounded quiet/error observation, quiet uninstall, signing disclosure, exact byte hashes, and promotion evidence.
- **Deep**: standard plus upgrade-data, native-ABI/rebuild, and any migration or installer-specific checks.

Use deep acceptance only for a first installer-path qualification; a change to NSIS/electron-builder, app identity/install scope, signing/updater policy, persistent-data/upgrade behavior, Electron/Node/native modules, or an explicit project requirement. Ordinary source-only changes still need their normal tests, but do not automatically require an upgrade fixture or duplicate ABI test.

## Qualification sequence

1. From the frozen commit's lockfile, resolve the package manager and dependency versions, then execute the project locked install.
2. On a Windows runner, execute the build/package entry point once and record the actual runner/toolchain in the ledger.
3. Perform the standard installer acceptance against the exact built bytes: real install, launch, packaged smoke, error-dialog check, bounded quiet window, and quiet uninstall. Offline or local-only fixtures should avoid browser/network dependencies.
4. When the selected tier is deep, validate the Electron ABI rebuild/load and upgrade-data preservation with isolated fixtures. Do not infer either fact from a successful package command.
5. Upload only the contract-listed installer, blockmap, updater metadata, manifest, and acceptance evidence.

## Packaged helper and runner boundary

Release-critical helper/runner code must be tested as packaged code, not through repository `node_modules`:

1. contract-test the producer and helper protocol together, including required identity/capability fields, byte limits, and fail-closed error cases;
2. build the exact bundle used by the packaged application and treat CJS/ESM interop warnings such as unusable `import.meta` as blockers;
3. inspect the bundle for development-only Electron package code and unresolved runtime imports that the packaged process cannot resolve;
4. run it from an isolated package-like directory or installed application, with repository module-resolution paths absent;
5. make any build-time stub narrow and fail closed if its unreachable API is invoked.

A helper smoke that passes only from the checkout does not prove the installed package. Keep this boundary in the staged canary whenever helper protocol, bundling, Electron/Node, or module resolution changes.

## 进程与窗口证据

一次进程观察至少绑定：

```text
PID + creation/start-time + canonical executable path + parent PID/start-time/path
```

仅 PID 会被重用；仅 exe 名称会碰撞；仅父 PID 也可能重用。采集失败、链路循环、父链过深或 path 无法确认时 fail closed。监视器要先启动并公布 ready 状态，launcher 要先写入 armed record，监视器确认根进程身份后才能放行目标命令。目标在 handshake 前快退即使返回 0 也不能视为验收成功。

Windows acceptance 要保存启动前后产品错误对话框快照，并且在被测树完全退出后保持有限 quiet window。quiet window 内新进程、错误对话框或身份不匹配都会重置或失败；不能只等待顶层 installer 返回。

## NSIS helper 的窄分类

electron-builder 的 NSIS 模板可能调用 PowerShell、`cmd.exe` 或 `find.exe` 做进程/能力 probe，其中 **精确** 的 no-match 分支会产生 `exit 1`。这不是全局成功码。

仅当以下条件全部成立时，才允许把 code 1 归为预期 probe：

1. code 确实为 1，且进程的 PID/start time/path/command line 已捕获；
2. image 是系统 PowerShell、`cmd.exe` 或 `find.exe` 的规范路径，不是同名任意文件；
3. command line 与项目已验证的 NSIS 模板 probe 完全匹配，而不是仅包含某个关键字；
4. 父链的每一边都由 PID、start time 和 path 匹配，且终止于同一次 armed installer/uninstaller root；
5. `cmd.exe` 与 `find.exe` 之间的关联也按精确父身份验证。

任何普通 PowerShell、任意 `find.exe`、未知命令行、缺失身份、另一个 Job Object 成员或非 1 的 exit 都是失败。不要添加“所有 helper exit 1 忽略”或按文件名/目录的宽泛 allowlist。

## TEMP 与 8.3 路径

NSIS uninstaller 可能复制到当前 TEMP 下的 `~nsu*.tmp` helper。`QueryFullProcessImageName` 有时给出 8.3 路径，因此只在以下狭窄情形规范化：文件仍可解析、解析后的完整路径位于可信的当前 TEMP 祖先内、名称与已验证的 NSIS helper 模式匹配、并且完整父链回到 armed root。不要因为路径字符串包含 `Temp`、`~` 或 `RUNNER~1` 就接受它，也不要为任意 TEMP executable 开豁免。

原始路径字符串不是文件身份：Windows 短路径、junction、大小写与用户目录别名都可能指向同一对象。安全判断应在打开目标后比较稳定文件身份（例如 volume serial + file index；其他平台用等价的 device + inode）并在解析后的可信根内验证 containment。测试要覆盖真实路径与别名路径指向同一对象、相似字符串指向不同对象、对象被替换、以及身份不可取得的 fail-closed 分支。只做 `realpath` 或字符串小写化不能证明身份。

## Deterministic asynchronous tests

Installer monitor、mock fetch、helper handshake 与退出观察要由被测事件触发的 deferred/promise、进程信号或受控 fake time 同步。短 `waitFor` 或固定 sleep 只能作为最终超时边界，不能作为步骤完成条件；提升任意 timeout 会把竞态延后到较慢 runner。对 release-critical 异步测试保留一个慢调度或重复执行的本地/canary profile，再进入完整 qualification。

## Deep upgrade acceptance

When deep acceptance is required, seed an isolated real-user-data fixture before installation; after the new version installs/starts, verify that the contract-listed schema, project, assets, recent state, or other data persists. Record fixture content, old-version source, and assertions as evidence. Do not use a successful install command as a substitute for data-preservation proof.

Uninstall remains a standard core check. Check only product-scoped residuals after the tested process tree exits; do not require the installer directory itself to disappear when the package manager legitimately leaves it behind.

## 常见边界

- 调整 NSIS、per-machine/per-user 或静默参数前先读项目配置与官方文档。
- 代码签名、自动更新、portable ZIP 和 release asset set 是独立决策；不要把 portable 文件混进 updater assets。
- 如 helper 分类要改动，先写 synthetic process-event 测试，覆盖合法 probe、相同名称但错误父链、PID reuse、未知 command line、8.3 非 TEMP 路径及 capture-before-exit 竞态。
