# Cloud execution strategy

Choose the path from the release delta, not from habit. The objective is the first valid same-SHA matrix with the least runner and elapsed time; a canary is useful only when it is cheaper than the failure it is likely to expose.

## Risk routing

| Release delta | Route | Early evidence |
| --- | --- | --- |
| Application-only source change; installer, runtime/native dependencies, smoke, evidence, profile, workflows, and promotion consumer unchanged; requested runners/toolchains have current green evidence | Parallel formal matrix | One same-SHA shared source gate, then all required platform qualifications in parallel |
| First qualification, changed runner/toolchain, Electron/Node/native dependency, installer/updater, package helper/runner, smoke protocol, workflow, profile, or qualification evidence producer/verifier | Staged canary | Shared source gate plus the smallest target-platform compatibility/contract canary; full required matrix starts only after green |
| Promotion consumer or local publication tooling changed while qualified bytes, producer receipts, and acceptance meaning are unchanged | Promotion replay | Replay genuine receipts through the final consumer and run local promotion preflight; do not build a platform canary |
| Known platform blocker or unresolved failure class | Diagnosis only | Existing logs/metadata, local replay, or one bounded non-promotable probe |
| Qualification is green and only local verification, download, upload, draft, or readback failed | Promotion resume | Local promotion preflight and read-only state-machine verification; no build |

“Current green evidence” must name the workflow revision, runner label/image family, relevant toolchain, command set, and unchanged boundary. Invalidate it when any of those identities, the hosted image generation, or release-critical dependency inputs change. A profile may impose a maximum age; without one, elapsed days alone neither prove nor invalidate compatibility. A merely recent green run from a different contract is not evidence.

## One source gate, complete platform coverage

Run platform-neutral lint, type checking, deterministic unit tests, and other source-level checks once for the frozen SHA when their semantics do not depend on an OS or architecture. Record the exact commands, lockfile/toolchain identity, result, and head SHA in a reusable receipt. Make package jobs depend on this receipt instead of rerunning the same suite.

For cross-workflow handoff, the receipt must identify its producer workflow/run/job, frozen SHA, command list, toolchain and lockfile hashes, result, and the explicit reason each check is platform-neutral. Qualification jobs verify those fields before reuse. A job that cannot consume this receipt runs its own required checks; it must not silently trust a green check name.

Keep target-specific checks in their target jobs:

- native binding load/rebuild and package helper execution on the actual architecture;
- Windows installer install, launch, quiet/error observation, packaged smoke, signing, and uninstall;
- project tests whose path, filesystem, process, registry, shell, or platform behavior is material.

Centralize a test only after proving it is platform-neutral. Saving minutes cannot erase coverage.

## Dispatch and cancellation

Use a concurrency group that identifies the release line or qualification purpose, with `cancel-in-progress` for superseded qualification SHAs. Keep publication mutation separately serialized so a new source push cannot interrupt an active verified release mutation.

For staged work:

1. Dispatch the shared source gate and bounded compatibility/contract canary.
2. When they are green, dispatch all required formal platform qualifications in parallel.
3. Promote only after every required platform binds the same frozen SHA, contract, profile, and exact bytes.

Prefer a non-packaging canary. When a representative target must build an installer to answer the risk and the project wants to avoid a duplicate build, declare that job as a formal platform qualification before dispatch and make it execute the entire frozen contract. A partial or retrospectively promoted canary remains non-promotable.

For a low-risk parallel route, dispatch the source gate first or make each package job depend on the same gate in one workflow graph. Do not serialize Windows, macOS ARM64, and macOS x64 merely to simplify observation.

## SHA changes and forward audit

A product, build, workflow, contract, profile, acceptance-meaning, or artifact-set fix creates a new source SHA. Immediately:

1. cancel in-flight qualifications for the superseded SHA;
2. mark its successful artifacts ineligible for the new release contract;
3. replay the observed failure locally or in the smallest non-promotable lane;
4. inspect every later stage the failed run had not reached: packaged helper protocol and isolated module resolution, bundle warnings, deterministic async waits, evidence finalize/order, exact asset set, and local promotion prerequisites;
5. dispatch the selected early gate, then one fresh formal matrix for the new SHA.

The forward audit is a bounded pass over the remaining release path, not a general refactor or full-repository review.

## Retry budget and time accounting

Record duration by source gate, locked install, package, acceptance, artifact upload/download, verification, and publication. Optimize the dominant stage rather than the total by guesswork.

Two consecutive failures in one stage exhaust its cloud retry budget. A new SHA does not reset this budget when it represents another unproven guess at the same root cause. Before any third formal run, require:

- one unified root cause with ranked alternatives;
- raw evidence that distinguishes them;
- a local or bounded canary RED-to-GREEN replay;
- the forward audit of all remaining stages.

Promotion-only environment failures consume no qualification retry. Repair the local toolchain or safely resume the state machine against the same run/attempt/artifact IDs.

A verifier-only or promotion-consumer correction may reuse qualification artifacts only when it is external to the frozen producer result and replay proves that source, artifact bytes, receipts, and acceptance meaning are unchanged. If the release scope deliberately moves that correction into the product's frozen source SHA, it becomes a new release input and the requested platforms qualify that new SHA.
