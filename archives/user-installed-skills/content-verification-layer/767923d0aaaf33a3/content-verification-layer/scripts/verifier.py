"""Phase 4 Turn 2 · content-verification-layer (A6' upgrade): Cite-or-Block strict audit.

Architect §4.2: anchor existence reverse-lookup against sources_dir is REQUIRED
to prevent LLM from fabricating PMIDs that pass naive verification.

R2 Phase-2-Quality-Fix 升级 (2026-04-26):
- _anchor_supports_claim: 双层语义检查 (Tier 1 substring + Tier 2 LLM)
- decisive token (代号药/NCT/PMID/汉字药名) 1 个不命中即 fail (HER2 SHR-A1811/RC48 错锅必抓)
- Tier 2 LLM 必须返回 supporting quote (anti-hallucinate guard)
- budget cap 耗尽 default fail (谨慎策略)

SF-2 Phase-2-Quality-Fix multi-anchor (2026-04-26):
- _anchor_supports_claim 接受 single dict OR list[dict]
- 扫所有 resolved sources 的 union text, decisive token 任一源命中即过
- verify_section 改 claim 为单位收集 ±anchors, multi-anchor 自然支持跨 trial /
  paper claim (取代 ALK pilot augment workaround)
"""
from __future__ import annotations
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Literal, Optional, TypedDict, Union


_ANCHOR_PATTERN = re.compile(
    r"\[(guideline|pmid|nct|aact|europepmc|bioc|pubtator|evidence|nmpa-page):([^:\]]+)(?::([^\]]+))?\]"
)


class AnchorRef:
    __slots__ = ("source_type", "source_id", "locator", "raw")

    def __init__(self, source_type: str, source_id: str, locator: str, raw: str) -> None:
        self.source_type = source_type
        self.source_id = source_id
        self.locator = locator
        self.raw = raw


class Violation(TypedDict):
    severity: Literal["critical", "warning"]
    claim: str
    anchor: str
    reason: str
    suggestion: str


class Verdict(TypedDict):
    verdict: Literal["ok", "blocked"]
    violations: list[Violation]
    verified_count: int


class AnchorAudit(TypedDict):
    total_claims: int
    total_anchors: int
    verified_count: int
    anchors_without_locator: list[str]
    violations_by_reason: dict[str, int]


# Heuristics for "fact claim" sentences (drugs/treatments/stats/recommendations)
_FACT_PATTERNS = (
    re.compile(r"(?:PFS|OS|HR|RR)\s*(?:is|为|约|=|approximately)?\s*[\d.]+"),
    re.compile(r"\b(?:1L|2L|3L|first[- ]?line|second[- ]?line|third[- ]?line|一线|二线|三线)\b"),
    re.compile(r"(?:Grade|grade)\s*[A-D]"),
    re.compile(r"(?:推荐等级|recommendation grade)\s*[A-D]"),
    re.compile(r"\d{1,3}(?:\.\d+)?\s*(?:%|percent|cases?|patients?|例)"),
    re.compile(r"(?:RMB|CNY|人民币|¥)[^\d\n]{0,30}\d+(?:,\d{3})*(?:\.\d+)?", re.I),
    # any -tinib / -mab / -nib / -tide / -glutide drug suffixes
    re.compile(r"\w+(?:替尼|单抗|阿克|tinib|mab|glutide|肽)\b"),
)
_NUMERIC_FACT_RE = re.compile(
    r"(?:"
    r"(?:RMB|CNY|人民币|¥)[^\d\n]{0,30}\d+(?:,\d{3})*(?:\.\d+)?"
    r"|"
    r"\d+(?:,\d{3})*(?:\.\d+)?\s*(?:%|‰|万|亿|例|人|人次|元|亿元|万元|RMB|CNY|人民币|¥|年|月|天|小时|/1000|per\s*1000(?:\s*patients?)?|patients?|cases?)"
    r")",
    re.I,
)
_NUMBER_VALUE_RE = re.compile(r"\d+(?:,\d{3})*(?:\.\d+)?")
_DEFERRED_PROCESS_TERMS = (
    "待 worker",
    "待Worker",
    "后续量化模型",
    "再补足量化模型",
    "后续补足",
)
_MIN_MERMAID_CHARS = 70
_MIN_MERMAID_EDGES = 3
_MAX_REPEATED_SENTENCE_COUNT = 8
_MAX_FORMULA_ANCHOR_SHARE = 0.30
_MIN_FORMULA_ANCHORS_FOR_DOMINANCE = 4
_MIN_TOTAL_ANCHORS_FOR_FORMULA_DOMINANCE = 8
_MAX_EVIDENCE_MATRIX_MENTIONS = 7
_MAX_NUMBERED_TEMPLATE_SCENARIOS = 9
_MERMAID_BLOCK_RE = re.compile(
    r"<div\b(?=[^>]*\bclass\s*=\s*(['\"])[^'\"]*\bmermaid\b[^'\"]*\1)[^>]*>(.*?)</div>",
    re.I | re.S,
)
_NUMBERED_TEMPLATE_SCENARIO_RE = re.compile(r"(?:场景\s*\d+|scenario\s*\d+)\s*[：:]", re.I)


def _split_into_claims(text: str) -> list[tuple[int, str]]:
    """Split paragraph text into sentence-like fragments with byte offsets."""
    out: list[tuple[int, str]] = []
    pos = 0
    for sentence in re.split(r"(?<=[。！？])\s*|(?<=[.!?])\s+|\n+", text):
        if sentence.strip():
            out.append((pos, sentence.strip()))
        pos += len(sentence) + 1
    return out


def _strip_html(html: str) -> str:
    html = re.sub(r"<(script|style|noscript)\b[^>]*>.*?</\1>", " ", html, flags=re.I | re.S)
    html = re.sub(r"<br\s*/?>", "\n", html, flags=re.I)
    html = re.sub(r"</(?:td|th)>", " ", html, flags=re.I)
    html = re.sub(
        r"</(?:p|tr|li|h[1-6]|section|article|div|table|thead|tbody|figure|figcaption|sub-page|main)>",
        "。\n",
        html,
        flags=re.I,
    )
    return re.sub(r"<[^>]+>", " ", html)


def _normalize_numeric_text(text: str) -> str:
    return re.sub(r"[\s,，]", "", text).lower()


def _first_number_text(text: str) -> str:
    match = _NUMBER_VALUE_RE.search(text)
    if not match:
        return ""
    return re.sub(r"[,，]", "", match.group(0)).lower()


