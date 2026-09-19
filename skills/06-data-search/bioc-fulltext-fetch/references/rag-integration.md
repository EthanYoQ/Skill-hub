# RAG Integration Examples

把 BioC chunk 入向量库的完整代码示例。本 skill 只产 chunk，向量化与检索由下游 pipeline 完成。

## 1. LangChain + Chroma

```python
from langchain.schema import Document
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings

from bioc_fulltext_fetch import (
    fetch_fulltext_bioc, fetch_abstract_bioc,
    to_rag_chunks, NotOpenAccessError,
)
from pubmed_eutils import elink_pmc_to_pubmed  # 见 pubmed-eutils skill

pmcids = ["PMC10234567", "PMC11122233", ...]
all_chunks = []
for pmcid in pmcids:
    try:
        doc = fetch_fulltext_bioc(pmcid)
    except NotOpenAccessError:
        # 回退到摘要
        pmid = elink_pmc_to_pubmed(pmcid)
        doc = fetch_abstract_bioc(pmid)
    all_chunks.extend(to_rag_chunks(doc, chunk_size=512, overlap=50))

lc_docs = [
    Document(page_content=c["text"], metadata=c["metadata"])
    for c in all_chunks
]

vectorstore = Chroma.from_documents(
    lc_docs,
    embedding=OpenAIEmbeddings(model="text-embedding-3-small"),
    collection_name="aml_literature",
    persist_directory="./chroma_aml",
)
```

### 元数据过滤检索

```python
# 只在 Methods 章节检索
retriever = vectorstore.as_retriever(
    search_kwargs={"filter": {"section": "METHODS"}, "k": 5}
)
results = retriever.invoke("flow cytometry gating strategy for AML blasts")

# 多条件：2023 年后的 RESULTS 章节
retriever = vectorstore.as_retriever(
    search_kwargs={
        "filter": {"$and": [
            {"section": "RESULTS"},
            {"year": {"$gte": 2023}},
        ]},
        "k": 10,
    }
)
```

## 2. LlamaIndex

```python
from llama_index.core import Document, VectorStoreIndex
from llama_index.embeddings.openai import OpenAIEmbedding

li_docs = [
    Document(
        text=c["text"],
        metadata=c["metadata"],
        doc_id=c["chunk_id"],
        excluded_llm_metadata_keys=["offset_start", "offset_end"],
    )
    for c in all_chunks
]
index = VectorStoreIndex.from_documents(
    li_docs,
    embed_model=OpenAIEmbedding(model="text-embedding-3-small"),
)
index.storage_context.persist("./li_aml_index")
```

## 3. 与 pubtator-entity-search 联用（实体叠加）

```python
from pubtator_entity_search import annotate_text  # 调实体标注

for chunk in all_chunks:
    ann = annotate_text(chunk["text"], concepts=["Gene", "Disease", "Chemical"])
    chunk["metadata"]["entities"] = [
        {"text": e["text"], "type": e["type"], "id": e["id"]}
        for e in ann["entities"]
    ]
```

`metadata.entities` 之后可以用作向量检索的辅助过滤器（"只取提到 FLT3 基因的 chunk"）。

## 4. 批量入库的工程要点

- **去重**：以 `chunk_id` 为主键，用 SQLite 或 vector store 自带的 upsert 避免重复
- **断点续传**：把已处理的 PMCID 写入 `processed.jsonl`，重启时跳过
- **失败隔离**：单篇失败不应阻断整批，捕获 `BioCFetchError` 后写入 `failed.jsonl`
- **embedding 成本**：text-embedding-3-small 约 $0.02/1M tokens；100 篇 PMC 全文 ≈ 5M tokens ≈ $0.10
- **并发**：fetch 阶段并发 5 RPS，embedding 阶段可并发 50（OpenAI batch API 更便宜）

## 5. medical-evidence-grading 联用示例

`medical-evidence-grading` skill 在做 sample size / study design 检测时，依赖本 skill 提供的 `extract_paragraphs` 输出（保留 section 标签）：

```python
from bioc_fulltext_fetch import fetch_fulltext_bioc, extract_paragraphs
from medical_evidence_grading import detect_sample_size, classify_design

doc = fetch_fulltext_bioc("PMC10234567")
paras = extract_paragraphs(doc)

methods_paras = [p for p in paras if p["section_label"] == "METHODS"]
n = detect_sample_size(methods_paras)            # 抽 n=312
design = classify_design(methods_paras)          # "RCT" / "cohort" / ...
```

## 6. 向量库选型速查

| 库 | 适合场景 | 元数据过滤 | 部署 |
|----|----------|-----------|------|
| Chroma | 本地、< 1M chunk | 强 | 单机/嵌入 |
| Qdrant | 生产、< 100M chunk | 强 | self-host / 云 |
| Weaviate | 混合检索 + GraphQL | 强 | self-host / 云 |
| Pinecone | 全托管 | 中 | 仅云 |
| pgvector | 已有 PostgreSQL | 用 SQL | 任意 PG |

医学文献场景推荐 **Qdrant** 或 **pgvector**：元数据过滤强、支持 hybrid search（BM25 + dense）。
