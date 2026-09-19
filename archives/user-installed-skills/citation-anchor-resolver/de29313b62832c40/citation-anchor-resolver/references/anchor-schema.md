# Citation 锚点 schema(项目级标准)

> 配套 skill: `citation-anchor-resolver`
> P0 守护见根 SKILL.md。任何"找不到"都返回 None / verified=False,**绝不**兜底。

## 1. 形式

```
[<source_type>:<source_id>:<locator>]
```

字段约束:

| 字段 | 必填 | 字符集 | 备注 |
|-----|-----|-------|------|
| `source_type` | ✅ | 字母开头,字母数字下划线连字符 | 必须在 8 种枚举内,见下 |
| `source_id` | ✅ | 除 `:` 与 `]` 外任意非空 | 通常是 slug / PMID / NCT / 文件名 / 批准文号 |
| `locator` | ❌ | 除 `]` 外任意非空(允许内含一个 `:`) | 章节号 / 行号 / 段名 |

## 2. 8 种 source_type 枚举

```python
ALLOWED_SOURCE_TYPES = {
    "guideline",    # 临床指南(CSCO / NCCN / NMPA / NHC / CDE)
    "pmid",         # PubMed PMID
    "nct",          # ClinicalTrials.gov NCT
    "aact",         # AACT(ClinicalTrials 镜像)
    "europepmc",    # Europe PMC
    "bioc",         # BioC(全文 chunk)
    "evidence",     # 项目内 evidence/ 目录(老格式向后兼容)
    "nmpa-page",    # NMPA 公开页(批准文号查询页等)
}
```

## 3. locator 形式

| 形如 | 含义 | 用于 |
|------|-----|------|
| `§5.5.2` | 章节号 | guideline(配合同名 .toc.json) |
| `abstract` | 摘要段 | pmid / europepmc |
| `title` | 标题 | pmid |
| `results` | 结果段 | nct / aact / bioc |
| `methods` | 方法段 | bioc |
| `intro` | 引言 | bioc |
| `eligibility` | 入组标准 | nct |
| `line:42` | 单行 | guideline / evidence |
| `line:42-58` | 行号区间 | guideline / evidence |
| (空) | 全文/全字段 | 任意 |

未知 locator:
- 在 guideline / evidence 文本里 → 退而求其次:在原文里找该字符串作为定位锚,返回其后 ~1500 字
- JSON 类型 → 当 key 用,取不到 → None

## 4. 反例(非法锚点)

| 锚点 | 为什么不合法 |
|------|--------|
| `[PMID:12345678]` | source_type 大小写错误(应为 `pmid` 全小写) |
| `[guideline::§5.5.2]` | source_id 为空 |
| `[unknown:xxx]` | source_type 不在 8 种枚举内 → resolve 返回 None |
| `[pmid:12345678:abstract` | 缺右括号 |
| `(pmid:12345678:abstract)` | 应为方括号 |

## 5. 推荐示例

```
[guideline:CSCO-2024-NSCLC:§5.5.2]
[guideline:NCCN-NSCLC-2024-v3:§INV-1]
[guideline:NMPA-CDE-2023-Lorlatinib:line:42-58]

[pmid:12345678:abstract]
[pmid:12345678:title]

[nct:NCT01828099:results]
[nct:NCT01828099:eligibility]

[aact:NCT01828099:results]

[europepmc:PMC1234567:abstract]
[bioc:PMC1234567:methods]

[evidence:01_literature.md:line:42-58]

[nmpa-page:H20180123]
```

## 6. P0 决策记录

- 为什么需要标准化锚点 schema?→ 让 cross-check 可机械化、可被任何下游 skill 调,无需"知识"。
- 为什么 source_type 是封闭枚举?→ 防止"自定义类型"导致的 fallback / 字典化漂移。
- 为什么不允许加 source 别名(如 `paper:` = `pmid:`)?→ 同上,任何"别名表"都是字典化的开端。

要扩展 source_type:
1. 改 `_anchor_schema.ALLOWED_SOURCE_TYPES`
2. 新增 `_source_loader.load_<new_type>`
3. 在 `_LOADERS` 注册
4. 写测试,fixture 必须是真文件,**不允许** mock 已知答案