def _numeric_equivalence_keys(text: str, *, source_side: bool = False) -> set[str]:
    """Return conservative equivalence keys for common unit translations.

    Chinese reports often cite English/JSON sources: "88例" may come from a
    ClinicalTrials.gov enrollment count of 88, and "42.6/1000" may come from
    "42.6 per 1000 patients". These are the same numeric claim, while derived
    large-unit conversions such as 3710398 -> 371.0398万 must still be backed by
    a formula/model file.
    """
    compact = _normalize_numeric_text(text)
    number = _first_number_text(text)
    keys: set[str] = {compact} if compact else set()
    if not number:
        return keys
    lower = compact
    if "/1000" in lower or "per1000" in lower:
        keys.add(f"rate1000:{number}")
    if re.search(r"(?:例|patients?|cases?|inpatients?|outpatients?)", lower, re.I):
        keys.add(f"count:{number}")
    if re.search(r"(?:小时|hours?)", lower, re.I):
        keys.add(f"hours:{number}")
    if "%" in lower:
        keys.add(f"percent:{number}")
    if "‰" in lower:
        keys.add(f"permille:{number}")
    if re.search(r"(?:rmb|cny|人民币|¥|元|亿元|万元)", lower, re.I):
        keys.add(f"money:{number}")
    if source_side:
        # JSON registries and source tables often store enrollment/sample counts
        # as bare numeric values. This key only helps claims whose own unit has
        # already been normalized to a compatible count/rate/hour key.
        keys.add(f"number:{number}")
        keys.add(f"count:{number}")
    return keys


def _source_numeric_equivalence_keys(text: str) -> set[str]:
    keys: set[str] = set()
    for match in _NUMERIC_FACT_RE.finditer(text):
        keys.update(_numeric_equivalence_keys(match.group(0), source_side=True))
    for match in _NUMBER_VALUE_RE.finditer(text):
        keys.update(_numeric_equivalence_keys(match.group(0), source_side=True))
    return keys


def _numeric_token_supported_by_text(token: str, source_text: str) -> bool:
    if token in _normalize_numeric_text(source_text):
        return True
    return bool(_numeric_equivalence_keys(token) & _source_numeric_equivalence_keys(source_text))


def _numeric_tokens_missing_from_text(claim_text: str, source_text: str) -> list[str]:
    missing: list[str] = []
    for token in _numeric_fact_tokens(claim_text):
        if not _numeric_token_supported_by_text(token, source_text):
            missing.append(token)
    return missing


def _numeric_fact_tokens(text: str) -> list[str]:
    return list(dict.fromkeys(_normalize_numeric_text(m.group(0)) for m in _NUMERIC_FACT_RE.finditer(text)))


def _numeric_fact_texts(text: str) -> list[str]:
    out: list[str] = []
    for match in _NUMERIC_FACT_RE.finditer(text):
        raw = match.group(0).strip()
        compact = re.sub(r"[\s,，]", "", raw)
        for candidate in (raw, compact):
            if candidate and candidate not in out:
                out.append(candidate)
    return out


def _parse_anchor_match(match: re.Match[str]) -> AnchorRef:
    return AnchorRef(
        source_type=match.group(1),
        source_id=match.group(2).strip(),
        locator=(match.group(3) or "").strip(),
        raw=match.group(0),
    )


def _parse_anchor(anchor: str) -> AnchorRef | None:
    match = _ANCHOR_PATTERN.fullmatch(anchor.strip())
    if match is None:
        return None
    return _parse_anchor_match(match)


def _anchor_has_locator(anchor: str) -> bool:
    parsed = _parse_anchor(anchor)
    return bool(parsed and parsed.locator)


def _anchors_without_locator(html: str) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for match in _ANCHOR_PATTERN.finditer(html):
        parsed = _parse_anchor_match(match)
        if parsed.locator or parsed.raw in seen:
            continue
        seen.add(parsed.raw)
        out.append(parsed.raw)
    return out


def _count_fact_claims(html: str) -> int:
    text = _strip_html(html)
    total = 0
    for _offset, sentence in _split_into_claims(text):
        if any(p.search(sentence) for p in _FACT_PATTERNS):
            total += 1
    return total


def _count_anchor_claim_groups(html: str) -> int:
    text = _strip_html(html)
    total = 0
    for _offset, sentence in _split_into_claims(text):
        if _ANCHOR_PATTERN.search(sentence):
            total += 1
    return total


def _count_cited_table_cells(html: str) -> int:
    total = 0
    for match in re.finditer(r"<t[dh]\b[^>]*>(.*?)</t[dh]>", html, re.I | re.S):
        if _ANCHOR_PATTERN.search(match.group(1)):
            total += 1
    return total


def _count_verified_claim_units(html: str, sources_dir: Path) -> int:
    resolved_anchor_occurrences = 0
    for match in _ANCHOR_PATTERN.finditer(html):
        if _anchor_resolves(match.group(0), sources_dir):
            resolved_anchor_occurrences += 1

    resolved_claim_groups = 0
    text = _strip_html(html)
    for _offset, sentence in _split_into_claims(text):
        if any(_anchor_resolves(match.group(0), sources_dir) for match in _ANCHOR_PATTERN.finditer(sentence)):
            resolved_claim_groups += 1

    resolved_table_cells = 0
    for match in re.finditer(r"<t[dh]\b[^>]*>(.*?)</t[dh]>", html, re.I | re.S):
        cell_html = match.group(1)
        if any(_anchor_resolves(anchor_match.group(0), sources_dir) for anchor_match in _ANCHOR_PATTERN.finditer(cell_html)):
            resolved_table_cells += 1

    return max(resolved_anchor_occurrences, resolved_claim_groups, resolved_table_cells)


def _is_repetition_gate_exempt(sentence: str) -> bool:
    normalized = re.sub(r"\s+", " ", sentence).strip()
    without_anchors = _ANCHOR_PATTERN.sub("", normalized)
    without_punctuation = re.sub(r"[\s\]\[\"'{}()<>:;,.。！？!?|/\\-]+", "", without_anchors)
    if not without_punctuation:
        return True
    structural_headers = {
        "来源 主题 源内标题/摘要信号 进入报告的用途 。",
        "队列 边界 市场接口 LP 。",
        "模块 触发 动作 证据 。",
        "层级 定义 公式 结果 证据 。",
        "诊疗路径 / 决策树。",
        "Market 测算依据 / 市场切入。",
        "BD动作与材料口径。",
        "TOP3 LP / LP动作。",
        "节点 触发 动作 证据 。",
        "材料模块 使用对象 必须出现的证据 禁止误读 。",
    }
    if normalized in structural_headers:
        return True
    if re.match(r"^(?:flowchart|graph)\s+(?:TD|TB|LR|RL)\b", normalized, re.I):
        return True
    if normalized.startswith("classDef "):
        return True
    return False


def _normalize_template_sentence(sentence: str) -> str:
    normalized = _ANCHOR_PATTERN.sub("[citation]", sentence)
    normalized = re.sub(r"\b(scenario|block)\s*\d+\b", r"\1 #", normalized, flags=re.I)
    normalized = re.sub(r"场景\s*\d+", "场景#", normalized)
    return normalized


