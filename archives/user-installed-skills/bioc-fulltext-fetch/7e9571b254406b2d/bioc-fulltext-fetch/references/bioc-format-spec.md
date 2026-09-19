# BioC Format Specification

NLM BioC 是 PubMed/PMC 的结构化全文交换格式，提供 XML 和 JSON 两种序列化。

## 1. 顶层结构

```json
{
  "source": "PubMed",
  "date": "20240515",
  "key": "collection.key",
  "infons": { "...collection-level metadata..." },
  "documents": [
    {
      "id": "PMC10234567",
      "infons": {
        "journal": "Nature",
        "year": "2024",
        "doi": "10.1038/s41586-024-xxxxx",
        "pmid": "39523456",
        "license": "CC BY 4.0"
      },
      "passages": [ ... ],
      "relations": []
    }
  ]
}
```

## 2. Passage 字段

每个 `passage` 是 BioC 的最小语义单元（标题、段落、表格 caption、图注、参考文献等）。

| 字段 | 类型 | 说明 |
|------|------|------|
| `offset` | int | 在原文档中的字符起始偏移 |
| `text` | string | 段落原始文本（unicode 端点已转义） |
| `infons.section_type` | string | 章节标签（见 §3） |
| `infons.type` | string | 段落子类型（`title`, `abstract`, `paragraph`, `fig_caption`, `table_caption`, `ref` 等） |
| `infons.iao_name_1` | string | 可选的 OBI/IAO 本体标签 |
| `infons.xml` | string | 原始 JATS XML 标签（如 `<table-wrap>`, `<fig>`） |
| `annotations` | array | 实体标注（PubTator3 端点才有；BioC PMC OA 通常为空） |
| `sentences` | array | 可选的句级切分（部分文档提供） |

## 3. section_type 取值（PMC OA）

观察 PMC OA 的 `section_type`：

```
TITLE          # 文章标题
ABSTRACT       # 摘要
INTRO          # Introduction
METHODS        # Methods / Materials and Methods（已归一）
RESULTS        # Results
DISCUSS        # Discussion
CONCL          # Conclusion
ACK_FUND       # Acknowledgements / Funding
AUTH_CONT      # Author contributions
COMP_INT       # Competing interests
SUPPL          # Supplementary
REF            # References
APPENDIX       # Appendix
FIG            # Figure caption
TABLE          # Table caption / table content
ABBR           # Abbreviations
```

**注意**：
- BioC 已对部分章节做归一化（`Methods` / `Materials and Methods` / `Subjects and Methods` 都映射到 `METHODS`），但仍有例外（综述/快讯偶尔出现 `INTRO_RESULTS` 合并段）
- BioC PubMed 端点（摘要级）只产 `TITLE` + `ABSTRACT`，不会有 `METHODS` 等

## 4. XML vs JSON

| 端点后缀 | 输出 |
|----------|------|
| `BioC_xml/{id}/unicode` | XML 序列化，体积大但保留完整 JATS 标签 |
| `BioC_json/{id}/unicode` | JSON 序列化，推荐用于 Python pipeline |
| `.../ascii` | 非 unicode 版本，希腊字母 / 数学符号丢失更严重 |

**建议**：默认 `BioC_json/.../unicode`；当需要还原表格单元格结构或公式时降级到 `BioC_xml`。

## 5. 字符 offset 一致性

- BioC `passage.offset` 是在拼接全文档（标题 + 摘要 + 全部 passage）后的字符位置
- offset 单位是 Unicode 码点，不是字节
- 多个 passage 文本拼接后即可还原原文（passage 之间会插入换行符以分隔）

## 6. 表格特殊处理

- 表格 caption 单独成为一个 passage（`infons.type=table_caption`）
- 表格本体（cell 数据）通常以一个 passage 出现，`infons.xml="table"`，`text` 字段是降维后的纯文本（行用换行分隔，列用 \t 分隔）
- 复杂表格的 rowspan/colspan 信息丢失，需要时回到 PMC OA 原始 XML

## 7. 参考资料

- BioC 官方规范：https://bioc.sourceforge.net/
- BioC PubMed API：https://www.ncbi.nlm.nih.gov/research/bionlp/APIs/BioC-PubMed/
- BioC PMC OA API：https://www.ncbi.nlm.nih.gov/research/bionlp/APIs/BioC-PMC/
- bioc Python 包：https://pypi.org/project/bioc/
