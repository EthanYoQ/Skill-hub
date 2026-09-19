"""R3c Phase-2-Quality-Fix · Mermaid → PNG 渲染封装.

封装 mmdc CLI subprocess. 三层 fallback:
1. shutil.which("mmdc") = None → ok=False + fallback_inline (mermaid_text)
2. subprocess 失败 (returncode 非零 / output 文件不存在) → ok=False + fallback_inline + stderr
3. subprocess 超时 (默认 30s) → ok=False + fallback_inline + "mmdc timeout"

orchestrator Phase 4.5 hook 收到 ok=False 时, 保留 inline <div class="mermaid"> 不阻塞.
"""
from __future__ import annotations

import shutil
import subprocess  # nosec B404 - controlled mmdc CLI invocation
import tempfile
from pathlib import Path
from typing import Optional


def _mmdc_command() -> list[str] | None:
    mmdc = shutil.which("mmdc")
    if mmdc is not None:
        return [mmdc]
    npx = shutil.which("npx")
    if npx is not None:
        return [npx, "-y", "@mermaid-js/mermaid-cli"]
    return None


def render_mermaid_to_png(
    mermaid_text: str,
    output_path: Path,
    timeout_sec: int = 30,
    width: int = 5000,
    scale: int = 2,
) -> dict:
    """渲染 Mermaid 文本为 PNG.

    Args:
        mermaid_text: Mermaid 图源码 (如 "graph TD; A-->B").
        output_path: 输出 PNG 路径 (调用方负责确保父目录存在 / 由本函数创建).
        timeout_sec: subprocess 超时秒数, 默认 30.
        width: Mermaid CLI render width, default 5000 for V25 readability.
        scale: Mermaid CLI render scale, default 2 for V25 readability.

    Returns:
        {
            "ok": bool,
            "path": Path | None,
            "fallback_inline": str | None,
            "reason": str,
        }
    """
    output_path = Path(output_path)

    command = _mmdc_command()
    # Layer 1: renderer CLI 不可用
    if command is None:
        return {
            "ok": False,
            "path": None,
            "fallback_inline": mermaid_text,
            "reason": "mmdc/npx not installed (see references/mmdc-install.md)",
            "render_width": width,
            "render_scale": scale,
        }

    # 落 .mmd 临时文件
    mmd_path: Optional[Path] = None
    try:
        with tempfile.NamedTemporaryFile(
            suffix=".mmd", delete=False, mode="w", encoding="utf-8"
        ) as f:
            f.write(mermaid_text)
            mmd_path = Path(f.name)

        # 确保 output_path 父目录存在
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # subprocess mmdc
        try:
            result = subprocess.run(  # nosec B603 - mmdc CLI with controlled args
                [
                    *command,
                    "-i",
                    str(mmd_path),
                    "-o",
                    str(output_path),
                    "-b",
                    "white",
                    "-w",
                    str(width),
                    "--scale",
                    str(scale),
                ],
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
                "render_width": width,
                "render_scale": scale,
            }
        except (OSError, FileNotFoundError) as e:
            return {
                "ok": False,
                "path": None,
                "fallback_inline": mermaid_text,
                "reason": f"mmdc subprocess error: {e}",
                "render_width": width,
                "render_scale": scale,
            }

        if result.returncode == 0 and output_path.exists():
            return {
                "ok": True,
                "path": output_path,
                "fallback_inline": None,
                "reason": f"{command[0]} ok",
                "render_width": width,
                "render_scale": scale,
            }

        # Layer 2: 渲染失败 (returncode 非零 或 output 文件未生成)
        return {
            "ok": False,
            "path": None,
            "fallback_inline": mermaid_text,
            "reason": f"mmdc exit {result.returncode}: {result.stderr[:500]}",
            "render_width": width,
            "render_scale": scale,
        }
    finally:
        if mmd_path is not None:
            mmd_path.unlink(missing_ok=True)
