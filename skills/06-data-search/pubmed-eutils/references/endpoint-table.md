# NCBI E-utilities Endpoint 速查表

主 SKILL.md 的扩展参考。完整 endpoint 行为 / 参数 / 速率细节。

## Endpoint 总览

| Endpoint   | 方法     | 用途                          | 推荐批量 | 速率(有 key) | 备注                       |
|------------|----------|-------------------------------|----------|--------------|----------------------------|
| esearch    | GET/POST | 检索 → PMID 列表 + WebEnv     | 单次     | 10 RPS       | 长 query 用 POST           |
| efetch     | GET/POST | 取摘要 + MeSH(XML)            | 200/批   | 10 RPS       | rettype=abstract retmode=xml |
| esummary   | GET      | 取轻量元数据(JSON/XML)        | 200/批   | 10 RPS       | 比 efetch 快 5-10x         |
| elink      | GET      | PMID ↔ PMCID / cited-in / refs| 200/批   | 10 RPS       | dbfrom=pubmed db=pmc       |
| einfo      | GET      | 字段/索引/MeSH 元信息          | 单次     | 10 RPS       | 调试 MeSH 用               |
| egquery    | GET      | 跨 NCBI 数据库全局查询         | 单次     | 10 RPS       | 不常用                     |
| espell     | GET      | 拼写建议                       | 单次     | 10 RPS       | 不常用                     |

## elink dbfrom/db 常用组合

| dbfrom  | db          | linkname                  | 用途                          |
|---------|-------------|---------------------------|-------------------------------|
| pubmed  | pmc         | pubmed_pmc                | PMID → PMCID(全文映射)        |
| pubmed  | pubmed      | pubmed_pubmed_citedin     | 被引文献                      |
| pubmed  | pubmed      | pubmed_pubmed_refs        | 参考文献                      |
| pubmed  | pubmed      | pubmed_pubmed             | 相似文献                      |
| pubmed  | mesh        | pubmed_mesh_major         | 主要 MeSH 词                  |

## 速率限制官方说明

| 模式      | RPS | 单批 PMID 上限 | 超时 |
|-----------|-----|----------------|------|
| 有 API key | 10  | 200            | 30s  |
| 无 key     | 3   | 200            | 30s  |

实现要求：
- 用令牌桶限流（`asyncio.Semaphore` 或 `aiolimiter`）
- 429/503 → 指数退避重试 3 次（1s → 2s → 4s）
- 5xx → 同上
- 单批 PMID > 200 → 自动切片
- 长 query (>2000 字符) → 改用 POST

## 必传参数

每次请求都要带：
- `email` — NCBI 礼貌要求
- `tool` — 项目名,便于 NCBI 联系
- `api_key` — 如有,把 RPS 从 3 升到 10

否则 NCBI 可能 ban IP。

## 参考链接
- E-utilities 完整文档: https://www.ncbi.nlm.nih.gov/books/NBK25500/
- E-utilities In Depth: https://www.ncbi.nlm.nih.gov/books/NBK25497/
- API key 申请: https://www.ncbi.nlm.nih.gov/account/settings/
- 速率限制官方说明: https://www.ncbi.nlm.nih.gov/books/NBK25497/#chapter2.Usage_Guidelines_and_Requiremen
