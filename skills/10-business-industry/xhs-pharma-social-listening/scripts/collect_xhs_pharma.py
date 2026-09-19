#!/usr/bin/env python
"""Collect Xiaohongshu pharma social-listening evidence via OpenCLI.

The collector is intentionally append-only and resumable. It writes JSONL files
after every successful command so a long run can be stopped and resumed without
losing completed work.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import math
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError as exc:  # pragma: no cover
    raise SystemExit("PyYAML is required. Install with: python -m pip install pyyaml") from exc


DEFAULT_QUERIES = [
    "外资药企",
    "药企打工人",
    "外企医药代表",
    "医药代表 外企",
    "药代 外企",
    "药企 裁员",
    "药企 离职",
    "药企 待遇",
    "药企 奖金",
    "药企 面试",
    "药企 内推",
    "药企 PIP",
    "医药代表 KPI",
    "医药代表 合规",
    "药企 合规",
    "药企 会议 新规",
    "药企 报销",
    "药企 垫付",
    "医学部 AI 药企",
    "药企 AI",
    "药代 AI",
    "MSL 药企",
    "MA MSL 药企",
    "医学部 药企",
    "CRA 药企 AI",
    "RWE 药企",
    "药企 数据 AI",
    "药企 临床 数据",
    "药企 市场部 mkt",
    "外企 mkt 药企",
    "诺华 药企",
    "N司 药企",
    "诺和诺德 药企",
    "NN司 药企",
    "辉瑞 P司",
    "P司 药企",
    "礼来 药企",
    "LL司 药企",
    "L司 药企",
    "阿斯利康 AZ 药企",
    "AZ 药企",
    "罗氏 R司",
    "R司 药企",
    "赛诺菲 S司",
    "S司 药企",
    "默沙东 药企",
    "M司 药企",
    "强生 J司 药企",
    "GSK 药企",
    "武田 T司 药企",
    "拜耳 药企",
    "B司 药企",
    "安进 药企",
    "艾伯维 药企",
    "百时美施贵宝 药企",
    "BMS 药企",
    "吉利德 药企",
    "P司 裁员",
    "N司 裁员",
    "NN司 裁员",
    "LL司 裁员",
    "AZ 合规",
    "AZ 会议",
    "R司 大瓜",
    "R司 裁员",
    "S司 裁员",
    "外资药企 裁员",
    "外资药企 合规",
]


def now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).astimezone().isoformat(timespec="seconds")


RATE_BLOCK_TERMS = [
    "Requests too frequent",
    "Try again later",
    "访问过于频繁",
    "请求过于频繁",
    "操作频繁",
]


def is_rate_block(*texts: str) -> bool:
    joined = "\n".join(texts)
    return any(term in joined for term in RATE_BLOCK_TERMS)


def parse_iso_datetime(value: Any) -> dt.datetime | None:
    if not value:
        return None
    try:
        parsed = dt.datetime.fromisoformat(str(value))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.astimezone()
    return parsed


def cooldown_marker_paths(out_dir: Path) -> list[Path]:
    return list(dict.fromkeys([
        Path.cwd() / "xhs_cooldown_until.json",
        out_dir / "xhs_cooldown_until.json",
        out_dir.parent / "xhs_cooldown_until.json",
        Path.home() / ".agent-reach" / "xhs_cooldown_until.json",
    ]))


def active_cooldown(out_dir: Path) -> dict[str, Any] | None:
    now = dt.datetime.now(dt.timezone.utc).astimezone()
    for path in cooldown_marker_paths(out_dir):
        if not path.exists():
            continue
        try:
            marker = json.loads(path.read_text(encoding="utf-8-sig"))
        except json.JSONDecodeError:
            continue
        until = parse_iso_datetime(marker.get("cooldown_until"))
        if until and until > now:
            marker["_path"] = str(path)
            return marker
    return None


def ensure_not_cooling(out_dir: Path) -> None:
    marker = active_cooldown(out_dir)
    if not marker:
        return
    raise SystemExit(
        "Xiaohongshu collection is cooling down until "
        f"{marker.get('cooldown_until')} because: {marker.get('reason')} "
        f"(marker: {marker.get('_path')})"
    )


def write_cooldown_marker(out_dir: Path, reason: str, source: str, hours: int = 3) -> None:
    now = dt.datetime.now(dt.timezone.utc).astimezone()
    marker = {
        "platform": "xiaohongshu",
        "reason": reason,
        "observed_at": now.isoformat(timespec="seconds"),
        "cooldown_until": (now + dt.timedelta(hours=hours)).isoformat(timespec="seconds"),
        "minimum_cooldown_hours": hours,
        "source": source,
    }
    for path in [Path.cwd() / "xhs_cooldown_until.json", out_dir / "xhs_cooldown_until.json"]:
        path.write_text(json.dumps(marker, ensure_ascii=False, indent=2), encoding="utf-8")


def append_jsonl(path: Path, row: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def note_id_from_url(url: str) -> str:
    match = re.search(r"/(?:search_result|explore)/([^?/#]+)", url or "")
    if match:
        return match.group(1)
    return re.sub(r"\W+", "_", url or "")[:80]


def parse_count(value: Any) -> int:
    if value is None:
        return 0
    if isinstance(value, (int, float)):
        return int(value)
    text = str(value).strip().replace(",", "")
    if not text:
        return 0
    mult = 1
    if text.endswith("万"):
        mult = 10000
        text = text[:-1]
    elif text.endswith("k") or text.endswith("K"):
        mult = 1000
        text = text[:-1]
    try:
        return int(float(text) * mult)
    except ValueError:
        digits = re.findall(r"\d+", text)
        return int(digits[0]) if digits else 0


def resolve_opencli_prefix() -> list[str]:
    npm_root = Path.home() / "AppData" / "Roaming" / "npm"
    main_js = npm_root / "node_modules" / "@jackwener" / "opencli" / "dist" / "src" / "main.js"
    node = shutil.which("node")
    if main_js.exists() and node:
        return [node, str(main_js)]
    for name in ("opencli.exe", "opencli"):
        found = shutil.which(name)
        if found:
            return [found]
    npm_cmd = npm_root / "opencli.cmd"
    if npm_cmd.exists():
        return [str(npm_cmd)]
    return ["opencli"]


def run_opencli(args: list[str], timeout: int, site_session: str, window: str) -> tuple[int, str, str]:
    cmd = [
        *resolve_opencli_prefix(),
        "xiaohongshu",
        *args,
        "--site-session",
        site_session,
        "--window",
        window,
        "-f",
        "yaml",
    ]
    proc = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
    )
    return proc.returncode, proc.stdout, proc.stderr


def parse_yaml_list(stdout: str) -> list[dict[str, Any]]:
    if not stdout.strip():
        return []
    loaded = yaml.safe_load(stdout)
    if loaded is None:
        return []
    if isinstance(loaded, list):
        return [row for row in loaded if isinstance(row, dict)]
    if isinstance(loaded, dict):
        return [loaded]
    return []


def parse_note_detail(rows: list[dict[str, Any]]) -> dict[str, Any]:
    detail: dict[str, Any] = {}
    for row in rows:
        if "field" in row:
            detail[str(row.get("field"))] = row.get("value")
        else:
            detail.update(row)
    return detail


def load_queries(args: argparse.Namespace) -> list[str]:
    if args.queries_file:
        path = Path(args.queries_file)
        queries = [line.strip() for line in path.read_text(encoding="utf-8").splitlines()]
        queries = [q for q in queries if q and not q.startswith("#")]
    else:
        queries = list(DEFAULT_QUERIES)
    if args.extra_query:
        queries.extend(args.extra_query)
    deduped: list[str] = []
    seen: set[str] = set()
    for query in queries:
        if query not in seen:
            deduped.append(query)
            seen.add(query)
    return deduped[: args.max_queries] if args.max_queries else deduped


def count_items(out_dir: Path) -> dict[str, int]:
    return {
        "search_results": len(read_jsonl(out_dir / "search_results.jsonl")),
        "note_details": len(read_jsonl(out_dir / "note_details.jsonl")),
        "comments": len(read_jsonl(out_dir / "comments.jsonl")),
        "errors": len(read_jsonl(out_dir / "errors.jsonl")),
    }


def comment_key(row: dict[str, Any]) -> str:
    if row.get("comment_id"):
        return str(row["comment_id"])
    return "|".join([
        str(row.get("note_id") or ""),
        str(row.get("userId") or row.get("author") or ""),
        str(row.get("time") or ""),
        str(row.get("text") or "")[:160],
    ])


def dedup_counts(out_dir: Path) -> dict[str, int]:
    search_rows = read_jsonl(out_dir / "search_results.jsonl")
    detail_rows = read_jsonl(out_dir / "note_details.jsonl")
    comment_rows = read_jsonl(out_dir / "comments.jsonl")
    unique_notes = {
        str(row.get("note_id") or row.get("url") or "")
        for row in search_rows + detail_rows
        if row.get("note_id") or row.get("url")
    }
    unique_comments = {
        comment_key(row)
        for row in comment_rows
        if comment_key(row)
    }
    return {
        "unique_notes": len(unique_notes),
        "unique_comments": len(unique_comments),
        "dedup_raw_items": len(unique_notes) + len(unique_comments),
    }


def target_reached(out_dir: Path, target: int) -> bool:
    return dedup_counts(out_dir)["dedup_raw_items"] >= target


def search_queries(args: argparse.Namespace, out_dir: Path, queries: list[str]) -> None:
    completed = {row.get("query") for row in read_jsonl(out_dir / "search_runs.jsonl")}
    for idx, query in enumerate(queries, start=1):
        ensure_not_cooling(out_dir)
        if args.resume and query in completed:
            continue
        print(f"[search {idx}/{len(queries)}] {query}", flush=True)
        started = now_iso()
        try:
            code, stdout, stderr = run_opencli(["search", query, "--limit", str(args.search_limit)], args.timeout, args.site_session, args.window)
            if is_rate_block(stdout, stderr):
                write_cooldown_marker(out_dir, "Requests too frequent / frequency block detected in OpenCLI search output.", f"search query: {query}")
                append_jsonl(out_dir / "errors.jsonl", {
                    "stage": "search",
                    "query": query,
                    "returncode": code,
                    "stderr": stderr,
                    "stdout": stdout[:1000],
                    "rate_block": True,
                    "time": now_iso(),
                })
                raise SystemExit("Xiaohongshu frequency block detected; cooling down for at least 3 hours.")
            rows = parse_yaml_list(stdout) if code == 0 else []
            if code != 0:
                append_jsonl(out_dir / "errors.jsonl", {
                    "stage": "search",
                    "query": query,
                    "returncode": code,
                    "stderr": stderr,
                    "time": now_iso(),
                })
            for row in rows:
                url = str(row.get("url") or "")
                record = {
                    "query": query,
                    "note_id": note_id_from_url(url),
                    "url": url,
                    "title": row.get("title"),
                    "author": row.get("author"),
                    "author_url": row.get("author_url"),
                    "likes": parse_count(row.get("likes")),
                    "published_at": row.get("published_at"),
                    "rank": row.get("rank"),
                    "collected_at": now_iso(),
                }
                append_jsonl(out_dir / "search_results.jsonl", record)
            append_jsonl(out_dir / "search_runs.jsonl", {
                "query": query,
                "started_at": started,
                "finished_at": now_iso(),
                "returncode": code,
                "rows": len(rows),
            })
        except Exception as exc:  # pragma: no cover
            append_jsonl(out_dir / "errors.jsonl", {
                "stage": "search",
                "query": query,
                "error": repr(exc),
                "time": now_iso(),
            })
        time.sleep(args.sleep)
        if args.stop_after_search_target and target_reached(out_dir, args.target_items):
            break


def choose_notes_for_detail(out_dir: Path, max_notes: int) -> list[dict[str, Any]]:
    rows = read_jsonl(out_dir / "search_results.jsonl")
    by_id: dict[str, dict[str, Any]] = {}
    for row in rows:
        note_id = str(row.get("note_id") or "")
        if not note_id:
            continue
        existing = by_id.get(note_id)
        if existing is None:
            row = dict(row)
            row["queries"] = [row.get("query")]
            by_id[note_id] = row
        else:
            existing["likes"] = max(parse_count(existing.get("likes")), parse_count(row.get("likes")))
            existing.setdefault("queries", [])
            if row.get("query") not in existing["queries"]:
                existing["queries"].append(row.get("query"))
    notes = list(by_id.values())
    notes.sort(key=lambda r: (len(r.get("queries") or []), parse_count(r.get("likes"))), reverse=True)
    return notes[:max_notes]


def fetch_details_and_comments(args: argparse.Namespace, out_dir: Path) -> None:
    detailed = {row.get("note_id") for row in read_jsonl(out_dir / "note_details.jsonl")}
    commented = {row.get("note_id") for row in read_jsonl(out_dir / "comment_runs.jsonl") if row.get("returncode") == 0}
    notes = choose_notes_for_detail(out_dir, args.max_notes)
    for idx, note in enumerate(notes, start=1):
        ensure_not_cooling(out_dir)
        note_id = note.get("note_id")
        url = note.get("url")
        if not url:
            continue
        if note_id not in detailed:
            print(f"[note {idx}/{len(notes)}] {note.get('title')}", flush=True)
            try:
                code, stdout, stderr = run_opencli(["note", str(url)], args.timeout, args.site_session, args.window)
                if is_rate_block(stdout, stderr):
                    write_cooldown_marker(out_dir, "Requests too frequent / frequency block detected in OpenCLI note output.", f"note url: {url}")
                    append_jsonl(out_dir / "errors.jsonl", {
                        "stage": "note",
                        "note_id": note_id,
                        "url": url,
                        "returncode": code,
                        "stderr": stderr,
                        "stdout": stdout[:1000],
                        "rate_block": True,
                        "time": now_iso(),
                    })
                    raise SystemExit("Xiaohongshu frequency block detected; cooling down for at least 3 hours.")
                rows = parse_yaml_list(stdout) if code == 0 else []
                detail = parse_note_detail(rows)
                if code == 0 and detail:
                    append_jsonl(out_dir / "note_details.jsonl", {
                        "note_id": note_id,
                        "url": url,
                        "queries": note.get("queries"),
                        "search_title": note.get("title"),
                        "search_author": note.get("author"),
                        "search_likes": note.get("likes"),
                        "detail": detail,
                        "collected_at": now_iso(),
                    })
                    detailed.add(note_id)
                else:
                    append_jsonl(out_dir / "errors.jsonl", {
                        "stage": "note",
                        "note_id": note_id,
                        "url": url,
                        "returncode": code,
                        "stderr": stderr,
                        "time": now_iso(),
                    })
            except Exception as exc:  # pragma: no cover
                append_jsonl(out_dir / "errors.jsonl", {
                    "stage": "note",
                    "note_id": note_id,
                    "url": url,
                    "error": repr(exc),
                    "time": now_iso(),
                })
            time.sleep(args.sleep)
        if args.stop_after_note_target and target_reached(out_dir, args.target_items):
            break
        if note_id not in commented:
            print(f"[comments {idx}/{len(notes)}] {note.get('title')}", flush=True)
            try:
                code, stdout, stderr = run_opencli(
                    ["comments", str(url), "--limit", str(args.comment_limit), "--with-replies", "true"],
                    args.timeout,
                    args.site_session,
                    args.window,
                )
                if is_rate_block(stdout, stderr):
                    write_cooldown_marker(out_dir, "Requests too frequent / frequency block detected in OpenCLI comments output.", f"comments url: {url}")
                    append_jsonl(out_dir / "errors.jsonl", {
                        "stage": "comments",
                        "note_id": note_id,
                        "url": url,
                        "returncode": code,
                        "stderr": stderr,
                        "stdout": stdout[:1000],
                        "rate_block": True,
                        "time": now_iso(),
                    })
                    raise SystemExit("Xiaohongshu frequency block detected; cooling down for at least 3 hours.")
                rows = parse_yaml_list(stdout) if code == 0 else []
                for row in rows:
                    record = dict(row)
                    record.update({
                        "note_id": note_id,
                        "note_url": url,
                        "note_title": note.get("title"),
                        "query_hits": note.get("queries"),
                        "likes": parse_count(record.get("likes")),
                        "collected_at": now_iso(),
                    })
                    append_jsonl(out_dir / "comments.jsonl", record)
                append_jsonl(out_dir / "comment_runs.jsonl", {
                    "note_id": note_id,
                    "url": url,
                    "returncode": code,
                    "rows": len(rows),
                    "time": now_iso(),
                })
                if code != 0:
                    append_jsonl(out_dir / "errors.jsonl", {
                        "stage": "comments",
                        "note_id": note_id,
                        "url": url,
                        "returncode": code,
                        "stderr": stderr,
                        "time": now_iso(),
                    })
            except Exception as exc:  # pragma: no cover
                append_jsonl(out_dir / "errors.jsonl", {
                    "stage": "comments",
                    "note_id": note_id,
                    "url": url,
                    "error": repr(exc),
                    "time": now_iso(),
                })
            time.sleep(args.sleep)
        if target_reached(out_dir, args.target_items):
            break


def write_meta(args: argparse.Namespace, out_dir: Path, queries: list[str]) -> None:
    search_rows = read_jsonl(out_dir / "search_results.jsonl")
    unique_note_ids = {row.get("note_id") for row in search_rows if row.get("note_id")}
    counts = count_items(out_dir)
    dedup = dedup_counts(out_dir)
    meta = {
        "created_at": now_iso(),
        "output_dir": str(out_dir),
        "queries_attempted": len(read_jsonl(out_dir / "search_runs.jsonl")),
        "queries_configured": len(queries),
        "unique_search_notes": len(unique_note_ids),
        "counts": counts,
        "raw_item_count": counts["search_results"] + counts["note_details"] + counts["comments"],
        "dedup_counts": dedup,
        "dedup_counting_rule": "unique notes by note_id/url plus unique comments by comment_id or note_id+user/time/text prefix; note detail rows are not counted as separate evidence items.",
        "args": vars(args),
    }
    (out_dir / "run_meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(meta, ensure_ascii=False, indent=2), flush=True)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--target-items", type=int, default=1200)
    parser.add_argument("--queries-file")
    parser.add_argument("--extra-query", action="append", default=[])
    parser.add_argument("--max-queries", type=int, default=40)
    parser.add_argument("--search-limit", type=int, default=20)
    parser.add_argument("--max-notes", type=int, default=80)
    parser.add_argument("--comment-limit", type=int, default=30)
    parser.add_argument("--sleep", type=float, default=2.5)
    parser.add_argument("--timeout", type=int, default=120)
    parser.add_argument("--site-session", choices=["ephemeral", "persistent"], default="ephemeral")
    parser.add_argument("--window", choices=["foreground", "background"], default="foreground")
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--stop-after-search-target", action="store_true", help="Allow stopping during search if the deduplicated target is reached.")
    parser.add_argument("--stop-after-note-target", action="store_true", help="Allow stopping after note detail fetch if the deduplicated target is reached.")
    args = parser.parse_args()

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    ensure_not_cooling(out_dir)
    queries = load_queries(args)
    write_meta(args, out_dir, queries)
    if not target_reached(out_dir, args.target_items):
        search_queries(args, out_dir, queries)
    if not target_reached(out_dir, args.target_items):
        fetch_details_and_comments(args, out_dir)
    write_meta(args, out_dir, queries)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
