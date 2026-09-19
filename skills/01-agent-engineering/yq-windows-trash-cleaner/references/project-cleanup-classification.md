# Project cleanup classification

Use this reference for repository-local cleanup. Git-ignored status, a familiar directory name, or large size is evidence only; none of them independently authorizes deletion.

## Usually safe only after repository evidence

- Dependency installs and caches such as `node_modules`, `.venv`, `.tox`, `.pytest_cache`, `.mypy_cache`, `__pycache__`, `.turbo`, `.vite`, and `.parcel-cache` need a matching manifest or lockfile, an inactive owner, exact containment, and a known regeneration command.
- Build outputs such as `target`, `.next`, `.nuxt`, `.svelte-kit`, `coverage`, and tool-specific temporary trees need proof that they are generated and not tracked or used as release evidence.
- Prefer the owning package manager's prune or clean operation over raw recursive deletion when it has narrower semantics.

## Review or archive first

- Untracked source, scripts, docs, tests, configs, migrations, assets, old product roots, and standalone clones.
- Registered worktrees, even when clean; require remote-default containment and use `git worktree remove`.
- `dist`, `build`, `output`, `release-*`, installers, archives, screenshots, and generated assets unless published hashes or another trusted archive prove recovery.
- `.runtime`, `test_dataset`, `manual_frontend_runs`, `manual_program_runs`, `raw_documents`, databases, transcripts, corpora, models, benchmarks, and audit ledgers.
- `.codex`, `.claude`, `.gstack`, `.codegraph`, and other agent/index state until ownership, activity, and evidence value are understood.

## Keep by default

- Git metadata, source, application entry points, manifests, lockfiles, build/release scripts, CI, tests, fixtures, migrations, public assets, and current project documentation.
- Dirty tracked or untracked work, unmerged branches, active worktrees, credentials, certificates, browser profiles, and user data.
- Anything outside the approved repository root or reached through a reparse point.

## Evidence rules

- Capture `git status --short`, `git clean -ndX`, `git clean -nd`, registered worktrees, active-owner evidence, repository instructions, and regeneration proof before classifying a target.
- A release package becomes a deletion candidate only when its name, size, and SHA256 match a trusted published asset or archive and the staging tree is reproducible.
- A tracked `build/` often contains packaging source. Classify exact ignored children rather than the whole directory.
- Do not export process command lines in a reusable/public audit artifact; record PID, process name, executable path, and a boolean path match.
- Re-run Git status, worktree registration, target size, and application smoke tests after any approved cleanup.
