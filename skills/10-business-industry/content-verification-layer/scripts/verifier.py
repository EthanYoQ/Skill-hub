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

Stage 3.2 Tier 0 provenance check (2026-04-27, architect af565bdc 修订 7):
- _resolve_anchor_to_path: 平行 _resolve_anchor_to_text 但返回 Path (修 spec v3 § 3.2 bug)
- _check_provenance: 检查 source sidecar provenance.json + checksum 一致
- grace period: source mtime < cleanup_baseline_date 视 legacy (severity=warning),
  新 source 严格 critical
- 默认 opt-in (enforce_provenance=False), backward compat (175 现有测试不破坏)
"""
from __future__ import annotations
import hashlib
import json
import os
import re
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Literal, Optional, TypedDict, Union


_ANCHOR_PATTERN = re.compile(
    r"\[(guideline|pmid|nct|aact|nmpa-page|evidence):([^\]]+)\]"
)


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


# Heuristics for "fact claim" sentences (drugs/treatments/stats/recommendations)
_FACT_PATTERNS = (
    re.compile(r"(?:PFS|OS|HR|RR)\s*(?:is|为|约|=|approximately)?\s*[\d.]+"),
    re.compile(r"\b(?:1L|2L|3L|first[- ]?line|second[- ]?line|third[- ]?line|一线|二线|三线)\b"),
    re.compile(r"(?:Grade|grade)\s*[A-D]"),
    re.compile(r"(?:推荐等级|recommendation grade)\s*[A-D]"),
    re.compile(r"\d{1,3}(?:\.\d+)?\s*(?:%|percent|cases?|patients?|例)"),
    # any -tinib / -mab / -nib / -tide / -glutide drug suffixes
    re.compile(r"\w+(?:替尼|单抗|阿克|tinib|mab|glutide|肽)\b"),
)


def _split_into_claims(text: str) -> list[tuple[int, str]]:
    """Split paragraph text into sentence-like fragments with byte offsets."""
    out: list[tuple[int, str]] = []
    pos = 0
    for sentence in re.split(r"(?<=[。.!!??])\s+", text):
        if sentence.strip():
            out.append((pos, sentence.strip()))
        pos += len(sentence) + 1
    return out


def _strip_html(html: str) -> str:
    return re.sub(r"<[^>]+>", " ", html)


def _anchor_resolves(anchor: str, sources_dir: Path) -> bool:
    m = _ANCHOR_PATTERN.fullmatch(anchor)
    if not m:
        return False
    src_type, locator = m.group(1), m.group(2)
    if src_type == "guideline":
        source_id = locator.split(":")[0]
        return (sources_dir / "guidelines" / f"{source_id}.txt").exists()
    if src_type == "pmid":
        pmid = locator.split(":")[0]
        return (sources_dir / "pubmed" / f"{pmid}.json").exists()
    if src_type == "nct":
        nct = locator.split(":")[0]
        return (sources_dir / "trials" / f"{nct}.json").exists()
    if src_type == "evidence":
        rel = locator.split(":")[0]
        return (sources_dir.parent.parent / rel).exists()
    return False


# ---------------------------------------------------------------------------
# R2 Phase-2-Quality-Fix · _anchor_supports_claim: Tier 1 + Tier 2 语义检查
# ---------------------------------------------------------------------------
# 现场命名规范: guidelines/<id>.txt · pubmed/<pmid>.json · trials/<nct>.json
# anchor 入参 dict 形式: {"type": "nct", "id": "NCT04400695"}


# ---------------------------------------------------------------------------
# Stage 3.2 Tier 0 · provenance check (架构师 af565bdc 修订 7)
# ---------------------------------------------------------------------------
# 默认 opt-in (enforce_provenance=False) — 不破坏 175 baseline 测试.
# Grace period: source mtime < cleanup_baseline_date → severity="warning" (legacy);
# mtime ≥ baseline → severity="critical" (post-cleanup, 必须有 provenance).
#
# baseline 配置: 环境变量 DISEASE_MARKET_SIZING_CLEANUP_BASELINE (ISO8601),
# 默认 2099 年远未来 (任何文件 mtime < 它 → 全 legacy → 仅 warning).
# Stage 3.3 跑 git tag pre-cleanup-cache-baseline 时把 baseline 改成 tag 时间戳.

_DEFAULT_CLEANUP_BASELINE = datetime(2099, 1, 1, tzinfo=timezone.utc)


def _get_cleanup_baseline() -> datetime:
    """Read baseline from env, fallback to far-future (legacy-friendly grace)."""
    raw = os.environ.get("DISEASE_MARKET_SIZING_CLEANUP_BASELINE")
    if raw:
        try:
            return datetime.fromisoformat(raw.replace("Z", "+00:00"))
        except ValueError:
            pass
    return _DEFAULT_CLEANUP_BASELINE


def _resolve_anchor_to_path(anchor: dict, sources_dir: Path) -> Optional[Path]:
    """Parallel to _resolve_anchor_to_text but returns Path (架构师修订 7 修 spec bug).

    spec v3 § 3.2 原代码 `source_path = _resolve_anchor_to_text(...)` 返 text 内容,
    后面 `json.load(source_path)` 必爆. 此函数走 path resolution 不读内容.
    """
    a_type = anchor.get("type", "")
    a_id = anchor.get("id", "")
    if not a_id:
        return None
    if a_type == "guideline":
        return sources_dir / "guidelines" / f"{a_id}.txt"
    if a_type == "pmid":
        return sources_dir / "pubmed" / f"{a_id}.json"
    if a_type == "nct":
        return sources_dir / "trials" / f"{a_id}.json"
    if a_type == "evidence":
        if Path(a_id).is_absolute():
            return Path(a_id)
        return sources_dir.parent.parent / a_id
    return None


def _check_provenance(
    anchor: dict,
    sources_dir: Path,
    cleanup_baseline: Optional[datetime] = None,
) -> tuple[bool, str, str]:
    """Tier 0 check: source 必须带 provenance sidecar + checksum 一致.

    Returns:
        (ok, severity, reason)
        - ok=True: severity="" reason="tier0: provenance verified"
        - ok=False: severity="warning" (legacy grace period)
            OR severity="critical" (post-cleanup, real failure)
    """
    source_path = _resolve_anchor_to_path(anchor, sources_dir)
    if source_path is None:
        return False, "critical", "tier0: anchor type/id invalid"
    if not source_path.exists():
        return False, "critical", f"tier0: source file not found: {source_path.name}"

    a_id = anchor.get("id", "")
    sidecar_name = f"{a_id}.provenance.json"
    sidecar_path = source_path.parent / sidecar_name

    baseline = cleanup_baseline or _get_cleanup_baseline()
    src_mtime = datetime.fromtimestamp(source_path.stat().st_mtime, tz=timezone.utc)
    is_legacy = src_mtime < baseline

    if not sidecar_path.exists():
        if is_legacy:
            return False, "warning", (
                f"tier0: legacy source missing provenance sidecar "
                f"(mtime {src_mtime.isoformat()} < baseline)"
            )
        return False, "critical", (
            f"tier0: provenance sidecar missing post-cleanup: {sidecar_path.name}"
        )

    # Sidecar exists — verify schema + checksum
    try:
        prov = json.loads(sidecar_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False, "critical", "tier0: provenance.json unreadable / malformed"

    raw_path_rel = prov.get("raw_path", "")
    expected_checksum = prov.get("checksum", "")
    if not raw_path_rel or not expected_checksum:
        return False, "critical", "tier0: provenance schema incomplete (missing raw_path or checksum)"

    raw_full = sources_dir / raw_path_rel
    if not raw_full.is_file():
        return False, "critical", f"tier0: raw_path missing: {raw_path_rel}"

    if not expected_checksum.startswith("sha256:"):
        return False, "critical", f"tier0: unsupported checksum format: {expected_checksum[:20]}"
    expected_hex = expected_checksum[len("sha256:"):]
    actual_hex = hashlib.sha256(raw_full.read_bytes()).hexdigest()
    if expected_hex != actual_hex:
        return False, "critical", (
            f"tier0: checksum mismatch (expected {expected_hex[:8]}.., got {actual_hex[:8]}..)"
        )

    return True, "", "tier0: provenance verified"


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
    elif a_type == "evidence":
        # evidence 路径相对仓 root, 不在 sources_dir 内
        path = sources_dir.parent.parent / a_id if not Path(a_id).is_absolute() else Path(a_id)
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

    # === Tier 1: decisive token (any-source-hit) + non-decisive ≥ 70% (union) ===
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

    excerpt = "\n\n---\n\n".join(t[:2000] for _, t in resolved)
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
                suggestion="add [guideline:.../pmid:.../nct:...] anchor or remove the claim",
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
            a_id = am.group(2).split(":")[0]
            key = f"{am.group(1)}:{a_id}"
            if key in seen_ids:
                continue
            seen_ids.add(key)
            if not _anchor_resolves(full, sources_dir):
                # Phase 1 anchor-existence 已报, semantic 阶段 skip
                continue
            anchor_dicts.append({"type": am.group(1), "id": a_id})
            raw.append(full)
        if anchor_dicts:
            groups.append((sentence, anchor_dicts, raw))
    return groups


def verify_section(
    section_html: str,
    sources_dir: Path,
    *,
    ask_llm_semantic: Optional[Callable] = None,
    budget_state: Optional[dict] = None,
    enforce_provenance: bool = False,
    cleanup_baseline: Optional[datetime] = None,
) -> Verdict:
    """Verify one HTML section. Combines:
       - enforce_citations_in_text (no unanchored fact claims)
       - anchor existence reverse-lookup (no fabricated source_ids)
       - Stage 3.2 Tier 0: provenance check (opt-in via enforce_provenance=True)
         · grace period: legacy sources (mtime < baseline) → warning only
         · post-cleanup: severity=critical → blocks verdict
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
            continue
        # Stage 3.2 Tier 0 provenance check (opt-in)
        if enforce_provenance:
            anchor_dict = {"type": m.group(1), "id": m.group(2).split(":")[0]}
            ok, severity, reason = _check_provenance(
                anchor_dict, sources_dir, cleanup_baseline=cleanup_baseline
            )
            if not ok and severity == "critical":
                violations.append(Violation(
                    severity="critical",
                    claim=section_html[max(0, m.start()-60):m.end()+60],
                    anchor=anchor,
                    reason=reason,
                    suggestion="re-fetch source via Stage 3.1b fetcher (含 provenance schema), 或 git tag pre-cleanup-cache-baseline 之前 mtime 视 legacy",
                ))
            # severity=="warning" (legacy grace) — silently allow, P0 期望迁移完成后转 critical

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
    return Verdict(verdict=verdict, violations=violations, verified_count=len(seen_anchors))


