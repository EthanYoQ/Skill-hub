---
name: citation-anchor-resolver
description: |
  Cite-or-Block 架构的基石原子 skill。把报告里的 citation 锚点
  (例如 [guideline:CSCO-2024-NSCLC:§5.5.2] / [pmid:12345678:abstract])
  解析为源文件片段,并核对事实声明里的关键词是否在引用源原文里出现。

  Foundation atomic skill for the Cite-or-Block architecture. Resolves
  citation anchors (e.g. [guideline:CSCO-2024-NSCLC:§5.5.2] /
  [pmid:12345678:abstract]) to raw source text fragments, and verifies
  whether claim keywords actually appear in the cited source.

  使用场景 / Use when:
    1. 报告生成后要做 fact-check (resolve_citation + verify_claim_against_source)
    2. content-verification-layer 要扫全报告锚点 (parse_citations_in_text)
    3. drug-citation-verifier / 任何 cross-check skill 需要"锚点 → 源原文"

  P0 守护:本 skill **绝不维护任何已知字典**。源里没有 = verified=False,
  无例外、无 fallback、无"已知答案兜底"。

  P0 guard: this skill **never maintains any built-in dictionary**.
  Not in source = verified=False. No fallback, no built-in answers.
version: 1.0.0
---

# citation-anchor-resolver

## TL;DR

输入:报告文本 + 一个 citation 锚点字符串 + sources_dir 目录
输出:锚点对应的源原文片段、或事实声明的关键词核对结果(verified True/False)

3 个公开函数:
- `parse_citations_in_text(text)` — 扫描文本提取所有锚点 + 上下文
- `resolve_citation(anchor, sources_dir)` — 锚点 → 源文本片段
- `verify_claim_against_source(claim_text, citation, sources_dir)` — 核对 claim 关键词

## Iron Law(P0 守护,绝对不可违反)

本 skill 是 **Cite-or-Block 架构的基石**。**永远不**做以下事:

- ❌ 维护"已知 PMID 列表 / 已知指南列表 / 已知药品列表"等任何字典
- ❌ 在 resolve 失败时 fallback 到"内置答案"
- ❌ 用 LLM 生成关键词的"语义匹配",必须用严格 substring(可加规范化)
- ❌ 任何形如 `_known_xxx_fallback.py` / `KNOWN_XX_LIST = [...]` 的代码

**唯一允许的姿势**:
- ✅ 打开 `sources_dir` 内的源文件(JSON/HTML/PDF/text)
- ✅ 用字符串 `in` 操作核对关键词
- ✅ 源里没有 → 返回 `verified=False`
- ✅ 锚点解析不出文件 → 返回 `None`

源里没有 = verified=False,无例外。

## Citation 锚点 schema

格式:`[<source_type>:<source_id>:<locator>]`

| source_type | source_id 形如 | 文件路径(相对 sources_dir)| locator 例 |
|------------|---------------|------------------------|-----------|
| `guideline` | `CSCO-2024-NSCLC` | `guidelines/CSCO-2024-NSCLC.{txt,md,html,pdf}` + `.toc.json` | `§5.5.2` |
| `pmid` | `12345678` | `pubmed/12345678.json` | `abstract` / `title` |
| `nct` | `NCT01828099` | `trials/NCT01828099.json` | `results` / `eligibility` |
| `aact` | `NCT01828099` | `aact/NCT01828099.json` | `results` |
| `europepmc` | `PMC1234567` | `europepmc/PMC1234567.json` | `abstract` |
| `bioc` | `PMC1234567` | `bioc/PMC1234567.json` | `intro` / `methods` / `results` |
| `evidence` | `01_lit.md` | `<sources_dir>/../evidence/01_lit.md` | `line:42` / `line:42-58` |
| `nmpa-page` | `H20180123` | `nmpa/H20180123.{html,json}` | (可空) |

详见 `references/anchor-schema.md` 和 `references/source-types.md`。

## 公开 API

```python
from resolver import (
    parse_citations_in_text,
    resolve_citation,
    verify_claim_against_source,
)

# 1. 扫文本拿锚点
cites = parse_citations_in_text(report_html)
# [{"anchor": Citation(...), "anchor_str": "[pmid:12345678:abstract]",
#   "claim_sentence": "...", "position": 42}, ...]

# 2. 锚点 → 源原文
src = resolve_citation("[guideline:CSCO-2024-NSCLC:§5.5.2]", sources_dir)
# str(源章节内容)or None

# 3. 核对关键词
res = verify_claim_against_source(
    claim_text="洛拉替尼商品名博瑞纳",
    citation="[guideline:CSCO-2024-NSCLC:§5.5.2]",
    sources_dir=sources_dir,
)
# {"verified": True, "matched_keywords": [...], "missing_keywords": [],
#  "source_excerpt": "...", "reason": "all keywords matched"}
```

