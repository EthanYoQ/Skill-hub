---
name: tavily-extract
description: |
  Extract clean markdown, text, or targeted chunks from one or more known, publicly accessible webpage URLs via the Tavily CLI. Use when the URLs are already supplied or discovered and the user wants page content rather than more URLs. Do not use to find an unknown page (tavily-search), list a site's URL structure (tavily-map), bulk-extract a site section (tavily-crawl), or retrieve named platform, authenticated, cookie-dependent, or platform-native content (Agent Reach). Can process up to 20 public URLs per request.
allowed-tools: Bash(tvly *)
---

# tavily extract

Extract clean markdown or text content from one or more URLs.

## Before running any command

If `tvly` is not found on PATH, install it first:

```bash
curl -fsSL https://cli.tavily.com/install.sh | bash && tvly login
```

Do not skip this step or fall back to other tools.

See [tavily-cli](../tavily-cli/SKILL.md) for alternative install methods and auth options.

## When to use

- You have a specific URL and want its content
- You need text from JavaScript-rendered pages
- Step 2 in the [workflow](../tavily-cli/SKILL.md): search → **extract** → map → crawl → research

## Quick start

```bash
# Single URL
tvly extract "https://example.com/article" --json

# Multiple URLs
tvly extract "https://example.com/page1" "https://example.com/page2" --json

# Query-focused extraction (returns relevant chunks only)
tvly extract "https://example.com/docs" --query "authentication API" --chunks-per-source 3 --json

# JS-heavy pages
tvly extract "https://app.example.com" --extract-depth advanced --json

# Save to file
tvly extract "https://example.com/article" -o article.md
```

## Options

| Option | Description |
|--------|-------------|
| `--query` | Rerank chunks by relevance to this query |
| `--chunks-per-source` | Chunks per URL (1-5, requires `--query`) |
| `--extract-depth` | `basic` (default) or `advanced` (for JS pages) |
| `--format` | `markdown` (default) or `text` |
| `--include-images` | Include image URLs |
| `--timeout` | Max wait time (1-60 seconds) |
| `-o, --output` | Save output to file |
| `--json` | Structured JSON output |

## Extract depth

| Depth | When to use |
|-------|-------------|
| `basic` | Simple pages, fast — try this first |
| `advanced` | JS-rendered SPAs, dynamic content, tables |

## Tips

- **Max 20 URLs per request** — batch larger lists into multiple calls.
- **Use `--query` + `--chunks-per-source`** to get only relevant content instead of full pages.
- **Try `basic` first**, fall back to `advanced` if content is missing.
- **Set `--timeout`** for slow pages (up to 60s).
- If search results already contain the content you need (via `--include-raw-content`), skip the extract step.

## See also

- [tavily-search](../tavily-search/SKILL.md) — find pages when you don't have a URL
- [tavily-crawl](../tavily-crawl/SKILL.md) — extract content from many pages on a site