def _violations_by_reason(violations: list[Violation]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for violation in violations:
        reason = violation["reason"]
        counts[reason] = counts.get(reason, 0) + 1
    return counts


def _build_anchor_audit(
    html: str,
    violations: list[Violation],
    verified_count: int,
) -> AnchorAudit:
    total_anchors = len(list(_ANCHOR_PATTERN.finditer(html)))
    return AnchorAudit(
        total_claims=max(
            _count_fact_claims(html),
            _count_anchor_claim_groups(html),
            _count_cited_table_cells(html),
            total_anchors,
        ),
        total_anchors=total_anchors,
        verified_count=verified_count,
        anchors_without_locator=_anchors_without_locator(html),
        violations_by_reason=_violations_by_reason(violations),
    )


def _audit_layer_source_anchors(audit_layer: dict[str, Any] | None) -> list[str]:
    if not isinstance(audit_layer, dict):
        return []
    anchors: list[str] = []

    def add(value: Any) -> None:
        if isinstance(value, str) and _ANCHOR_PATTERN.fullmatch(value.strip()):
            anchors.append(value.strip())
        elif isinstance(value, list):
            for item in value:
                add(item)

    for section_name in ("evidence_support_table", "reader_to_audit_mapping", "claims"):
        section = audit_layer.get(section_name)
        if not isinstance(section, list):
            continue
        for item in section:
            if not isinstance(item, dict):
                continue
            add(item.get("source_anchors"))
            add(item.get("anchors"))
            add(item.get("anchor"))
    return list(dict.fromkeys(anchors))


def _audit_layer_claim_rows(audit_layer: dict[str, Any] | None) -> list[dict[str, Any]]:
    if not isinstance(audit_layer, dict):
        return []
    claims = audit_layer.get("claims")
    if isinstance(claims, list) and claims:
        return [claim for claim in claims if isinstance(claim, dict)]

    rows: list[dict[str, Any]] = []
    for item in audit_layer.get("reader_to_audit_mapping", []):
        if not isinstance(item, dict):
            continue
        anchors = item.get("source_anchors")
        if not isinstance(anchors, list):
            continue
        rows.append(
            {
                "claim_id": item.get("conclusion_id") or item.get("badge_id") or "",
                "claim_text": item.get("market_judgment")
                or item.get("reader_title")
                or item.get("support_summary")
                or "reader conclusion",
                "source_anchors": anchors,
                "classification": "general",
            }
        )
    return rows


def _anchor_dict_from_raw(anchor: str) -> dict[str, str] | None:
    parsed = _parse_anchor(anchor)
    if parsed is None:
        return None
    return {
        "type": parsed.source_type,
        "id": parsed.source_id,
        "locator": parsed.locator,
    }


def _verify_audit_layer(
    audit_layer: dict[str, Any] | None,
    sources_dir: Path,
    *,
    ask_llm_semantic: Optional[Callable] = None,
    budget_state: Optional[dict] = None,
) -> tuple[list[Violation], AnchorAudit]:
    claims = _audit_layer_claim_rows(audit_layer)
    source_anchors = _audit_layer_source_anchors(audit_layer)
    violations: list[Violation] = []
    verified_count = 0
    anchors_without_locator = [
        anchor for anchor in source_anchors if not _anchor_has_locator(anchor)
    ]
    seen_anchors: set[str] = set()

    if not source_anchors:
        violations.append(Violation(
            severity="critical",
            claim="reader audit layer",
            anchor="",
            reason="reader audit layer has no source anchors",
            suggestion="map each reader evidence badge to source anchors in audit_layer",
        ))

    for anchor in source_anchors:
        if anchor in seen_anchors:
            continue
        seen_anchors.add(anchor)
        if _anchor_resolves(anchor, sources_dir):
            verified_count += 1
        else:
            violations.append(Violation(
                severity="critical",
                claim="reader audit layer",
                anchor=anchor,
                reason="audit layer anchor source not found in sources/",
                suggestion="use a resolvable current-run source anchor or remove the mapped claim",
            ))

    for anchor in anchors_without_locator:
        violations.append(Violation(
            severity="critical",
            claim="reader audit layer",
            anchor=anchor,
            reason="audit layer anchor missing locator context",
            suggestion="use locator-level anchors such as [guideline:ID:line:42]",
        ))

    for claim in claims:
        claim_text = str(claim.get("claim_text") or claim.get("text") or "")
        raw_anchors = [
            str(anchor)
            for anchor in claim.get("source_anchors", claim.get("anchors", []))
            if isinstance(anchor, str)
        ]
        anchor_dicts = [
            anchor_dict for anchor in raw_anchors
            if (anchor_dict := _anchor_dict_from_raw(anchor)) is not None
            and _anchor_resolves(anchor, sources_dir)
        ]
        if not raw_anchors:
            violations.append(Violation(
                severity="critical",
                claim=claim_text[:200],
                anchor="",
                reason="audit layer claim has no source anchors",
                suggestion="add source_anchors to the audit-layer claim",
            ))
            continue
        violation = _numeric_support_violation(
            claim_text,
            anchor_dicts,
            raw_anchors,
            sources_dir,
        )
        if violation is not None:
            violations.append(violation)
        if ask_llm_semantic is not None or budget_state is not None:
            supports, reason = _anchor_supports_claim(
                claim=claim_text,
                anchor=anchor_dicts,
                sources_dir=sources_dir,
                ask_llm_semantic=ask_llm_semantic,
                budget_state=budget_state,
            )
            if not supports:
                violations.append(Violation(
                    severity="critical",
                    claim=claim_text[:200],
                    anchor=" ".join(raw_anchors),
                    reason=f"audit layer semantic check failed: {reason}",
                    suggestion="核对 reader claim 与 audit anchor 指向的源是否一致",
                ))

    claims_by_id = {
        str(claim.get("claim_id")): claim
        for claim in claims
        if claim.get("claim_id") is not None
    }
    support_table = audit_layer.get("evidence_support_table") if isinstance(audit_layer, dict) else None
    if isinstance(support_table, list):
        for row in support_table:
            if not isinstance(row, dict):
                continue
            claim_ids = [
                str(claim_id)
                for claim_id in row.get("claim_ids", [])
                if claim_id is not None
            ]
            raw_row_anchors = [
                str(anchor)
                for anchor in row.get("source_anchors", row.get("anchors", []))
                if isinstance(anchor, str)
            ]
            if not claim_ids or not raw_row_anchors:
                continue
            for claim_id in claim_ids:
                claim = claims_by_id.get(claim_id)
                if claim is None:
                    violations.append(Violation(
                        severity="critical",
                        claim=claim_id,
                        anchor=" ".join(raw_row_anchors),
                        reason="evidence_support_table references an unknown claim_id",
                        suggestion="remove the row or add the referenced claim to audit_layer.claims",
                    ))
                    continue
                claim_anchor_set = {
                    str(anchor)
                    for anchor in claim.get("source_anchors", claim.get("anchors", []))
                    if isinstance(anchor, str)
                }
                if set(raw_row_anchors) <= claim_anchor_set:
                    continue
                violations.append(Violation(
                    severity="critical",
                    claim=str(claim.get("claim_text") or claim.get("text") or "")[:200],
                    anchor=" ".join(raw_row_anchors),
                    reason=(
                        "evidence_support_table maps claim_id to anchors not listed on "
                        "audit_layer.claims; support rows must not rotate unrelated sources"
                    ),
                    suggestion=(
                        "make the support-row anchors match the referenced claim source_anchors "
                        "or create a separate claim with its own source support"
                    ),
                ))

    anchor_audit = AnchorAudit(
        total_claims=max(len(claims), len(source_anchors)),
        total_anchors=len(source_anchors),
        verified_count=verified_count,
        anchors_without_locator=anchors_without_locator,
        violations_by_reason=_violations_by_reason(violations),
    )
    return violations, anchor_audit


def _reader_badge_violations(html: str, audit_layer: dict[str, Any] | None) -> list[Violation]:
    if not isinstance(audit_layer, dict):
        return []
    badge_ids = {
        str(item.get("badge_id"))
        for item in audit_layer.get("evidence_support_table", [])
        if isinstance(item, dict) and item.get("badge_id")
    }
    visible_badges = set(
        re.findall(
            r'class=["\'][^"\']*evidence-badge[^"\']*["\'][^>]*>\s*([A-Za-z]\d+)',
            html,
            re.I,
        )
    )
    missing = sorted(badge for badge in visible_badges if badge not in badge_ids)
    if not missing:
        return []
    return [
        Violation(
            severity="critical",
            claim="reader evidence badges",
            anchor="",
            reason=f"reader evidence badge missing audit mapping: {missing}",
            suggestion="add every visible evidence badge to audit_layer.evidence_support_table",
        )
    ]


def _report_substance_violations(html: str) -> list[Violation]:
    """Block report-shaped filler that can pass Cite-or-Block syntax.

    Citation correctness is necessary but not sufficient. A production report
    must not use source inventory rows, process notes, or toy Mermaid diagrams
    as substitutes for market-analysis content.
    """
    text = _strip_html(html)
    violations: list[Violation] = []

    source_saved_count = text.count("已保存")
    appendix_filler_count = text.count("附录证据说明")
    source_index_count = text.count("来源索引")
    if source_saved_count >= 30 or appendix_filler_count >= 20 or source_index_count >= 20:
        violations.append(Violation(
            severity="critical",
            claim="report body",
            anchor="",
            reason="report substance gate failed: source-index/process filler dominates visible body",
            suggestion="move source inventory to concise appendix/reference index and write actual market-analysis content",
        ))

    deferred_hits = [term for term in _DEFERRED_PROCESS_TERMS if term in text]
    if deferred_hits:
        violations.append(Violation(
            severity="critical",
            claim="report body",
            anchor="",
            reason=f"report substance gate failed: deferred-model/process language {deferred_hits}",
            suggestion="final report must contain the market model or explicitly block generation before bundle",
        ))

    evidence_matrix_count = text.count("证据消化矩阵")
    if evidence_matrix_count > _MAX_EVIDENCE_MATRIX_MENTIONS:
        violations.append(Violation(
            severity="critical",
            claim="report body",
            anchor="",
            reason=(
                "report substance gate failed: evidence-digest matrix dominates "
                f"visible body (count={evidence_matrix_count})"
            ),
            suggestion=(
                "move digest inventory to appendix and write V25-level narrative "
                "synthesis in the main body"
            ),
        ))

    anchors = [_parse_anchor_match(m) for m in _ANCHOR_PATTERN.finditer(html)]
    formula_anchors = [
        anchor for anchor in anchors
        if (
            anchor.source_type == "evidence"
            and "formula" in f"{anchor.source_id}:{anchor.locator}".lower()
        )
        or "formula-dag-evidence" in anchor.raw.lower()
    ]
    if (
        len(anchors) >= _MIN_TOTAL_ANCHORS_FOR_FORMULA_DOMINANCE
        and len(formula_anchors) >= _MIN_FORMULA_ANCHORS_FOR_DOMINANCE
        and (len(formula_anchors) / len(anchors)) > _MAX_FORMULA_ANCHOR_SHARE
    ):
        violations.append(Violation(
            severity="critical",
            claim="report body",
            anchor=" ".join(a.raw for a in formula_anchors[:5]),
            reason=(
                "report substance gate failed: formula/model evidence anchors dominate "
                f"body citations ({len(formula_anchors)}/{len(anchors)})"
            ),
            suggestion=(
                "use saved formula/model evidence only for derived numbers; anchor "
                "clinical pathway, epidemiology, trials, and competitive claims to "
                "current-run source files"
            ),
        ))

    sentence_counts: dict[str, int] = {}
    for _offset, sentence in _split_into_claims(text):
        normalized = re.sub(r"\s+", " ", sentence).strip()
        if len(normalized) < 10:
            continue
        if _is_repetition_gate_exempt(normalized):
            continue
        normalized = _normalize_template_sentence(normalized)
        sentence_counts[normalized] = sentence_counts.get(normalized, 0) + 1
    repeated = [
        {"text": sentence[:160], "count": count}
        for sentence, count in sentence_counts.items()
        if count >= _MAX_REPEATED_SENTENCE_COUNT
    ]
    if repeated:
        violations.append(Violation(
            severity="critical",
            claim="report body",
            anchor="",
            reason=f"report substance gate failed: template sentence repetition {repeated[:5]}",
            suggestion="replace repeated row-purpose/template sentences with source-specific synthesis",
        ))

    numbered_scenarios = _NUMBERED_TEMPLATE_SCENARIO_RE.findall(text)
    if len(numbered_scenarios) > _MAX_NUMBERED_TEMPLATE_SCENARIOS:
        violations.append(Violation(
            severity="critical",
            claim="report body",
            anchor="",
            reason=(
                "report substance gate failed: numbered template scenarios dominate "
                f"visible body (count={len(numbered_scenarios)})"
            ),
            suggestion=(
                "replace bulk 场景1/场景2/... padding with V25-level cohort synthesis, "
                "distinct pathway logic, and quantified cross-points"
            ),
        ))

    for i, match in enumerate(_MERMAID_BLOCK_RE.finditer(html)):
        block = match.group(2)
        diagram = re.sub(r"\s+", " ", block).strip()
        edge_count = len(re.findall(r"(?:-->|---|==>|-.->)", diagram))
        if len(diagram) < _MIN_MERMAID_CHARS or edge_count < _MIN_MERMAID_EDGES:
            violations.append(Violation(
                severity="critical",
                claim=f"mermaid block {i}",
                anchor="",
                reason=(
                    "report substance gate failed: shallow Mermaid "
                    f"(chars={len(diagram)}, edges={edge_count})"
                ),
                suggestion="replace toy diagram with a real decision tree/pathway carrying clinical and LP logic",
            ))

    return violations


def _anchor_resolves(anchor: str, sources_dir: Path) -> bool:
    parsed = _parse_anchor(anchor)
    if parsed is None:
        return False
    src_type, source_id = parsed.source_type, parsed.source_id
    if src_type == "guideline":
        return any(
            (sources_dir / "guidelines" / f"{source_id}{suffix}").exists()
            for suffix in (".txt", ".md", ".html", ".pdf")
        )
    if src_type == "pmid":
        return (sources_dir / "pubmed" / f"{source_id}.json").exists()
    if src_type == "nct":
        return any(
            (sources_dir / dirname / f"{source_id}.json").exists()
            for dirname in ("trials", "clinical_trials")
        )
    if src_type in {"aact", "europepmc", "bioc", "pubtator"}:
        return (sources_dir / src_type / f"{source_id}.json").exists()
    if src_type == "nmpa-page":
        return any(
            (sources_dir / "nmpa" / f"{source_id}{suffix}").exists()
            for suffix in (".html", ".htm", ".txt", ".md", ".json")
        )
    if src_type == "evidence":
        rel = source_id.replace("\\", "/").lstrip("/")
        local_evidence = sources_dir / "evidence" / rel
        local_candidates = [local_evidence]
        if not Path(rel).suffix:
            local_candidates.extend(local_evidence.with_suffix(suffix) for suffix in (".txt", ".json", ".md"))
        return any(
            candidate.exists()
            for candidate in (
                *local_candidates,
                sources_dir / rel,
                sources_dir.parent / "evidence" / rel,
                sources_dir.parent.parent / rel,
            )
        )
    return False


# ---------------------------------------------------------------------------
# R2 Phase-2-Quality-Fix · _anchor_supports_claim: Tier 1 + Tier 2 语义检查
# ---------------------------------------------------------------------------
# 现场命名规范: guidelines/<id>.txt · pubmed/<pmid>.json · trials/<nct>.json
# anchor 入参 dict 形式: {"type": "nct", "id": "NCT04400695"}


def _resolve_anchor_to_text(anchor: dict, sources_dir: Path) -> Optional[str]:
    """根据 dict anchor type 找源文件 + 返回文本内容. 与现场命名规范一致."""
    a_type = anchor.get("type", "")
    a_id = anchor.get("id", "")
    if not a_id:
        return None
    if a_type == "guideline":
        path = sources_dir / "guidelines" / f"{a_id}.txt"
    elif a_type == "pmid":
        path = sources_dir / "pubmed" / f"{a_id}.json"
    elif a_type == "nct":
        path = sources_dir / "trials" / f"{a_id}.json"
        if not path.exists():
            path = sources_dir / "clinical_trials" / f"{a_id}.json"
    elif a_type in {"aact", "europepmc", "bioc", "pubtator"}:
        path = sources_dir / a_type / f"{a_id}.json"
    elif a_type == "nmpa-page":
        base = sources_dir / "nmpa" / a_id
        path = next(
            (
                candidate
                for candidate in (
                    base.with_suffix(".html"),
                    base.with_suffix(".htm"),
                    base.with_suffix(".txt"),
                    base.with_suffix(".md"),
                    base.with_suffix(".json"),
                )
                if candidate.exists()
            ),
            base.with_suffix(".html"),
        )
    elif a_type == "evidence":
        rel = str(a_id).replace("\\", "/").lstrip("/")
        local_evidence = sources_dir / "evidence" / rel
        candidates = [
            local_evidence,
            sources_dir / rel,
            sources_dir.parent / "evidence" / rel,
            sources_dir.parent.parent / rel,
        ]
        if not Path(rel).suffix:
            candidates[1:1] = [
                local_evidence.with_suffix(suffix)
                for suffix in (".txt", ".json", ".md")
            ]
        path = next((candidate for candidate in candidates if candidate.exists()), candidates[0])
    else:
        return None
    if not path.exists():
        return None
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None


def _append_audit_log(log_path: Path, claim: str, anchor: dict, verdict: dict) -> None:
    """每次 Tier 2 调用 append 一行 jsonl 给人 spot-check.

    含 ts / claim / anchor / verdict (含 supporting_quote / reasoning).
    audit log 让用户区分 'tier1 decisive miss' vs 'tier1 partial + budget exhausted'.
    """
    log_path.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "claim": claim,
        "anchor": anchor,
        "verdict": verdict,
    }
    with log_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def _semantic_excerpt_for_claim(
    claim: str,
    resolved: list[tuple[dict, str]],
    *,
    max_chars_per_source: int = 2000,
) -> str:
    """Build a semantic-audit excerpt around claim evidence, not file headers.

    Long guideline/html captures often start with navigation/login boilerplate.
    Tier 0 already checks numeric tokens against the full source; Tier 2 must
    receive the nearby evidence window or it will falsely fail valid anchors.
    """
    number_candidates = _numeric_fact_texts(claim)
    claim_words = [
        word.lower()
        for word in re.findall(r"[A-Za-z0-9一-鿿]{2,}", _ANCHOR_PATTERN.sub(" ", claim))
        if not re.fullmatch(r"\d+", word)
    ]
    chunks: list[str] = []
    for anchor, text in resolved:
        source_chunks: list[str] = []
        lower = text.lower()
        for candidate in number_candidates:
            for needle in {candidate, re.sub(r"[\s,，]", "", candidate)}:
                if not needle:
                    continue
                idx = lower.find(needle.lower())
                if idx < 0:
                    continue
                start = max(0, idx - 700)
                end = min(len(text), idx + 900)
                source_chunks.append(text[start:end])
        if not source_chunks:
            scored: list[tuple[int, str]] = []
            for line in re.split(r"(?<=[。.!?])\s*|\n+", text):
                line = line.strip()
                if not line:
                    continue
                normalized_line = _normalize_numeric_text(line)
                line_lower = line.lower()
                score = 0
                score += 5 * sum(
                    1 for token in _numeric_fact_tokens(claim)
                    if token and (
                        token in normalized_line
                        or _numeric_token_supported_by_text(token, line)
                    )
                )
                score += sum(1 for word in claim_words if word in line_lower)
                if score:
                    scored.append((score, line))
            scored.sort(key=lambda item: item[0], reverse=True)
            source_chunks = [line for _score, line in scored[:4]]
        if not source_chunks:
            source_chunks = [text[:max_chars_per_source]]
        merged = "\n".join(dict.fromkeys(source_chunks))
        chunks.append(
            f"[{anchor.get('type')}:{anchor.get('id')}:{anchor.get('locator','')}]\n"
            + merged[:max_chars_per_source]
        )
    return "\n\n---\n\n".join(chunks)


