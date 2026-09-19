# GPT-6 Pro Context Packet Template

Use this template when preparing a consultation packet.

````markdown
CONTEXT_PACKET_V1

```json
{
  "task_id": "gpt6-pro-consult-YYYYMMDD-HHMMSS",
  "sentinel": "GPT6_PRO_RESULT_YYYYMMDD_HHMMSS",
  "task_type": "plan_review|architecture_review|business_consult|skill_design|risk_review|orchestrator_loop|other",
  "consult_mode": "reviewer|orchestrator_loop",
  "review_round": 1,
  "context_strategy": "problem_first_full_context",
  "credential_status": "no_executable_credentials",
  "context_hash": "<sha256 of markdown body>",
  "required_output": [
    "reasoning_brief",
    "direct_judgment",
    "biggest_flaw",
    "specific_revisions",
    "adoption_decision"
  ]
}
```

## TASK

## BACKGROUND

## USER_INTENT

## LOCAL_JUDGMENT

## EVIDENCE

## ATTEMPTS_SO_FAR

## OPTIONS

## RISKS

## ASK

Please act as a strict reviewer or orchestrator. Find the biggest flaw first, then give the strongest revised path and explicit acceptance criteria for Codex to verify locally. Do not provide generic encouragement. Do not reveal hidden chain-of-thought; instead output a concise reasoning brief with assumptions, decision frame, evidence weighting, counterarguments, and tradeoffs.

## RETURN_FORMAT

First line must be: GPT6_PRO_RESULT_YYYYMMDD_HHMMSS

Then use:
1. Reasoning brief: assumptions, frame, evidence, counterargument, tradeoffs
2. Direct judgment
3. Biggest flaw
4. Required changes
5. What to ignore
6. Final adoption recommendation
````
