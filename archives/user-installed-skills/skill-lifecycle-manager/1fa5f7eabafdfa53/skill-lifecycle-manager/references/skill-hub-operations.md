# Skill Hub Operations

Read this reference for Skill Hub pull, push, new-skill synchronization,
junction setup, or index maintenance.

## Repository Model

Treat a Skill Hub checkout as a structured source repository, not as the
runtime install root.

- `skills/<domain>/<skill>/`: shared skills intended for reuse.
- `projects/<project>/<skill>/`: project-private skills; normal shared sync must
  not flatten these into global roots.
- `_meta/skills-lock.json`: machine-readable skill-to-path mapping.
- `_meta/skill-upstreams.json`: evidence-backed source classification.
- `scripts/sync-pull.ps1`: repository shared skills to a flat local root.
- `scripts/sync-push.ps1`: mapped flat local skills to grouped repository paths.
- `scripts/setup-junctions.ps1`: make multiple runtimes share one physical
  root.
- `scripts/build-indexes.ps1`: rebuild counts, by-name, by-domain, and the
  by-platform pending-classification block.

Keep these environment variables distinct:

- `SKILL_HUB_LOCAL_SOURCE`: flat local root for sync pull/push.
- `SKILL_HUB_SOURCE`: single physical source for junction targets.

## Classify The Operation

| Mode | User intent | First action | Main risk |
| --- | --- | --- | --- |
| Repo to local | Pull/install shared repository skills | `sync-pull.ps1 -DryRun` | Overwrite local edits |
| Local to repo | Save local skills into Skill Hub | Confirm lock mapping, then `sync-push.ps1 -DryRun` | Wrong category or target |
| Manual merge | Both copies changed | Compare behavior and files | Losing trigger or safety changes |
| Junction setup | Share one root across runtimes | `setup-junctions.ps1 -DryRun` | Ownership and blast-radius change |

Before live work, run `git status`, include dirty state in the report, resolve
absolute roots, and back up every destination that may be replaced.

## Repository To Local

```powershell
.\scripts\sync-pull.ps1 -LocalTarget "<local-skill-root>" -RepoRoot "<Skill-hub>" -DryRun
```

Observed script behavior:

- Scans only `RepoRoot\skills\`, not `projects\`.
- Finds SKILL.md directories recursively and flattens by directory name.
- Reports same-name conflicts and skips them.
- Live mode removes each target skill directory before copying.

Before live mode:

- Confirm `LocalTarget` is the intended active root.
- Compare local and repository copies.
- Back up locally edited targets.
- Exclude project-private skills and managed roots.

## Local To Repository

```powershell
.\scripts\sync-push.ps1 -LocalSource "<local-skill-root>" -RepoRoot "<Skill-hub>" -DryRun
```

Observed script behavior:

- Reads `_meta/skills-lock.json` for mapping.
- Pushes shared entries only.
- Skips project-private entries.
- Reports unmapped local skills instead of auto-classifying them.
- Live mode removes the mapped repository destination before copying.

For an unmapped skill, first decide shared versus project-private. Add the lock
mapping and rebuild indexes before relying on sync-push.

## Link-Based Single Source

Use links only when the user explicitly wants one physical root. Confirm that
every target runtime follows the proposed link type before changing ownership.

```powershell
.\scripts\setup-junctions.ps1 -Source "<single-source-root>" -Targets "<target1>;<target2>" -DryRun
```

Observed script behavior:

- Backs up existing targets as `<path>.old-<timestamp>`.
- Creates Windows junctions with `mklink /J`.
- Verifies by comparing SKILL.md counts.

The bundled helper is Windows-specific. On macOS/Linux, use a symbolic link
only after the same dry-run, backup, strict containment, and target verification
steps. Claude Code supports personal and project skill-directory symlinks in
current releases, but marketplace plugin symlinks follow separate cache rules;
do not link into or mutate the installed plugin cache.

Include every intended runtime root explicitly. Do not choose junctions or
symlinks as the default update mechanism because they change ownership and
failure blast radius.

## New Skill Synchronization

For a newly created skill:

1. Validate the source skill.
2. Classify broadly reusable skills under `skills/`; put project-only skills
   under `projects/`.
3. Establish the final path mapping in `_meta/skills-lock.json` and source
   classification in `_meta/skill-upstreams.json` before any copy. If those
   records already exist, verify them and keep an idempotent no-op instead of
   rewriting correct metadata.
4. Compare the installed and repository trees. If both contain material
   changes, back up the replacement target and merge deliberately; do not run
   a destructive sync-push that would discard repository-only files.
5. Add or update the Chinese description and metadata only when the desired
   final state differs.
6. Run `scripts/build-indexes.ps1 -DryRun` and verify counts.
7. Run the live index build only when source or metadata changes require it and
   after the dry-run inventory is correct. Report an idempotent no-op when no
   rebuild is needed.
8. Manually classify new entries in `_meta/by-platform.md` when appropriate.
9. Validate source and installed copies separately and compare hashes. If a
   safe sync is blocked, report the differing files and blocker instead of
   claiming the copies are synchronized.

## Index Rebuild

The index script resolves `-RepoRoot` to an absolute path, so both of these are
supported:

```powershell
.\scripts\build-indexes.ps1 -DryRun
.\scripts\build-indexes.ps1 -RepoRoot . -DryRun
```

After the dry run, verify shared, project, and total counts against actual
SKILL.md files. The script excludes its previous auto-generated by-platform
block when calculating missing classifications, then rebuilds that block from
current repository state.

Run the live command with the same root form that passed dry-run. Finish with
JSON parsing and `git diff --check`.