def _anchors_list(anchor_or_anchors: Union[dict, list, None]) -> list[dict]:
    """SF-2 backward-compat helper: 把 single dict 或 list[dict] 归一化成 list[dict].

    None / 非法形态返回 []. 用于 _anchor_supports_claim 接受两种入参.
    """
    if anchor_or_anchors is None:
        return []
    if isinstance(anchor_or_anchors, dict):
        return [anchor_or_anchors] if anchor_or_anchors.get("id") else []
    if isinstance(anchor_or_anchors, list):
        return [a for a in anchor_or_anchors if isinstance(a, dict) and a.get("id")]
    return []


def _anchor_supports_claim(
    claim: str,
    anchor: Union[dict, list],
    sources_dir: Path,
    ask_llm_semantic: Optional[Callable] = None,
    budget_state: Optional[dict] = None,
) -> tuple[bool, str]:
    """SF-2 multi-anchor 双层语义检查: Tier 1 substring + Tier 2 LLM 反查.

    Tier 1: decisive token (代号药/NCT/PMID/汉字药名) 在所有 anchored sources 的
        union text 中任一源命中即过; non-decisive ≥ 70% hit rate (按 union 计算)
    Tier 2: LLM 必须返回 supporting_quote (anti-hallucinate guard), excerpt 由
        多源拼接 (每源 ≤2000 char)
    Budget cap 耗尽: default fail (谨慎策略避免 false-positive 通过)

    Args:
        claim: 自然语言 claim 文本
        anchor: dict {"type": ..., "id": ...} OR list[dict] (SF-2: 支持多锚)
        sources_dir: .cache/<slug>/sources 目录
        ask_llm_semantic: callback (claim, source_excerpt, require_supporting_quote) -> dict
        budget_state: dict {"calls_remaining": int, "audit_log_path": Path}

    Returns:
        (supports: bool, reason: str)
    """
    anchors = _anchors_list(anchor)
    if not anchors:
        return False, "no anchors provided (empty list / unresolved input)"

    resolved: list[tuple[dict, str]] = []
    for a in anchors:
        text = _resolve_anchor_to_text(a, sources_dir)
        if text is not None:
            resolved.append((a, text))

    if not resolved:
        return False, "anchor unresolved (source file not found)"

    union_text = "\n\n---\n\n".join(t for _, t in resolved)
    union_lower = union_text.lower()
    n_src = len(resolved)
    src_tag = "" if n_src == 1 else f" across {n_src} sources"

    numeric_tokens = _numeric_fact_tokens(claim)
    numeric_miss = _numeric_tokens_missing_from_text(claim, union_text)
    if numeric_miss:
        return False, (
            f"tier0: numeric token miss{src_tag}: {numeric_miss[:5]}; "
            "derived values must be saved in and cited from a model/evidence file"
        )

    # === Tier 1: decisive token (any-source-hit) + non-decisive ≥ 70% (union) ===
    local_scripts = Path(__file__).resolve().parent
    if str(local_scripts) not in sys.path:
        sys.path.insert(0, str(local_scripts))
    from _token_classifier import classify_tokens

    decisive, non_decisive = classify_tokens(claim)
    decisive_miss = [t for t in decisive if t.lower() not in union_lower]
    if decisive_miss:
        # SF-5 Tier 1.5 bilingual fallback (2026-04-27):
        # 中文 decisive token 在英文 PubMed source 必 miss (en drug name ≠ cn drug
        # name). 自动扫 sources_dir/guidelines/ 全部 (.txt/.md/.json) 找中文 token,
        # 命中即视为 recover. 非中文 decisive_miss 不参与 fallback.
        chinese_miss = [t for t in decisive_miss if re.search(r"[一-鿿]", t)]
        if chinese_miss:
            guidelines_dir = sources_dir / "guidelines"
            if guidelines_dir.exists():
                recovered_files: set[str] = set()
                recovered_tokens: set[str] = set()
                for gf in sorted(guidelines_dir.iterdir()):
                    if gf.suffix.lower() not in (".txt", ".md", ".json"):
                        continue
                    try:
                        gtext = gf.read_text(encoding="utf-8")
                    except (OSError, UnicodeDecodeError):
                        continue
                    for tok in chinese_miss:
                        if tok in gtext:
                            recovered_tokens.add(tok)
                            recovered_files.add(gf.name)
                still_miss = [t for t in decisive_miss if t not in recovered_tokens]
                if not still_miss:
                    files_str = ",".join(sorted(recovered_files))
                    return True, (
                        f"tier1.5: bilingual fallback hit guideline:{files_str}"
                    )
        return False, f"tier1: decisive token miss{src_tag}: {decisive_miss[:3]}"

    if not non_decisive:
        return True, f"tier1: only decisive tokens, all hit{src_tag}"

    nd_hits = [t for t in non_decisive if t.lower() in union_lower]
    hit_rate = len(nd_hits) / len(non_decisive)
    if hit_rate >= 0.7:
        return True, (
            f"tier1: decisive ✓ + non-decisive {len(nd_hits)}/{len(non_decisive)} "
            f"({hit_rate:.0%}){src_tag}"
        )

    # === Tier 2: LLM semantic + supporting quote 强制 (多源 excerpt 拼接) ===
    if ask_llm_semantic is None:
        return False, "tier1 partial + no LLM (cannot escalate)"
    if budget_state is not None and budget_state.get("calls_remaining", 0) <= 0:
        return False, "tier1 partial + LLM budget exhausted (default fail)"

    excerpt = _semantic_excerpt_for_claim(claim, resolved)
    verdict = ask_llm_semantic(
        claim=claim,
        source_excerpt=excerpt,
        require_supporting_quote=True,
    )
    if budget_state is not None:
        budget_state["calls_remaining"] = budget_state.get("calls_remaining", 0) - 1
        log_path = budget_state.get("audit_log_path")
        if log_path is not None:
            # backward compat: single anchor → 写 dict; multi → 写 list (audit log)
            log_anchor = anchors[0] if len(anchors) == 1 else anchors
            _append_audit_log(Path(log_path), claim, log_anchor, verdict)

    if not verdict.get("supports"):
        return False, f"tier2: {verdict.get('reasoning', 'no support')}"
    quote = verdict.get("supporting_quote") or ""
    if not quote.strip():
        return False, "tier2: LLM verdict but no supporting quote (anti-hallucinate guard)"

    return True, f"tier2: {quote[:80]}..."


