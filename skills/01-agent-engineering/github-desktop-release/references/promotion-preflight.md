# Local promotion preflight

Run this read-only, zero-side-effect preflight before any large artifact download or Release mutation. Its completion criterion is a recorded pass for every item below against the exact promotion plan.

## Identity and remote access

- Resolve the source/helper repository and destination release repository explicitly; never infer either from the current directory.
- Verify `gh` is installed, inspect authenticated accounts, and prove read access to the qualification runs/artifacts plus the destination repository. Bind each command to the intended account with an isolated CLI config or per-process credential selection; do not change the user's global active account as a hidden setup step.
- Check tag/Release state and qualification run metadata read-only. Record workflow, run ID, attempt, artifact ID, head SHA, conclusion, expiry, and artifact size before transfer.
- Keep tokens and credential material out of command output, logs, plans, and evidence.

## Local tools and capacity

- Resolve the verifier's pinned Node runtime and required package manager from the project/Skill contract.
- Resolve every archive tool the package actually needs (`unzip`, `tar`, or platform equivalent) by executable path and a harmless version/help probe. PATH absence is a preflight failure even if another installed application happens to contain the executable; select that known executable explicitly or repair PATH before transfer.
- Validate the committed release profile and promotion inputs without writing remote state.
- Resolve an existing absolute output/cache directory, verify it is within the authorized task-owned location, inspect permissions without creating a probe file, and reject a non-empty destination when its ownership/provenance is unknown.
- Compare free space with the sum of remote artifact sizes plus extraction and verified-package headroom. Use a project-recorded multiplier or measured prior ratio; when neither exists, stop and establish a conservative plan rather than downloading until the disk fills.

## Transfer gate

Only after the preflight passes:

1. download the exact artifacts selected by workflow/run/attempt/artifact ID;
2. preserve their outer archive digests;
3. extract with the preflighted tools into the authorized location;
4. run read-only cross-platform verification;
5. enter the GitHub Release state machine with write permission only for the final publish stage.

If this preflight or later local verification fails while qualification bytes and contract meaning remain unchanged, fix the local environment and resume. Do not dispatch a new build. Rebuild only when evidence proves the qualified source, artifact bytes, or acceptance facts must change.
