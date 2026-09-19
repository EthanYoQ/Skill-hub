"""轻量级 JSON cache for drug registry lookups。

设计:
- 文件路径: <cache_dir>/drug_registry.json
- TTL: 默认 7 天(超时则视为过期,但仍返回作为离线 fallback)
- 不依赖 SQLite (future work)
- 不阻塞主流程: cache load 失败时静默降级为 in-memory

数据结构:
{
    "fetched_at": "2026-04-26T10:23:00Z",
    "ttl_days": 7,
    "records": {
        "<query_name_normalized>": {<DrugRecord dict>}
    }
}
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

CACHE_FILENAME = "drug_registry.json"
DEFAULT_TTL_DAYS = 7


def _normalize_key(name: str) -> str:
    """统一 cache key。大小写保留中文,英文转 lower。"""
    return name.strip().lower()


def load_cache(cache_dir: Path | None) -> dict[str, Any]:
    """读取 cache。失败 → 返回空 dict(不抛异常)。"""
    if cache_dir is None:
        return {}
    cache_path = Path(cache_dir) / CACHE_FILENAME
    if not cache_path.exists():
        return {}
    try:
        with open(cache_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def is_fresh(cache: dict[str, Any], ttl_days: int = DEFAULT_TTL_DAYS) -> bool:
    """判断 cache 是否在 TTL 内。"""
    fetched = cache.get("fetched_at")
    if not fetched:
        return False
    try:
        fetched_dt = datetime.fromisoformat(fetched.replace("Z", "+00:00"))
    except ValueError:
        return False
    return datetime.now(timezone.utc) - fetched_dt < timedelta(days=ttl_days)


def get_record(cache: dict[str, Any], name: str) -> dict | None:
    """从 cache 取记录,不存在返回 None。"""
    records = cache.get("records", {})
    return records.get(_normalize_key(name))


def save_record(cache_dir: Path | None, name: str, record_dict: dict) -> None:
    """落盘单条记录。失败静默(不阻塞主流程)。"""
    if cache_dir is None:
        return
    cache_dir = Path(cache_dir)
    try:
        cache_dir.mkdir(parents=True, exist_ok=True)
    except OSError:
        return

    cache = load_cache(cache_dir)
    if "records" not in cache:
        cache["records"] = {}
    cache["records"][_normalize_key(name)] = record_dict
    cache["fetched_at"] = datetime.now(timezone.utc).isoformat()
    cache["ttl_days"] = DEFAULT_TTL_DAYS

    cache_path = cache_dir / CACHE_FILENAME
    try:
        with open(cache_path, "w", encoding="utf-8") as f:
            json.dump(cache, f, ensure_ascii=False, indent=2)
    except OSError:
        pass
