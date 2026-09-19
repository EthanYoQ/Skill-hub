"""Phase 1 · contract-elicitor: ask 4-6 startup questions, write contract.json."""
from __future__ import annotations
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Any


class ContractElicitationError(Exception):
    """Raised when contract is incomplete or fails schema validation."""


# Field-by-field questions. The orchestrator's LLM provides ask_user callback.
DEFAULT_QUESTIONS: list[dict[str, str]] = [
    {
        "field": "evidence_window_start",
        "type": "date",
        "question": "Evidence window start date (YYYY-MM-DD)? Recommended: >=5 years for cancers, >=3 for chronic diseases.",
    },
    {
        "field": "evidence_window_end",
        "type": "date",
        "question": "Evidence window end date (YYYY-MM-DD)? Default: today.",
    },
    {
        "field": "geography",
        "type": "string",
        "question": "Primary geography for market sizing (e.g. China, USA, Global)?",
    },
    {
        "field": "include_intl_comparison",
        "type": "bool",
        "question": "Include international comparison section? (true/false)",
    },
    {
        "field": "report_depth",
        "type": "enum:executive,full,deep",
        "question": "Report depth: executive (~5 pages) / full (~30 pages) / deep (~80 pages)?",
    },
    {
        "field": "user_role",
        "type": "enum:BD,medical_affairs,investor,other",
        "question": "Your primary role (BD / medical_affairs / investor / other)?",
    },
]

_LOCALE_HINTS_CN = ("做", "市场", "调研", "研究", "中国", "亚太")
_ACTION_VERBS = ("做", "Run", "Generate", "Create", "Build", "市场调研",
                 "市场研究", "调研", "research", "market sizing for")


def parse_disease_and_locale(user_one_liner: str) -> tuple[str, str]:
    """Extract disease name + infer locale from a user one-liner."""
    text = user_one_liner.strip()

    # locale: detect Chinese characters or CN context
    has_cn_chars = bool(re.search(r"[一-鿿]", text))
    locale = "zh-CN" if has_cn_chars else "en-US"

    # strip action verbs (longest first)
    cleaned = text
    for verb in sorted(_ACTION_VERBS, key=len, reverse=True):
        cleaned = re.sub(re.escape(verb), " ", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s+", " ", cleaned).strip(" ,，。.")

    if not cleaned:
        raise ContractElicitationError("Could not extract disease name from input.")

    return cleaned, locale


def _slugify(disease: str, geography: str) -> str:
    raw = f"{disease}-{geography}".lower()
    raw = re.sub(r"[一-鿿]+", lambda m: m.group(0), raw)  # keep CJK
    raw = re.sub(r"[+/\\\\]", "-", raw)
    raw = re.sub(r"[\s_]+", "-", raw)
    raw = re.sub(r"[^\w一-鿿\-]", "", raw)
    raw = re.sub(r"-+", "-", raw).strip("-")
    return raw or "untitled"


def _coerce(value: Any, q_type: str) -> Any:
    if q_type == "date":
        if not re.match(r"^\d{4}-\d{2}-\d{2}$", str(value)):
            raise ContractElicitationError(f"Invalid date format: {value!r}")
        return str(value)
    if q_type == "bool":
        if isinstance(value, bool):
            return value
        s = str(value).strip().lower()
        if s in ("true", "yes", "y", "是"):
            return True
        if s in ("false", "no", "n", "否"):
            return False
        raise ContractElicitationError(f"Invalid bool: {value!r}")
    if q_type.startswith("enum:"):
        allowed = q_type.removeprefix("enum:").split(",")
        if str(value) not in allowed:
            raise ContractElicitationError(f"Value {value!r} not in {allowed}")
        return str(value)
    return str(value)


def elicit_contract(
    user_one_liner: str,
    project_root: Path,
    ask_user: Callable[[str, str, str], Any],
) -> Path:
    """Run Phase 1: parse one-liner, ask 4-6 questions via ask_user, write contract.json.

    `ask_user(field, question_text, locale) -> answer`.
    Returns path to written contract.json.
    """
    disease, locale = parse_disease_and_locale(user_one_liner)

    # ask remaining fields
    answers: dict[str, Any] = {}
    for q in DEFAULT_QUESTIONS:
        raw = ask_user(q["field"], q["question"], locale)
        answers[q["field"]] = _coerce(raw, q["type"])

    contract = {
        "disease": disease,
        "locale": locale,
        "evidence_window": {
            "start": answers["evidence_window_start"],
            "end": answers["evidence_window_end"],
        },
        "geography": answers["geography"],
        "include_intl_comparison": answers["include_intl_comparison"],
        "report_depth": answers["report_depth"],
        "user_role": answers["user_role"],
        "version": "1.0",
        "elicited_at": datetime.now(timezone.utc).isoformat(),
    }

    slug = _slugify(disease, answers["geography"])
    cache_dir = project_root / ".cache" / slug
    cache_dir.mkdir(parents=True, exist_ok=True)
    contract_path = cache_dir / "contract.json"
    contract_path.write_text(
        json.dumps(contract, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return contract_path


import jsonschema


def _schema_path() -> Path:
    """Locate schemas/contract.schema.json relative to skill snapshot."""
    here = Path(__file__).resolve()
    repo_root = here.parents[3]
    return repo_root / "schemas" / "contract.schema.json"


def assert_contract_complete(contract_path: Path) -> None:
    """Hard precondition for phases 2-5. Raises ContractElicitationError if missing or invalid."""
    if not contract_path.exists():
        raise ContractElicitationError(
            f"Contract not found: {contract_path}. "
            f"Run contract-elicitor (phase 1) first."
        )
    try:
        payload = json.loads(contract_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ContractElicitationError(f"Contract not valid JSON: {exc}") from exc

    schema = json.loads(_schema_path().read_text(encoding="utf-8"))
    try:
        jsonschema.validate(payload, schema)
    except jsonschema.ValidationError as exc:
        raise ContractElicitationError(
            f"Contract schema violation: {exc.message} "
            f"(at path: {list(exc.absolute_path)})"
        ) from exc