## 协作矩阵 / Collaboration matrix

| 上游(给本 skill 喂源) | 内容 | 下游(调本 skill 做 verify) | 用途 |
|--------------------|------|------------------------|------|
| `cn-clinical-guidelines-fetch` (A1') | 原文存到 `sources/guidelines/<id>.{txt,html,pdf}` + `.toc.json` | `drug-citation-verifier` (A5') | 核对每个药品提及的 citation |
| `pubmed-eutils` | PMID JSON 存 `sources/pubmed/<pmid>.json` | `content-verification-layer` (A6') | 核对每段事实声明 |
| `clinical-trials-v2` | NCT JSON 存 `sources/trials/<nct>.json` | `disease-market-sizing-orchestration` (A2') | Step 8 全报告 cross-check |
| `aact-bulk-trials` | AACT 切片存 `sources/aact/<nct>.json` | quality eval (A8) | citation coverage 审计 |
| `europepmc-search` | PMC 摘要存 `sources/europepmc/<pmcid>.json` | CI lint (A10) | 无 citation 的事实声明 = build fail |
| `bioc-fulltext-fetch` | 全文 chunk 存 `sources/bioc/<pmcid>.json` | — | — |

## 工作流

```
1. parse_citations_in_text(html)  # 拿到所有锚点 + claim 上下文
   ↓
2. for each citation:
     resolve_citation(anchor, sources_dir)   # → 源文本片段 or None
        ↓
     verify_claim_against_source(claim, anchor, sources_dir)
        ↓
     {verified: True/False, matched: [...], missing: [...]}
   ↓
3. 任一 verified=False 或 None → 报告写错了/源不支持 → 上层 (A6'/A2') 阻断重写
```

## 反例(给将来的 reviewer)

❌ **不要**做这些事:

```python
# ❌ 反例 1:维护已知字典
KNOWN_PMIDS = {"12345678": "Lorlatinib paper", ...}

def resolve_citation_BAD(anchor, sources_dir):
    if anchor in KNOWN_PMIDS:        # ← 字典!
        return KNOWN_PMIDS[anchor]
    ...
```

```python
# ❌ 反例 2:fallback 到"内置答案"
def resolve_citation_BAD(anchor, sources_dir):
    src = load_from_disk(anchor, sources_dir)
    if src is None:
        return BUILT_IN_ANSWERS[anchor]   # ← fallback!
    return src
```

```python
# ❌ 反例 3:语义匹配代替源核对
def verify_BAD(claim, citation, sources_dir):
    return llm.judge(f"is `{claim}` consistent with the literature?")
    # ← LLM 凭训练知识判断,绕过了"必须在源里"的约束
```

✅ **正确姿势**:打开文件,字符串 in,源里没有 = False。

## 跨平台

- Python 3.10+
- 标准库 `re` + `json` + `pathlib`(必需)
- 可选依赖:`pypdf`(只在 guideline 锚点指向 PDF 时使用,缺失则跳过 PDF 锚点返回 None)
- 不需要联网

## 文件结构

```
citation-anchor-resolver/
├── SKILL.md                      # 本文件
├── scripts/
│   ├── __init__.py
│   ├── _anchor_schema.py         # Citation dataclass + 解析正则
│   ├── _source_loader.py         # 8 source_type 的加载器
│   ├── _keyword_match.py         # 中英文关键词在源里的核对
│   └── resolver.py               # 3 个公开函数
└── references/
    ├── anchor-schema.md          # 完整锚点 schema 文档
    ├── source-types.md           # 8 种 source_type 详细
    └── failure-modes.md          # 失败模式 + 排错指南
```

## 决策检查清单(每次修改本 skill 必过一遍)

- [ ] 我没有在维护"已知 XX 列表"?
- [ ] 我的 cross-check 是"核对源"不是"查表"?
- [ ] 这个 skill 在我从未见过的疾病/药/数字上能工作吗?
- [ ] resolve_citation 找不到时返回 None,**不 fallback**?
- [ ] verify_claim_against_source 用严格 substring 而不是语义判断?

任一项 No → 停下来重设计。

---

*本 skill 由 Phase 1.5 Task A11 实现,2026-04-26 commit。*
*P0 铁律见项目根 CLAUDE.md。*
