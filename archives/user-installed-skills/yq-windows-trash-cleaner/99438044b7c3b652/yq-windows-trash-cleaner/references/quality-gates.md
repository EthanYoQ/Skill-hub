# Quality gates

## Memory

- Samples belong to one boot and include boot time.
- Representative workload and post-workload periods are present.
- No warning/critical threshold or sustained monotonic growth.
- Maximum sample gap is compatible with the claimed duration.
- High total memory is reconciled with processes versus kernel pool.
- Root-cause wording matches the evidence hierarchy.
- Touched functions pass and no new related event-log error appears.

## Disk

- Current free bytes and historical delta are recorded.
- Every selected fixed volume and project scan root is recorded; access failures and excluded roots are disclosed.
- Top consumers are measured without following reparse points.
- Git repositories and worktrees are classified by canonical root, dirty/untracked state, remote-default containment, activity, and project instructions.
- Every removal maps to an approved manifest ID.
- Package and project caches have an owning manifest or lockfile, semantic action, inactive owner, and tested regeneration path.
- Docker logical use and VHDX physical allocation are separate.
- Volumes, sessions, databases, backups, and worktrees receive semantic checks.
- Candidate logical size, allocated size where available, per-action free-byte delta, and whole-run net delta are not conflated.
- Actual released bytes and retained recoverability are reported.

## Outcome labels

- `VERIFIED_FIXED`
- `HEALTHY_SO_FAR_PENDING_LONG_RUN`
- `ROOT_CAUSE_NOT_PROVEN`
- `WARNING_REVIEW_REQUIRED`
- `ROLLBACK_REQUIRED`

Fail a hard gate rather than soften the wording.
