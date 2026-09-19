#!/usr/bin/env python3
"""Deterministic semantic deck planner and anti-repetition validator."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


STYLE_INDEX = Path(__file__).resolve().parents[1] / "references" / "style-index.json"

COMPOSITIONS = {
    "statement-full-bleed": {"geometry": "statement", "relations": {"statement", "none"}},
    "dominant-metric-marginalia": {"geometry": "asymmetric", "relations": {"single-value", "kpi"}},
    "chart-notes-asymmetric": {"geometry": "split", "relations": {"comparison", "trend", "distribution"}},
    "comparison-split": {"geometry": "split", "relations": {"comparison", "before-after"}},
    "ledger-takeaway-band": {"geometry": "ledger", "relations": {"kpi", "limits", "evidence", "comparison"}},
    "process-rail": {"geometry": "process", "relations": {"sequence", "workflow", "timeline"}},
    "matrix-marginalia": {"geometry": "matrix", "relations": {"matching", "matrix", "portfolio"}},
    "small-multiple-field": {"geometry": "chart-field", "relations": {"comparison", "trend", "distribution"}},
    "image-text-offset": {"geometry": "image", "relations": {"case", "product", "none"}, "needs_media": True},
    "editorial-mosaic": {"geometry": "mosaic", "relations": {"kpi", "evidence", "case", "portfolio"}},
}

RELATION_CANDIDATES = {
    "single-value": ["dominant-metric-marginalia", "statement-full-bleed"],
    "kpi": ["dominant-metric-marginalia", "ledger-takeaway-band", "editorial-mosaic"],
    "comparison": ["chart-notes-asymmetric", "comparison-split", "small-multiple-field", "ledger-takeaway-band"],
    "trend": ["chart-notes-asymmetric", "small-multiple-field"],
    "distribution": ["small-multiple-field", "chart-notes-asymmetric"],
    "timeline": ["process-rail", "editorial-mosaic"],
    "sequence": ["process-rail", "editorial-mosaic"],
    "workflow": ["process-rail", "matrix-marginalia"],
    "matching": ["matrix-marginalia", "ledger-takeaway-band"],
    "matrix": ["matrix-marginalia", "ledger-takeaway-band"],
    "before-after": ["comparison-split", "editorial-mosaic"],
    "evidence": ["ledger-takeaway-band", "chart-notes-asymmetric", "editorial-mosaic"],
    "limits": ["ledger-takeaway-band", "comparison-split"],
    "portfolio": ["matrix-marginalia", "editorial-mosaic", "small-multiple-field"],
    "case": ["image-text-offset", "editorial-mosaic", "statement-full-bleed"],
    "product": ["image-text-offset", "comparison-split", "editorial-mosaic"],
    "statement": ["statement-full-bleed", "image-text-offset"],
    "none": ["statement-full-bleed", "editorial-mosaic", "image-text-offset"],
}

ROLE_PREFERENCES = {
    "opener": ["statement-full-bleed", "image-text-offset"],
    "tension": ["dominant-metric-marginalia", "statement-full-bleed"],
    "proof": ["chart-notes-asymmetric", "ledger-takeaway-band"],
    "decision": ["comparison-split", "matrix-marginalia"],
    "transition": ["statement-full-bleed", "image-text-offset"],
    "close": ["statement-full-bleed", "image-text-offset"],
}


def _stable_order(items: list[str], seed: str) -> list[str]:
    return sorted(items, key=lambda item: hashlib.sha256(f"{seed}|{item}".encode("utf-8")).hexdigest())


def load_profiles() -> list[dict[str, Any]]:
    return json.loads(STYLE_INDEX.read_text(encoding="utf-8"))["profiles"]


def select_profile(brief: dict[str, Any]) -> dict[str, Any]:
    profiles = load_profiles()
    output_format = str(brief.get("output_format", "html")).lower()
    profiles = [profile for profile in profiles if output_format in profile.get("formats", ["html", "pptx"])]
    if not profiles:
        raise ValueError(f"No style profiles support output_format: {output_format}")
    locked = brief.get("locked_profile")
    if locked:
        for profile in profiles:
            if profile["id"] == locked:
                return profile
        raise ValueError(f"Unknown or unsupported locked_profile for {output_format}: {locked}")

    requested = {
        str(brief.get("mood", "")).lower(),
        str(brief.get("tone", "")).lower(),
        str(brief.get("formality", "medium-high")).lower(),
        str(brief.get("density_mode", "balanced")).lower(),
        str(brief.get("scheme", "")).lower(),
    }
    purpose = str(brief.get("purpose", "")).lower()
    audience = str(brief.get("audience", "")).lower()
    seed = str(brief.get("seed", f"{purpose}|{audience}"))

    ranked = []
    for profile in profiles:
        metadata = {
            str(value).lower()
            for key in ("mood", "tone", "formality", "density")
            for value in profile.get(key, [])
        }
        metadata.add(str(profile.get("scheme", "")).lower())
        score = len((requested - {""}) & metadata) * 4
        score += sum(3 for phrase in profile.get("best_for", []) if phrase.lower() in f"{purpose} {audience}")
        score -= sum(5 for phrase in profile.get("avoid_for", []) if phrase.lower() in f"{purpose} {audience}")
        tie = hashlib.sha256(f"{seed}|{profile['id']}".encode("utf-8")).hexdigest()
        ranked.append((-score, tie, profile))
    return sorted(ranked, key=lambda row: (row[0], row[1]))[0][2]


def _candidate_score(candidate: str, slide: dict[str, Any], history: list[dict[str, Any]], seed: str) -> tuple[int, str]:
    role = str(slide.get("narrative_role", "content"))
    preferred = ROLE_PREFERENCES.get(role, [])
    score = preferred.index(candidate) * 4 if candidate in preferred else 12
    recent = history[-2:]
    if recent and recent[-1]["composition_id"] == candidate:
        score += 100
    geometry = COMPOSITIONS[candidate]["geometry"]
    score += sum(14 for previous in recent if previous["dominant_geometry"] == geometry)
    if candidate == "dominant-metric-marginalia" and int(slide.get("cardinality", {}).get("items", 1)) > 4:
        score += 18
    if candidate == "ledger-takeaway-band" and slide.get("density_mode") == "speaker-led":
        score += 10
    tie = hashlib.sha256(f"{seed}|{slide.get('id')}|{candidate}".encode("utf-8")).hexdigest()
    return score, tie


def _expression_family(relation: str, composition: str) -> str:
    if relation in {"comparison", "trend", "distribution"}:
        return "small-multiples" if composition == "small-multiple-field" else "annotated-chart"
    if relation in {"timeline", "sequence", "workflow"}:
        return "process"
    if relation in {"matching", "matrix", "portfolio"}:
        return "matrix"
    if relation in {"single-value", "kpi"}:
        return "metric-editorial"
    if relation in {"evidence", "limits"}:
        return "evidence-ledger"
    return "editorial-narrative"


def plan_deck(payload: dict[str, Any]) -> dict[str, Any]:
    brief = dict(payload.get("brief", {}))
    density = str(brief.get("density_mode", "balanced"))
    seed = str(brief.get("seed", json.dumps(brief, ensure_ascii=False, sort_keys=True)))
    profile = select_profile(brief)
    cadence = profile["cadence"]
    history: list[dict[str, Any]] = []

    for index, raw in enumerate(payload.get("slides", [])):
        slide = dict(raw)
        slide.setdefault("id", f"s{index + 1:02d}")
        slide["density_mode"] = density
        relation = str(slide.get("data_relation", "none"))
        candidates = list(RELATION_CANDIDATES.get(relation, RELATION_CANDIDATES["none"]))
        if not slide.get("media_available"):
            candidates = [candidate for candidate in candidates if not COMPOSITIONS[candidate].get("needs_media")]
        if not candidates:
            candidates = ["statement-full-bleed"]
        candidates = _stable_order(candidates, f"{seed}|{slide['id']}")
        composition = min(candidates, key=lambda candidate: _candidate_score(candidate, slide, history, seed))
        geometry = COMPOSITIONS[composition]["geometry"]

        tone = cadence[index % len(cadence)]
        if len(history) >= 2 and history[-1]["tone_id"] == history[-2]["tone_id"] == tone:
            alternatives = [value for value in cadence if value != tone]
            tone = _stable_order(alternatives, f"{seed}|tone|{slide['id']}")[0]

        planned = {
            **slide,
            "expression_family": _expression_family(relation, composition),
            "composition_id": composition,
            "dominant_geometry": geometry,
            "tone_id": tone,
            "continuation_of": slide.get("continuation_of"),
        }
        history.append(planned)

    manifest = {
        "schema_version": 1,
        "deck_profile": profile["id"],
        "density_mode": density,
        "seed": seed,
        "palette": profile["palette"],
        "slides": history,
    }
    manifest["validation"] = validate_manifest(manifest)
    return manifest


def validate_manifest(manifest: dict[str, Any]) -> dict[str, Any]:
    slides = list(manifest.get("slides", []))
    errors: list[str] = []
    warnings: list[str] = []

    for previous, current in zip(slides, slides[1:]):
        if not current.get("continuation_of") and previous.get("composition_id") == current.get("composition_id"):
            errors.append(f"Adjacent composition repetition: {previous.get('id')} and {current.get('id')}")

    for field, label in (("dominant_geometry", "geometry"), ("tone_id", "tone")):
        for index in range(2, len(slides)):
            values = [slides[index - offset].get(field) for offset in (2, 1, 0)]
            if values[0] and len(set(values)) == 1:
                errors.append(f"Three-slide {label} run ending at {slides[index].get('id')}: {values[0]}")

    non_title = [slide for slide in slides if slide.get("narrative_role") not in {"opener", "transition", "close"}]
    if non_title:
        card_like = sum(slide.get("composition_id") == "editorial-mosaic" for slide in non_title)
        if card_like / len(non_title) > 0.40:
            errors.append("Generic mosaic/card-like anatomy exceeds 40% of non-title slides")

    if len(slides) >= 10:
        compositions = {slide.get("composition_id") for slide in slides}
        geometries = {slide.get("dominant_geometry") for slide in slides}
        if len(compositions) < 5:
            warnings.append(f"Only {len(compositions)} distinct compositions; target is at least 5")
        if len(geometries) < 4:
            warnings.append(f"Only {len(geometries)} dominant geometries; target is at least 4")

    return {"passed": not errors, "errors": errors, "warnings": warnings}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="Input brief/slides JSON or an existing manifest")
    parser.add_argument("--output", "-o", type=Path)
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()

    payload = json.loads(args.input.read_text(encoding="utf-8"))
    result = validate_manifest(payload) if args.validate_only else plan_deck(payload)
    text = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text + "\n", encoding="utf-8")
    else:
        print(text)
    return 0 if result.get("passed", result.get("validation", {}).get("passed", False)) else 2


if __name__ == "__main__":
    raise SystemExit(main())
