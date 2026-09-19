# Reasoning-leakage examples

Use these examples to identify governing principles, not as text templates. This file deliberately quotes leaked wording as calibration material; exclude the skill's directory when it falls inside an audit scope.

## Dead citations

### Decision ordinal with a committed owner

**Leaked:** "Slash input resolves against the visible catalog (decision 21)."

**Fixed:** "Slash input resolves against the visible catalog; the committed input-pipeline decision record owns the rationale."

The ordinal resolves nowhere at the current revision; the decision's name and committed path do. Link the real owning path at least once where the surface supports links; later mentions may use the searchable name alone.

### Decision ordinal without an owner

**Leaked:** "The registry rejects duplicate names (decision 7: names are flat, no namespacing)."

**Fixed:** "The registry rejects duplicate names; names are flat, with no namespacing."

No committed artifact owns "decision 7", so the citation is deleted — but its factual clause (flat names) is restated to stand alone, not deleted with it.

### Audit item codes

**Leaked:** "Rendering is pure: same snapshot, same string (audit R3)."

**Fixed:** "Rendering is pure: same snapshot, same string."

There is no audit document in the repo; the code is pure session shorthand carrying zero propositions.

### Section numbers of uncommitted drafts

**Leaked:** "Layering follows the design (v2 §3.2): `src/core/` is the pure core."

**Fixed:** "Layering: `src/core/` is the pure core."

`§N` of a draft nobody committed is unresolvable. Contrast: "escapes per RFC 9110 §10.1.5" stays — an external standard resolves outside the repo by design, and a committed doc that owns its §-numbering may be cited by section.

### Plan-phase labels

**Leaked:** "`src/client/` is the shell (T4); the P-I migration owns the adapters."

**Fixed:** "`src/client/` is the shell; the adapters live in `src/client/adapters/`."

Phase labels index a plan that never landed. Replace the label with what the phase produced.

## Stack and PR vantage

### Stack position in durable prose

**Leaked:** "A future remote backend implements this interface (the sandbox backend is a later PR in this stack)."

**Fixed:** "A remote backend can implement this interface without changing the render layer."

Durable prose cannot see the stack. Keep the extension-point contract; the pending work's home is the PR itself, a `TODO`, or an issue.

### "This PR" in a README

**Leaked:** "This PR adds cursor-based pagination to the session list."

**Fixed:** "The session list paginates by cursor."

A README outlives every PR; state the mechanism as current fact.

## Change narration and version stamps

### War story with a PR number

**Leaked:** "Colors used to come from `--widget-*` tokens, which nothing defined, so it always rendered the fallbacks; the alias tokens fixed that (PR #88)."

**Fixed:** "Colors come from the alias tokens; an undefined token renders the fallbacks."

Both live facts survive — the current mechanism and the standing failure behavior — restated in the present. The bug's biography belongs to the PR and its owning decision or postmortem.

### Removal narration

**Leaked:** "The `probe` field is gone with the removal cut; badges ride the generic projection pair now."

**Fixed:** "Badges use the generic projection pair."

Readers who never saw `probe` learn nothing from its absence. "Now" contrasting with a deleted past is a version stamp.

### Fixed regression → counterfactual present

**Leaked:** "This used to double-encode multibyte labels."

**Fixed:** "Without the byte-length guard, multibyte labels double-encode."

The regression pin survives as a present-tense counterfactual that names the guard; "used to" pins it to repo archaeology instead.

### Indexical version stamps

**Leaked:** "Batch rendering is synchronous this cut; the async path is roadmap work."

**Fixed:** "Batch rendering is synchronous." (The deferral lives in `TODO(widget-batch):` at the call site.)

"This cut" / "v1" / "today" go stale the moment they merge. A historical stage name inside a decision record's history section ("the first cut shipped X") is current-state-safe; the indexical form never is.

## Review choreography

### Review verdicts as prose

**Leaked:** "Rejected in review: caching the resolved spec. We keep resolution per-call."

