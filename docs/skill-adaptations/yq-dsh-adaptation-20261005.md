> 历史候选报告。四组待决定项已在后续通用化中处理。当前状态见 [通用化结果](yq-dsh-generalization-20261005.md)。

# 三个 yq Skill 的最小删除适配记录

已完成三个本地候选、逐项差异表、来源记录和仓库索引。
没有安装到全局，没有提交或推送，没有修改已有 yq Skill。

本次保留原文，只执行允许的名称变更、DSH 片段删除、链接目标调整和索引更新。
没有翻译 description，没有新增工作流程，也没有把严格或意见性的规则视作 DSH 专用内容。
四组混合内容无法安全分离，已保留原文并列为待决定项。
因此，本次候选尚未完全去除 DSH 依赖。

## 名称、作用与触发条件

| 上游 | 本地候选 | 具体作用与案例 | 触发条件 |
| --- | --- | --- | --- |
| dsh-ci-test-reliability | [yq-stable-tests](../../skills/01-agent-engineering/yq-stable-tests/SKILL.md) | 两个 CI 进程抢占同一端口或临时路径时，按资源所有权、原子分配和清理完成信号定位问题。避免靠重试或整套串行掩盖问题。 | 新增或修改涉及并发、共享资源、时钟、全局状态、子进程、网络监听或异步清理的测试；诊断偶发失败；审查测试隔离。 |
| agent-experience | [yq-clear-context](../../skills/01-agent-engineering/yq-clear-context/SKILL.md) | 工具返回几十万字符且参数规则重复时，指导提供有界摘要和发现入口，把参数规则放回参数说明，并测量上下文开销。 | 编写或修改工具名称、说明、参数 schema、系统提示词片段；设计 Skill、上下文加载或多步流程。 |
| dsh-client-ui-ux | [yq-ui-checks](../../skills/07-media-content/yq-ui-checks/SKILL.md) | 删除操作关闭面板后 Toast 消失时，要求 Toast 的宿主比面板存活更久。还可审查失败时保留数据、菜单裁切和双主题可读性。 | 新增或修改用户可见 GUI 行为，或审查此类 PR。 |

yq-stable-tests 主要治理偶发失败，不保证缩短 CI 时间。
如果耗时来自反复重跑或资源冲突，它可能减少这些浪费。

## 固定原件与引用处理

