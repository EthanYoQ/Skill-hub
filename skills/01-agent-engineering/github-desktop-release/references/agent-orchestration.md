# Agent orchestration

Keep one owner for the complete evidence path even when implementation is parallelized.

## Roles

- **Primary orchestrator**: freeze scope and contract, control authorization, integrate changes, approve dispatch, and make the final release claim.
- **Platform executor**: implement or diagnose one Windows or macOS qualification branch against the frozen profile.
- **End-to-end evidence owner**: trace real platform bytes through receipts, finalize, verifier, promotion plan, publication, and authoritative readback.
- **Adversarial reviewer**: receive the frozen contract and raw artifacts without the intended answer; challenge false positives, unsafe normalization, hidden rebuilds, and unsupported claims.

## Boundaries

- Do not split producer, verifier, and promotion into isolated green checks without an end-to-end owner.
- Give reviewers raw artifacts, logs, receipts, and the frozen specification rather than the implementer's diagnosis.
- Keep platform-specific work independent, but require both branches to bind to the same source SHA and contract semantics before promotion.
- Let only the primary orchestrator authorize remote writes. A reviewer or platform executor cannot broaden scope, delete remote residue, force-update a tag, or approve publication.
- After a verifier change, require the evidence owner to replay every real receipt and prove whether existing qualification artifacts remain valid.
