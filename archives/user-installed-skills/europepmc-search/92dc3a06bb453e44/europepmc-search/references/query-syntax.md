# Europe PMC 查询语法 cheatsheet

主 SKILL.md §5 的扩展参考。Europe PMC 兼容 Lucene 风格,字段名大写,字符串值用双引号包裹。

## 全部字段一览

| 字段 | 含义 | 示例 |
|------|------|------|
| `TITLE` | 标题 | `TITLE:"CAR-T"` |
| `TITLE_ABS` | 标题或摘要 | `TITLE_ABS:"acute myeloid leukemia"` |
| `ABSTRACT` | 摘要 | `ABSTRACT:cytokine` |
| `AUTH` | 作者 | `AUTH:"Smith J"` |
| `AUTH_ID` | ORCID | `AUTH_ID:"0000-0002-..."` |
| `AFF` | 单位 | `AFF:"Dana-Farber"` |
| `JOURNAL` | 期刊全名 | `JOURNAL:"Nature"` |
| `JOURNAL_ISO` | ISO 缩写 | `JOURNAL_ISO:"N Engl J Med"` |
| `ISSN` | ISSN | `ISSN:"0028-4793"` |
| `PUB_YEAR` | 年份/范围 | `PUB_YEAR:[2020 TO 2024]` |
| `FIRST_PDATE` | 首次发表日期 | `FIRST_PDATE:[2024-01-01 TO 2024-12-31]` |
| `PUB_TYPE` | 文献类型 | `PUB_TYPE:"Review"` / `"Randomized Controlled Trial"` |
| `SRC` | 来源数据库 | `SRC:MED`, `SRC:PPR`, `SRC:PMC` |
| `HAS_FT` | 有全文 | `HAS_FT:Y` |
| `OPEN_ACCESS` | OA 状态 | `OPEN_ACCESS:Y` |
| `IN_EPMC` | 在 Europe PMC 全文集中 | `IN_EPMC:Y` |
| `IN_PMC` | 在 PMC 中 | `IN_PMC:Y` |
| `MESH` | MeSH 主题词 | `MESH:"Hematologic Neoplasms"` |
| `KW` | 关键词 | `KW:"single-cell"` |
| `GRANT_ID` | 资助号 | `GRANT_ID:"R01CA12345"` |
| `FUNDER` | 资助方 | `FUNDER:"Wellcome Trust"` |
| `DOI` | DOI | `DOI:"10.1038/s41586-020-2196-x"` |
| `EXT_ID` | 外部 ID(PMID 等) | `EXT_ID:"38123456" AND SRC:MED` |
| `LANG` | 语种 | `LANG:eng` |
| `HAS_DATA` | 有数据声明 | `HAS_DATA:Y` |
| `HAS_SUPPL` | 有补充材料 | `HAS_SUPPL:Y` |

## 布尔与组合

- `AND` / `OR` / `NOT` 必须大写
- 用括号显式分组:`(A OR B) AND (C OR D)`
- 通配符:`leuk*` 匹配 leukemia/leukaemia/leukocyte 等
- 短语:用双引号 `"acute myeloid leukemia"`
- 邻近搜索:`"car-t therapy"~3` (3 词以内)

## 常用配方

```text
# 1) 急性髓系白血病近 5 年综述,含全文,PubMed + 预印本
(TITLE_ABS:"acute myeloid leukemia") AND PUB_TYPE:"Review" 
AND PUB_YEAR:[2020 TO 2025] AND HAS_FT:Y AND (SRC:MED OR SRC:PPR)

# 2) NIH R01 资助的 CAR-T 临床研究
(GRANT_ID:R01* AND FUNDER:"NIH") AND TITLE_ABS:"CAR-T"
AND PUB_TYPE:"Clinical Trial"

# 3) bioRxiv 上 2024 年的免疫治疗预印本
SRC:PPR AND ABSTRACT:"immunotherapy" AND FIRST_PDATE:[2024-01-01 TO 2024-12-31]

# 4) 拿 DOI 反查
DOI:"10.1056/NEJMoa2024850"

# 5) 排除已被正式期刊取代的预印本
(SRC:PPR AND TITLE_ABS:"AML") NOT (SRC:MED)
```

## 排序参数 `sort`

- 默认:相关性
- `sort=date` 或 `sort=P_PDATE_D desc`:按日期降序
- `sort=cited`:按被引次数降序
- `sort=FIRST_IDATE desc`:按 Europe PMC 首次索引日期降序

## 字段大小写陷阱

字段名 **必须大写**(`TITLE`),值大小写不敏感。`title:foo` 会被当成普通短语,导致命中量异常。