def enforce_citations_in_text(html: str) -> list[Violation]:
    """Find fact-bearing claims that lack citation anchors. P0 守门."""
    text = _strip_html(html)
    violations: list[Violation] = []
    for offset, sentence in _split_into_claims(text):
        if not any(p.search(sentence) for p in _FACT_PATTERNS):
            continue
        if not _ANCHOR_PATTERN.search(sentence):
            violations.append(Violation(
                severity="critical",
                claim=sentence[:200],
                anchor="",
                reason="fact-bearing claim has no citation anchor",
                suggestion="add [guideline:.../pmid:.../nct:.../pubtator:...] anchor or remove the claim",
            ))
    return violations


def _channel_has_source_files(sources_dir: Path, channel: str) -> bool:
    channel_dirs = {
        "clinical_trials": ("clinical_trials", "trials"),
        "trials": ("clinical_trials", "trials"),
        "pubtator": ("pubtator",),
        "pubmed": ("pubmed",),
        "europepmc": ("europepmc",),
        "bioc": ("bioc",),
    }.get(channel, (channel,))
    for dirname in channel_dirs:
        path = sources_dir / dirname
        if not path.exists():
            continue
        if any(p.is_file() and p.suffix.lower() in {".json", ".txt", ".md", ".html"} for p in path.rglob("*")):
            return True
    return False


