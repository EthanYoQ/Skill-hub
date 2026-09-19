# 缓存层 Schema + TTL 策略

> 本文档由 `medical-evidence-grading/SKILL.md` 引用。所有缓存细节在此。

## 路径

```
~/.claude/skills/medical-evidence-grading/cache.sqlite
```

跨平台等价路径(由代码用 `Path.home()` 自动解析):
- macOS / Linux: `/home/<user>/.claude/skills/medical-evidence-grading/cache.sqlite`
- Windows: `C:\Users\<user>\.claude\skills\medical-evidence-grading\cache.sqlite`
- Codex: `$CODEX_HOME/skills/medical-evidence-grading/cache.sqlite`

## 表结构

### evidence_cache (查询级缓存,7 天 TTL)

```sql
CREATE TABLE IF NOT EXISTS evidence_cache (
    query_hash TEXT PRIMARY KEY,        -- SHA256(query + target_grade + date_range + include_preprints)
    query_text TEXT NOT NULL,
    target_grade TEXT,
    date_range TEXT,
    result_json TEXT NOT NULL,          -- 完整 evidence_search 返回值
    created_at TIMESTAMP NOT NULL,
    expires_at TIMESTAMP NOT NULL,      -- created_at + 7 days
    fast_path_used BOOLEAN,
    total_results INTEGER,
    grade_rule_version TEXT             -- 命中后用于检测规则更新
);

CREATE INDEX idx_evidence_expires ON evidence_cache(expires_at);
```

### pmid_grade_cache (PMID 级缓存,30 天 TTL)

```sql
CREATE TABLE IF NOT EXISTS pmid_grade_cache (
    pmid TEXT PRIMARY KEY,
    pmcid TEXT,
    doi TEXT,
    publication_types TEXT,             -- JSON array
    sample_size INTEGER,                -- 可空
    journal TEXT,
    year INTEGER,
    is_preprint BOOLEAN DEFAULT 0,
    grade TEXT NOT NULL,                -- A / B / C / D / D- / excluded
    grade_rationale TEXT,
    grade_rule_version TEXT NOT NULL,   -- 例如 "v1.0.0"
    inferred BOOLEAN DEFAULT 0,         -- 是否启发式推断
    cached_at TIMESTAMP NOT NULL,
    expires_at TIMESTAMP NOT NULL       -- cached_at + 30 days
);

CREATE INDEX idx_pmid_grade_expires ON pmid_grade_cache(expires_at);
CREATE INDEX idx_pmid_grade_rule ON pmid_grade_cache(grade_rule_version);
```

### query_log (审计日志)

```sql
CREATE TABLE IF NOT EXISTS query_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    query_text TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    path_used TEXT,                     -- 'biomcp' | 'slow' | 'cache'
    elapsed_seconds REAL,
    total_results INTEGER,
    fallback_reason TEXT
);
```

## TTL 策略说明

| 缓存类型 | TTL | 理由 |
|---------|-----|------|
| evidence_cache (查询级) | 7 天 | 文献世界更新有滞后,7 天足以覆盖新指南/新 RCT 的发布 |
| pmid_grade_cache (PMID 级) | 30 天 | publication_type MeSH 索引一旦建立基本不变;只有撤稿/勘误才变 |
| query_log | 永久(可手动 vacuum) | 审计与调试需要 |

## 命中检测逻辑

```python
def check_cache(query_hash: str) -> dict | None:
    cur = conn.execute("""
        SELECT result_json, grade_rule_version
        FROM evidence_cache
        WHERE query_hash = ?
          AND expires_at > datetime('now')
    """, (query_hash,))
    row = cur.fetchone()
    if not row:
        return None

    cached_version, current_version = row[1], GRADE_RULE_VERSION
    if cached_version != current_version:
        # 规则更新过,缓存作废,但不立即删 — 标记 stale,首次请求重算并刷新
        return None

    return json.loads(row[0])
```

## 关键不变量(确保缓存正确性)

1. **GRADE 规则版本变更 → 强制重算**: 改了 `grade-rules.md` 必须 bump `GRADE_RULE_VERSION`;否则旧缓存的 grade 字段可能与新规则不一致。
2. **缓存损坏自愈**: 任何 `sqlite3.DatabaseError` 触发自动重建(drop & recreate),保留 `query_log`。
3. **不缓存负面结果**: `evidence_search` 返回 0 条不写缓存(避免某次 NCBI 限流被永久记录为"无结果")。
4. **过期清理**: 启动时自动 `DELETE FROM ... WHERE expires_at < datetime('now')`。

## 性能预期

- 查询级命中: <500ms (SQLite 单查询 + JSON 反序列化)
- PMID 级命中(批量 100 条): <800ms
- 完全 miss + slow-path: 15-25s
- 加速比: 命中时 30-50x

## 缓存维护命令

```python
def cache_stats() -> dict:
    return {
        "evidence_cache_count": conn.execute("SELECT COUNT(*) FROM evidence_cache").fetchone()[0],
        "pmid_grade_cache_count": conn.execute("SELECT COUNT(*) FROM pmid_grade_cache").fetchone()[0],
        "db_size_mb": Path(CACHE_DB).stat().st_size / 1024 / 1024,
        "oldest_entry": conn.execute("SELECT MIN(created_at) FROM evidence_cache").fetchone()[0],
    }

def cache_purge_expired():
    conn.execute("DELETE FROM evidence_cache WHERE expires_at < datetime('now')")
    conn.execute("DELETE FROM pmid_grade_cache WHERE expires_at < datetime('now')")
    conn.execute("VACUUM")

def cache_invalidate_by_rule_bump(new_version: str):
    """手动调用,当 grade-rules.md 更新后触发重算"""
    conn.execute(
        "DELETE FROM pmid_grade_cache WHERE grade_rule_version != ?",
        (new_version,)
    )
```
