#!/usr/bin/env python
"""Verify local README image references, dimensions, and basic render health."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

from PIL import Image, ImageStat


MARKDOWN_IMAGE = re.compile(r"!\[([^\]]*)\]\(([^)\s]+)(?:\s+['\"][^'\"]*['\"])?\)")
HTML_IMAGE = re.compile(r"<img\b[^>]*\bsrc=['\"]([^'\"]+)['\"][^>]*>", re.IGNORECASE)
HTML_ALT = re.compile(r"\balt=['\"]([^'\"]*)['\"]", re.IGNORECASE)
README_CANDIDATES = (
    "README.md",
    "README_zh.md",
    "README.zh.md",
    "README.en.md",
    "README_en.md",
    "README_EN.md",
)
PRODUCT_PROOF_PROFILE = "product-proof-split-v1"
PRODUCT_PROOF_SIZE = (2560, 1280)
ALLOWED_CAPTURE_PROVENANCE = {
    "computer-use-capture",
    "playwright-capture",
    "provided-real-screenshot",
    "project-authored-screenshot",
}


def parse_expected_size(value: str) -> tuple[str, tuple[int, int]]:
    try:
        path, size = value.rsplit("=", 1)
        width, height = size.lower().split("x", 1)
        return path.replace("\\", "/"), (int(width), int(height))
    except ValueError as exc:
        raise argparse.ArgumentTypeError("expected PATH=WIDTHxHEIGHT") from exc


def image_refs(markdown: str) -> list[dict[str, str]]:
    refs = [
        {"src": match.group(2), "alt": match.group(1).strip(), "syntax": "markdown"}
        for match in MARKDOWN_IMAGE.finditer(markdown)
    ]
    for match in HTML_IMAGE.finditer(markdown):
        tag = match.group(0)
        alt_match = HTML_ALT.search(tag)
        refs.append({
            "src": match.group(1),
            "alt": alt_match.group(1).strip() if alt_match else "",
            "alt_present": bool(alt_match),
            "syntax": "html",
        })
    return refs


def is_remote(src: str) -> bool:
    lowered = src.lower()
    return lowered.startswith(("http://", "https://", "data:", "#"))


def contained_path(repo: Path, value: str, label: str, errors: list[str]) -> Path | None:
    path = (repo / value).resolve()
    if path != repo and repo not in path.parents:
        errors.append(f"{label} escapes repository: {value}")
        return None
    return path


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_product_proof_manifest(
    repo: Path,
    manifest_value: str,
    expected_profile: str | None,
    readme_local_paths: dict[str, set[str]],
    errors: list[str],
    warnings: list[str],
) -> dict:
    manifest_path = contained_path(repo, manifest_value, "manifest", errors)
    result: dict = {"path": manifest_value}
    if manifest_path is None:
        return result
    if not manifest_path.exists():
        errors.append(f"manifest not found: {manifest_value}")
        return result
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        errors.append(f"unreadable manifest: {manifest_value}: {exc}")
        return result

    result["profile"] = manifest.get("profile")
    if manifest.get("schema_version") != 1:
        errors.append("visual manifest schema_version must be 1")
    profile = manifest.get("profile")
    if expected_profile and profile != expected_profile:
        errors.append(f"manifest profile is {profile!r}, expected {expected_profile!r}")
    if profile != PRODUCT_PROOF_PROFILE:
        errors.append(f"unsupported manifest profile: {profile!r}")
        return result

    composition_value = manifest.get("composition_source")
    if not isinstance(composition_value, str) or not composition_value:
        errors.append("manifest composition_source is required")
    else:
        composition_path = contained_path(repo, composition_value, "composition source", errors)
        if composition_path is not None:
            if not composition_path.exists():
                errors.append(f"composition source not found: {composition_value}")
            else:
                canonical_template = Path(__file__).resolve().parents[1] / "assets" / "product-proof-split-v1.html"
                if not canonical_template.exists():
                    errors.append(f"canonical Product-proof template is missing from Skill: {canonical_template}")
                elif file_sha256(composition_path) != file_sha256(canonical_template):
                    errors.append("composition source is not byte-identical to the canonical Product-proof split v1 template")

    data_value = manifest.get("data_source")
    if not isinstance(data_value, str) or not data_value:
        errors.append("manifest data_source is required")
    else:
        data_path = contained_path(repo, data_value, "data source", errors)
        if data_path is not None and not data_path.exists():
            errors.append(f"data source not found: {data_value}")

    heroes = manifest.get("heroes")
    if not isinstance(heroes, dict) or not heroes:
        errors.append("manifest heroes must be a non-empty object")
        return result

    screenshot_counts: dict[str, int] = {}
    result_heroes: dict[str, dict] = {}
    for locale, hero in heroes.items():
        if not isinstance(hero, dict):
            errors.append(f"manifest hero {locale!r} must be an object")
            continue
        readme_name = hero.get("readme")
        output_value = hero.get("output")
        ui_locale = hero.get("ui_locale")
        locale_result: dict = {"readme": readme_name, "output": output_value, "ui_locale": ui_locale}
        result_heroes[str(locale)] = locale_result

        if not isinstance(readme_name, str) or not readme_name:
            errors.append(f"manifest hero {locale!r} requires readme")
        elif readme_name not in readme_local_paths:
            errors.append(f"manifest hero {locale!r} README was not inspected: {readme_name}")

        if not isinstance(ui_locale, str) or not ui_locale:
            errors.append(f"manifest hero {locale!r} requires ui_locale")

        if not isinstance(output_value, str) or not output_value:
            errors.append(f"manifest hero {locale!r} requires output")
        else:
            output_path = contained_path(repo, output_value, f"hero output {locale}", errors)
            if output_path is not None:
                if not output_path.exists():
                    errors.append(f"hero output not found: {output_value}")
                else:
                    try:
                        with Image.open(output_path) as image:
                            if image.size != PRODUCT_PROOF_SIZE:
                                errors.append(
                                    f"Product-proof hero {output_value} is {image.width}x{image.height}, "
                                    f"expected {PRODUCT_PROOF_SIZE[0]}x{PRODUCT_PROOF_SIZE[1]}"
                                )
                    except Exception as exc:
                        errors.append(f"unreadable hero output {output_value}: {exc}")
            if isinstance(readme_name, str) and output_value not in readme_local_paths.get(readme_name, set()):
                errors.append(f"manifest hero output is not referenced by {readme_name}: {output_value}")

        screenshots = hero.get("screenshots")
        if not isinstance(screenshots, list) or not 4 <= len(screenshots) <= 6:
            count = len(screenshots) if isinstance(screenshots, list) else "invalid"
            errors.append(f"manifest hero {locale!r} requires four to six screenshots, found {count}")
            continue
        screenshot_counts[str(locale)] = len(screenshots)
        locale_result["screenshot_count"] = len(screenshots)
        roles = [shot.get("role") if isinstance(shot, dict) else None for shot in screenshots]
        if roles[0] != "primary" or roles.count("primary") != 1:
            errors.append(f"manifest hero {locale!r} must have exactly one primary screenshot in first position")

        seen_paths: set[str] = set()
        seen_hashes: dict[str, str] = {}
        for index, screenshot in enumerate(screenshots):
            label = f"manifest hero {locale!r} screenshot {index + 1}"
            if not isinstance(screenshot, dict):
                errors.append(f"{label} must be an object")
                continue
            screenshot_value = screenshot.get("path")
            if not isinstance(screenshot_value, str) or not screenshot_value:
                errors.append(f"{label} requires path")
                continue
            if screenshot_value in seen_paths:
                errors.append(f"duplicate screenshot path in hero {locale!r}: {screenshot_value}")
            seen_paths.add(screenshot_value)
            if screenshot.get("capture_provenance") not in ALLOWED_CAPTURE_PROVENANCE:
                errors.append(f"{label} has invalid capture_provenance: {screenshot.get('capture_provenance')!r}")
            if screenshot.get("complete_window") is not True:
                errors.append(f"{label} must attest complete_window=true")
            if screenshot.get("ui_locale") != ui_locale:
                errors.append(
                    f"{label} ui_locale {screenshot.get('ui_locale')!r} does not match hero ui_locale {ui_locale!r}"
                )
            screenshot_path = contained_path(repo, screenshot_value, label, errors)
            if screenshot_path is None:
                continue
            if not screenshot_path.exists():
                errors.append(f"screenshot not found: {screenshot_value}")
                continue
            try:
                digest = file_sha256(screenshot_path)
                if digest in seen_hashes:
                    errors.append(
                        f"duplicate screenshot content in hero {locale!r}: {screenshot_value} matches {seen_hashes[digest]}"
                    )
                else:
                    seen_hashes[digest] = screenshot_value
                with Image.open(screenshot_path) as image:
                    ratio = image.width / image.height
                    if abs(ratio - (4 / 3)) > 0.01:
                        errors.append(
                            f"Product-proof screenshot {screenshot_value} is {image.width}x{image.height}; expected 4:3"
                        )
            except Exception as exc:
                errors.append(f"unreadable screenshot {screenshot_value}: {exc}")

    result["heroes"] = result_heroes
    if len(screenshot_counts) > 1 and len(set(screenshot_counts.values())) > 1:
        errors.append(f"Product-proof localized screenshot counts differ: {screenshot_counts}")
    if len(heroes) == 1:
        warnings.append("Product-proof manifest contains one locale; add another only when the repository has another README locale")
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--readme", action="append", default=[])
    parser.add_argument("--expected-size", action="append", default=[], type=parse_expected_size)
    parser.add_argument("--manifest")
    parser.add_argument("--expected-profile")
    args = parser.parse_args()

    repo = args.repo.expanduser().resolve()
    expected_sizes = dict(args.expected_size)
    readme_names = args.readme or [name for name in README_CANDIDATES if (repo / name).exists()]
    errors: list[str] = []
    warnings: list[str] = []
    readme_results: list[dict] = []
    seen_local_paths: set[str] = set()
    readme_local_paths: dict[str, set[str]] = {}

    if not readme_names:
        errors.append("no README files found")

    local_counts: dict[str, int] = {}
    for name in readme_names:
        readme_path = (repo / name).resolve()
        if repo not in readme_path.parents and readme_path != repo:
            errors.append(f"README escapes repository: {name}")
            continue
        if not readme_path.exists():
            errors.append(f"README not found: {name}")
            continue

        refs = image_refs(readme_path.read_text(encoding="utf-8"))
        images: list[dict] = []
        for ref in refs:
            src = ref["src"]
            if is_remote(src):
                images.append({**ref, "remote": True})
                continue
            normalized = src.split("#", 1)[0].split("?", 1)[0]
            image_path = (readme_path.parent / normalized).resolve()
            if repo not in image_path.parents:
                errors.append(f"image escapes repository: {name} -> {src}")
                continue
            item = {**ref, "remote": False, "path": image_path.relative_to(repo).as_posix()}
            seen_local_paths.add(item["path"])
            if ref["syntax"] == "markdown" and not ref["alt"]:
                errors.append(f"missing alt text: {name} -> {src}")
            if not image_path.exists():
                errors.append(f"missing image: {name} -> {src}")
                images.append(item)
                continue
            if image_path.suffix.lower() == ".svg":
                item["vector"] = True
                images.append(item)
                continue
            try:
                with Image.open(image_path) as image:
                    width, height = image.size
                    rgb = image.convert("RGB")
                    stat = ImageStat.Stat(rgb.resize((32, 32)))
                    extrema = rgb.getextrema()
                    luminance = sum(stat.mean) / 3
                    dynamic_range = max(high for _, high in extrema) - min(low for low, _ in extrema)
                item.update({"width": width, "height": height})
                expected = expected_sizes.get(item["path"])
                if expected and (width, height) != expected:
                    errors.append(
                        f"wrong dimensions: {item['path']} is {width}x{height}, expected {expected[0]}x{expected[1]}"
                    )
                if dynamic_range <= 10 and max(stat.stddev) <= 3:
                    errors.append(f"probable blank or uniform render: {item['path']}")
            except Exception as exc:
                errors.append(f"unreadable image: {item['path']}: {exc}")
            images.append(item)

        local_counts[name] = sum(1 for item in images if not item.get("remote"))
        readme_local_paths[name] = {
            item["path"] for item in images if not item.get("remote") and "path" in item
        }
        readme_results.append({"readme": name, "images": images})

    if len(local_counts) > 1 and len(set(local_counts.values())) > 1:
        warnings.append(f"localized README local-image counts differ: {local_counts}")
    for expected_path in sorted(set(expected_sizes) - seen_local_paths):
        errors.append(f"expected-size path is not referenced by inspected READMEs: {expected_path}")

    manifest_result = None
    if args.manifest:
        manifest_result = validate_product_proof_manifest(
            repo,
            args.manifest,
            args.expected_profile,
            readme_local_paths,
            errors,
            warnings,
        )
    elif args.expected_profile:
        errors.append("--expected-profile requires --manifest")

    report = {
        "ok": not errors,
        "repo": str(repo),
        "errors": errors,
        "warnings": warnings,
        "readmes": readme_results,
        "manifest": manifest_result,
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
