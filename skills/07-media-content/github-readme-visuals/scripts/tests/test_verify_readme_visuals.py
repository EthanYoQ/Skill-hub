from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image


SKILL_ROOT = Path(__file__).resolve().parents[2]
VERIFIER = SKILL_ROOT / "scripts" / "verify_readme_visuals.py"
TEMPLATE = SKILL_ROOT / "assets" / "product-proof-split-v1.html"


class ProductProofManifestTests(unittest.TestCase):
    def test_canonical_template_preserves_approved_geometry(self) -> None:
        source = TEMPLATE.read_text(encoding="utf-8")
        required_tokens = [
            'data-profile="product-proof-split-v1"',
            'width: 1060px;',
            'width: 800px;',
            'height: 600px;',
            '.shot-a { left: 1400px; top: -230px; transform: rotate(8deg); z-index: 2; }',
            '.shot-b { left: 2170px; top: -75px; transform: rotate(8deg); z-index: 3; }',
            '.shot-main { left: 1198px; top: 335px; transform: rotate(8deg); z-index: 9; }',
            '.shot-c { left: 1944px; top: 533px; transform: rotate(8deg); z-index: 7; }',
            '.shot-d { left: 1102px; top: 841px; transform: rotate(8deg); z-index: 5; }',
            '.shot-e { left: 1937px; top: 1007px; transform: rotate(8deg); z-index: 6; }',
            'transform: rotate(141deg);',
            'transform: rotate(154deg);',
            'const slotOrder = [".shot-main", ".shot-a", ".shot-c", ".shot-d", ".shot-b", ".shot-e"];',
        ]
        for token in required_tokens:
            self.assertIn(token, source)

    def build_repo(self, root: Path, *, duplicate: bool = False, modify_template: bool = False) -> None:
        visuals = root / "docs" / "readme-visuals"
        images = root / "docs" / "images"
        screens = images / "screens"
        visuals.mkdir(parents=True)
        screens.mkdir(parents=True)
        shutil.copy2(TEMPLATE, visuals / "product-proof-split-v1.html")
        if modify_template:
            with (visuals / "product-proof-split-v1.html").open("a", encoding="utf-8") as handle:
                handle.write("\n<!-- geometry drift -->\n")
        (visuals / "hero-data.js").write_text("window.README_HERO_CONFIG = {};\n", encoding="utf-8")
        hero = Image.new("RGB", (2560, 1280), (244, 246, 250))
        hero.paste((10, 20, 35), (0, 0, 960, 1280))
        hero.paste((80, 110, 150), (1100, 160, 2000, 920))
        hero.paste((170, 190, 215), (1780, 500, 2560, 1280))
        hero.save(images / "product-hero-zh.png")

        screenshot_entries = []
        colors = [(20, 40, 60), (60, 80, 100), (100, 120, 140), (140, 160, 180)]
        for index, color in enumerate(colors):
            path = screens / f"screen-{index + 1}.png"
            source_color = colors[0] if duplicate and index == 1 else color
            Image.new("RGB", (1200, 900), source_color).save(path)
            screenshot_entries.append({
                "path": path.relative_to(root).as_posix(),
                "role": "primary" if index == 0 else "secondary",
                "capture_provenance": "computer-use-capture",
                "complete_window": True,
                "ui_locale": "zh-CN",
            })

        (root / "README.md").write_text(
            "# Demo\n\n![产品首图](docs/images/product-hero-zh.png)\n",
            encoding="utf-8",
        )
        manifest = {
            "schema_version": 1,
            "profile": "product-proof-split-v1",
            "composition_source": "docs/readme-visuals/product-proof-split-v1.html",
            "data_source": "docs/readme-visuals/hero-data.js",
            "heroes": {
                "zh": {
                    "readme": "README.md",
                    "output": "docs/images/product-hero-zh.png",
                    "ui_locale": "zh-CN",
                    "screenshots": screenshot_entries,
                }
            },
        }
        (visuals / "visual-manifest.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def run_verifier(self, repo: Path, *extra: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(VERIFIER), "--repo", str(repo), *extra],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )

    def test_valid_product_proof_manifest_passes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            self.build_repo(repo)
            result = self.run_verifier(
                repo,
                "--manifest",
                "docs/readme-visuals/visual-manifest.json",
                "--expected-profile",
                "product-proof-split-v1",
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_expected_profile_without_manifest_fails(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            self.build_repo(repo)
            result = self.run_verifier(repo, "--expected-profile", "product-proof-split-v1")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("requires --manifest", result.stdout)

    def test_duplicate_screenshot_content_fails(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            self.build_repo(repo, duplicate=True)
            result = self.run_verifier(
                repo,
                "--manifest",
                "docs/readme-visuals/visual-manifest.json",
                "--expected-profile",
                "product-proof-split-v1",
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("duplicate screenshot content", result.stdout)

    def test_modified_canonical_template_fails(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            self.build_repo(repo, modify_template=True)
            result = self.run_verifier(
                repo,
                "--manifest",
                "docs/readme-visuals/visual-manifest.json",
                "--expected-profile",
                "product-proof-split-v1",
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("not byte-identical", result.stdout)


if __name__ == "__main__":
    unittest.main()
