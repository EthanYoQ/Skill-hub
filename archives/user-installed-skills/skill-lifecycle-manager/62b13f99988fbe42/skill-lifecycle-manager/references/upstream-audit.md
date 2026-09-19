# Upstream Audit And Upgrade

Read this reference before comparing skill upstreams, responding to a legacy
`skill-upgrade` request, or running `scripts/check_upstreams.ps1`.

## Evidence Index

Use `_meta/skill-upstreams.json` when present. Each source entry records:

- `name` and repository-local `path`
- `classification`: `open-source`, `self`, `local`, `candidate`, or `unknown`
- Verified `upstream.url`, `upstream.path`, and `upstream.ref`
- Checked commit in `lastChecked.commit`
- `updatePolicy`: `mirror`, `mapped`, `manual`, or `none`
- Evidence, notes, and verification paths

Interpret policies conservatively:

| Policy | Meaning | Allowed action |
| --- | --- | --- |
| `mirror` | Local source should match verified upstream | Replace only after normalized diff and backup |
| `mapped` | Local copy intentionally adapts upstream | Produce mapped diff and preserve adaptations |
| `manual` | Human review is required | Report only |
| `none` | Self/local/project or unverified source | Do not overwrite |

Verify upstream with a strong signal: explicit source URL, exact directory
match, official vendor repository, or a prior evidence-backed source entry.
Never upgrade by name alone.

## Bundled Helper

Use the manager's canonical helper:

```powershell
.\skills\01-agent-engineering\skill-lifecycle-manager\scripts\check_upstreams.ps1 -SelfTest
```

Run read-only repository audit:

```powershell
.\skills\01-agent-engineering\skill-lifecycle-manager\scripts\check_upstreams.ps1 -Mode Repo -RepoRoot "<Skill-hub>"
```

Run read-only local audit:

```powershell
.\skills\01-agent-engineering\skill-lifecycle-manager\scripts\check_upstreams.ps1 -Mode Local -SkillRoots "<root1>","<root2>"
```

Read-only mode does not replace skill content, but it may clone or fetch Git
metadata under `WorkDir`. Report that local side effect when it matters.
If the execution environment prohibits even that temporary metadata, do not
use `-Apply`; report the blocked prerequisite and retain the read-only evidence
that was available.

## Applied Repository Audit

```powershell
.\skills\01-agent-engineering\skill-lifecycle-manager\scripts\check_upstreams.ps1 `
  -Mode Repo `
  -RepoRoot "<Skill-hub>" `
  -BackupRoot "<persistent-backup-root>" `
  -Apply
```

Applied repository mode:

- Rejects a target equal to `RepoRoot`.
- Rejects sibling-prefix and traversal paths outside `RepoRoot`.
- Mirrors only verified `mirror` entries with detected drift.
- Creates a timestamped backup before clearing the target directory.
- Returns `backupPath` for every applied mirror.
- Writes source-index status only in apply mode.

Require a non-empty reported `backupPath` only for a mirror that was actually
applied. For a no-op audit, report that no backup was created and why no Apply
was eligible.

If `BackupRoot` is omitted, the default is
`<RepoRoot>/.backups/skill-upstream-audit/`. Keep this directory ignored by
Git but persistent long enough for rollback.

Do not treat `mapped` drift as automatically applied. Review and merge mapped
adaptations manually.

## Applied Local Audit

```powershell
.\skills\01-agent-engineering\skill-lifecycle-manager\scripts\check_upstreams.ps1 `
  -Mode Local `
  -SkillRoots "<root1>","<root2>" `
  -Apply
```

Local mode:

- Inventories SKILL.md files in configured roots.
- Groups git-backed sources by repository root.
- Fetches origin metadata.
- Fast-forwards only clean repositories that are behind an upstream.
- Does not replace standalone copied skills.
- Labels standalone copies as source candidates or local/unknown.

Before local apply, review every discovered Git root. Backups and source
checkouts nested under skill roots can appear in inventory, so exclude or
interpret them deliberately.

## Merge Rules

When upstream and local versions both changed:

1. Compare trigger behavior.
2. Compare tool and dependency assumptions.
3. Compare destructive-operation and credential behavior.
4. Compare outputs and compatibility.
5. Compare scripts, references, assets, and evals.
6. Preserve user-maintained behavior unless the user approves a change.

If a conflict materially changes behavior, report facts and ask for the
decision instead of selecting a winner by recency.

## Upstream Audit Report

```text
Mode:
Source index:
Checked roots:
WorkDir side effects:
Upgraded:
Backups:
Current:
Mapped/manual drift:
Dirty or blocked:
Unverified candidates:
Source-index coverage:
Apply used:
Validation:
Unverified:
```
