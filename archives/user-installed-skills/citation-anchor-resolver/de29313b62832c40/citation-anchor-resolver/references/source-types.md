# 8 种 source_type 详细

> 每种 source_type 的:文件路径、文件格式、locator 行为、典型上游 skill。

## 文件根目录约定

```
.cache/<slug>/sources/        ← 这是 sources_dir
├── guidelines/               ← guideline source_type
├── pubmed/                   ← pmid source_type
├── trials/                   ← nct source_type
├── aact/                     ← aact source_type
├── europepmc/                ← europepmc source_type
├── bioc/                     ← bioc source_type
└── nmpa/                     ← nmpa-page source_type

<project_root>/evidence/      ← evidence source_type(sources_dir 同级父级)
```

## 1. `guideline`

- 路径:`<sources_dir>/guidelines/<source_id>.{txt,md,html,pdf}`
- 可选 TOC:`<sources_dir>/guidelines/<source_id>.toc.json`
- TOC schema:
  ```json
  {
    "§5.5.2": {"start_line": 1, "end_line": 4},
    "§5.5.3": {"start_line": 5, "end_line": 12}
  }
  ```
- locator:章节号(`§X.X.X`)、`line:N`、`line:N-M`,或空(全文)
- PDF 通过可选 `pypdf` 读;缺失则该锚点解析失败 → None
- 上游:`cn-clinical-guidelines-fetch`

## 2. `pmid`

- 路径:`<sources_dir>/pubmed/<pmid>.json`
- JSON schema:
  ```json
  {"title": "...", "abstract": "...", "authors": [...], "journal": "...", "year": 2024}
  ```
- locator:`abstract` / `title` / 任意 key / 空(title + abstract 拼接)
- 上游:`pubmed-eutils`

## 3. `nct`

- 路径:`<sources_dir>/trials/<NCT_id>.json`
- JSON schema(扁平 string/list 字段):
  ```json
  {
    "title": "...", "phase": "Phase 3",
    "eligibility": "...", "results": "...",
    "interventions": ["Lorlatinib", "Crizotinib"]
  }
  ```
- locator:任意 key / 空(拼所有 string 字段)
- 上游:`clinical-trials-v2`

## 4. `aact`

- 路径:`<sources_dir>/aact/<NCT_id>.json`
- 与 `nct` 同 schema 风格
- 上游:`aact-bulk-trials`

## 5. `europepmc`

- 路径:`<sources_dir>/europepmc/<PMCID>.json`
- JSON schema 类似 PMID,加 `pmcid` / `full_text_url`
- 上游:`europepmc-search`

## 6. `bioc`

- 路径:`<sources_dir>/bioc/<PMCID>.json`
- JSON schema(章节切片):
  ```json
  {"intro": "...", "methods": "...", "results": "...", "discussion": "..."}
  ```
- locator:`intro` / `methods` / `results` / `discussion`
- 上游:`bioc-fulltext-fetch`

## 7. `evidence`(老格式)

- 路径:`<sources_dir>/../evidence/<filename>` (项目根 evidence/ 目录)
- 文件类型:任意文本(.md / .txt)
- locator:`line:N` / `line:N-M` / 空(全文)
- 用途:向后兼容老格式 evidence 文档

## 8. `nmpa-page`

- 路径:`<sources_dir>/nmpa/<approval_no>.{html,htm,txt,md,json}`
- 内容:NMPA 公开页(批准文号查询页等)的归档
- locator:任意子串(在原文里 in 后取 ~1500 字)
- 上游:NMPA 公开页归档(无固定 skill,Step 0a 视需要保存)

## 加载失败的语义

任何 source_type 加载失败(文件不存在 / JSON 不可解析 / locator 不匹配)→ `None`。

**不允许**在加载层做 fallback:
- 不允许"找不到 PMID 12345678 的 JSON,就用 abstract 库的旧数据"
- 不允许"PDF 解析失败,就用 LLM 描述这篇指南内容"

P0 一致姿势:**找不到 = None,无例外**。