def _channel_used_by_anchors(html: str, channel: str) -> bool:
    used_types = {m.group(1) for m in _ANCHOR_PATTERN.finditer(html)}
    expected_anchor_types = {
        "clinical_trials": {"nct", "aact"},
        "trials": {"nct", "aact"},
        "pubtator": {"pubtator"},
        "pubmed": {"pmid"},
        "europepmc": {"europepmc"},
        "bioc": {"bioc"},
    }.get(channel, {channel})
    return bool(used_types & expected_anchor_types)


def _required_source_channel_violations(
    html: str,
    sources_dir: Path,
    required_source_channels: tuple[str, ...] | list[str] | None,
) -> list[Violation]:
    if not required_source_channels:
        return []
    violations: list[Violation] = []
    for channel in required_source_channels:
        if not _channel_has_source_files(sources_dir, channel):
            continue
        if _channel_used_by_anchors(html, channel):
            continue
        violations.append(Violation(
            severity="critical",
            claim="report body",
            anchor="",
            reason=(
                "required source channel not used in body anchors: "
                f"{channel}"
            ),
            suggestion=(
                "either use this current-run source channel in body analysis with "
                "resolvable anchors or exclude it before verification with a recorded reason"
            ),
        ))
    return violations


def _iter_claim_groups(
    section_html: str, sources_dir: Path
) -> "list[tuple[str, list[dict], list[str]]]":
    """SF-2 multi-anchor: 按 sentence 分组锚点, 返回 (claim_text, anchor_dicts, raw_anchors).

    每个 sentence 内的所有锚点共享同一 claim 上下文, 一次性调
    `_anchor_supports_claim(anchors=[...])`. 跨 trial / paper claim 的 decisive
    token 可在 union sources 任一源命中.

    raw_anchors 用于 violation.anchor 字段填充 (报错时显示原始锚点串).
    """
    plain = _strip_html(section_html)
    groups: list[tuple[str, list[dict], list[str]]] = []
    for _offset, sentence in _split_into_claims(plain):
        anchor_dicts: list[dict] = []
        raw: list[str] = []
        seen_ids: set[str] = set()
        for am in _ANCHOR_PATTERN.finditer(sentence):
            full = am.group(0)
            parsed = _parse_anchor_match(am)
            key = f"{parsed.source_type}:{parsed.source_id}:{parsed.locator}"
            if key in seen_ids:
                continue
            seen_ids.add(key)
            if not _anchor_resolves(full, sources_dir):
                # Phase 1 anchor-existence 已报, semantic 阶段 skip
                continue
            anchor_dicts.append({
                "type": parsed.source_type,
                "id": parsed.source_id,
                "locator": parsed.locator,
            })
            raw.append(full)
        if anchor_dicts:
            groups.append((sentence, anchor_dicts, raw))
    return groups


