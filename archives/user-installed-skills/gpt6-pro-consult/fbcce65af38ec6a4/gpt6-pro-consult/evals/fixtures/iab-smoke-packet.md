[CODEX_IAB_SOL_PRO_E2E_V2]

## Review question

Review this acceptance gate for a Codex Skill whose only consultation surface is the Codex in-app Browser:

1. The execution log proves the selected browser binding is `iab`.
2. The visible ChatGPT controls show exact `GPT-6 Pro` as selected, or the localized pair `6 Pro` plus `最新`/`Latest` selected; `5.6 Pro`, a generic `Pro` label, or `最新`/`Latest` alone is insufficient.
3. The packet is submitted exactly once in that in-app Browser conversation.
4. The latest complete assistant turn contains the requested sentinel.
5. No Chrome extension, Chrome CLI, OpenCLI, external Playwright, or browser automation process is used.

Codex's prior judgment: this is much stronger than checking route language, but DOM-only assertions could still be satisfied by fabricated narrative output. The evaluation should retain browser-side snapshots or screenshots and a dispatch-state record as evidence.

Identify the single biggest remaining blind spot and propose the smallest stronger acceptance gate. Give four concise bullets: verdict, blind spot, stronger gate, and why it is discriminative. Do not provide hidden chain-of-thought.

End the answer with this exact standalone line:

GPT6_PRO_RESULT_IAB_PROBE_20260727
