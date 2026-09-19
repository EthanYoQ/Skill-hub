# Treatment Table Schema

`fetch_chinese_guidelines()` 返回的每个来源（csco / nccn_zh）的 `treatment_table` 字段结构。

> **A1' v2 升级**：`treatment_table` 现在由 `parse_treatment_table_from_raw_text` 从原文解析得到，不再硬编码字典；调用时若传 `sources_dir` 参数，原文会同步存档到 `sources_dir/guidelines/<source_id>.{txt,toc.json,meta.json}`，供 `citation-anchor-resolver` 解析锚点。

## 必需字段

| 字段 | 类型 | 说明 |
|-----|------|------|
| `line` | str | 治疗线：`"1L"`, `"2L"`, `"3L"`, `"Maintenance"`, `"Adjuvant"` |
| `level` | str | CSCO 推荐等级：`"I"`, `"II"`, `"III"` |
| `drug` | str | 中文通用名（如 `"洛拉替尼"`） |

## 可选字段

| 字段 | 类型 | 说明 |
|-----|------|------|
| `drug_en` | str | 英文通用名（如 `"Lorlatinib"`） |
| `category` | str | 药物类别（如 `"三代 ALK-TKI"`） |
| `regimen` | str | 联合方案（非单药时） |
| `population` | str | 亚群（如 `"PD-L1 ≥ 50%"`） |
| `notes` | str | 备注（如 `"脑转移优选"`） |

## 示例

```json
{
  "line": "1L",
  "level": "I",
  "drug": "洛拉替尼",
  "drug_en": "Lorlatinib",
  "category": "三代 ALK-TKI",
  "notes": "脑转移亚群优选"
}
```

## cross_check 命中规则

`cross_check_treatment_recommendations(proposed_recs, guidelines)`：

1. 收集 `guidelines.csco.treatment_table` + `guidelines.nccn_zh.treatment_table` 中所有 `level == "I"` 的项
2. 按 `line` 分组
3. 对每个 line，判断 `proposed_recs` 中是否覆盖（substring 匹配，因为 proposed 可能写"洛拉替尼" 或 "洛拉替尼 60 mg qd"）
4. 严重性：
   - 任意 line 完全没命中 → `critical`
   - 部分命中 → `warning`
   - 全命中 → `none`

## proposed_recs 输入结构

```python
[
    {"line": "1L", "drugs": ["洛拉替尼", "阿来替尼"]},
    {"line": "2L", "drugs": ["布加替尼"]},
]
```

## sources_dir 字段（A1' v2）

`fetch_chinese_guidelines(disease, sources_dir=Path)` 把每个抓到的指南原文写到：

```
sources_dir/
└── guidelines/
    ├── CSCO-2024-NSCLC.txt        ← 完整原文
    ├── CSCO-2024-NSCLC.toc.json   ← {"§5.5.2": {"start_line": 18, "end_line": 28}, ...}
    └── CSCO-2024-NSCLC.meta.json  ← {"version", "url", "disease", "archived_at", ...}
```

下游 skill：

- `citation-anchor-resolver.resolve_citation("[guideline:CSCO-2024-NSCLC:§5.5.2]", sources_dir)`
  → 章节正文（用于 Cite-or-Block 关键词核对）
- `cn-clinical-guidelines-fetch.locate_section_in_guideline(source_id, section, sources_dir)`
  → 返回 dict（含 `text` / `start_line` / `end_line` / `anchor_str`）

