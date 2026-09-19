# Runtime Adapters

Read this reference when the target runtime is Claude Code, Codex, multiple
runtimes, or unknown. Apply the common source/install/ownership contract first,
then use the runtime-specific loader and update mechanism below.

## Detect The Target Runtime

Do not infer the managed runtime from the agent currently executing this skill.
Inspect the requested target, configured roots, environment, project files, and
available CLIs.

| Runtime/scope | Active skill location | Ownership/update authority |
| --- | --- | --- |
| Codex user | `~/.codex/skills` or configured Codex root | User or source repository |
| Codex project | project `.codex/skills` or configured project root | Project repository |
| Shared Agent Skills root | `~/.agents/skills` or another host-neutral root | Runtime remains `agent-skills` or `unknown` until loader evidence identifies a host |
| Claude Code personal | `${CLAUDE_CONFIG_DIR:-~/.claude}/skills/<name>/SKILL.md` | User or source repository |
| Claude Code project | `.claude/skills/<name>/SKILL.md`, including relevant nested package roots | Project repository |
| Claude Code plugin | plugin `skills/` directory; installed copy under the Claude plugin cache | `claude plugin` and marketplace metadata |
| Enterprise/system | host-specific managed settings, bundled roots, or system cache | Administrator/runtime; read-only for normal work |

On Windows, `~/.claude` resolves under `%USERPROFILE%`. Respect
`CLAUDE_CONFIG_DIR` when it is set; do not silently scan the default directory
instead. Claude Code project skills can be discovered from parent and nested
`.claude/skills` directories, so a project audit must state which project and
package roots were checked.

`CLAUDE_CONFIG_DIR` changes Claude Code roots only. It does not redefine the
operating-system user home or move the default
`~/.skill-lifecycle/skill-upstreams.json` index. Use another index location only
when `-IndexPath` or an existing legacy index establishes it.

## Claude Code Standalone Skills

Personal and project skills are ordinary Agent Skills directories and can use
the same source-index workflow as Codex installs. Keep separate index entries
for separate canonical install paths even when both runtimes load the same
source skill.

Run a Claude Code-focused local audit on PowerShell 7:

```powershell
pwsh ./scripts/check_upstreams.ps1 `
  -Mode Local `
  -Runtime ClaudeCode `
  -ProjectRoots "/path/to/project" `
  -BootstrapIndex
```

The portable default index is
`~/.skill-lifecycle/skill-upstreams.json`. If the legacy
`~/.agents/skill-upstreams.json` already exists, the helper continues using it
unless `-IndexPath` is supplied. The index records `install.runtime` and
`install.scope` in addition to the canonical path.

For project skills, prefer the repository's `.claude/skills` directory and
commit it when the skill is meant for collaborators. A personal skill under
`~/.claude/skills` applies across local projects but is not automatically
available in remote/cloud sessions. For those sessions, use a committed project
skill, a repository-declared plugin, or the account-level skill mechanism
appropriate to that Claude surface.

## Claude Code Plugins

Treat marketplace-installed plugin directories as managed cache, not as source
or user-maintained installs. Claude Code copies each installed version under
`~/.claude/plugins/cache`; direct edits can be discarded, can target an orphaned
version, and bypass plugin metadata.

Use the plugin manager:

```text
claude plugin list --json
claude plugin details <plugin-or-plugin@marketplace>
claude plugin update <plugin-or-plugin@marketplace> --scope <user|project|local|managed>
```

Follow the installed CLI's post-update instruction. Current Claude Code CLI
reports that a restart is required to apply `claude plugin update`; do not claim
that editing the cache or reloading a standalone SKILL.md applies the new
plugin version.

Before updating, record plugin identity, marketplace/source, installed version
or commit, enabled scope, and dirty/development state when applicable. Pass the
same installed scope to `claude plugin update`; do not silently fall back to
the command's default user scope. Do not
apply a standalone-skill `mirror` policy to a plugin cache path. Managed-scope
plugins are read-only unless the administrator-provided mechanism explicitly
allows an update.

A locally developed plugin loaded with `--plugin-dir` is source/development
state, not an installed marketplace copy. Compare and edit its source repository
instead of the cache.

## Scope And Name Precedence

Claude Code standalone skill precedence is enterprise over personal over
project; plugin skills use a plugin namespace. Record both runtime and scope so
the audit does not mistake a shadowed copy for the active one.

Treat `~/.agents/skills` as a shared Agent Skills root. Confirm which runtime
loads a given path instead of labeling any entry there as Codex-owned by
default. Report `runtime=agent-skills` or `runtime=unknown` until loader evidence
establishes Codex or another host. Apply the same neutral label in section
headings, tables, and summaries; a later caveat does not repair a misleading
`Codex` heading.

When duplicate content is intentionally shared across Codex and Claude Code:

- Keep one source checkout or Skill Hub mapping.
- Keep one exact-path install entry per runtime/scope.
- Compare each active install separately.
- Use symlinks/junctions only when the user explicitly accepts shared ownership
  and the runtime supports the link form.

## Reload And Validation

For Claude Code:

- Existing standalone `SKILL.md` edits are detected live.
- Creating a top-level skills directory after session start can require a
  restart so Claude Code starts watching it.
- During local plugin development, plugin skill text is live, while changed
  agents, hooks, MCP, or output styles require `/reload-plugins`; monitors can
  require a restart. Marketplace plugin updates follow the CLI's restart
  instruction.
- Validate discovery from a fresh `claude` session or an isolated
  `claude -p` run. Seeing the skill listed is not behavior validation, so run
  representative eval prompts with and without the skill.

For Codex, report the actual refresh/restart behavior observed by that runtime;
do not reuse Claude Code reload instructions.

## Runtime-Aware Report

```text
Runtime:
Scope:
Loader root:
Source index:
Standalone skills checked:
Managed plugins checked:
Plugin cache excluded:
Current or updated:
Unresolved mappings:
Validation:
Reload or restart:
```
