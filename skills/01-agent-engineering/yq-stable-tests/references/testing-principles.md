# Testing principles

The target repository owns its test tiers, commands, coverage thresholds, and external-service requirements.

## Prefer the real implementation over a mock

Mock only the expensive or non-deterministic boundary (LLM adapter, network, clock); keep everything downstream real. A hand-rolled stand-in proves the bridge moves bytes, not that the shipping tool behaves as asserted. Bridge tool-call tests keep the real tool registry and pipeline behind the scripted mock model.

Recovery tests separate pre/post-chunk failures by step and prove failed chunks derive no message or tool side effect. Cover exhaustion, cancellation, policy composition, persistence, status, wire counts, transport-closing idle timeouts, and shipping application composition.

## Verify the world, not the self-report

An e2e assertion re-runs the command or re-reads the file externally; a keyword probe on the agent's own output lets a cheating agent pass. Assert untouched files are byte-identical. e2e tests own their resources: create it in the test, dispose in `afterEach` (even on failure/retry/timeout); shared fixtures live in a plain `tests/harness.ts`, never another `*.e2e.ts` (importing a spec re-registers its `describe` and duplicates real API calls).

## Test the real entry path

- Product-visible plugins require a non-unit REAL-composition test. Hand-built in-process suites are insufficient: boot the test configuration through the application's real startup path, mock only external services or nondeterministic inputs, and assert model-visible request/log, durable state, or user-visible output. Keep opt-ins out of shipped defaults.
- A guard only guards if the regression fails it. For public export contracts, add explicit export-shape and consumer round-trip assertions, and prove it: introduce the regression, watch red, revert.
- "Real entry path" means the published artifact: a package `bin` runs its built entry point under plain `node`, exposing failures tsx masks (settle races, module resolution, swallowed load failures). The same applies to non-index runtime entries and singleton modules shared across bundles. Keep the built-artifact smokes green, and assert a genuinely-missing config exits non-zero.

