# Batch Collection Options

Use this reference when Agent Reach/OpenCLI browser collection is too slow or the run needs more than 1,000 independent evidence items (deduplicated notes plus deduplicated comments). Search rows and detail rows remain collection diagnostics, not extra independent evidence.

## Execution Owner

Run Xiaohongshu information collection in a collector subagent when subagent tools are available. The main agent should not spend the whole turn waiting on browser/crawler I/O if it can refine queries, prepare schema mapping, or review methodology in parallel.

Model choice:

- Prefer the environment's current general-purpose tool-using model because XHS collection involves tool handling, login/captcha observation, error judgment, and structured reporting.
- Use a cheaper or faster available model only for narrow deterministic subtasks: counting rows, converting files, validating schema, or running a known smoke command.
- Do not pin model identifiers in this reference. If the environment cannot enumerate or override models, omit the override.

Use one active XHS collector per logged-in account/session by default. More parallelism can increase platform-risk; split keyword shards across multiple collectors only when the user explicitly asks for parallel collection.

## Known Facts

- Agent Reach/OpenCLI is reliable for logged-in browser access and spot validation, but each command carries browser/CLI overhead.
- MediaCrawler is the strongest open-source batch candidate found so far:
  - Repo: `NanmiCoder/MediaCrawler`
  - Supports Xiaohongshu keyword search, specified-note detail, creator crawl, first-level comments, optional second-level comments, login state, CDP/local Chrome mode, proxy settings, and JSONL/SQLite/Excel storage.
  - CLI verified locally with `uv run main.py --help`.
  - License is `NON-COMMERCIAL LEARNING LICENSE 1.1`; do not treat it as cleared for commercial use.
- XHS-Downloader is useful for link extraction and single-work metadata/download workflows, but it is not verified as a primary comment social-listening crawler.
- Redbook-Search-Comment-MCP2.0 can search/read notes/comments, but it also exposes comment-posting tools; treat it as read-only only after code audit.
- yangsijie666/xiaohongshu-crawler has a complete browser-crawler shape with search/detail/comment and JSON/Excel output, but lower repository maturity.
- Local 2026-07-05 evidence: MediaCrawler hit Xiaohongshu CAPTCHA/HTTP 461 on both a broad company query (`辉瑞`) and a low-frequency anchored query (`RWE 药企`). The same `RWE 药企` search, note read, and comment read succeeded through Agent Reach/OpenCLI. This supports preserving the broad query matrix and treating 461 as backend/session execution risk unless proven otherwise.

## MediaCrawler POC

Run a small POC before replacing the default collector:

```powershell
cd "<workspace>\_research\MediaCrawler"
uv run main.py --platform xhs --lt qrcode --type search --keywords "辉瑞,诺华,药代,MSL" --crawler_max_notes_count 10 --max_comments_count_singlenotes 10 --max_concurrency_num 1 --save_data_option jsonl --save_data_path "<workspace>\xhs-mediacrawler-poc"
```

POC query rule:

- Start with broad single terms for company names (`辉瑞`, `诺华`), aliases (`P司`, `N司`), and pharma-specific roles (`药代`, `MSL`, `医学部`). Do not use generic work or pain terms as standalone searches.
- Add paired terms such as `辉瑞 药代`, `诺华 MSL`, `药企 裁员`, or `医药代表 KPI` after broad terms establish baseline recall and noise.
- Treat `--crawler_max_notes_count` as per-keyword, not global. Four keywords at `10` means up to 40 notes before comments.

If CDP existing-browser mode cannot connect, either start Chrome with remote debugging on port `9222` or set `CDP_CONNECT_EXISTING = False` in `config/base_config.py` for the POC so MediaCrawler launches its own Chrome profile.

POC success criteria:

- Produces XHS content rows and comment rows in JSONL, SQLite, or Excel.
- Captures `note_id`, title/desc, note URL, source keyword, like/comment/share counts, comment content, comment like count, and parent note linkage.
- Finishes at materially higher throughput than one OpenCLI call per note, without repeated login/captcha failures.
- Output can be mapped into this skill's analyzer schema without losing raw note links or comment linkage.

