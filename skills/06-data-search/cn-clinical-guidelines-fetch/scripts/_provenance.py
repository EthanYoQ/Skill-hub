"""Stage 3.1b 强约束级 provenance helper · 2026-04-27 architect af265bdc 修订 2.

P0 第 3 条铁律守门:抓到的指南/文献等源材料必须完整保存,可追溯。

本模块功能:
- compute_and_write_provenance: 把 raw HTTP response (bytes) 写盘到 _raw/<doc_id>,
  计算 sha256 checksum,返回 provenance dict (fetched_at + endpoint + raw_path + checksum)
- read_provenance: 从已存档的 provenance.json 反读 (verifier Tier 0 用)

provenance schema (统一格式,与 docs/RETRIEVAL_PROVENANCE_CONTRACT.md 一致):

    {
        "fetched_at": "ISO8601 UTC, e.g. 2026-04-27T10:23:00Z",
        "endpoint":   "原始 HTTP URL (含 query params)",
        "raw_path":   "_raw/guidelines/CSCO-2024-NSCLC.html",   # 相对 sources_dir/
        "checksum":   "sha256:abc123def456..."                  # SHA-256 of raw bytes
    }

verifier (`content-verification-layer`) Tier 0 check 拿 raw_path / checksum 校验源真实存在。
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _now_iso8601_utc() -> str:
    """ISO8601 UTC timestamp, 'Z' suffix not '+00:00' (verifier expects this format)."""
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def compute_and_write_provenance(
    content: bytes,
    raw_dir: Path,
    doc_id: str,
    endpoint: str,
    extension: str = "html",
    sources_dir: Path | None = None,
) -> dict[str, Any]:
    """Write raw bytes to `raw_dir/<doc_id>.<extension>` and return provenance dict.

    Args:
        content: Raw HTTP response bytes (or text encoded utf-8).
        raw_dir: Absolute path to write the raw file (e.g. sources_dir / "_raw" / "guidelines").
        doc_id: Document identifier (e.g. "CSCO-2024-NSCLC").
        endpoint: Original HTTP URL with query params.
        extension: File extension for the raw artifact (default "html"; use "xml"/"json"/"pdf" as appropriate).
        sources_dir: If provided, raw_path in returned dict is relative to this dir.
            Otherwise raw_path is the absolute string.

    Returns:
        Provenance dict with keys: fetched_at, endpoint, raw_path, checksum.

    Side effect:
        Writes content to raw_dir/<doc_id>.<extension>. Creates raw_dir if missing.
    """
    raw_dir = Path(raw_dir)
    raw_dir.mkdir(parents=True, exist_ok=True)

    raw_filename = f"{doc_id}.{extension}"
    raw_full_path = raw_dir / raw_filename
    raw_full_path.write_bytes(content)

    sha = hashlib.sha256(content).hexdigest()

    if sources_dir is not None:
        try:
            raw_path_rel = str(raw_full_path.relative_to(Path(sources_dir))).replace("\\", "/")
        except ValueError:
            # raw_dir 不在 sources_dir 子树下 — fallback 到绝对路径
            raw_path_rel = str(raw_full_path).replace("\\", "/")
    else:
        raw_path_rel = str(raw_full_path).replace("\\", "/")

    return {
        "fetched_at": _now_iso8601_utc(),
        "endpoint": endpoint,
        "raw_path": raw_path_rel,
        "checksum": f"sha256:{sha}",
    }


def write_provenance_json(provenance: dict[str, Any], target_path: Path) -> None:
    """Write provenance dict to JSON file at target_path."""
    target_path = Path(target_path)
    target_path.parent.mkdir(parents=True, exist_ok=True)
    target_path.write_text(
        json.dumps(provenance, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def read_provenance_json(provenance_path: Path) -> dict[str, Any] | None:
    """Read provenance JSON file. Returns None if file missing or unparseable."""
    provenance_path = Path(provenance_path)
    if not provenance_path.is_file():
        return None
    try:
        return json.loads(provenance_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def verify_checksum(raw_full_path: Path, expected_checksum: str) -> bool:
    """Verify sha256 of file matches expected checksum string ('sha256:abc...')."""
    raw_full_path = Path(raw_full_path)
    if not raw_full_path.is_file():
        return False
    if not expected_checksum.startswith("sha256:"):
        return False
    expected_hex = expected_checksum[len("sha256:") :]
    actual_hex = hashlib.sha256(raw_full_path.read_bytes()).hexdigest()
    return actual_hex == expected_hex


def attach_provenance_to_guideline(
    guideline_data: dict[str, Any],
    raw_text: str,
    sources_dir: Path,
    source_id: str,
    endpoint: str,
) -> dict[str, Any]:
    """Convenience wrapper: attach provenance to a guideline data dict.

    Pattern usage in `_csco.py` / `_nccn.py` / `_cde.py` after raw_text is loaded/fetched:

        from _provenance import attach_provenance_to_guideline

        data = {"version": "2024", "source_id": source_id, "raw_text": raw_text, ...}
        if sources_dir is not None:
            data = attach_provenance_to_guideline(
                data, raw_text, sources_dir, source_id,
                endpoint="https://www.csco.org.cn/guidelines/2024-NSCLC.pdf",
            )
        return data
    """
    raw_dir = Path(sources_dir) / "_raw" / "guidelines"
    provenance = compute_and_write_provenance(
        content=raw_text.encode("utf-8"),
        raw_dir=raw_dir,
        doc_id=source_id,
        endpoint=endpoint,
        extension="raw.txt",
        sources_dir=sources_dir,
    )

    # Also write sidecar provenance.json next to the guideline raw text
    sidecar_path = Path(sources_dir) / "guidelines" / f"{source_id}.provenance.json"
    write_provenance_json(provenance, sidecar_path)

    out = dict(guideline_data)
    out["provenance"] = provenance
    return out
