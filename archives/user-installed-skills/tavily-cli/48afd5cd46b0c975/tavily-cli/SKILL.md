---
name: tavily-cli
description: |
  Route ordinary public-web information tasks to the correct Tavily CLI operation. Use when the task concerns publicly accessible webpages and needs web discovery, clean extraction, URL mapping, same-site crawling, or public-web-only research, but the exact Tavily operation is not yet clear or several operations must be sequenced. Prefer the specific leaf skill when intent is clear: tavily-search for discovery without a URL, tavily-extract for known URLs, tavily-map for URL/site-structure discovery, tavily-crawl for content from many pages on one site, tavily-research for cited multi-source synthesis, and tavily-dynamic-search for programmatic filtering with context isolation. Do not use for named social/community/media/career/code platforms, login or cookie-dependent content, platform-native discussions, or cross-platform collection; use Agent Reach there. Do not use for local files, Git operations, deployments, or ordinary code editing.
metadata:
  compatibility: Requires tavily-cli (`curl -fsSL https://cli.tavily.com/install.sh | bash`) and a Tavily API key from tavily.com.
allowed-tools: Bash(tvly *)
---

# Tavily CLI

Web search, content extraction, site crawling, URL discovery, and deep research. Returns JSON optimized for LLM consumption.

## Boundary With Agent Reach

Route by source and access method:

- Use Tavily for ordinary, publicly accessible webpages.
- Use Agent Reach for named platforms, platform-native content, login state,
  browser sessions, specialized APIs/CLIs, and cross-platform collection.
- For mixed tasks, Agent Reach retrieves platform evidence and Tavily handles
  the ordinary webpages.
- If one capability is unavailable, state the fallback and use the other only
  when it can satisfy the request without overstating coverage.

When a Tavily operation is already clear, load the corresponding leaf skill
instead of keeping this router as the only instruction source.

Run `tvly --help` or `tvly <command> --help` for full option details.

## Prerequisites

Must be installed and authenticated. Check with `tvly --status`.

```bash
tavily v0.1.0

> Authenticated via OAuth (tvly login)
```

If not ready:

```bash
curl -fsSL https://cli.tavily.com/install.sh | bash
```

Or manually: `uv tool install tavily-cli` / `pip install tavily-cli`

Then authenticate:

```bash
tvly login --api-key tvly-YOUR_KEY
# or: export TAVILY_API_KEY=tvly-YOUR_KEY
# or: tvly login  (opens browser for OAuth)
```

## Workflow

Follow this escalation pattern — start simple, escalate when needed:

1. **Search** — No specific URL; discover ordinary public webpages.
2. **Extract** — Known public URL(s); retrieve content directly.
3. **Map** — Known site root; discover URLs without extracting content.
4. **Crawl** — Known public site/section; extract content from many pages.
5. **Research** — Public-web-only, multi-source synthesis with citations.

| Need | Command | When |
|------|---------|------|
| Find pages on a topic | `tvly search` | No specific URL yet |
| Get a page's content | `tvly extract` | Have a URL |
| Find URLs within a site | `tvly map` | Need to locate a specific subpage |
| Bulk extract a site section | `tvly crawl` | Need many pages (e.g., all /docs/) |
| Deep research with citations | `tvly research` | Need multi-source synthesis |

For detailed command reference, use the individual skill for each command (e.g., `tavily-search`, `tavily-crawl`) or run `tvly <command> --help`.

## Output

All commands support `--json` for structured, machine-readable output and `-o` to save to a file.

```bash
tvly search "react hooks" --json -o results.json
tvly extract "https://example.com/docs" -o docs.md
tvly crawl "https://docs.example.com" --output-dir ./docs/
```

## Tips

- **Always quote URLs** — shell interprets `?` and `&` as special characters.
- **Use `--json` for agentic workflows** — every command supports it.
- **Read from stdin with `-`** — `echo "query" | tvly search -`
- **Exit codes**: 0 = success, 2 = bad input, 3 = auth error, 4 = API error.
