# Upstream Audit And Upgrade

Read this reference before comparing skill upstreams, responding to a legacy
`skill-upgrade` request, or running `scripts/check_upstreams.ps1`.

## Evidence Index

Use `_meta/skill-upstreams.json` for a Skill Hub and a local source index such
as `~/.skill-lifecycle/skill-upstreams.json` for standalone installed copies.
Existing `~/.agents/skill-upstreams.json` indexes remain supported. The index
is JSON, not a database service. Each verified source entry records:

- `name` and repository-local `path`
- for a local index, canonical `install.path`, `install.runtime`, and
  `install.scope`; the path is the identity key
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

## Bootstrap A Missing Source Map

Do not skip source discovery when a first-time user has no index or when an
installed path has no verified entry. Create an inventory/index scaffold first:

```powershell
.\scripts\check_upstreams.ps1 `
  -Mode Local `
  -Runtime All `
  -SkillRoots "$HOME\.agents\skills","$HOME\.codex\skills","$HOME\.claude\skills" `
  -IndexPath "$HOME\.skill-lifecycle\skill-upstreams.json" `
  -BootstrapIndex
```

`-BootstrapIndex` is the only local discovery action that writes without
`-Apply`. It preserves existing entries and adds exact installed paths with
observed provenance or unresolved discovery queues. It does not promote an
embedded GitHub URL to a verified upstream.

For each `candidate` or `unknown` entry, resolve the source in this order:

1. Inspect deterministic local provenance: containing Git repository and
   `origin`, junction/symlink target, installer or lock receipt, adjacent source
   checkout, explicit `source`/`repository` metadata, README attribution, and
   URLs in SKILL.md or bundled files.
2. Search current GitHub/skills registries for the exact frontmatter name, then
   one or two distinctive body phrases. Use `gh search code` or current web
   search; do not rely on remembered repository ownership.
3. Clone or fetch a candidate, resolve its default/ref branch, locate the exact
   skill subdirectory, and compare the whole directory. Check the frontmatter
   name, distinctive instructions, resource layout, and Git history when the
   local copy may be older.
4. Reject false provenance. A repository that is merely a dependency, example,
   fork with unexplained changes, aggregator copy, or same-name project is not
   automatically the original source.
5. Persist the decision. Verified external sources become `open-source` with
   exact `upstream.url`, `upstream.path`, `upstream.ref`, evidence, comparison
   commit, and an explicit `updatePolicy`. User-created skills become `self`;
   project/private skills become `local`; unresolved options remain `candidate`
   or `unknown` with verification steps.

Agent Skills do not require standard `source`, `repository`, or semantic
`version` frontmatter. Inspect such fields only when they actually exist, and
treat them as candidate evidence until repository/path verification succeeds.
Do not invent freshness intervals or mark an index stale by age unless the
user's policy or index schema defines that rule.

Use these evidence levels:

| Level | Minimum evidence | Index/action |
| --- | --- | --- |
| Verified | Explicit provenance or exact path plus distinctive-content/history confirmation | Record upstream; comparison allowed |
| Candidate | Name, embedded URL, registry hit, or partial content overlap only | Record candidates; no overwrite |
| Unresolved | No defensible candidate or conflicting candidates | Record search attempts; no overwrite |

For a local index, key a mapping by canonical `install.path`. `name` remains
descriptive only. Never reuse a verified mapping for another path solely
because the frontmatter names match.

Example verified local entry:

```json
{
  "name": "example-skill",
  "install": {
    "path": "C:/Users/me/.claude/skills/example-skill",
    "runtime": "claude-code",
    "scope": "personal"
  },
  "classification": "open-source",
  "upstream": {
    "url": "https://github.com/owner/repository",
    "path": "skills/example-skill/",
    "ref": "main"
  },
  "lastChecked": {
    "date": "2026-07-19",
    "commit": "<immutable commit>"
  },
  "updatePolicy": "mirror",
  "status": "current",
  "evidence": [
    "Exact upstream directory and distinctive instructions verified."
  ],
  "verificationPath": [
    "Compare normalized full-directory hashes before Apply."
  ]
}
```

## Repeat Audit From A Source Map

Once mappings exist, every upgrade check must reuse and refresh them:

1. Match the canonical installed path to exactly one index entry.
2. Fetch the recorded ref and resolve an immutable upstream commit.
3. Compare the complete local and upstream skill trees using the recorded
   normalization rule.
4. Report `current`, `drift`, `mapped-drift`, unresolved, or blocked. A newer
   commit timestamp alone does not prove that an adapted local copy is behind.
5. Apply only a verified `mirror` drift after backup. Review `mapped` and
   `manual` differences; never auto-apply `candidate`, `unknown`, `self`, or
   `local` entries.
6. In apply mode, persist the checked date, commit, and resulting status so the
   next audit has a stable baseline.

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

Use `-Runtime Codex`, `-Runtime ClaudeCode`, or `-Runtime All` to select
default roots. For Claude Code project skills, pass `-ProjectRoots` or explicit
`.claude/skills` roots. Plugin caches are not standalone roots; inventory and
update them through `claude plugin` as defined in `runtime-adapters.md`.

Pass `-IndexPath` to make Local mode compare verified standalone mappings. If
the index is absent, bootstrap it and complete source discovery before claiming
that all local skills were checked for upgrades.

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

- Inventories direct loadable SKILL.md children in configured roots; source
  checkouts, eval fixtures, and historical workspaces nested below them are not
  treated as active installs.
- Groups git-backed sources by repository root.
- Fetches origin metadata.
- Fast-forwards only clean repositories that are behind an upstream.
- Loads exact-path mappings from the local source index.
- Compares verified standalone copied skills to the recorded upstream.
- Mirrors a standalone copy only with `-Apply`, verified `mirror` policy, path
  containment, and a timestamped backup.
- Labels unmapped copies as source candidates or local/unknown and returns a
  discovery queue.
- Reports runtime and scope for indexed installs and keeps Claude Code plugin
  cache paths outside standalone mirror operations.

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
Source-discovery queue:
Apply used:
Validation:
Unverified:
```
