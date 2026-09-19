# Whole-computer project audit

## Discovery scope

Inventory known workspace roots on every fixed volume, registered Git worktrees, user Documents/Desktop, temporary development roots, and configured source/skill roots. Avoid recursively scanning protected Windows and installed-application trees unless a measured anomaly points there.

Record scan roots, exclusions, reparse points, access failures, and maximum depth. A partial scan must be described as partial.

## Project identity

Strong signals are a `.git` directory/file, a registered worktree, or a manifest such as `package.json`, `pyproject.toml`, `Cargo.toml`, `go.mod`, `pom.xml`, `*.sln`, or `*.csproj`. A folder name alone is not proof.

For Git projects capture canonical top-level root, remotes, branch, HEAD, status, upstream/default branch, submodules, and worktrees. Do not collapse nested repositories into the parent.

## Cache classification

Usually rebuildable after checking owner inactivity and manifests:

- `node_modules`, package download caches, `.next/cache`, `.turbo`, `.parcel-cache`;
- Python bytecode/test/lint caches and a reproducible virtual environment;
- Rust `target`, Gradle/Maven build caches, coverage and browser-test output;
- CodeGraph databases when verified as indexes and rebuild configuration is valid.

Review rather than auto-delete:

- `dist`, `build`, `output`, `release`, installers, archives, screenshots, reports;
- datasets, models, database files, migrations, fixtures, recordings, research runs;
- `.codex`, `.claude`, `.agents`, `.runtime`, proof/verification folders;
- clean clones whose remote/default-branch relationship has not been proven.

Keep dirty/untracked source, active worktrees, unmerged commits, current evidence, and any path referenced by repository instructions.

## Activity and rebuild proof

Use one process inventory and match normalized command lines or executable working context to project roots. A process name alone is insufficient. Verify lockfiles and the exact regeneration command; “can reinstall somehow” is not enough for automatic classification.

## Deletion method

Use exact pathspec previews for generated ignored paths. Never whole-repo `git clean -fdX` when the preview includes data, evidence, release output, agent context, or unknown content. Use Git to remove registered worktrees. Save status/remotes/worktrees and patches before structural changes.
