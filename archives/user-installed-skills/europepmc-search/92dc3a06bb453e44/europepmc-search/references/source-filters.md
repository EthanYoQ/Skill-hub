# Europe PMC 来源代码 (SRC) 完整列表

主 SKILL.md §4.1 `source_filter` 参数的扩展参考。每条结果的 `source` 字段使用以下代码之一。

## 核心来源

| code | 含义 | 量级 | 典型用途 |
|------|------|------|---------|
| `MED` | PubMed (MEDLINE + PubMed-not-MEDLINE) | ~38M | 主流生物医学,有 PMID,有 MeSH |
| `PMC` | PubMed Central 开放获取全文 | ~10M | 有全文 XML,有 PMCID |
| `PPR` | 预印本(bioRxiv/medRxiv/ChemRxiv 等) | ~700K | 未同行评议,有 DOI |
| `AGR` | AGRICOLA(美国农业部) | ~5M | 农业/食品科学,医学项目通常不需要 |
| `CBA` | CABI(Centre for Agriculture & Bioscience) | ~13M | 兽医/全球健康/热带病 |
| `PAT` | 专利(EPO/USPTO) | ~7M | 药物/器械专利全文检索 |
| `CTX` | CiteXplore | 历史 | 已迁移,几乎不再返回 |
| `ETH` | British Library EThOS 论文 | ~600K | 英国博士论文 |
| `HIR` | NHS Evidence | 已停用 | — |
| `NBK` | NCBI Bookshelf | ~600K | 教科书章节、指南、报告 |

## 预印本子源(PPR 内部)

`SRC:PPR` 不是单一来源,而是聚合了:
- bioRxiv
- medRxiv
- ChemRxiv
- arXiv(生命科学子集)
- Research Square
- SSRN(医学子集)
- Preprints.org
- F1000Research(部分)

每条 PPR 结果在本 skill 输出中带 `preprint_server` 字段,标明具体上游。

## 选择策略

| 任务类型 | 推荐 source_filter |
|---------|-------------------|
| RAG 知识库(医学正文献) | `["MED", "PMC", "PPR"]` |
| 仅同行评议 | `["MED", "PMC"]` |
| 只要 OA 全文 | `["PMC"]` + `HAS_FT:Y AND OPEN_ACCESS:Y` |
| 预印本快报 | `["PPR"]` |
| 兽医/热带病/动物模型 | `["MED", "PMC", "CBA"]` |
| 药物专利图谱 | `["PAT"]` |
| 临床指南 + 教科书 | `["MED", "NBK"]` |
| 全部撒网(默认) | `None`(等价于全部 SRC) |

## 在 query 中限定 source

两种方式等价,但语法位置不同:

```python
# 方式 A:source_filter 参数(推荐)
search_articles(query="leukemia", source_filter=["MED", "PPR"])

# 方式 B:query 内 SRC 字段
search_articles(query="leukemia AND (SRC:MED OR SRC:PPR)")
```

混用会取交集,通常导致结果意外为空。**只用其中一种**。
