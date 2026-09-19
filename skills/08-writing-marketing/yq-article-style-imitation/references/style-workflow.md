# Style Workflow

## Output Package

For each style run, create:

1. `source-fetch-log.md`
2. `style-reference-corpus.md`
3. `raw-sources/S1.md`, `raw-sources/S2.md`, etc. for accepted style sources
4. `style-mechanism-breakdown.md`
5. `evidence-ledger.md`
6. `imitation-draft.md`
7. `imitation-repair-notes.md`
8. `reviews/01-source-audit.md`
9. `reviews/02-style-audit.md`
10. `reviews/03-fact-audit.md`
11. `reviews/04-platform-audit.md` when platform drafts exist
12. platform drafts only after the imitation draft passes repair

Do not collapse these into one mixed file. A single file containing corpus, teardown, facts, and draft hides whether the chain is solid.

## Source Fetch Log

Search results are candidates, not sources. Record every candidate before accepting or rejecting it:

- query
- URL
- open/access result
- title observed after opening
- byline observed after opening
- readable text captured: yes/no
- rejection reason if rejected

Do not move a candidate into `style-reference-corpus.md` as a style source until a readable page or local text has been captured.

## Reference Corpus

Record sources, but do not turn the final article into a citation page.

Minimum fields:

- source_id
- target_writer
- role: `primary-style-source` or `background-only`
- source_grade: `A`, `B`, `C`, or `D`
- access_status: `ok`, `blocked`, `404`, `login-required`, `snippet-only`, or equivalent
- text_available: `yes` or `no`
- local_text_path
- title
- byline / author
- source URL or local path
- date
- authorship evidence
- accepted_for: `style`, `background`, `fact`, or `rejected`
- why selected
- what part of style it teaches

For copyrighted material, quote only short snippets when truly necessary; prefer summary.

Primary style sources must be written by the target writer. Background sources can help confirm biography, publication context, or representative works, but they cannot teach style and cannot justify drafting.

Style sources do not need to match the target article topic. A target writer's essay about one topic can teach style for an article about another topic if it is readable, author-written, and substantially available. Topic evidence belongs in `evidence-ledger.md`, not in the style corpus.

Do not reject third-party reposts by host alone. A medical site repost, blog archive, or media repost may be accepted as grade `B` if it has clear byline/provenance and substantial readable text. If the page is inaccessible, snippet-only, or only visible in search results, grade it `C` and do not use it for style.

Reject these as primary style sources:

- encyclopedia or author profile pages;
- book metadata pages;
- news reports about the writer;
- interviews where the writer is the subject, not the bylined author;
- platform blurbs, reviews, summaries, or short detached quotes.

If fewer than two primary style sources exist for a target writer, stop and write a source-gap note unless Ethan explicitly approves the smaller corpus.

## Mode Selection

Honor the user's requested imitation mode.

- If Ethan says `仿[作家]`, `按[作家]文风`, `直接仿写`, or names any writer as the target style, use direct imitation mode by default.
- Direct imitation mode may target any living or historical writer. Match observable style behavior: scene entry, narrative distance, paragraph rhythm, sentence functions, question movement, evidence placement, image system, restraint or humor, and ending shape.
- Do not soften the task into generic mechanism transfer just because the writer is living.
- Do not copy source sentences, distinctive coined phrases, or paragraph sequences. Do not claim the reference writer authored, reviewed, or endorsed the output.
- Use mechanism transfer only when Ethan asks for a looser adaptation, public-risk conversion, or an original house style derived from references.

## Expression-DNA Teardown

Analyze the target writer's expression DNA at three layers. This follows the Nuwa-style distillation idea: extract how the person expresses, not just what they once said.

Every observation must be traceable to primary source IDs. Use a compact form:

`Observation -> source_id(s) -> article position -> do-not-copy warning`

Do not use a source ID in teardown if it is grade `C`/`D`, inaccessible, 404, missing local text, or accepted only for background.

Macro:

- where the article begins
- how it moves from person to public issue
- when judgment appears
- where evidence enters
- how the ending returns to the person or scene

Paragraph:

- paragraph length rhythm
- transition methods
- question placement
- scene-to-analysis ratio
- how abstract nouns are avoided or justified

Sentence:

- concrete nouns
- verbs of seeing, asking, waiting, checking
- whether the sentence observes, turns, judges, verifies, or closes
- phrases that must not be copied

## Evidence Ledger

Keep formal evidence handling outside the article.

Use this file for:

- URLs
- source dates
- exact official claims
- known facts
- candidate hypotheses
- verification paths
- safe wording
- legal/medical/compliance cautions