def verify_full_report(
    html: str,
    sources_dir: Path,
    *,
    ask_llm_semantic: Optional[Callable] = None,
    budget_state: Optional[dict] = None,
    enforce_provenance: bool = False,
    cleanup_baseline: Optional[datetime] = None,
) -> Verdict:
    """Verify full HTML report by aggregating per-section verdicts.

    R2 升级: 可选 kwargs ask_llm_semantic / budget_state. 默认 None 时行为与 119 现有测试一致;
    提供时调 _anchor_supports_claim 做 Tier 1+2 语义检查 (HER2 SHR-A1811/RC48 错锅必抓).

    Stage 3.2 升级: enforce_provenance=True 启用 Tier 0 (default off, backward compat).
    """
    sections = re.split(r"(?=<section\b)", html)
    if not sections:
        sections = [html]

    all_violations: list[Violation] = []
    total_verified = 0
    for sec in sections:
        if not sec.strip():
            continue
        result = verify_section(
            sec, sources_dir,
            ask_llm_semantic=ask_llm_semantic,
            budget_state=budget_state,
            enforce_provenance=enforce_provenance,
            cleanup_baseline=cleanup_baseline,
        )
        all_violations.extend(result["violations"])
        total_verified += result["verified_count"]

    verdict: Literal["ok", "blocked"] = "blocked" if all_violations else "ok"
    return Verdict(verdict=verdict, violations=all_violations, verified_count=total_verified)


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
    enforce_provenance: bool = False,
    cleanup_baseline: Optional[datetime] = None,
) -> Verdict:
    base = _verify_section_basic(
        section_html, sources_dir,
        ask_llm_semantic=ask_llm_semantic,
        budget_state=budget_state,
        enforce_provenance=enforce_provenance,
        cleanup_baseline=cleanup_baseline,
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
