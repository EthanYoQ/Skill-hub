# 失败模式 + 排错指南

> 列出 `citation-anchor-resolver` 各种"看似失败"的情形,
> 区分:**真失败**(P0 守护正确触发)vs **配置/集成错**(实际可修)。
>
> P0 守护下,任何一类都**不允许**在本 skill 内 fallback 解决。修正点在调用方或上游 skill。

## 1. `resolve_citation` 返回 None

### 1.1 锚点格式非法

锚点不匹配 `[<type>:<id>:<locator>]` 正则(如缺括号、source_type 不合法字符)。

**修法**:在生成报告时,强制使用本 skill 的 schema 格式。**不要**在 resolver 里加"宽容解析"。

### 1.2 `source_type` 不在 8 种枚举

例如 `[paper:12345678:abstract]`(`paper` 不是合法 type)。

**修法**:把 `paper` 映射到 `pmid` 是上游 skill 的责任(报告生成时用合法 type),
**不**在 resolver 里加别名。

### 1.3 文件不存在

例如 `sources/pubmed/12345678.json` 没下载到磁盘。

**修法**:让上游召回 skill(`pubmed-eutils` 等)在 Step 1-5 召回时把 JSON 写盘。
**不**在 resolver 里"跳过这条 PMID 改用其他 PMID 兜底"。

### 1.4 locator 找不到对应章节/key

例如 `[guideline:CSCO-2024-NSCLC:§99.99.99]` — 该章节不存在。

**修法**:锚点写错了,LLM 重写;或上游 TOC 没建好。**不**在 resolver 里"找最相似的章节"。

### 1.5 PDF 锚点但 pypdf 未安装

可选依赖 `pypdf` 没装 → PDF 锚点返回 None。

**修法**:装 `pypdf`,或上游 skill 在抓 PDF 时同步 OCR/转 .txt。

## 2. `verify_claim_against_source` 返回 verified=False

### 2.1 reason="anchor unresolvable: [...]"

resolve_citation 链路 None,见上面 1.x。

### 2.2 reason="no keywords to verify"

claim_text 抽不出任何候选关键词(全是虚词/标点)。

**修法**:调用方显式传 `keywords=[...]`,或者改 claim 文本让其包含实词。

### 2.3 reason="source missing: <kw1>, <kw2>"

关键词在源里找不到。

**这是本 skill 设计上要触发的核心 P0 行为**:
- LLM 写错了/凭记忆写的 → 重写到引用正确的源
- 引用源选错了(关键词在另一个源里有,但锚点指向了别的源)→ 修锚点
- 关键词被规范化后仍不匹配(如 OCR 错字、繁简差异) → 增强 `_keyword_match.normalize_for_match`
  (繁简映射可考虑接入,但这本身**不是字典化业务知识**)

**绝对不要**在 resolver 里"用 LLM 判断语义相似" / "查内置近义词表"。

## 3. `parse_citations_in_text` 返回空列表

文本里没有任何合法锚点。

**这正是 Cite-or-Block 要捕捉的违规**:
- 上层(`content-verification-layer`)据此判定该段无 citation → critical violation → 阻断重写

## 4. 调用方常见误用

| 误用 | 现象 | 修法 |
|-----|------|------|
| 把 `sources_dir` 传成项目根 | 所有 resolve 都 None | 传 `.cache/<slug>/sources/` 而非项目根 |
| 把 `sources_dir` 传成相对路径,但 cwd 不对 | 偶尔成功偶尔 None | 传 `Path.resolve()` 后的绝对路径 |
| 期望 evidence 文件在 sources/evidence/ | None | evidence 路径是 `<sources_dir>/../evidence/`,不是 sources 内 |
| guideline 用错后缀(.pdf 但没 pypdf) | 解析失败 | 同时存 .txt 备份;让上游 cn-clinical-guidelines-fetch 双格式存 |

## 5. P0 反例(本 skill 永远不修这些)

| 想法 | 为什么禁止 |
|------|----------|
| "找不到 PMID JSON 就用 LLM 写一段同主题摘要兜底" | 违反 P0 — LLM 凭记忆即捏造 |
| "未知 source_type 默认按 evidence 处理" | 违反 P0 — 别名映射是字典化的入口 |
| "关键词找不到时调 LLM 判断语义相似" | 违反 P0 — 绕过了"必须在源里"的约束 |
| "维护一个 'PMID → 内置摘要' 表作为 cache" | 违反 P0 — 这就是字典 |

任何 implementer 想加上述功能 → **停下来,问 P0**。