def _numeric_support_violation(
    claim_text: str,
    anchor_dicts: list[dict],
    raw_anchors: list[str],
    sources_dir: Path,
) -> Violation | None:
    numeric_tokens = _numeric_fact_tokens(claim_text)
    if not numeric_tokens:
        return None
    missing_locator = [anchor for anchor in raw_anchors if not _anchor_has_locator(anchor)]
    if missing_locator:
        return Violation(
            severity="critical",
            claim=claim_text[:200],
            anchor=" ".join(missing_locator),
            reason=(
                "numeric claim anchor missing locator context; strict verification "
                "requires source_id and locator"
            ),
            suggestion=(
                "cite the exact source location, for example "
                "[guideline:ID:line:42] or [evidence:file.md:line:42]"
            ),
        )
    resolved_texts = [
        text for anchor in anchor_dicts
        if (text := _resolve_anchor_to_text(anchor, sources_dir)) is not None
    ]
    missing = _numeric_tokens_missing_from_text(claim_text, "\n".join(resolved_texts))
    if not missing:
        return None
    return Violation(
        severity="critical",
        claim=claim_text[:200],
        anchor=" ".join(raw_anchors),
        reason=(
            f"numeric token miss: {missing[:5]}; derived values must be saved in "
            "and cited from a model/evidence file"
        ),
        suggestion=(
            "cite a source/model file that contains the exact number(s), formula, "
            "inputs, and units, or remove the numeric claim"
        ),
    )


def verify_section(
    section_html: str,
    sources_dir: Path,
    *,
    ask_llm_semantic: Optional[Callable] = None,
    budget_state: Optional[dict] = None,
) -> Verdict:
    """Verify one HTML section. Combines:
       - enforce_citations_in_text (no unanchored fact claims)
       - anchor existence reverse-lookup (no fabricated source_ids)
       - R2 + SF-2: semantic check via _anchor_supports_claim 按 claim 分组多锚
         (callbacks 提供时启用)
    """
    violations: list[Violation] = list(enforce_citations_in_text(section_html))

    # Phase 1: per-anchor existence reverse-lookup (unchanged)
    seen_anchors: set[str] = set()
    for m in _ANCHOR_PATTERN.finditer(section_html):
        anchor = m.group(0)
        if anchor in seen_anchors:
            continue
        seen_anchors.add(anchor)
        if not _anchor_resolves(anchor, sources_dir):
            violations.append(Violation(
                severity="critical",
                claim=section_html[max(0, m.start()-60):m.end()+60],
                anchor=anchor,
                reason="anchor source not found in sources/ (resolves to no file)",
                suggestion="ensure source was fetched in phase 3 OR remove the claim",
            ))

    for claim_text, anchor_dicts, raw_anchors in _iter_claim_groups(section_html, sources_dir):
        violation = _numeric_support_violation(
            claim_text,
            anchor_dicts,
            raw_anchors,
            sources_dir,
        )
        if violation is not None:
            violations.append(violation)

    # Phase 2: SF-2 multi-anchor semantic check (按 sentence 分组)
    if ask_llm_semantic is not None or budget_state is not None:
        for claim_text, anchor_dicts, raw_anchors in _iter_claim_groups(
            section_html, sources_dir
        ):
            supports, reason = _anchor_supports_claim(
                claim=claim_text,
                anchor=anchor_dicts,
                sources_dir=sources_dir,
                ask_llm_semantic=ask_llm_semantic,
                budget_state=budget_state,
            )
            if not supports:
                violations.append(Violation(
                    severity="critical",
                    claim=claim_text[:200],
                    anchor=" ".join(raw_anchors),
                    reason=f"semantic check failed: {reason}",
                    suggestion="claim 与源不一致 — 核对 anchor 真指代或换正确 anchor",
                ))

    verdict: Literal["ok", "blocked"] = "blocked" if violations else "ok"
    return Verdict(
        verdict=verdict,
        violations=violations,
        verified_count=_count_verified_claim_units(section_html, sources_dir),
    )


