"""Internal helper migrated from former `mermaid-renderer` skill (deleted 2026-04-27).

Renders Mermaid text to PNG via `mmdc` CLI, with three-tier graceful fallback
preserved per architect review af265bdc revision 5:

1. mmdc unavailable → ok=False + fallback_inline (mermaid_text)
2. subprocess failure (non-zero exit / output missing) → ok=False + fallback_inline + stderr
3. subprocess timeout (default 30s) → ok=False + fallback_inline + "mmdc timeout"

Orchestrator Phase 4.5 keeps inline `<div class="mermaid">` when ok=False
(browser can render via mermaid.js CDN), so a missing mmdc never blocks the pipeline.
"""
from __future__ import annotations

import shutil
import subprocess  # nosec B404 - controlled mmdc CLI invocation
import tempfile
from pathlib import Path
from typing import Optional


def render_mermaid_to_png(
    mermaid_text: str,
    output_path: Path,
    timeout_sec: int = 30,
) -> dict:
    """Render Mermaid text to PNG. See module docstring for fallback semantics."""
    output_path = Path(output_path)

    # Layer 1: mmdc unavailable
    if shutil.which("mmdc") is None:
        return {
            "ok": False,
            "path": None,
            "fallback_inline": mermaid_text,
            "reason": "mmdc not installed (npm install -g @mermaid-js/mermaid-cli)",
        }

    mmd_path: Optional[Path] = None
    try:
        with tempfile.NamedTemporaryFile(
            suffix=".mmd", delete=False, mode="w", encoding="utf-8"
        ) as f:
            f.write(mermaid_text)
            mmd_path = Path(f.name)

        output_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            result = subprocess.run(  # nosec B603 - mmdc CLI with controlled args
                ["mmdc", "-i", str(mmd_path), "-o", str(output_path), "-b", "white"],
                timeout=timeout_sec,
                capture_output=True,
                text=True,
            )
        except subprocess.TimeoutExpired:
            return {
                "ok": False,
                "path": None,
                "fallback_inline": mermaid_text,
                "reason": f"mmdc timeout after {timeout_sec}s",
            }
        except (OSError, FileNotFoundError) as e:
            return {
                "ok": False,
                "path": None,
                "fallback_inline": mermaid_text,
                "reason": f"mmdc subprocess error: {e}",
            }

        if result.returncode == 0 and output_path.exists():
            return {
                "ok": True,
                "path": output_path,
                "fallback_inline": None,
                "reason": "mmdc ok",
            }

        # Layer 2: subprocess failure (non-zero exit or missing output)
        return {
            "ok": False,
            "path": None,
            "fallback_inline": mermaid_text,
            "reason": f"mmdc exit {result.returncode}: {result.stderr[:500]}",
        }
    finally:
        if mmd_path is not None:
            mmd_path.unlink(missing_ok=True)
