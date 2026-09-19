"""简单的 7 天 TTL JSON 缓存。"""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


def cache_path(cache_dir: Path, filename: str) -> Path:
    cache_dir = Path(cache_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir / filename


def load_if_fresh(
    cache_dir: Path | None,
    filename: str,
    ttl_days: int = 7,
) -> dict[str, Any] | None:
    """加载缓存若未过期。"""
    if cache_dir is None:
        return None
    p = Path(cache_dir) / filename
    if not p.exists():
        return None
    try:
        raw = json.loads(p.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None
    cached_at = raw.get("_cached_at")
    if cached_at:
        try:
            ts = datetime.fromisoformat(cached_at)
        except ValueError:
            ts = None
        if ts is not None and datetime.now(timezone.utc) - ts > timedelta(
            days=ttl_days
        ):
            return None
    return raw.get("data")


def save(cache_dir: Path, filename: str, data: dict[str, Any]) -> None:
    """保存数据 + 时间戳。"""
    p = cache_path(cache_dir, filename)
    payload = {
        "_cached_at": datetime.now(timezone.utc).isoformat(),
        "data": data,
    }
    p.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