If MediaCrawler returns `CAPTCHA appeared`, `Verifytype`, or HTTP `461`, stop the POC. Do not retry repeatedly in the same turn. Run an OpenCLI control query on the same keyword before making any conclusion about the query strategy:

```powershell
opencli xiaohongshu search "<same keyword>" --limit 5 -f json
opencli xiaohongshu note "<returned note url>" -f json
opencli xiaohongshu comments "<returned note url>" --limit 5 -f json
```

If OpenCLI succeeds, record the MediaCrawler path as blocked and continue with Agent Reach/OpenCLI collection. If OpenCLI also fails, pause automated collection because the account/browser/session may be challenged.

## Candidate Command For Large Run

Use only after the POC succeeds:

```powershell
uv run main.py --platform xhs --lt qrcode --type search --keywords "<comma-separated query matrix>" --crawler_max_notes_count 200 --max_comments_count_singlenotes 20 --max_concurrency_num 2 --get_comment true --get_sub_comment false --save_data_option jsonl --save_data_path "<workspace>\xhs-mediacrawler-run"
```

Keep concurrency conservative until captcha and account-risk behavior are observed. Increase only after a benchmark.

Do not run the large command unless a same-day low-volume MediaCrawler smoke succeeds. Minimum smoke:

```powershell
uv run main.py --platform xhs --lt qrcode --type search --keywords "RWE 药企" --crawler_max_notes_count 5 --max_comments_count_singlenotes 3 --max_concurrency_num 1 --get_comment true --get_sub_comment false --save_data_option jsonl --save_data_path "<workspace>\xhs-mediacrawler-smoke"
```

If that smoke returns 461 but OpenCLI works, use OpenCLI for collection and let MediaCrawler cool down for 12-24 hours.

Large-run query strategy:

1. Broad recall layer: single company and alias terms (`辉瑞`, `诺华`, `P司`, `N司`, `AZ`, `LL司`).
2. Role layer: single pharma-specific role terms (`药代`, `医药代表`, `MSL`, `MA`, `医学部`, `CRA`, `医学事务`, `市场准入`, `准入`).
3. Anchored pain layer: pair generic pain terms with pharma context anchors, for example `药企 裁员`, `外资药企 离职`, `药企 合规`, `医药代表 KPI`, `药企 报销`, `药企 背调`, `辉瑞 背调`, `诺华 薪资`, `药企 市场部`, `外资药企 市场部`.
4. Precision layer: entity + role, entity + pain, alias + pain pairs. Use these to raise signal, not to define the whole corpus.

Never run standalone `市场部`, `报销`, `背调`, `外企`, `裁员`, `离职`, `合规`, `薪资`, or `KPI`. These terms are valid only when paired with a company, alias, pharma role, or pharma industry anchor.

## Integration Notes

- Do not claim MediaCrawler is faster until a timed POC has been run on the user's machine. The speed advantage is a candidate hypothesis based on architecture: one process/session plus API pagination instead of one browser command per note.
- Prefer JSONL or SQLite for analysis. Excel is useful for manual review but less ideal as the canonical pipeline input.
- Map note rows to `note_details.jsonl` and comment rows to `comments.jsonl`; keep `source_keyword` and `note_url` intact for citation.
- Use Agent Reach/OpenCLI to spot-check sampled MediaCrawler links and investigate gaps or suspected parsing errors.

## Decision Table

| Need | Preferred path | Notes |
| --- | --- | --- |
| Quick source discovery | Agent Reach/OpenCLI | Reuses logged-in Chrome and is easy to inspect manually. |
| Large keyword sweep with comments | MediaCrawler only after same-day smoke succeeds | Best candidate when available; requires POC, license/rate-limit caution, and immediate fallback on 461. |
| MediaCrawler CAPTCHA/461 while OpenCLI works | Agent Reach/OpenCLI | Treat as backend/session execution risk; preserve query matrix, collect more slowly, and cool down MediaCrawler. |
| Extract search/user result links | XHS-Downloader userscript | Good helper, not primary evidence collector. |
| MCP-style read tools | Redbook MCP or yangsijie crawler | Sandbox only; avoid write/comment tools. |
| Stable enterprise monitoring | Paid social-data platform/API | Requires account/budget; verify data coverage and raw-link access. |