上游：[https://github.com/deepseek-ai/deepseek-harness](https://github.com/deepseek-ai/deepseek-harness)。

固定 commit：`5badb15009ae1756c3afe0ae0cef1faafc290ccc`。14 个读取文件均核对 Git blob ID 和 SHA-256。

agent-experience 的入口是符号链接，本次使用其真实目标内容。

[.agents/skills/agent-experience/SKILL.md:1](https://github.com/deepseek-ai/deepseek-harness/blob/5badb15009ae1756c3afe0ae0cef1faafc290ccc/.agents/skills/agent-experience/SKILL.md#L1) → [packages/preset/agent-preset/skills/agent-experience/SKILL.md:1](https://github.com/deepseek-ai/deepseek-harness/blob/5badb15009ae1756c3afe0ae0cef1faafc290ccc/packages/preset/agent-preset/skills/agent-experience/SKILL.md#L1)。

| 已读引用 | 处理 |
| --- | --- |
| [.agents/skills/dsh-ci-test-reliability/references/ci-flake-diagnosis.md:1](https://github.com/deepseek-ai/deepseek-harness/blob/5badb15009ae1756c3afe0ae0cef1faafc290ccc/.agents/skills/dsh-ci-test-reliability/references/ci-flake-diagnosis.md#L1) | 原字节复制，没有改动。 |
| [docs/defensive-patterns.md:1](https://github.com/deepseek-ai/deepseek-harness/blob/5badb15009ae1756c3afe0ae0cef1faafc290ccc/docs/defensive-patterns.md#L1) | 复制通用参考，删除明确 DSH 片段并调整链接；混合 API 句保留待决定。 |
| [docs/testing.md:1](https://github.com/deepseek-ai/deepseek-harness/blob/5badb15009ae1756c3afe0ae0cef1faafc290ccc/docs/testing.md#L1) | 完整读取。DSH 测试分层、命令与通用要求混合。引用保留，指向固定 commit，依赖待决定。 |
| [snapshots/AGENTS.md:1](https://github.com/deepseek-ai/deepseek-harness/blob/5badb15009ae1756c3afe0ae0cef1faafc290ccc/snapshots/AGENTS.md#L1) | 读取后删除 DSH recorded-session 指令引用；不复制 DSH 场景目录、录制和重放规范。 |
| [.agents/skills/dsh-pre-push-checks/SKILL.md:1](https://github.com/deepseek-ai/deepseek-harness/blob/5badb15009ae1756c3afe0ae0cef1faafc290ccc/.agents/skills/dsh-pre-push-checks/SKILL.md#L1) | 读取后链接指向已有 yq-pre-push-checks，没有修改现有技能。 |
| [.agents/skills/dsh-prose-standard/SKILL.md:1](https://github.com/deepseek-ai/deepseek-harness/blob/5badb15009ae1756c3afe0ae0cef1faafc290ccc/.agents/skills/dsh-prose-standard/SKILL.md#L1) | 读取后链接指向已有 yq-technical-writing，没有修改现有技能。 |
| [.agents/notes/implemented/architecture/2026-08-23-locale-owned-client-ui-copy.md:1](https://github.com/deepseek-ai/deepseek-harness/blob/5badb15009ae1756c3afe0ae0cef1faafc290ccc/.agents/notes/implemented/architecture/2026-08-23-locale-owned-client-ui-copy.md#L1) | 读取后删除 Cordis、typed t 和 DSH client 包的 locale ownership 引用。 |
| [docs/web-styling.md:1](https://github.com/deepseek-ai/deepseek-harness/blob/5badb15009ae1756c3afe0ae0cef1faafc290ccc/docs/web-styling.md#L1) | 读取后删除 DSH styling ownership 引用。混合字体与窗口规则保留待决定。 |
| [packages/client/ui-primitives/README.md:1](https://github.com/deepseek-ai/deepseek-harness/blob/5badb15009ae1756c3afe0ae0cef1faafc290ccc/packages/client/ui-primitives/README.md#L1) | 读取后删除 DSH 组件目录所有权引用。sidebar slot 规则证据不足，整条保留。 |
| [LICENSE:1](https://github.com/deepseek-ai/deepseek-harness/blob/5badb15009ae1756c3afe0ae0cef1faafc290ccc/LICENSE#L1) | MIT LICENSE 原字节复制到三个候选目录。来源署名不属于应删除的运行依赖。 |

三个入口没有引用需迁移的 templates 或 scripts。CI diagnosis 参考已完整复制。
未复制的混合 DSH 政策通过固定 commit 链接保留。没有复制整套 DSH 仓库依赖树。

## 逐项变更表

每个差异均记录原文位置、改动、依据和能力影响。
评审人员名单在报告中使用占位符；精确原文仍在本地审计清单与固定上游文件内。

| ID、文件及原文位置 | 原文 | 改动 | DSH 绑定依据或允许理由 | 能力影响 |
| --- | --- | --- | --- | --- |
| C01<br>[skills/01-agent-engineering/yq-stable-tests/SKILL.md](../../skills/01-agent-engineering/yq-stable-tests/SKILL.md)<br>[.agents/skills/dsh-ci-test-reliability/SKILL.md:2](https://github.com/deepseek-ai/deepseek-harness/blob/5badb15009ae1756c3afe0ae0cef1faafc290ccc/.agents/skills/dsh-ci-test-reliability/SKILL.md#L2) | <code>name: dsh-ci-test-reliability</code> | <code>name: yq-stable-tests</code> | User-authorized simple yq name. | Only skill identity changes. |
| C02<br>[skills/01-agent-engineering/yq-stable-tests/SKILL.md](../../skills/01-agent-engineering/yq-stable-tests/SKILL.md)<br>[.agents/skills/dsh-ci-test-reliability/SKILL.md:3](https://github.com/deepseek-ai/deepseek-harness/blob/5badb15009ae1756c3afe0ae0cef1faafc290ccc/.agents/skills/dsh-ci-test-reliability/SKILL.md#L3) | <code>DeepSeek Harness </code> | 删除该片段，不补写替代规则。 | Upstream product name in description. | Generic trigger and risks remain unchanged. |
| C03<br>[skills/01-agent-engineering/yq-stable-tests/SKILL.md](../../skills/01-agent-engineering/yq-stable-tests/SKILL.md)<br>[.agents/skills/dsh-ci-test-reliability/SKILL.md:6](https://github.com/deepseek-ai/deepseek-harness/blob/5badb15009ae1756c3afe0ae0cef1faafc290ccc/.agents/skills/dsh-ci-test-reliability/SKILL.md#L6) | <code># Reliable DSH CI tests</code> | <code># Reliable CI tests</code> | DSH product abbreviation in heading. | No rule changes. |
| C04<br>[skills/01-agent-engineering/yq-stable-tests/SKILL.md](../../skills/01-agent-engineering/yq-stable-tests/SKILL.md)<br>[.agents/skills/dsh-ci-test-reliability/SKILL.md:3](https://github.com/deepseek-ai/deepseek-harness/blob/5badb15009ae1756c3afe0ae0cef1faafc290ccc/.agents/skills/dsh-ci-test-reliability/SKILL.md#L3) | <code>dsh-pre-push-checks separately</code> | <code>pre-push-checks separately</code> | DSH skill prefix; the existing yq-pre-push-checks is its local adaptation. | Command selection remains delegated; local dependency is not claimed byte-equivalent. |
| C05<br>[skills/01-agent-engineering/yq-stable-tests/SKILL.md](../../skills/01-agent-engineering/yq-stable-tests/SKILL.md)<br>[.agents/skills/dsh-ci-test-reliability/SKILL.md:12](https://github.com/deepseek-ai/deepseek-harness/blob/5badb15009ae1756c3afe0ae0cef1faafc290ccc/.agents/skills/dsh-ci-test-reliability/SKILL.md#L12) | <code>../../../docs/testing.md</code> | <code>https://github.com/deepseek-ai/deepseek-harness/blob/5badb15009ae1756c3afe0ae0cef1faafc290ccc/docs/testing.md</code> | Mixed DSH policy and generic evidence-selection instruction cannot be safely separated. Retarget the uncopied DSH document to its immutable original. | Generic selection requirement is restored verbatim. The DSH policy dependency remains pending; no equivalent policy invented. |
| C06<br>[skills/01-agent-engineering/yq-stable-tests/SKILL.md](../../skills/01-agent-engineering/yq-stable-tests/SKILL.md)<br>[.agents/skills/dsh-ci-test-reliability/SKILL.md:13](https://github.com/deepseek-ai/deepseek-harness/blob/5badb15009ae1756c3afe0ae0cef1faafc290ccc/.agents/skills/dsh-ci-test-reliability/SKILL.md#L13) | <code>../../../docs/defensive-patterns.md</code> | <code>references/defensive-patterns.md</code> | Copied reusable reference into this skill. | Reference remains accessible. |
| C07<br>[skills/01-agent-engineering/yq-stable-tests/SKILL.md](../../skills/01-agent-engineering/yq-stable-tests/SKILL.md)<br>[.agents/skills/dsh-ci-test-reliability/SKILL.md:15](https://github.com/deepseek-ai/deepseek-harness/blob/5badb15009ae1756c3afe0ae0cef1faafc290ccc/.agents/skills/dsh-ci-test-reliability/SKILL.md#L15) | <code>- For recorded-session scenarios, also follow [the snapshot instructions](../../../snapshots/AGENTS.md).<br></code> | 删除该片段，不补写替代规则。 | snapshots/AGENTS.md prescribes DSH session filenames, replay/record entry points and snapshot profiles. | DSH recorded-session instructions no longer imposed. |
| C08<br>[skills/01-agent-engineering/yq-stable-tests/SKILL.md](../../skills/01-agent-engineering/yq-stable-tests/SKILL.md)<br>[.agents/skills/dsh-ci-test-reliability/SKILL.md:16](https://github.com/deepseek-ai/deepseek-harness/blob/5badb15009ae1756c3afe0ae0cef1faafc290ccc/.agents/skills/dsh-ci-test-reliability/SKILL.md#L16) | <code>[dsh-pre-push-checks](../dsh-pre-push-checks/SKILL.md) after</code> | <code>[pre-push-checks](../yq-pre-push-checks/SKILL.md) after</code> | Existing locally adapted pre-push skill; delete DSH label prefix and adjust target. | Retains delegation without copying or changing existing yq skill. |
| C09<br>[skills/01-agent-engineering/yq-stable-tests/SKILL.md](../../skills/01-agent-engineering/yq-stable-tests/SKILL.md)<br>[.agents/skills/dsh-ci-test-reliability/SKILL.md:131](https://github.com/deepseek-ai/deepseek-harness/blob/5badb15009ae1756c3afe0ae0cef1faafc290ccc/.agents/skills/dsh-ci-test-reliability/SKILL.md#L131) | <code>[dsh-pre-push-checks](../dsh-pre-push-checks/SKILL.md).</code> | <code>[pre-push-checks](../yq-pre-push-checks/SKILL.md).</code> | Same local dependency mapping. | No automatic push authorization added. |
| C10<br>[skills/01-agent-engineering/yq-stable-tests/references/defensive-patterns.md](../../skills/01-agent-engineering/yq-stable-tests/references/defensive-patterns.md)<br>[docs/defensive-patterns.md:3](https://github.com/deepseek-ai/deepseek-harness/blob/5badb15009ae1756c3afe0ae0cef1faafc290ccc/docs/defensive-patterns.md#L3) | <code>English &#124; [中文](defensive-patterns.zh.md)<br></code> | 删除该片段，不补写替代规则。 | DSH documentation language navigation points to the uncopied DSH translation. | Removes repository navigation, not the English rules. |
| C11<br>[skills/01-agent-engineering/yq-stable-tests/references/defensive-patterns.md](../../skills/01-agent-engineering/yq-stable-tests/references/defensive-patterns.md)<br>[docs/defensive-patterns.md:5](https://github.com/deepseek-ai/deepseek-harness/blob/5badb15009ae1756c3afe0ae0cef1faafc290ccc/docs/defensive-patterns.md#L5) | <code>(testing.md)</code> | <code>(https://github.com/deepseek-ai/deepseek-harness/blob/5badb15009ae1756c3afe0ae0cef1faafc290ccc/docs/testing.md)</code> | Same mixed DSH testing-policy dependency. Necessary target change after copying the reference. | Entire generic counterpart sentence is restored verbatim. External policy dependency remains pending. |
| C12<br>[skills/01-agent-engineering/yq-stable-tests/references/defensive-patterns.md](../../skills/01-agent-engineering/yq-stable-tests/references/defensive-patterns.md)<br>[docs/defensive-patterns.md:13](https://github.com/deepseek-ai/deepseek-harness/blob/5badb15009ae1756c3afe0ae0cef1faafc290ccc/docs/defensive-patterns.md#L13) | <code> `LlmAdapter.stream()` implementations may throw or emit `finish {kind:'error'&#124;'aborted'}`, but `LlmRuntime.stream()` exposes model-request failures only as terminal finish chunks; middleware and consumer defects remain thrown.</code> | 删除该片段，不补写替代规则。 | Exact DSH adapter/runtime public API contract stated in this upstream reference. | Generic public-outcome normalization, rationale and consumer verification stay verbatim. |
| C13<br>[skills/01-agent-engineering/yq-stable-tests/references/defensive-patterns.md](../../skills/01-agent-engineering/yq-stable-tests/references/defensive-patterns.md)<br>[docs/defensive-patterns.md:17](https://github.com/deepseek-ai/deepseek-harness/blob/5badb15009ae1756c3afe0ae0cef1faafc290ccc/docs/defensive-patterns.md#L17) | <code>`agent.followup()` has no per-message completion or result; </code> | 删除该片段，不补写替代规则。 | Explicit agent.followup per-message result/completion contract belongs to the DSH agent API in this source. | All generic background-job timing, reader lifecycle, run ownership, interval attribution and impossible-wait rules remain unchanged. Mixed agent/status and whenIdle sentence remains pending. |
| C14<br>[skills/01-agent-engineering/yq-clear-context/SKILL.md](../../skills/01-agent-engineering/yq-clear-context/SKILL.md)<br>[packages/preset/agent-preset/skills/agent-experience/SKILL.md:2](https://github.com/deepseek-ai/deepseek-harness/blob/5badb15009ae1756c3afe0ae0cef1faafc290ccc/packages/preset/agent-preset/skills/agent-experience/SKILL.md#L2) | <code>name: agent-experience</code> | <code>name: yq-clear-context</code> | User-authorized simple yq name; source symlink resolved. | Description and entire body remain byte-identical. |
| C15<br>[skills/07-media-content/yq-ui-checks/SKILL.md](../../skills/07-media-content/yq-ui-checks/SKILL.md)<br>[.agents/skills/dsh-client-ui-ux/SKILL.md:2](https://github.com/deepseek-ai/deepseek-harness/blob/5badb15009ae1756c3afe0ae0cef1faafc290ccc/.agents/skills/dsh-client-ui-ux/SKILL.md#L2) | <code>name: dsh-client-ui-ux</code> | <code>name: yq-ui-checks</code> | User-authorized simple yq name. | Only skill identity changes. |
| C16<br>[skills/07-media-content/yq-ui-checks/SKILL.md](../../skills/07-media-content/yq-ui-checks/SKILL.md)<br>[.agents/skills/dsh-client-ui-ux/SKILL.md:3](https://github.com/deepseek-ai/deepseek-harness/blob/5badb15009ae1756c3afe0ae0cef1faafc290ccc/.agents/skills/dsh-client-ui-ux/SKILL.md#L3) | <code>Design and review DeepSeek Harness client UI changes</code> | <code>Design and review client UI changes</code> | DSH product name in description. | UI scope and triggers remain. |
| C17<br>[skills/07-media-content/yq-ui-checks/SKILL.md](../../skills/07-media-content/yq-ui-checks/SKILL.md)<br>[.agents/skills/dsh-client-ui-ux/SKILL.md:3](https://github.com/deepseek-ai/deepseek-harness/blob/5badb15009ae1756c3afe0ae0cef1faafc290ccc/.agents/skills/dsh-client-ui-ux/SKILL.md#L3) | <code> in packages/client</code> | 删除该片段，不补写替代规则。 | Exact DSH client package scope. | Trigger no longer restricted to the DSH package tree. |
| C18<br>[skills/07-media-content/yq-ui-checks/SKILL.md](../../skills/07-media-content/yq-ui-checks/SKILL.md)<br>[.agents/skills/dsh-client-ui-ux/SKILL.md:6](https://github.com/deepseek-ai/deepseek-harness/blob/5badb15009ae1756c3afe0ae0cef1faafc290ccc/.agents/skills/dsh-client-ui-ux/SKILL.md#L6) | <code># DeepSeek Harness Client UI/UX</code> | <code># Client UI/UX</code> | DSH product name in heading. | No rule changes. |
| C19<br>[skills/07-media-content/yq-ui-checks/SKILL.md](../../skills/07-media-content/yq-ui-checks/SKILL.md)<br>[.agents/skills/dsh-client-ui-ux/SKILL.md:8](https://github.com/deepseek-ai/deepseek-harness/blob/5badb15009ae1756c3afe0ae0cef1faafc290ccc/.agents/skills/dsh-client-ui-ux/SKILL.md#L8) | <code>[dsh-prose-standard](../dsh-prose-standard/SKILL.md)</code> | <code>[prose-standard](../../08-writing-marketing/yq-technical-writing/SKILL.md)</code> | Existing local adaptation covers sentence-level prose; delete DSH label prefix and retarget. | Dependency changes to existing yq skill; no equivalence of all upstream rules asserted. |
| C20<br>[skills/07-media-content/yq-ui-checks/SKILL.md](../../skills/07-media-content/yq-ui-checks/SKILL.md)<br>[.agents/skills/dsh-client-ui-ux/SKILL.md:8](https://github.com/deepseek-ai/deepseek-harness/blob/5badb15009ae1756c3afe0ae0cef1faafc290ccc/.agents/skills/dsh-client-ui-ux/SKILL.md#L8) | <code>; locale ownership follows the [locale-owned copy decision](../../notes/implemented/architecture/2026-08-23-locale-owned-client-ui-copy.md); styling ownership and token rules live in [docs/web-styling.md](../../../docs/web-styling.md) and the [ui-primitives component catalog](../../../packages/client/ui-primitives/README.md#component-catalog)</code> | 删除该片段，不补写替代规则。 | DSH locale ADR and web-styling/catalog ownership clauses refer to Cordis and DSH client packages. | Only separable DSH ownership references removed. The generic judgment/no-duplicate-rules sentence remains unchanged. |
| C21<br>[skills/07-media-content/yq-ui-checks/SKILL.md](../../skills/07-media-content/yq-ui-checks/SKILL.md)<br>[.agents/skills/dsh-client-ui-ux/SKILL.md:12](https://github.com/deepseek-ai/deepseek-harness/blob/5badb15009ae1756c3afe0ae0cef1faafc290ccc/.agents/skills/dsh-client-ui-ux/SKILL.md#L12) | <code> (the Plugins page is the usual reference for full-page surfaces)</code> | 删除该片段，不补写替代规则。 | Named DSH product page used as repository-specific design reference. | Target page and nearest established sibling search remain. |
| C22<br>[skills/07-media-content/yq-ui-checks/SKILL.md](../../skills/07-media-content/yq-ui-checks/SKILL.md)<br>[.agents/skills/dsh-client-ui-ux/SKILL.md:15](https://github.com/deepseek-ai/deepseek-harness/blob/5badb15009ae1756c3afe0ae0cef1faafc290ccc/.agents/skills/dsh-client-ui-ux/SKILL.md#L15) | <code> (13px is the established row/detail size)</code> | 删除该片段，不补写替代规则。 | Fixed local typography scale; web-styling locates values in DSH ui-theme. | Existing theme/page typography-scale selection remains. |
| C24<br>[skills/07-media-content/yq-ui-checks/SKILL.md](../../skills/07-media-content/yq-ui-checks/SKILL.md)<br>[.agents/skills/dsh-client-ui-ux/SKILL.md:29](https://github.com/deepseek-ai/deepseek-harness/blob/5badb15009ae1756c3afe0ae0cef1faafc290ccc/.agents/skills/dsh-client-ui-ux/SKILL.md#L29) | <code> (a `shell.overlay` entry, as RowActionToast does)</code> | 删除该片段，不补写替代规则。 | Named DSH shell service and component example. | Toast owner must still outlive the reporting surface. |
| C26<br>[skills/07-media-content/yq-ui-checks/SKILL.md](../../skills/07-media-content/yq-ui-checks/SKILL.md)<br>[.agents/skills/dsh-client-ui-ux/SKILL.md:62](https://github.com/deepseek-ai/deepseek-harness/blob/5badb15009ae1756c3afe0ae0cef1faafc290ccc/.agents/skills/dsh-client-ui-ux/SKILL.md#L62) | <code> (roster as of 2026-09: &lt;upstream reviewer roster&gt;; update this list here when membership changes)</code> | 删除该片段，不补写替代规则。 | DSH design/product reviewer membership list. | Mandatory design/product review and requesting an appropriate reviewer remain. |

## 保留待决定的四组内容

这些内容实际保留在候选内，不能称为已经解除 DSH 绑定。

1. [skills/07-media-content/yq-ui-checks/SKILL.md](../../skills/07-media-content/yq-ui-checks/SKILL.md)：字体 500 上限、禁止 600+、以字号或颜色强调和 ui-theme 例外处于同一条规则。不能删除 DSH 部分而保证通用能力与要求强度不变。

```text
- **Font weight tops out at 500 in feature CSS you add or change.** Do not use 600+ for emphasis; differentiate with size or ink instead. The markdown typography tokens owned by ui-theme are the standing exception.
```

2. [skills/01-agent-engineering/yq-stable-tests/SKILL.md](../../skills/01-agent-engineering/yq-stable-tests/SKILL.md)：CI 证据类型选择仍引用 DSH testing policy，defensive reference 的 counterpart 链接也指向该政策。保留通用句，不自行编写通用等价命令。

```text
- Use [the testing policy](https://github.com/deepseek-ai/deepseek-harness/blob/5badb15009ae1756c3afe0ae0cef1faafc290ccc/docs/testing.md) to select unit, coverage, expected-output, snapshot, browser, or real-API evidence.
```

3. [skills/01-agent-engineering/yq-stable-tests/references/defensive-patterns.md](../../skills/01-agent-engineering/yq-stable-tests/references/defensive-patterns.md)：agent/status、whenIdle 与并发 follow-up 的归因限制位于同一句。删除整句会丢失通用的异步归因要求。

```text
Never treat `agent/status` or `whenIdle()` as the result of one follow-up: several queued follow-ups, steering, and injected work may share one `running` interval, while cancellation or disposal can discard unstarted items.
```

4. [skills/07-media-content/yq-ui-checks/SKILL.md](../../skills/07-media-content/yq-ui-checks/SKILL.md)：DSH titlebar token 与页面局部调整、禁止为单页修改全局变量和样式断言混合。整个混合部分原样保留。

```text
On macOS the titlebar clearance is `--dsh-frame-top-clearance`, consumed by Menu, Modal, and overlay primitives as their top safe margin — **never change the global variable to fix one page**. Add a scoped `[data-platform='darwin']` override on the page's own inset instead, and assert the override in the page's stylesheet spec.
```

右侧栏 slot 规则不列为已确认的 DSH 专用约束。证据不足，本次整条保留。

## 文件与哈希

| 文件 | 原文 SHA-256 | 候选 SHA-256 | 编辑数 |
| --- | --- | --- | --- |
| [skills/01-agent-engineering/yq-stable-tests/SKILL.md](../../skills/01-agent-engineering/yq-stable-tests/SKILL.md) | `58e5de5c9cf7061eb4f39240dfcadc2e2e4a0cbf124f9c268f7e878bbf451dc1` | `a17a5c6e602a63008c800844f46c97a8c10ce2b01208a8837313d121a2c9c9b6` | 9 |
| [skills/01-agent-engineering/yq-stable-tests/references/ci-flake-diagnosis.md](../../skills/01-agent-engineering/yq-stable-tests/references/ci-flake-diagnosis.md) | `9fb8d3a56e9e90331dd2155f5bc55a9bea7d000f7dd2b519a4e59524a97f2b44` | `9fb8d3a56e9e90331dd2155f5bc55a9bea7d000f7dd2b519a4e59524a97f2b44` | 0 |
| [skills/01-agent-engineering/yq-stable-tests/references/defensive-patterns.md](../../skills/01-agent-engineering/yq-stable-tests/references/defensive-patterns.md) | `919d27a033c655ea6187496872caa4aa9babf08d87179562ca23545301108bb1` | `9ddcd490600c1d19c5ae273e6301bf2f182a5db13f71d0bbb51e6eb0846d3b28` | 4 |
| [skills/01-agent-engineering/yq-clear-context/SKILL.md](../../skills/01-agent-engineering/yq-clear-context/SKILL.md) | `1244928710cb7e399325c416e80312037d4da249559a09fe289515cc66ee1752` | `2134b9c0a5093cd5bff9d1ecbef05194cf4d163b3ff1c6f859c8199d290dad38` | 1 |
| [skills/07-media-content/yq-ui-checks/SKILL.md](../../skills/07-media-content/yq-ui-checks/SKILL.md) | `2b00d1e4d079a45beda500fbfff9d7f1e2f8f0ea0e10b0f6ad8a9d660a7036ff` | `708203b225a796a7a45cebcdb0de433efa21625b207c18dfc4e870f65a3114b9` | 10 |
| [skills/01-agent-engineering/yq-stable-tests/LICENSE](../../skills/01-agent-engineering/yq-stable-tests/LICENSE) | `ebb4f09972aee8608be255debaf78451a68e95c290f55c240dec2ecfa16ea6be` | `ebb4f09972aee8608be255debaf78451a68e95c290f55c240dec2ecfa16ea6be` | 0 |
| [skills/01-agent-engineering/yq-clear-context/LICENSE](../../skills/01-agent-engineering/yq-clear-context/LICENSE) | `ebb4f09972aee8608be255debaf78451a68e95c290f55c240dec2ecfa16ea6be` | `ebb4f09972aee8608be255debaf78451a68e95c290f55c240dec2ecfa16ea6be` | 0 |
| [skills/07-media-content/yq-ui-checks/LICENSE](../../skills/07-media-content/yq-ui-checks/LICENSE) | `ebb4f09972aee8608be255debaf78451a68e95c290f55c240dec2ecfa16ea6be` | `ebb4f09972aee8608be255debaf78451a68e95c290f55c240dec2ecfa16ea6be` | 0 |

## 索引与来源记录

| 文件 | 允许的变化 | 检查 |
| --- | --- | --- |
| [_meta/skills-lock.json](../../_meta/skills-lock.json) | 新增三条路径与中文索引简介；更新重建日期、数量。 | 既有条目内容未改。 |
| [_meta/by-name.md](../../_meta/by-name.md) | 自动重建 A–Z 索引，新增三项并更新编号、数量。 | 使用仓库脚本。 |
| [_meta/by-domain.md](../../_meta/by-domain.md) | 自动重建能力域索引，新增三项并更新数量。 | 使用仓库脚本。 |
| [_meta/skill-upstreams.json](../../_meta/skill-upstreams.json) | 新增三条固定 commit 来源和适配记录；更新日期、数量。 | 既有条目内容未改。 |

新来源分类为 open-source，更新策略为 none，不允许自动覆盖个人适配版本。
当前索引为 55 个共享技能、8 个项目技能，共 63 个。
中文说明只写入索引，没有翻译候选 frontmatter 的英文 description。

## 验收结论

**原文保留检查通过。**

- 三个候选通过平台 quick_validate.py 的名称与 frontmatter 检查。
- 八个复制文件通过 24 个登记字节范围的重建检查。
- 范围以外的正文、标点、换行、规则顺序和验证要求未改。
- yq-clear-context 的 description 和全部正文与真实目标逐字节一致。
- CI diagnosis 参考及三个 LICENSE 与原件逐字节一致。
- 五个本地 Markdown 链接存在；远程政策链接固定到同一 commit。
- 1,381 个既有 skill、项目或非目标元数据文件哈希未变。
- 既有 lock 与来源条目逐项未变，包含已有 yq Skill 的记录。
- 四组待决定内容仍在候选内，独立复核未发现剩余越界通用规则删除。

**适配后行为检查：离线案例范围通过。**

| 离线案例 | 实际应用结果 | 未验证范围 |
| --- | --- | --- |
| 两个进程共用端口和路径，kill 不等待退出 | 提出宿主资源冲突与不完整清理风险；要求原子分配、独立路径和退出完成信号；诊断请求保持只读。 | 未读取实际 CI 日志，未跑并发测试，未确认真实根因。 |
| 工具返回 300000 字符，参数规则重复，延迟资源无入口 | 提出有界摘要、分页或详情、参数就地说明和发现入口；要求测量首轮 prompt tokens。 | 未修改实际工具，未测 token 节省。 |
| 删除后 Toast 丢失，错误清空内容，菜单裁切，未测暗色 | 要求更长寿命 Toast 宿主、失败保留数据、菜单逃离 overflow 和双主题验证；保留设计或产品评审要求。 | 未运行真实 GUI，未测对比度或窗口行为。 |

三个离线案例由独立检查代理应用；恢复混合句后再次复核。
未执行上游原有 CI、浏览器、模型或仓库验证流程。
不宣称保留上游全部验证结论，不宣称真实产品已经验收通过。

## 本地审计材料

缓存目录：.runtime/.cache/yq-dsh-adapt-20261005/。

- sources.json：固定 commit、14 个源文件 Git blob 与 SHA-256。
- changes.json：24 个精确字节编辑范围和四组待决定项。
- verification.json：原文、链接、既有文件与元数据检查结果。
- verify.py：按登记范围重建候选并检查未登记差异。
- candidate.diff：候选与上游的完整差异。
- retention.json：缓存保留理由与到期日期。

可重建缓存保留至 2026-11-05，供本次候选复核。
本报告和候选无需全局安装即可审查。