**Fixed (in a decision record's Alternatives considered):** "**Caching the resolved spec.** Rejected: the spec depends on per-call cwd, so a cache keyed by request would serve stale roots."

The alternatives-considered genre is the sanctioned home; the reviewer and the round are not part of the rationale.

### Draft ordinals

**Leaked:** "As of v5 of this note, the loader also validates manifests."

**Fixed:** "The loader validates manifests."

An implemented note states shipped reality; its own revision history lives in git.

## Reviewer-addressed justification

### Arguing a cast

**Leaked:** "The cast is safe — the SDK constructed the object, it simply doesn't declare the optionals strictly enough."

**Fixed:** "The SDK constructs this object with every optional populated; the declared type is looser than the runtime guarantee."

State the invariant a maintainer must not break. "It simply…" is a voice answering an objection nobody at HEAD raised. If the invariant is visible in the code, delete the comment instead.

### Appeal to review authority

**Leaked:** "This is correct because the reviewer confirmed the wrapping order."

**Fixed:** (deleted; the wrapping order is stated in the function's `@returns`.)

Correctness claims cite invariants or tests, never people.

## Restatement and derivation

### Control-flow narration

**Leaked:** "First we normalize the label, then we truncate it, then we wrap it."

**Fixed:** (deleted.)

The three lines below the comment say the same thing in code.

### Test walkthrough

**Leaked:** "This test creates a session, sends two messages, waits for the second reply, and then asserts the log has four entries."

**Fixed:** "Two round-trips must produce exactly four log entries — the projection dedupes the shared prefix."

Keep only the non-obvious assertion rationale; the walkthrough restates the test body.

## Hedges and planning residue

### Unmarked deferral

**Leaked:** "Probably fine to render eagerly for now."

**Fixed:** (deleted; the deferral already has its `TODO(widget-batch):` marker.)

A hedge without an owner is planning residue. When repository edits are authorized, replace it with a concrete marker such as `TODO(name): coalesce per animation frame`. Otherwise report the proposed marker. Creating or updating an external issue is a separate action that requires explicit authorization.

### Vague sizing

**Leaked:** "A 64 KiB buffer should be enough for most cases."

**Fixed:** "64 KiB holds the largest observed frame (48 KiB) with headroom; a larger frame fails loudly in `decode`."

Replace the hedge with the actual bound and the failure behavior when it is exceeded.

## Authoring-language slips

**Leaked:** "The renderer runs on the client 端; see the 设计稿 for spacing. ---- 私有 ----"

**Fixed:** "The renderer runs on the client side; spacing follows the Figma frame `widget-badges`."

Working-language fragments and session separators are transcription residue. The Figma frame name stays: external provenance that resolves outside the repo by design.

## Keeps

### Issue references are durable on every surface

**Keep:** "The cap applies to the complete rendered value, wrappers included (issue #1470 owns the follow-up)."

Issue references can remain on any surface when the tracker is part of the project: "#N owns the follow-up" gives deferred work a durable home even in a README. Decision records and postmortems can additionally cite merged changes as evidence.

### Dead name-drops are not "naming the owner"

**Delete:** "Badge renderer over the widget seam (see the widget-rendering RFC)."

The test is resolvability, not form: no committed file answers to "the widget-rendering RFC", so the pointer is dead. Retarget it to the committed owner if one exists; otherwise delete it.

### Suppression justifications

**Keep (after fixing):** `// oxlint-disable-next-line no-non-null-assertion -- the one-element literal guarantees index 0.`

The justification clause is required prose. When the stated reason is false (the original said "the loop guard above proves a frame exists" with no loop in sight), fix the reason; never delete it.

### Measured bounds

**Keep:** "Depth cap (measured: 512 nests ≈ 0.15s synchronous; 4096 blocks the loop)."

The measurement pins the constant against uninformed retuning, and "measured" is the provenance that distinguishes data from a guess.

### Runtime old/new is not change history

**Keep:** "The old connection drains before the new one accepts."

"Old" and "new" here name two live runtime objects during handover, not repository states. The change-narration ban is about repo history, not lifecycle vocabulary.

## Overcorrection traps

These traps show edits that appear cleaner while losing or changing a proposition. Enumerate a passage's propositions before trimming it.

### Flipping an obligation into an endorsement

**Original:** "These direct registrations are exceptions pending migration to slots."

**Overcorrected:** "These direct registrations are sanctioned exceptions."

**Right:** "These direct registrations are exceptions pending migration to slots."

"Pending migration" is an obligation; "sanctioned" blesses the status quo. The trim inverted the sentence's modality while shortening it.

### Promoting a hypothetical to a shipped feature

**Original:** "A future IPC-based shell subclasses the executor and overrides `spawn`."

**Overcorrected:** "An IPC-based shell subclasses the executor and overrides `spawn`."

**Right:** "A hypothetical IPC-based shell — no such shell exists — would subclass the executor and override `spawn`."

Deleting the future-marker alone turns a design illustration into a claim that the class ships. Mark the hypothetical explicitly instead of just unmarking the future.

### Deleting a true fact with the transcript around it

**Original:** "The gate notice narrates the check order; the notice text is also what the generated-pages check compiles against."

**Overcorrected:** "…" (whole sentence deleted as narration.)

**Right:** "The notice text is what the generated-pages check compiles against."

Half the sentence was narration; the other half was a load-bearing coupling. Delete clauses, not sentences, when propositions share a line.

### Dropping provenance while keeping the number

**Original:** "The 4 MiB ceiling is measured: the largest generated client-bindings module is 3.1 MiB."

**Overcorrected:** "The ceiling is 4 MiB; the largest generated client-bindings module is 3.1 MiB."

**Right:** keep "measured".

Without "measured" the 3.1 MiB reads as a definition rather than an observation, and nobody re-measures before raising the ceiling.
