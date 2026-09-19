# BioMCP 集成: fast-path 检测 + 配置 + 兜底

> 本文档由 `medical-evidence-grading/SKILL.md` 引用。`evidence_search()` 在启动时调用此处的检测逻辑决定 fast/slow path。

## BioMCP 是什么

[genomoncology/biomcp](https://github.com/genomoncology/biomcp) 是 MCP server,一次性 fan-out 到:
- PubMed (NCBI E-utilities)
- Europe PMC RESTful API
- ClinicalTrials.gov v2 API
- PubTator3
- BioC fulltext

暴露的 MCP 工具:
- `mcp__biomcp__article_searcher(query, ...)` — 文献多源检索
- `mcp__biomcp__trial_searcher(condition, ...)` — 临床试验检索
- `mcp__biomcp__variant_searcher(gene, ...)` — 基因变异检索
- `mcp__biomcp__article_details(pmid)` — 单文献完整元数据

## 检测逻辑

```python
def detect_biomcp_available() -> bool:
    """
    三路检测,任一命中返回 True:
    1. 环境变量 BIOMCP_ENDPOINT 存在
    2. 配置文件含 'biomcp' 字符串
    3. 已加载工具列表含 mcp__biomcp__* 工具
    """
    import os
    from pathlib import Path

    # Path 1: env var
    if os.environ.get("BIOMCP_ENDPOINT"):
        return True

    # Path 2: config files (跨平台)
    candidate_paths = [
        Path.home() / ".claude" / "mcp.json",
        Path.home() / ".claude" / "settings.json",
        Path.home() / ".claude.json",
        Path.home() / ".codex" / "config.toml",
        Path.home() / ".gemini" / "settings.json",
    ]
    for cfg in candidate_paths:
        if cfg.exists():
            try:
                text = cfg.read_text(encoding="utf-8")
                if "biomcp" in text.lower():
                    return True
            except (UnicodeDecodeError, PermissionError):
                continue

    # Path 3: 运行时工具反射
    # (在 Claude Code 内由调用方注入 available_tools 列表)
    available_tools = globals().get("AVAILABLE_TOOLS", [])
    if any(t.startswith("mcp__biomcp__") for t in available_tools):
        return True

    return False
```

## fast-path 调用流程

```python
async def biomcp_fast_path(query: str, max_results: int = 200) -> list[dict]:
    # 1. 一次调用,获取 PubMed + EuropePMC + PubTator 联合结果
    raw = await mcp__biomcp__article_searcher(
        query=query,
        page_size=max_results,
        include_preprints=False,  # 由上层 evidence_search 参数控制
    )
    # 2. BioMCP 已做 PMID/DOI 去重,无需自建
    # 3. 但 publication_type 可能不全 → 必要时用 article_details 补全
    incomplete = [r for r in raw if not r.get("publication_types")]
    if incomplete:
        details = await asyncio.gather(*[
            mcp__biomcp__article_details(pmid=r["pmid"])
            for r in incomplete[:50]  # 限速保护
        ])
        # 合并 publication_types 字段
        ...
    return raw
```

## fall-back 触发条件

满足以下任一条件,从 fast-path 静默回退到 slow-path:

1. `mcp__biomcp__article_searcher` 调用抛出 `MCPServerError`
2. 返回结果数 < `max_results * 0.3` (显著少于预期)
3. 返回结果中 publication_types 缺失率 > 50% 且 article_details 重试也失败
4. 单次调用延迟 > 30s (BioMCP server 可能宕机)

```python
async def evidence_search_with_fallback(query, max_results, ...):
    if detect_biomcp_available():
        try:
            results = await asyncio.wait_for(
                biomcp_fast_path(query, max_results),
                timeout=30,
            )
            if len(results) >= max_results * 0.3:
                return results, {"path": "biomcp", "fallback": False}
            # 否则继续走 slow
        except (TimeoutError, MCPServerError, Exception) as e:
            log.warning(f"BioMCP failed: {e}, falling back to slow-path")

    return await slow_path_fanout(query, max_results), {"path": "slow", "fallback": True}
```

## slow-path 自建 fan-out

当 BioMCP 不可用,本 skill 自己并发调底层原子 skill:

```python
async def slow_path_fanout(query: str, max_results: int) -> list[dict]:
    # Phase 1: 并发拉 ID 列表
    pubmed_task = pubmed_eutils.esearch_pubmed(query, retmax=max_results)
    europepmc_task = europepmc_search.search_articles(query, page_size=max_results)
    trials_task = clinical_trials_v2.search_studies(condition=query, max_studies=50)

    pmids, epmc_hits, trials = await asyncio.gather(
        pubmed_task, europepmc_task, trials_task
    )

    # Phase 2: 三段去重 (PMID > PMCID > DOI)
    merged = deduplicate(
        pubmed_hits=pmids,
        epmc_hits=epmc_hits,
        trials=trials,
        priority=["pmid", "pmcid", "doi"],
    )

    # Phase 3: 拿 publication_type (efetch 批量)
    pmid_chunks = [list(merged.keys())[i:i+200] for i in range(0, len(merged), 200)]
    pub_types = []
    for chunk in pmid_chunks:
        pub_types.extend(await pubmed_eutils.efetch_pubmed(chunk, rettype="xml"))

    # Phase 4: 对疑似 RCT/Cohort 抽样本量 (可选)
    # 见 grade-rules.md 样本量提取规则

    return merged
```

## 性能对比

| 模式 | 100 条文献延迟 | API 调用数 | 缓存命中后 |
|------|---------------|-----------|-----------|
| Fast-path (BioMCP) | ~3-5s | 1 | <500ms |
| Slow-path (自建) | ~15-25s | 6-10 | <500ms |

## 常见配置

### Claude Code (`~/.claude/mcp.json`)
```json
{
  "mcpServers": {
    "biomcp": {
      "command": "uvx",
      "args": ["biomcp"],
      "env": {}
    }
  }
}
```

### Codex (`~/.codex/config.toml`)
```toml
[mcp_servers.biomcp]
command = "uvx"
args = ["biomcp"]
```

### 环境变量(任何平台)
```bash
export BIOMCP_ENDPOINT=http://localhost:8765
```
