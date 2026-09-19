# Whole-computer storage classification

## Safe rebuildable candidates

Require exact path/object identity, proven regeneration, owner inactivity, path containment, no reparse escape, and current size verification. Prefer the owning tool's prune or clean command.

Examples include verified package download caches, old compiler/build caches, expired temporary directories, clean merged worktrees, and stale index databases with a tested rebuild path.

## Review required

Sessions, backups, installers, downloads, browser local models, inactive images/containers, clean clones, virtual environments, and dependency trees can be recreated but carry time, bandwidth, reproducibility, or history cost. Explain the tradeoff and use recoverable removal where practical.

## Keep user or evidence

Keep source, dirty/unmerged work, user documents, project output with release/research value, databases, Docker volumes, restore evidence, credentials, current sessions, active environments, and unknown ownership.

## System managed

Do not hand-delete pagefile, hiberfil, swapfile, WinSxS, DriverStore, Windows Installer, Recovery, Reserved Storage, VSS, restore points, or protected update databases. Use official analysis first and keep unknown results out of reclaim estimates.

## Package-manager semantics

- npm: inventory/verify first; use its cache clean only when approved.
- pnpm: confirm `pnpm store path`; use `pnpm store prune`, not raw deletion of the current store.
- uv: use `uv cache prune` or its documented clean command.
- pip: use `pip cache info` and `pip cache purge` only for an approved cache.
- Cargo: preserve installed toolchains and registry/source cache needed offline; use documented clean operations per project.
- NuGet, Gradle, and Maven: distinguish downloaded dependency caches from project-local outputs and expect redownload cost.

Total cache size is an upper bound; prune commands may reclaim only a subset.
