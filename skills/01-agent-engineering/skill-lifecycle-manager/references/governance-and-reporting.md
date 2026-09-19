# Skill Governance And Reporting

Read this reference for discovery, recommendation, install scope, quality
audit, usage cleanup, packaging, publication, and detailed reports.

## Discovery And Source Quality

Use the existing discovery stack:

- `find-skills` and `npx skills find <query>` for skills.sh.
- GitHub CLI for repository proof, stars, activity, license, and raw files.
- English and Chinese query variants for bilingual needs.
- Popular sources before long-tail repositories.

Quality thresholds are evidence, not absolute rules:

- Prefer 1K+ installs when skills.sh counts exist.
- Prefer 100+ GitHub stars when stars are relevant.
- Treat official or widely used publishers as stronger evidence.
- Treat unknown or zero-star sources as experimental unless niche exploration
  is intentional or no stronger candidate exists.

Verify each candidate before recommending or installing:

- Exact source repository, path, ref, and skill directory
- Candidate SKILL.md and same-name false positives
- License and update activity
- Scripts, dependencies, network behavior, credentials, and destructive steps
- Observed or unavailable install count, stars, and source reputation

## Install Scope

Choose global/user scope when the workflow is broadly reusable, trusted,
stable, and not tied to one repository.

Choose project scope when the skill contains private conventions, local
architecture, experiments, or trigger behavior that should not affect other
projects.

Resolve scope through the target runtime. For Claude Code, personal skills live
under `${CLAUDE_CONFIG_DIR:-~/.claude}/skills`, project skills under relevant
`.claude/skills` roots, and shared/versioned plugins are managed by
`claude plugin`. For Codex, use its configured user/project roots. Do not
install into every detected runtime unless the user asked for multi-runtime
availability.

Before install:

- Check every active root for the same name.
- Compare existing and candidate versions.
- Prefer merging a user-maintained copy over adding a duplicate.
- Report runtime-specific refresh behavior. Claude Code detects existing
  standalone SKILL.md edits live, may need a restart for a newly created
  top-level skills directory, and uses `/reload-plugins` for non-skill plugin
  components.

## Quality Audit Gate

Check:

- Valid SKILL.md frontmatter with name and trigger-oriented description
- Compact core instructions and correctly routed references
- Existing referenced scripts, references, assets, and eval files
- Surprising network, credential, destructive, or persistence behavior
- Documented dependencies and required CLIs
- No undeclared private services or unavailable tools
- No secrets, tokens, private data, or accidental personal paths
- No UI emoji, pseudo-icons, handwritten SVG paths, or mixed icon conventions
- Realistic eval prompts and verifiable expectations for objective workflows

Separate observation, judgement, and unverified claims. Example:

```text
Observed: eval prompts exist and the script self-test passes.
Judgement: static operational risk is controlled.
Unverified: real-world trigger accuracy across hosts.
```

## Usage Audit And Cleanup

Do not use `LastAccessTime` as usage evidence. Loaders, searches, backups, and
audits can modify access time.

Prefer evidence in this order:

1. Explicit user request to use the skill
2. Session or conversation logs naming the skill
3. Tool evidence that its SKILL.md was read
4. Available-skill metadata showing it was loadable
5. Repository or filesystem presence only

Classify candidates:

- **Confirmed active**: explicit use evidence
- **Likely active**: strong task mapping with partial logs
- **Installed but no observed usage**: present/loadable without use evidence
- **Duplicate candidate**: same or near-same skill in several roots
- **Managed**: system/plugin-owned; skip normal cleanup and use the runtime's
  manager, such as `claude plugin`, when an update or uninstall is requested

Resolve and contain every target path. Reject the root itself. Quarantine or
back up uncertain candidates and use one shell end-to-end for Windows file
operations.

## Packaging And Publishing

- Run the quality and secret/privacy audit first and persist its report before
  creating or copying the package. The report timestamp must precede package
  creation.
- Inventory every source file and scan file names and contents. At minimum,
  detect quoted or unquoted JSON/YAML credential keys (`password`, `secret`,
  `token`, `api_key`, `client_secret`, and equivalents), environment-variable
  assignments, bearer tokens, private-key blocks, personal absolute paths,
  email addresses, and account identifiers.
- Fail closed when a source file cannot be read, a finding is not classified,
  or the audit pattern set cannot examine the file type. Correct the audit and
  rerun it before packaging; a post-package scan cannot satisfy this gate.
- Keep only an explicit allowlist of SKILL.md and required scripts, references,
  assets, and evals. Filename exclusion is defense in depth, not a substitute
  for the content scan.
- Remove caches, generated outputs, logs, credentials, and personal paths.
- Record provenance and version when derived from another source.
- Update Skill Hub lock, source, name, domain, platform, and README counts.
- Validate repository and installed copies separately.
- Review Git status, diff, anonymization, and intended publication scope before
  commit or push.

## Report Templates

Discovery:

| Candidate | Source | Installs | Stars | Source verified | Scope | Decision |
| --- | --- | --- | --- | --- | --- | --- |

Upgrade:

```text
Source and ref:
Target and owner:
Backup:
Behavior changes:
Changed files:
Validation:
Unverified:
Restart needed:
```

Skill Hub sync:

```text
RepoRoot:
Mode:
Local root:
Mapped path:
Dry-run result:
Backup:
Live action:
Index rebuild:
Validation:
Unmapped or conflicts:
Unverified:
```

Cleanup:

```text
Root scanned:
Evidence method:
Confirmed active:
No observed usage:
Duplicates:
Managed paths skipped:
Actions taken:
Quarantine or backup:
Unverified:
```

Quality audit:

```text
Skill:
Observed evidence:
Pass:
Findings:
Risks:
Missing evidence:
Recommended next validation:
```

Publication:

```text
Source repository:
Package contents:
Provenance:
Indexes updated:
Installed copy synchronized:
Validation:
Commit or push status:
Unverified:
```
