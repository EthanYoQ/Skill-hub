# Large-repository documentation audit

Use this playbook when documentation spans several roots, the repository has years of accumulated prose, or broad filesystem size makes an undirected scan expensive. The objective is a bounded source-of-truth map and an actionable remediation frontier, not an indiscriminate rewrite.

## 1. Bound the inventory

Start from the repository root and registered worktrees. Record the checkout, branch, revision, merge base when relevant, dirty state or stable status fingerprint, applicable instructions, and requested write authority. Capture the same identity again before reporting. If it changed, do not mix before-and-after observations: anchor completed findings to the original revision and list the later delta as uninspected.

Treat each worktree as a separate evidence surface keyed by its path and revision. Compare their documentation contracts explicitly when useful, but do not collapse different branches, dirty states, or task outputs into one ownership row.

Inventory tracked prose first. Add relevant untracked docs only after confirming that they belong to the project. When known ignored roots contain task reports, runtime evidence, or local issue state, inventory only those roots and classify them separately; a normal untracked-file query omits ignored files. Constrain searches to known roots and exclude `.git`, dependency stores, generated output, caches, binaries, archives, fixtures, snapshots, and vendored trees according to project rules. Do not scan tens of gigabytes of build or runtime data merely to find Markdown.

Useful probes include:

```sh
git ls-files '*.md' '*.mdx' '*.rst' '*.adoc'
rg --files docs .github packages apps src | rg '\.(md|mdx|rst|adoc)$'
rg -n 'distinctive claim or old path' <bounded-roots>
git log -1 --format='%h %ad %s' -- <document>
```

Adapt roots and extensions to the repository. Git history is triage metadata, never truth by itself.

## 2. Build the ownership map

Use one row per document or claim family:

| Field | Meaning |
| --- | --- |
| Surface | File, heading, JSDoc symbol, generated catalog, or comment family |
| Role | Orientation, tutorial, runbook, reference, decision, incident, derivative, archive |
| Subject owner | Package, service, workflow, team boundary, generator, or decision record responsible for the fact |
| Authority tier | Canonical, summary, derivative, historical, task-state, or external evidence |
| Mutability | Active, frozen, generated, or local-only |
| Freshness contract | Owner, as-of point, invalidation event, and explicit supersession relation |
| Consumers | Navigation entries, inbound links, commands, tooling, operators, users, or agents that rely on it |
| Verification | Code, config, schema, runtime observation, test, external standard, or current decision |
| State | Current, partially stale, fully superseded, duplicated, conflicting, misplaced, or historical |
| Action | Keep, repair, consolidate, move, regenerate, archive, delete, or defer |
| Confidence | Proven, likely, or unknown, with the missing evidence named |

Dates and titles help find candidates. They do not identify the current owner. A current owner is established by responsibility, shipped behavior, project rules, and inbound dependencies.

When a claim depends on a spreadsheet, PDF, JSON export, screenshot, archive, or remote artifact, index the evidence separately. Record a content hash, exact storage location, acquisition time, retrievability, privacy or commit boundary, and every claim that cites it. A matching filename is not identity. Do not rewrite or parse non-prose evidence merely because its citing document is in scope; use the appropriate document or data capability when content inspection is required.

## 3. Prioritize by consequence

Review high-consequence surfaces before cosmetic or low-traffic prose:

1. installation, onboarding, and first successful run;
2. production deployment, security, credentials, backup, restore, rollback, and incident response;
3. public APIs, schemas, compatibility, migrations, and integration contracts;
4. architecture and decision records used to justify current seams;
5. contributor workflows, release gates, and generated-document ownership;
6. tutorials, examples, navigation, package READMEs, and lower-risk explanatory prose.

Within each area, prioritize contradictory claims and commands that users may execute over mere length. Large files are candidates for structural review, not automatic trimming.

## 4. Find conflict and rot

Search distinctive phrases, product names, ports, versions, file paths, environment variables, commands, defaults, status words, and duplicated headings. Read dense documents without a pattern in hand; pattern searches under-detect conceptual conflicts.

For each conflict, separate:

- intended contract;
- observed implementation or runtime state;
- historical rationale;
- temporary plan or status;
- derivative copy.

Do not collapse an unresolved implementation/spec mismatch into one convenient sentence. Name the mismatch, its owner, and the evidence needed to resolve it.

## 5. Remediate owner-first

Work in reviewable batches organized by an owner or claim family:

1. repair or establish the canonical owner;
2. preserve unique rationale, alternatives, compatibility obligations, and recovery knowledge;
3. replace redundant copies with audience-appropriate summaries and links;
4. regenerate derived artifacts and update translations or paired docs;
5. move/archive/delete only after inbound references and surviving obligations are known;
6. validate commands, links, anchors, generators, and affected behavior;
7. report unresolved conflicts with a proposed owner and evidence gap; create a repository TODO only when repository edits are authorized, and create or update an external issue only with explicit authorization.

Avoid a single giant cleanup commit when smaller batches can preserve provenance and simplify review.

## 6. Validate without creating evidence

Classify a command before running it: read-only check, source rewrite, generated-output write, build/cache write, runtime-state mutation, database mutation, or external side effect. A no-edit audit may run only checks proven read-only from their implementation, documentation, or help. Record useful commands that were not run and why.

When the repository has no documentation validator, use bounded read-only fallbacks appropriate to the audited roots:

- resolve Markdown links and anchors;
- check literal or code-formatted repository paths;
- identify active documents with no navigation or inbound path, without treating historical evidence as an orphan defect;
- search for distinctive retired terms, defaults, status claims, and conflicting command forms;
- confirm documented commands still exist in manifests, task runners, or CLI help;
- compare generated, localized, and navigation surfaces with their declared owners;
- use `git diff --check` only when there is a diff to inspect.

These checks establish structural consistency. They do not certify product truth or replace runtime, external-source, or owner evidence.

## Completion criteria

The audit is complete for its declared boundary when:

- every high-consequence surface in scope has an identified owner and state;
- every discovered contradiction is resolved or explicitly deferred with missing evidence and an owner;
- full supersession claims account for surviving behavior, compatibility, rationale, and inbound links;
- changed examples and commands have observable verification;
- generated, localized, and navigation surfaces agree with their owners;
- the final checkout identity is compared with the opening snapshot, and any drift is excluded or explicitly bounded;
- the final report distinguishes inspected coverage from uninspected areas and does not infer zero problems from a partial scan.
