# Failure classification and retry budget

Classify the failing stage before deciding whether another build is justified.

| Class | Evidence | Default action |
| --- | --- | --- |
| `product` | Packaged application behavior violates product acceptance | Fix product, create a new SHA and contract, then requalify |
| `build` | Locked install, compile, package, native/vendor input, or runner/toolchain contract fails | Fix one proven build input; create a new qualification run |
| `acceptance` | Installer/package is built but a real install, launch, upgrade, uninstall, mount, architecture, signing, or notarization gate fails | Preserve artifact and receipts; fix product or acceptance producer according to evidence |
| `gate-false-positive` | Known-good real bytes are rejected because decoding, normalization, schema, path, timestamp, version, or policy logic is wrong | Fix verifier locally; replay all real receipts; reuse qualification artifacts when their identity and acceptance facts remain valid |
| `promotion` | Cross-run selection, manifest/hash verification, tag/draft/assets state, upload, publish, or authoritative readback fails | Do not rebuild; repair or safely resume the promotion state machine |

## Retry budget

1. Record the exact stage, class, hypothesis, expected distinguishing evidence, and whether any product or artifact bytes changed.
2. Change one falsifiable input before a new run.
3. After two consecutive failures in the same stage, stop formal cloud execution. Require a unified root cause, ranked alternatives, raw evidence capture, and local red-to-green replay before another dispatch.
4. A verifier-only change does not automatically invalidate already qualified artifacts. Revalidate their immutable contract, receipts, manifest, and hashes through the corrected consumer.
5. A product, source, toolchain, artifact-set, or acceptance-meaning change creates a new contract and requires requalification.

Never describe a gate false positive as another installer build failure. Keep runner time, wall-clock diagnosis time, and agent/token work as separate cost measurements.

For a structured decision record, run:

```text
node <skill-root>/scripts/classify-actions-failure.mjs --record <failure.json>
```

The script accepts an evidence-backed failure surface; it does not guess from raw log keywords.
