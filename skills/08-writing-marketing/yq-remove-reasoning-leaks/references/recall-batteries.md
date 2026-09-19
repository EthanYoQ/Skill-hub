# Recall batteries

These searches probe the taxonomy in [the skill](../SKILL.md). Every hit needs semantic judgment. The batteries over-match by design and under-match by nature, so pair them with an unpatterned read of the densest prose in scope.

## Invocation rules

- Add `--hidden --glob '!.git/**'` when hidden project directories may contain active decisions or agent documentation.
- Put exclusions after inclusion globs so a later include cannot re-admit third-party, generated, dependency, archive, fixture, snapshot, or recorded-output paths. Discover the repository's actual paths rather than assuming one layout.
- If this skill's own directory is inside the audited scope, exclude it because its examples deliberately quote leaked wording.
- Natural-language probes use `-i` so sentence-initial capitalization still matches. Keep code-like phase-label probes case-sensitive to limit noise.
- A zero-hit pattern proves nothing until the command has matched a known-positive test string and the searched boundary is known to be complete.

## English battery

```sh
rg -n --hidden '\(decision \d|\(audit [A-Z]\d|design §|plan §|design ledger|\(B ruling|\bP-I\b|\bW\d\b|\bT\d\b' <scope> <exclusions>
rg -n --hidden -i 'this PR|this branch|this stack|later PR|previous commit|this commit' <scope> <exclusions>
rg -n --hidden -i 'used to |no longer|previously|the old |was renamed|was moved' <scope> <exclusions>
rg -n --hidden -i '\bv1\b|this cut|\bcut \d|\btoday\b|\bfor now\b|roadmap' <scope> <exclusions>
rg -n --hidden -i 'rejected in review|review round|reviewer|as of v\d' <scope> <exclusions>
rg -n --hidden -i 'probably |should be enough|should suffice|it simply|is safe —|is safe --' <scope> <exclusions>
rg -n --hidden '§\d' <scope> <exclusions>
```

## Chinese battery

```sh
rg -n --hidden '设计稿|上一?轮(?:评审|修改)|评审(?:确认|认为|否决|结论)|旧版(?:实现|方案)|老的(?:实现|方案)|不再(?:需要|使用|支持)|以前(?:我们|这里|该)|本版(?:改动|方案)|遗留(?:TODO|问题)|----.*私有.*----' <scope> <exclusions>
rg -n --hidden '(^|[^a-zA-Z])端([^a-zA-Z]|$)' --glob '*.md' <scope> <exclusions>
```

Replace `<scope>` and `<exclusions>` with concrete arguments before execution.

Bare `评审`, `遗留`, and `私有` are low-signal in Chinese technical repositories because they often name legitimate review processes, legacy systems, or private members. Use them only as optional probes over a small, already relevant prose scope; never use those bare terms as the first corpus-wide battery.

## Known false-positive families

- **Instrumental “used to”** — “the key used to sign requests” can mean purpose, not past state.
- **Runtime old/new** — “the old connection drains before the new one accepts” names live objects during handover.
- **PR language in process docs** — documentation about PR workflow legitimately says “the PR”; leakage is a durable product doc adopting one PR's temporary vantage.
- **`v1` identifiers** — `/v1/chat`, protocol versions, and schema names are identifiers, not automatically indexical stamps.
- **Resolvable `§N` references** — committed documents and external standards may own stable section numbering.
- **Measured or quoted output** — timestamps, “today,” and narration inside recorded evidence preserve the observed text.
- **Alternatives sections** — “rejected” inside a decision record's alternatives section is the sanctioned genre.
- **Chinese current-release wording** — a phrase can be valid inside a versioned release artifact; judge whether it is a bare unstable stamp or owned release context.
