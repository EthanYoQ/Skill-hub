# Chunking Strategies for BioC Fulltext

文献全文 RAG 入库的切片策略。核心原则：**不跨章节、段落优先、token 单位、可追溯**。

## 1. 切片单位：token 而非字符

- 用 `tiktoken.encoding_for_model("text-embedding-3-small")`（即 `cl100k_base`）
- 默认 `chunk_size=512` token，`overlap=50` token
- 字符数与 token 比对英文文献约 1 token ≈ 3.5 char；中文约 1 token ≈ 1.5 char

```python
import tiktoken
enc = tiktoken.get_encoding("cl100k_base")
n_tokens = len(enc.encode(text))
```

## 2. 不跨章节切（关键）

每个 `section_type` 独立切片，避免 chunk 跨越 Methods/Results 边界。

理由：
- Methods 描述实验设计，Results 描述数据；语义不同，混在同一 chunk 里降低检索精度
- section 标签作为 metadata 提供过滤，跨章节切会让过滤失效

实现：

```python
def to_rag_chunks(doc, chunk_size=512, overlap=50):
    # 1. 按 section 分组 passage
    by_section = group_passages_by_section(doc.passages)

    chunks = []
    for section, passages in by_section.items():
        # 2. 每个 section 内部独立切
        section_text = "\n\n".join(p.text for p in passages)
        chunks.extend(_split_section(section_text, section, chunk_size, overlap))
    return chunks
```

## 3. 段落优先 + 硬切兜底

切片时优先在段落（`\n\n`）边界切；如果单段超过 `chunk_size`，再降级到句子边界（`. `），最后才硬切 token。

```python
def _split_section(text, section, chunk_size, overlap):
    # Try paragraph boundary
    paragraphs = text.split("\n\n")
    current, current_tokens = [], 0
    for para in paragraphs:
        para_tokens = count_tokens(para)
        if current_tokens + para_tokens <= chunk_size:
            current.append(para); current_tokens += para_tokens
        else:
            if current:
                yield make_chunk(current, section)
            if para_tokens > chunk_size:
                # 单段超长 → 按句切
                yield from _split_by_sentence(para, section, chunk_size, overlap)
                current, current_tokens = [], 0
            else:
                current = [para]; current_tokens = para_tokens
    if current:
        yield make_chunk(current, section)
```

## 4. Overlap 策略

`overlap=50` token 的目的是保证语义连续性（一个概念被切成两半时检索仍能命中）。

- overlap 取自前一 chunk 末尾的 token，前置到下一 chunk 开头
- 太小（< 20）丢上下文；太大（> 100）冗余多、向量库膨胀
- 推荐：医学文献 50；法律/合同 100；社交媒体短文本 0

## 5. chunk_id 设计

`{pmcid}_{section}_{offset_start}` 三段式：

- `pmcid` 唯一锁定文献
- `section` 便于按章节聚合
- `offset_start` 在同 section 内唯一（同一 section 不会有两个 chunk 起点相同）

例：`PMC10234567_METHODS_2890`

好处：
- 重复入库时可作为 upsert 主键
- 可逆向定位回原文（offset 配合 BioC 文档可精确还原段落）

## 6. 元数据负载

每个 chunk 带的 metadata 必须够用且不冗余：

```python
{
    "pmcid": "PMC10234567",
    "pmid": "39523456",
    "doi": "10.1038/s41586-024-xxxxx",
    "title": "Targeting FLT3 in AML: ...",
    "journal": "Nature",
    "year": 2024,
    "section": "METHODS",          # ← 用于过滤检索
    "offset_start": 2890,
    "offset_end": 3401,
    "is_oa": True,
    "license": "CC BY 4.0",
}
```

不要塞：
- 完整 abstract（应作为独立 chunk）
- 全部作者列表（太长，检索用不到）
- 全部 MeSH（用 `entities` 字段，由 pubtator-entity-search 后置叠加）

## 7. 表格上下文 chunk

表格通过 `extract_tables_context` 单独成 chunk，metadata 加：

```python
{
    "section": "TABLE",
    "table_id": "T1",
    "caption": "Patient baseline characteristics",
    "context_window": 200,
}
```

`text` 字段用 `caption + before_context + after_context` 拼接，便于检索"表 1 描述了什么"这类问题。

## 8. 极端情况

| 情况 | 策略 |
|------|------|
| 单段 > 2048 token（超长 Methods） | 按句切，仍维持 overlap |
| section 只有 1 段且 < 100 token（短 Conclusion） | 不切，整段作一个 chunk |
| 摘要级文档（fetch_abstract_bioc） | 标题 + 摘要合并为单 chunk（通常 < 512 token） |
| 中文/西班牙文 | tiktoken cl100k_base 仍可用，但建议改 multilingual embedding |
| 公式密集（数学/化学） | 切之前先用 `extract_formulas` 替换为占位符（避免 token 浪费） |

## 9. 评测建议

切片质量用以下指标量化：

- **Recall@5**：在 100 个已知问题上，top-5 检索是否含正确 chunk
- **章节一致性**：随机抽 50 个 chunk 检查 `section` metadata 是否正确
- **平均 chunk token 数**：应接近 `chunk_size`（< 80% 说明太多短 chunk）
- **重复率**：相邻 chunk 的 jaccard 相似度（去除 overlap 部分），> 0.3 说明 overlap 过大