def verify_full_report(
    html: str,
    sources_dir: Path,
    *,
    ask_llm_semantic: Optional[Callable] = None,
    budget_state: Optional[dict] = None,
    source_manifest_path: Path | None = None,
    required_source_channels: tuple[str, ...] | list[str] | None = None,
    audit_layer: dict[str, Any] | None = None,
) -> Verdict:
    """Verify full HTML report by aggregating per-section verdicts.

    R2 升级: 可选 kwargs ask_llm_semantic / budget_state. 默认 None 时行为与 119 现有测试一致;
    提供时调 _anchor_supports_claim 做 Tier 1+2 语义检查 (HER2 SHR-A1811/RC48 错锅必抓).
    """
    sections = re.split(r"(?=<section\b)", html)
    if not sections:
        sections = [html]

    all_violations: list[Violation] = []
    if source_manifest_path is not None:
        repo_root = Path(__file__).resolve().parents[3]
        scripts_dir = repo_root / "scripts"
        if str(scripts_dir) not in sys.path:
            sys.path.insert(0, str(scripts_dir))
        from source_provenance import verify_manifest_provenance

        provenance = verify_manifest_provenance(
            source_manifest_path, Path(source_manifest_path).parent
        )
        if not provenance.ok:
            for err in provenance.errors:
                all_violations.append(Violation(
                    severity="critical",
                    claim="source manifest",
                    anchor="",
                    reason=f"source manifest provenance failed: {err}",
                    suggestion="fetch raw source again and regenerate source_manifest.json",
                ))

    all_violations.extend(_report_substance_violations(html))

    if isinstance(audit_layer, dict):
        audit_violations, anchor_audit = _verify_audit_layer(
            audit_layer,
            sources_dir,
            ask_llm_semantic=ask_llm_semantic,
            budget_state=budget_state,
        )
        all_violations.extend(audit_violations)
        all_violations.extend(_reader_badge_violations(html, audit_layer))
        audit_anchor_html = " ".join(_audit_layer_source_anchors(audit_layer))
        all_violations.extend(_required_source_channel_violations(
            audit_anchor_html,
            sources_dir,
            required_source_channels,
        ))
        verdict: Literal["ok", "blocked"] = "blocked" if all_violations else "ok"
        payload = Verdict(
            verdict=verdict,
            violations=all_violations,
            verified_count=anchor_audit["verified_count"],
        )
        payload["anchor_audit"] = AnchorAudit(  # type: ignore[typeddict-unknown-key]
            total_claims=anchor_audit["total_claims"],
            total_anchors=anchor_audit["total_anchors"],
            verified_count=anchor_audit["verified_count"],
            anchors_without_locator=anchor_audit["anchors_without_locator"],
            violations_by_reason=_violations_by_reason(all_violations),
        )
        return payload

    all_violations.extend(_required_source_channel_violations(
        html,
        sources_dir,
        required_source_channels,
    ))

    total_verified = 0
    for sec in sections:
        if not sec.strip():
            continue
        result = verify_section(
            sec, sources_dir,
            ask_llm_semantic=ask_llm_semantic,
            budget_state=budget_state,
        )
        all_violations.extend(result["violations"])
        total_verified += result["verified_count"]

    verdict: Literal["ok", "blocked"] = "blocked" if all_violations else "ok"
    payload = Verdict(verdict=verdict, violations=all_violations, verified_count=total_verified)
    payload["anchor_audit"] = _build_anchor_audit(html, all_violations, total_verified)  # type: ignore[typeddict-unknown-key]
    return payload


# ---------------------------------------------------------------------------
# T13: route drug claims through drug-citation-verifier (A5')
# ---------------------------------------------------------------------------
import importlib.util as _ilu

_HERE_VERIFIER = Path(__file__).resolve()
_A5_PRIME_FILE = _HERE_VERIFIER.parents[2] / "drug-citation-verifier" / "scripts" / "verifier.py"


def _load_drug_verifier():
    """Import drug-citation-verifier with a unique module name to avoid
    colliding with this module (both files are named verifier.py)."""
    if not _A5_PRIME_FILE.exists():
        return None
    a5_scripts_dir = str(_A5_PRIME_FILE.parent)
    if a5_scripts_dir not in sys.path:
        sys.path.insert(0, a5_scripts_dir)
    spec = _ilu.spec_from_file_location("_a5_prime_drug_verifier", str(_A5_PRIME_FILE))
    if spec is None or spec.loader is None:
        return None
    mod = _ilu.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_a5_module = _load_drug_verifier()


def _default_drug_verifier(text, sources_dir):
    return {"ok": True, "drug_mentions": [], "violation_severity": "none"}


verify_drug_mentions_in_text = (
    getattr(_a5_module, "verify_drug_mentions_in_text", _default_drug_verifier)
    if _a5_module
    else _default_drug_verifier
)


_DRUG_SUFFIX_RE = re.compile(r"\w+(?:替尼|单抗|阿克|tinib|mab|glutide|肽|nib)\b")


def _has_drug_mention(text: str) -> bool:
    return bool(_DRUG_SUFFIX_RE.search(text))


# Wrap verify_section so drug-bearing sections are also cross-checked via A5'.
_verify_section_basic = verify_section


def verify_section(  # noqa: F811
    section_html: str,
    sources_dir: Path,
    *,
    ask_llm_semantic: Optional[Callable] = None,
    budget_state: Optional[dict] = None,
) -> Verdict:
    base = _verify_section_basic(
        section_html, sources_dir,
        ask_llm_semantic=ask_llm_semantic,
        budget_state=budget_state,
    )
    plain = _strip_html(section_html)
    if not _has_drug_mention(plain):
        return base

    a5_result = verify_drug_mentions_in_text(plain, sources_dir)
    if a5_result.get("violation_severity") == "critical":
        for mention in a5_result.get("drug_mentions", []):
            if mention.get("verified", True):
                continue
            base["violations"].append(Violation(
                severity="critical",
                claim=mention.get("text", ""),
                anchor=mention.get("citation", "") or "",
                reason=mention.get("reason", "drug mention not verified against source"),
                suggestion="remove drug name claim or cite NMPA registration page",
            ))
        base["verdict"] = "blocked"
    return base
