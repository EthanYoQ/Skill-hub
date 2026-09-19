# Verification Flow

> 详细描述 `verify_drug_mentions_in_text` 的内部流程。

## 流程图

```
┌──────────────────────────────────────────────────────────────────┐
│ Input: text (报告片段) + sources_dir (.cache/<slug>/sources/)   │
└──────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│ Step 1: extract_drug_mentions_with_context(text)                 │
│  - 中文后缀正则(替尼/单抗/...)                                  │
│  - 英文后缀正则(-tinib/-mab/...)                                │
│  - 紧跟药名后的"(...)"作为 brand_in_context                      │
│  - 输出 [{text, brand_in_context, context, position}, ...]       │
└──────────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    没有疑似药 → return ok=True
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│ Step 2: A11.parse_citations_in_text(text)                        │
│  - 扫描所有 [type:id:locator] 锚点                               │
│  - 输出 [{anchor, anchor_str, claim_sentence, position}, ...]    │
└──────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│ Step 3: 对每个 mention:                                          │
│  ┌────────────────────────────────────────────────────────┐      │
│  │ find_nearest_citation(mention.position, citations, text)│      │
│  │  - 同句优先(_sentence_span)                          │      │
│  │  - 同段其次(_paragraph_span)                          │      │
│  │  - 跨段 → None                                          │      │
│  └────────────────────────────────────────────────────────┘      │
│                              │                                    │
│            ┌─────────────────┴────────────────┐                   │
│            ▼ None                             ▼ Citation          │
│   severity=critical              ┌──────────────────────────┐    │
│   reason="no citation near       │ A11.verify_claim_against │    │
│           drug mention"          │       _source(           │    │
│                                  │   claim=name+(brand),    │    │
│                                  │   citation=anchor,       │    │
│                                  │   sources_dir,           │    │
│                                  │   keywords=[name, brand] │    │
│                                  │ )                        │    │
│                                  └──────────────────────────┘    │
│                                              │                    │
│                                ┌─────────────┴─────────┐          │
│                                ▼ verified=True         ▼ False    │
│                              severity=none        severity=critical│
└──────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│ Step 4: violation_severity = max(severity for m in mentions)     │
└──────────────────────────────────────────────────────────────────┘
                              │
                              ▼
                   ok = (violation_severity == "none")
```

## 阶梯式 fallback(就近匹配)

`find_nearest_citation` 的 3 层策略:

1. **同句**:在 mention 位置所在的句子(以 `。!?!?\n` 划分)内的所有锚点
   → 取距离最近的
2. **同段**:在 mention 位置所在的段落(以 `\n\s*\n` 划分)内的所有锚点
   → 取距离最近的
3. **跨段**:返回 None,触发 critical violation

### 为什么不允许跨段?

跨段意味着"这段话没有 citation 锚定",即使该报告其他地方有锚点,
也不能用来"代为背书"(那是语义猜测,违反 Cite-or-Block 严格性)。

## Keyword 构造规则

`_build_claim_phrase(mention)` 构造的 keywords:

| Mention 字段 | 输出 keyword |
|-------------|--------------|
| `text="洛拉替尼"`           | `"洛拉替尼"`            |
| `brand_in_context="博瑞纳"` | `"博瑞纳"`              |
| `brand_in_context="博瑞纳:Lorbrena"` | `"博瑞纳"`, `"Lorbrena"` |
| `brand_in_context="商品名:博瑞纳"` | `"博瑞纳"`(过滤掉"商品名"标签词) |

每个 keyword 都必须**严格 substring 出现在源里**,任一缺失 → verified=False。

## 与 A11 的契约

- **输入**:claim_text(用于显示) + keywords(严格匹配) + citation + sources_dir
- **输出**:`{"verified", "matched_keywords", "missing_keywords", "source_excerpt", "reason"}`
- A11 只做"严格 substring 核对",不做"已知答案 fallback"

本 skill 完全信任 A11 的输出,**不**对其结果做任何二次包装(只把 verified
结果映射成 severity)。