The article may absorb the meaning, but not the ledger labels.

Separate evidence types:

- `fact`: sourced claim that can support factual statements.
- `user-case`: user-provided case, screenshot, transcript, or interview material.
- `observation`: reasonable social observation; can inform tone but cannot support numerical, institutional, or universal claims.

If there is no `user-case` or real interview material, do not write a first-person interview article.

## Form Selection

Do not automatically turn any writer imitation into a single genre. The source corpus and Ethan's request decide the form.

Default choices:

- reflective essay;
- scene-led commentary;
- first-person reflection without fake interviews;
- third-person composite narrative if the user permits fiction/composite writing.

Use reportage only when real case/interview/source material exists or Ethan explicitly asks for it.

Use pseudo-documentary/literary reportage only when Ethan explicitly asks for `伪纪实文学` or `伪纪实`. In that mode, composite scenes are allowed, but fake reporting claims are still risky; prefer third-person narration over `我问他`.

## Evidence-To-Prose Translation

Before drafting, translate each hard fact into one of four prose forms:

| Evidence type | Article form |
|---|---|
| Official policy | "后来我查到..." / "这份文件没有回答全部问题，但它至少说明..." |
| Number | Use only when it changes the reader's understanding |
| Uncertainty | Put doubt inside a sentence, not as `候选假设` |
| Verification path | Turn into the narrator's next question or a concrete action |

Do not paste URLs, source IDs, table labels, or risk-gate labels into the article.

## Point-Of-View Continuity

A style imitation can still fail after passing URL and report-language checks if it changes narrative level.

Wrong level:

- "写这个题目..."
- "如果要查清楚..."
- "这篇文章能走到..."
- "不能从某个大词开始..."
- "最危险的是..."

These are backstage writing/investigation comments. They may belong in repair notes or evidence ledgers, not in the article.

Right level:

- a patient asks why this box is gone;
- a doctor explains what can and cannot be changed;
- a pharmacist looks up a manufacturer, specification, or stock status;
- the narrator checks a document and narrows one claim;
- the ending returns to the person, object, or scene.

For verification paths, convert "how a reporter should check" into "what the person in the scene still does not know." Example:

Bad:

> If this is to be investigated clearly, start from the molecule, brand, specification, hospital, city, and time.

Better:

> The question becomes smaller only when it lands on one box: this drug name, this manufacturer, this specification, this hospital, this date.

## Repair The Imitation Draft First

If a draft has a good opening and a weak second half, do not patch words one by one. Diagnose which mode took over:

- evidence dump
- policy summary
- AI safety disclaimer
- consultant/report conclusion
- platform copywriting
- meta-writing or investigation-method commentary

Rewrite that section in the target style before adapting to any platform.

## Common Failure From Baseline Test

A zero-context agent wrote a strong first half, then switched to:

- inline URLs;
- `已知事实 / 候选假设 / 验证路径`;
- words like `根因`, `写死`, `边界`;
- report-like endings;
- meta-writing commentary such as `所以，写...`, `如果要把它查清楚...`, and `不能从...这个大词开始`.

This happens when the skill tells the agent to be evidence-safe but does not teach evidence-to-prose translation.

A later run fixed URLs and report labels but still failed by leaking verification method into the article voice. That means the skill also needs a point-of-view continuity gate.

The fix is not to remove evidence discipline. The fix is to keep evidence discipline in companion files and make the article hide its scaffolding.

## Independent Review

This skill uses a Nuwa-style split between mechanical validation and independent judgment.

Python scripts are responsible for checks that can be made deterministic:

- required package files exist;
- corpus rows contain source access and local text fields;
- style teardown references valid source IDs;
- draft text does not leak URLs, risk labels, or known AI/report phrases;
- independent review artifacts exist and contain explicit verdicts.

Independent reviewer agents are responsible for judgment:

- whether a source is really useful as style evidence, not just technically present;
- whether the expression-DNA teardown is specific enough to guide imitation;
- whether the draft sounds like the target writer throughout, not only in the opening;
- whether factual uncertainty is handled without turning the article into a report;
- whether platform adaptation is based on reviewed platform evidence.

The drafting agent cannot mark its own run as final. At minimum, run:

1. Source auditor after corpus and raw source capture.
2. Style auditor after imitation draft and repair.
3. Fact auditor before publication.
4. Platform auditor when WeChat/Xiaohongshu outputs exist.

Each reviewer writes one file under `reviews/` with `reviewer_role`, `verdict`, `checked_files`, `critical_findings`, `required_changes`, and `independence_note`.

Run `scripts/review_style_run.py` only after those files exist. The script checks the review package; it does not replace the reviewers.
