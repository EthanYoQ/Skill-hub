# 三个 yq Skill 的通用化结果

本轮根据用户的新指令，把 DSH 专项要求转换成目标项目自己的约束。
只改混合绑定及必要引用，其他内容能保留就保留。
未安装到全局，未提交或推送，未修改之前已有的六个 yq Skill。

上一轮四组待决定内容均已处理，没有剩余待决定的 DSH 执行依赖。
MIT LICENSE 的 DeepSeek 版权署名和来源记录继续保留。
它们属于许可证及来源信息，不是执行依赖。

## 结果与能力

| Skill | 本轮改动 | 保留的能力与案例 | 触发条件 |
| --- | --- | --- | --- |
| [yq-stable-tests](../../skills/01-agent-engineering/yq-stable-tests/SKILL.md) | 测试政策改由目标仓库决定。移除 DSH 异步 API 名称。将通用测试原则复制到本地引用。 | CI 端口冲突、共享路径和未完成清理的诊断；保留不以重试掩盖问题、真实入口验证、外部状态核验和负向对照。 | 新增或修改具有并发、共享资源、时钟、子进程或异步清理风险的测试；审查隔离或诊断偶发失败。 |
| [yq-clear-context](../../skills/01-agent-engineering/yq-clear-context/SKILL.md) | 本轮没有改动。 | 工具返回大量文本或说明重复时，指导有界输出、参数就地说明和资源发现路径。 | 工具定义、系统提示词片段、Skill 设计、上下文加载及多步流程。 |
| [yq-ui-checks](../../skills/07-media-content/yq-ui-checks/SKILL.md) | 固定字重改为既有主题层级。侧栏使用既有扩展机制。窗口适配使用应用自己的避让规则。 | 保留深浅色可读性、组件复用、Toast 生命周期、错误保留数据、菜单安全和设计评审。 | 新增或修改用户可见界面，或审查相关 PR。 |

字重 600、700 本身不再被禁止。它们必须属于目标应用既有的主题层级。
不得为了单个页面修改共享窗口避让量。页面调整仍需测试断言。
共享 agent idle 仍不能证明某条消息已经完成。
测试层级、命令、覆盖率门槛和外部服务要求由目标仓库决定。

## 逐项差异

本表只记录本轮相对于上一轮候选的差异。
新增 testing-principles.md 的原件是固定上游 testing.md 中三个相邻章节的字节片段。
没有把整套 DSH 测试政策、命令或目录规范迁移成通用要求。

