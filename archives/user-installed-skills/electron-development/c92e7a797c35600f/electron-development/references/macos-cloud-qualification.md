# macOS cloud qualification

Read this reference for every Electron macOS GitHub Actions build or qualification. Its purpose is to find packaging failures before the expensive matrix runs, then qualify every architecture requested by the frozen release profile from one commit.

## State machine

1. Freeze the commit SHA, release version, expected asset names, architectures, signing/notarization posture, workflow revision, lockfile, and toolchain versions.
2. Classify the outgoing diff and choose a dispatch mode from the risk table below.
3. Complete the package-like preflight. Every gate that can run without producing a distributable must be green before paid packaging minutes begin.
4. Run the selected cloud gate. Record stage durations and artifact sizes so later work targets the actual bottleneck.
5. Build DMG/ZIP assets into the builder output directory, then mount or unpack the packaged app and smoke that copy.
6. Project only the declared assets, checksums, and sanitized evidence into a separate qualification artifact.
7. Confirm every requested architecture is green at the frozen SHA. Hand those bytes to `github-desktop-release` for promotion; publication must not rebuild them.

The qualification is complete only when the expected architecture jobs identify the same SHA, their packaged smokes pass, asset projection is exact, checksums are recorded, and signing/notarization state is disclosed.

## Dispatch by risk

| Outgoing change | First cloud action | Fan-out |
| --- | --- | --- |
| GitHub workflow, lockfile/toolchain, packaging config, packaged-smoke client, helper IPC/security protocol, runner bundle, evidence writer/schema, signing, or notarization | Run a fast representative macOS canary that exercises the changed gate and stops before redundant packaging where possible | Start all requested architecture qualifications in parallel only after the canary is green |
| Ordinary product code while the release infrastructure is unchanged and the exact workflows have a recent green run | Skip the serial canary | Start all requested architecture qualifications in parallel |
| Unclear blast radius or no trustworthy recent green baseline | Treat as release-infrastructure risk | Canary, then parallel qualification |

A canary is a risk probe, not a permanent extra tax. Keep it focused on locked install, changed tests, helper/bundle construction, packaging configuration validation, and the relevant smoke contract. If the repository supports a shared source gate, run proven platform-independent checks once per SHA and let architecture jobs depend on it; keep native-module, architecture, packaging, and mounted-smoke checks in each architecture job. Do not remove duplicate checks until their platform independence and the evidence contract are explicit.

Prefer a canary that stops before producing a distributable. If the smallest useful probe must build and mount a package, decide before dispatch whether it is a non-promotable diagnostic or a formal qualification for that architecture. A formal representative job may count toward the requested matrix only when it executes the complete frozen qualification contract, emits the exact evidence artifact, and is never retroactively upgraded after seeing a green result. This avoids rebuilding one architecture solely because it was called a canary.

Use workflow concurrency groups with `cancel-in-progress` so a superseded SHA does not continue consuming macOS minutes. Key the group tightly enough that unrelated releases are not canceled.

## Package-like preflight

Repository tests are not packaged proof: running from the checkout can resolve dev dependencies through its `node_modules`. Exercise the same compiled helper and runner that the app will ship from an isolated directory, mounted DMG, unpacked `.app`, or another environment whose module lookup cannot reach the checkout. Assert the process cwd, module paths, and executable paths used by the smoke.

Before dispatch, cover these failure-prone boundaries:

### Helper IPC contract

- Build the helper first, then run the smoke client against that built helper rather than a test double.
- Keep request/response schemas versioned or shared. Contract tests must send every required identity, root, size/limit, and capability field and reject an intentionally incomplete request.
- Treat a secure-filesystem path rejection as a protocol mismatch until the request payload, root identity, canonical path, and size limits have been compared with the helper implementation.

### Runner bundle

- Decide how the packaged runtime obtains Electron APIs. An `ELECTRON_RUN_AS_NODE` child does not make the development `electron` package resolvable. Externalize `electron` only when the target runtime demonstrably resolves it; otherwise use a narrow build-time alias or stub for an unreachable Electron-only branch, and make that stub fail closed if invoked.
- Inspect the emitted bundle, not only the source config. Fail the preflight if it contains development Electron bootstrap code, a packaged-path `require("electron")` that cannot resolve, or another forbidden checkout dependency.
- Treat esbuild warnings about `import.meta` in CommonJS as blockers. Provide a deliberate file-URL banner/define or emit a compatible module format, then execute the emitted bundle in the isolated environment.

### Portable tests

- Compare file identity when validating security roots or aliases. On macOS, `/var` and `/private/var` can name the same inode; other platforms have their own aliases. Prefer device/inode identity where available, with canonical paths as a documented fallback, instead of asserting raw path strings.
- Synchronize asynchronous tests on a deterministic event, deferred promise, callback, or fake clock. A short polling timeout that passes on one runner class is not a qualification gate. Exercise timing-sensitive tests under a slower or repeated profile before dispatch rather than increasing an arbitrary delay.

## Cloud qualification gates

For each architecture job:

- Verify the runner architecture and the packaged executable architecture independently; do not infer either from the image label or filename.
- Use a locked dependency install and record the resolved runtime, package-manager, Electron, and builder versions.
- Build into a non-qualification directory. Copy only the release contract's DMG/ZIP files into the qualification directory after package and smoke gates pass.
- Mount the DMG or unpack the ZIP, launch or exercise the packaged app/helper from that location, and prove it cannot resolve through the checkout.
- Inspect bundle contents for unexpected credentials, development dependencies, duplicate Electron runtimes, and undeclared files.
- Record `codesign` and Gatekeeper/notarization results. Unsigned, ad-hoc, or unnotarized output may be valid only when the frozen release profile allows it; disclose the user-visible installation consequence instead of reporting it as signed.
- Upload exact assets, checksums, stage timings, and sanitized logs/evidence even when the job fails late enough to produce useful diagnostics. Keep secrets and machine-specific credentials out of evidence.

Cache only reconstructable dependency data with keys that include the lockfile and relevant runtime/architecture inputs. Avoid caching final packages, `node_modules`, or mutable build outputs as qualification evidence. Upload builder intermediates only as short-lived diagnostics on failure; the qualified artifact remains small and exact.

## Failure and retry discipline

Classify a failure before rerunning: source/shared gate, helper or bundle, package, mounted smoke, architecture/signing, or evidence projection. Fix the root cause, then audit every remaining downstream stage for the same changed contract. A one-failure-at-a-time loop wastes the most expensive minutes.

- When a fix changes the commit SHA, cancel all in-flight runs for the old SHA immediately. Successful old-SHA assets cannot satisfy the new qualification.
- After a SHA-changing fix, perform a forward audit from the failed stage through evidence projection before dispatching the new run.
- If the same stage fails twice during one repair attempt, stop. Do not start a third cloud run until a local/isolated reproduction, stronger diagnostic artifact, or a newly identified cause changes the evidence.
- If both architecture qualifications are green and only local verification, download, promotion, or publication tooling fails, preserve the qualified artifacts and resume that later state with `github-desktop-release`; do not rebuild.
- A rerun without a SHA change is appropriate only for a classified transient runner/service failure with unchanged inputs and sufficient evidence to distinguish it from a deterministic defect.

At handoff, report the frozen SHA, workflow/run identifiers, every requested architecture, exact asset names and digests, signing/notarization posture, stage timings, and any intentionally retained diagnostic artifact.
