# Astra transition skill snapshots

Audit completed: `2026-09-05T23:03:17+08:00`

This record documents the user-requested backup of video skills before their
active Codex installations were removed. The hashes below cover the installed
source trees before repository-only license files or privacy edits were added.

## HyperFrames

- Installed plugin: `hyperframes@openai-curated` version `0.1.2`
- Repository: `https://github.com/heygen-com/hyperframes`
- Verified upstream commit: `ae3d80c30f89f8811e27189838f8a1f34572d062`
- License: Apache-2.0
- Snapshot policy: preserve the installed trees. Eight matched the verified
  upstream; `hyperframes-creative/references/house-style.md` and
  `hyperframes-registry/references/contributing.md` were older than that commit
  and remain intentionally unchanged in this snapshot.

| Skill | Files | Source tree SHA-256 |
| --- | ---: | --- |
| `general-video` | 4 | `36943f2f522eb5e6f1e221dbe5f3e584d0f2b64980527b4682c4e8423f1c3eaa` |
| `hyperframes` | 17 | `6d00dafc48e30b168eb266c0072b1301d42bb64af3db2f7752132e9148cff9b4` |
| `hyperframes-animation` | 121 | `d5cdafaae084d222d40f9e616e2ba417a5dffe9e3228a788b38dce32a5f78fd1` |
| `hyperframes-audio` | 7 | `6b2a95c13fc994faf05fcb783cba0b6ea6ff103ac6400ff3ec262aa2abcb932c` |
| `hyperframes-cli` | 11 | `a8218eef7a74b8ab796ababc911e14191583f861d3395e5744565f1713647e27` |
| `hyperframes-core` | 20 | `0e50c07442cfcf8c488d4f772e19630aa8dc53d96ff137c2656a615b71a40d21` |
| `hyperframes-creative` | 78 | `e5829c348fe2bbff15f9f5f18efc4a2a2abd0b8e99aadb690d6eb35a2bf16979` |
| `hyperframes-keyframes` | 3 | `5c9d6c97523f8c8cbf446a3d4d5064505361b08033cbff5342a3c03430c909b2` |
| `hyperframes-registry` | 12 | `14e9ef6f309fd7776e3a91cea21da19ec53ea39460750aa95146868cd78e0fe6` |
| `media-use` | 153 | `a0db0e9bd3ec374221a7d2bc958856bda2985de2da03ffb128a56802b05b52bc` |

## Remotion

- Installed plugin: `remotion@openai-curated` version `1.0.3`
- Declared repository: `https://github.com/remotion-dev/remotion`
- Upstream reference commit observed during backup:
  `cb053ab25292f8e7559dc5295f4286cde2268481`
- License: MIT, from `packages/agent-plugin/LICENSE` at that commit
- Installed skill tree: 40 files, SHA-256
  `e740cd96c72ba65531652672d8d10d7d631ecfbc51763b3447d3482f78d7fd93`
- Repository adaptation: the existing `remotion-video-creation` backup is
  replaced with this installed snapshot; its frontmatter name remains the
  repository folder name so the Skill Hub index stays valid. Markdown trailing
  whitespace was normalized to satisfy the repository diff gate.

## Privacy and packaging gate

- Text sources were scanned for personal absolute paths, private-key blocks,
  bearer tokens, credential assignments, signed URLs, email addresses, and
  account identifiers before copying.
- No personal path, private key, bearer token, signed URL, or user credential
  was found.
- One embedded PostHog project key in `media-use` was classified as unsuitable
  for this public backup and is replaced with a non-secret placeholder in the
  repository copy. The repository copy treats that placeholder as telemetry
  disabled, so it cannot send an invalid or accidental event.
- The validator rejects angle brackets in descriptions, so the
  `hyperframes-audio` frontmatter spells the `hf-audio-group` element without
  literal angle brackets. Runtime meaning is unchanged.
- Vendor support addresses and `example.com` test fixtures were classified as
  public/vendor or synthetic data, not personal data.
- Binary files are limited to upstream MP3 fixtures and WOFF2 fonts. They are
  retained as runtime-relevant skill assets and are covered by the upstream
  Apache-2.0 license.

## Restore coordinates

- HyperFrames skills: copy the desired directory from
  `skills/07-media-content/` into the active user skill root, or reinstall
  `hyperframes@openai-curated` for the managed plugin.
- Remotion plugin: reinstall `remotion@openai-curated`; the repository snapshot
  is evidence and a fallback, not a replacement for the managed plugin.