| ID 与文件 | 原文 | 通用化改动 | 移除的绑定 | 保留的约束 |
| --- | --- | --- | --- | --- |
| G01<br>[skills/01-agent-engineering/yq-stable-tests/SKILL.md](../../skills/01-agent-engineering/yq-stable-tests/SKILL.md)<br>原候选或片段第 12 行 | <code>[the testing policy](https://github.com/deepseek-ai/deepseek-harness/blob/5badb15009ae1756c3afe0ae0cef1faafc290ccc/docs/testing.md)</code> | <code>the target repository's testing policy</code> | Remove the DSH test-tier/command policy dependency. | Same test evidence types and selection requirement; owning policy is the target repository. |
| G02<br>[skills/01-agent-engineering/yq-stable-tests/references/defensive-patterns.md](../../skills/01-agent-engineering/yq-stable-tests/references/defensive-patterns.md)<br>原候选或片段第 4 行 | <code>is a class of defect that actually shipped or nearly shipped here, stated as</code> | <code>is stated as</code> | Remove the copied reference identity claim about defects shipped in the DSH repository. | Bug-class rules, lifecycle/concurrency/subprocess/teardown scope remain. |
| G03<br>[skills/01-agent-engineering/yq-stable-tests/references/defensive-patterns.md](../../skills/01-agent-engineering/yq-stable-tests/references/defensive-patterns.md)<br>原候选或片段第 4 行 | <code>[testing.md](https://github.com/deepseek-ai/deepseek-harness/blob/5badb15009ae1756c3afe0ae0cef1faafc290ccc/docs/testing.md)</code> | <code>[testing principles](testing-principles.md)</code> | Replace the external DSH policy dependency with locally preserved generic principles. | Real entry path, world verification and resource ownership remain discoverable. |
| G04<br>[skills/01-agent-engineering/yq-stable-tests/references/defensive-patterns.md](../../skills/01-agent-engineering/yq-stable-tests/references/defensive-patterns.md)<br>原候选或片段第 16 行 | <code>a background job's completion races turn boundaries; `reader.close()` fires for both EOF and disposal.</code> | <code>A background job's completion races turn boundaries; a reader's close signal can represent either EOF or disposal.</code> | Replace a concrete reader API assumption with a portable warning about completion versus disposal. | Do not infer natural completion from a shared close signal; background completion can cross turns. |
| G05<br>[skills/01-agent-engineering/yq-stable-tests/references/defensive-patterns.md](../../skills/01-agent-engineering/yq-stable-tests/references/defensive-patterns.md)<br>原候选或片段第 16 行 | <code>`agent/status` or `whenIdle()`</code> | <code>shared agent status or a whole-agent idle signal</code> | Replace DSH asynchronous API names with the state semantics they illustrate. | Shared idle/running state does not prove one message completed; queueing, cancellation and interval-wide attribution remain verbatim. |
| G06<br>[skills/07-media-content/yq-ui-checks/SKILL.md](../../skills/07-media-content/yq-ui-checks/SKILL.md)<br>原候选或片段第 14 行 | <code>- **Font weight tops out at 500 in feature CSS you add or change.** Do not use 600+ for emphasis; differentiate with size or ink instead. The markdown typography tokens owned by ui-theme are the standing exception.</code> | <code>- **Font weight follows the existing theme typography scale in feature CSS you add or change.** Do not introduce an off-scale weight for emphasis; differentiate with size or ink instead. Markdown typography follows its owning theme tokens.</code> | Remove the DSH fixed 500 cap and named ui-theme exception; use the target design system ownership. | Theme-owned weight choices, no arbitrary emphasis weight, and size/ink alternatives remain. |
| G07<br>[skills/07-media-content/yq-ui-checks/SKILL.md](../../skills/07-media-content/yq-ui-checks/SKILL.md)<br>原候选或片段第 22 行 | <code>- **Right-sidebar content registers a slot in the existing sidebar**, never a separate sidebar.</code> | <code>- **When sidebar content extends an existing sidebar, use its existing extension mechanism**, never a separate sidebar.</code> | Remove the assumption that every application has a right-sidebar slot API. | Reuse the existing sidebar instead of creating a parallel sidebar; per-tab semantic icons unchanged. |
| G08<br>[skills/07-media-content/yq-ui-checks/SKILL.md](../../skills/07-media-content/yq-ui-checks/SKILL.md)<br>原候选或片段第 52 行 | <code>On macOS the titlebar clearance is `--dsh-frame-top-clearance`, consumed by Menu, Modal, and overlay primitives as their top safe margin — **never change the global variable to fix one page**. Add a scoped `[data-platform='darwin']` override on the page's own inset instead, and assert the override in the page's stylesheet spec.</code> | <code>On macOS use the application's existing titlebar clearance as the top safe margin for menus, modals, and overlays — **never change the shared clearance to fix one page**. Add a platform-scoped override on the page's own inset instead, and assert the override in a focused style or layout test.</code> | Remove the DSH clearance token, data-platform selector and stylesheet test naming convention. | Platform chrome adaptation, shared-versus-local ownership, page-scoped inset and required assertion remain. Total-offset review sentence unchanged. |
| G09<br>[skills/01-agent-engineering/yq-stable-tests/references/testing-principles.md](../../skills/01-agent-engineering/yq-stable-tests/references/testing-principles.md)<br>原候选或片段第 1 行 | <code>## Prefer the real implementation over a mock</code> | <code># Testing principles<br><br>The target repository owns its test tiers, commands, coverage thresholds, and external-service requirements.<br><br>## Prefer the real implementation over a mock</code> | Provide local generic guidance rather than the DSH repository policy; required ownership statement replaces the upstream repository-specific scope. | Reference guidance does not impose DSH tiers, commands or thresholds. |
| G10<br>[skills/01-agent-engineering/yq-stable-tests/references/testing-principles.md](../../skills/01-agent-engineering/yq-stable-tests/references/testing-principles.md)<br>原候选或片段第 3 行 | <code> Bridge tool-call tests keep the real tool registry and pipeline behind the scripted mock model: `makeBridgeHarness()` mounts the loop, session store, tool registry, and JSONL persistence with a `MockAdapter` as the only mock (packages/acp/acp/tests/harness.ts).</code> | <code> Bridge tool-call tests keep the real tool registry and pipeline behind the scripted mock model.</code> | Remove the DSH makeBridgeHarness/MockAdapter composition and package path example. | Keep real downstream registry/pipeline and mock only external/nondeterministic boundary. |
| G11<br>[skills/01-agent-engineering/yq-stable-tests/references/testing-principles.md](../../skills/01-agent-engineering/yq-stable-tests/references/testing-principles.md)<br>原候选或片段第 5 行 | <code>shipping Loader composition</code> | <code>shipping application composition</code> | Replace the DSH Loader owner with the actual shipping application composition. | Recovery tests still cover the shipping composition. |
| G12<br>[skills/01-agent-engineering/yq-stable-tests/references/testing-principles.md](../../skills/01-agent-engineering/yq-stable-tests/references/testing-principles.md)<br>原候选或片段第 13 行 | <code>Hand-built `ctx.plugin(...)` suites are insufficient: boot test-only `cordis.yml` through Loader and app/process</code> | <code>Hand-built in-process suites are insufficient: boot the test configuration through the application's real startup path</code> | Replace Cordis ctx.plugin/cordis.yml/Loader entry path with the target application real entry path. | Require a non-unit real-composition test, external-only mocks and externally visible/durable assertions. Opt-in scope unchanged. |
| G13<br>[skills/01-agent-engineering/yq-stable-tests/references/testing-principles.md](../../skills/01-agent-engineering/yq-stable-tests/references/testing-principles.md)<br>原候选或片段第 14 行 | <code>For a plugin without `inject` (bundle/composition plugins), a Loader smoke stays green when a default export replaces the required named exports — add an explicit `expect('default' in mod).toBe(false)` plus an `unwrapExports` round-trip assertion</code> | <code>For public export contracts, add explicit export-shape and consumer round-trip assertions</code> | Replace DSH named-export/default-export/inject/unwrapExports contract with the target public export contract. | Keep the negative control: introduce regression, observe failure, revert. |
| G14<br>[skills/01-agent-engineering/yq-stable-tests/references/testing-principles.md](../../skills/01-agent-engineering/yq-stable-tests/references/testing-principles.md)<br>原候选或片段第 15 行 | <code>runs built `lib/bin.js`</code> | <code>runs its built entry point</code> | Remove the DSH package build-output path. | Published bin must be tested under plain Node, rather than masked by source runners. |
| G15<br>[skills/01-agent-engineering/yq-stable-tests/references/testing-principles.md](../../skills/01-agent-engineering/yq-stable-tests/references/testing-principles.md)<br>原候选或片段第 15 行 | <code> (the Node program bootstrap `lib/process.js`)</code> | 删除该 DSH 路径示例。 | Remove the DSH bootstrap output path example. | Non-index runtime entries remain in scope. |
| G16<br>[skills/01-agent-engineering/yq-stable-tests/references/testing-principles.md](../../skills/01-agent-engineering/yq-stable-tests/references/testing-principles.md)<br>原候选或片段第 15 行 | <code> (`packages/sdk/server/tests/built-scope-carrier.e2e.ts`)</code> | 删除该 DSH 路径示例。 | Remove the DSH SDK test path example. | Singleton modules shared across bundles remain in scope. |
| G17<br>[skills/01-agent-engineering/yq-stable-tests/references/testing-principles.md](../../skills/01-agent-engineering/yq-stable-tests/references/testing-principles.md)<br>原候选或片段第 15 行 | <code> (`packages/examples/*/tests/built-bin.e2e.ts`, `packages/ptc-runtime/ptc-runtime-node/tests/built-lib.e2e.ts`)</code> | 删除该 DSH 路径示例。 | Remove the DSH built-artifact smoke test paths. | Built-artifact smoke tests must remain green; genuinely missing config must exit non-zero. |

## 本轮字节检查

| 文件 | 改前 SHA-256 | 改后 SHA-256 | 编辑范围数 |
| --- | --- | --- | --- |
| [skills/01-agent-engineering/yq-stable-tests/SKILL.md](../../skills/01-agent-engineering/yq-stable-tests/SKILL.md) | `a17a5c6e602a63008c800844f46c97a8c10ce2b01208a8837313d121a2c9c9b6` | `776a76abc2240ef2f58ab1a798d5dbfff05218bcd4c7dde40debb4f924c95608` | 1 |
| [skills/01-agent-engineering/yq-stable-tests/references/defensive-patterns.md](../../skills/01-agent-engineering/yq-stable-tests/references/defensive-patterns.md) | `9ddcd490600c1d19c5ae273e6301bf2f182a5db13f71d0bbb51e6eb0846d3b28` | `796e871effb10239882c8fb7ae90fa78a698d64930835bd1fe0bb045b8423d34` | 4 |
| [skills/07-media-content/yq-ui-checks/SKILL.md](../../skills/07-media-content/yq-ui-checks/SKILL.md) | `708203b225a796a7a45cebcdb0de433efa21625b207c18dfc4e870f65a3114b9` | `76b6df2187a2d5fb1ff6d995d64bc3f61dbe6f034f680d8def769552e98c3543` | 3 |
| [skills/01-agent-engineering/yq-stable-tests/references/testing-principles.md](../../skills/01-agent-engineering/yq-stable-tests/references/testing-principles.md) | `169213d459576a8f49e8fc2da3fada19417f8b6cc2467155b94564514f31f1cc` | `7847d29c7d965209e2be36d8c1901f7c8436088e69bf684b683db11f03a0cfdb` | 9 |

新增参考的固定来源是 deepseek-ai/deepseek-harness，commit 为：
`5badb15009ae1756c3afe0ae0cef1faafc290ccc`。

来源片段包含 Prefer the real implementation over a mock、Verify the world, not the self-report、Test the real entry path。
它们的通用正文尽量保留原文。
只把 Cordis/Loader、内部工具名和包路径改成真实应用入口及公共契约。

**允许范围之外的原文保留检查通过。**

- 按登记的 17 个字节范围重建四个文件，结果与实际文件一致。
- 本轮未改的 1,389 个既有文件哈希保持一致。
- yq-clear-context、CI diagnosis 参考和三个 LICENSE 本轮逐字节未改。
- 三个 Skill 均通过平台名称与 frontmatter 检查。
- 六个本地引用链接均存在。
- 源于 DSH 的执行名称、政策链接、组件包和内部路径扫描结果为零。
- 原来的六个 yq Skill 及其来源条目未改。
- 索引名称、description 和路径没有变化，不需要重建索引。
- 来源记录只更新新候选 yq-stable-tests、yq-ui-checks 的适配状态、说明和证据。

DSH 字符扫描不包含 LICENSE 版权署名、来源记录及本审计报告。
扫描用于补充逐项语义复核，不能独自证明通用能力完整。

## 行为检查范围

独立检查使用三个案例，检查目标仓库政策、既有主题层级及异步归因规则。
三个离线前向案例通过，结果如下。

| 案例 | 实际技能应用结果 |
| --- | --- |
| 目标仓库使用 85% coverage、可选真实 API，并有端口及路径碰撞 | 遵守目标仓库门槛，不引入 DSH 的 100% 门槛或命令。分别识别资源碰撞和超时后退出 0 的报告问题。保持只读诊断边界。 |
| 现有 heading 字重 700，新加 650，单页修改共享避让量 | 允许现有 700，拒绝任意增加 650。要求使用实际平台 class 调整页面 inset，保留总偏移核验和 Toast 宿主寿命要求。 |
| 两条消息共享 idle，后一条在启动前取消 | 不把最后输出归因于后一条消息。要求消息级证据；证据不足时只报告区间输出。保持审计权限边界。 |

独立复核确认真实下游实现、外部状态验证、资源清理、真实入口和负向对照仍保留。
按 Prove It Works 原则复核实际文件字节差异，而非只看 frontmatter 验证结果。
没有执行真实产品、CI 或上游完整验证流程。
不宣称沿用上游全部验证结论。

## 审计材料

本轮缓存位于 .runtime/.cache/yq-dsh-adapt-20261005/generalization/。
changes.json 包含精确编辑范围；verification.json 包含检查结果。
verify.py 可重新检查登记范围之外是否发生变化。
candidate.diff 展示全部本轮正文差异。

缓存沿用父目录 retention.json 的保留原因和 2026-11-05 到期日期。
上一轮报告保留为历史记录，以本报告作为当前通用化状态。
