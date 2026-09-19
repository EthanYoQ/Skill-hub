---
name: pubmed-eutils
description: Search PubMed and retrieve structured biomedical literature with PMID lists, abstracts, MeSH terms, publication types, and PMC IDs for full-text access. Use this skill whenever the user mentions PubMed, PMID, MeSH terms, Clinical Queries, NCBI, E-utilities, or needs evidence for systematic reviews, RCT searches, drug-disease research, mechanism mapping, market research, or clinical evidence gathering. Make sure to use at the START of any medical evidence pipeline (diagnostic queries, prognosis, therapy effectiveness, observational studies, real-world evidence, clinical guidelines). Outputs structured records (title, abstract, journal, year, MeSH, publication type, PMID↔PMCID mapping)—does NOT perform semantic reranking (delegated to medical-evidence-grading), full-text extraction (delegated to bioc-fulltext-fetch), or entity annotation (delegated to pubtator-entity-search). Free official NCBI API covering 37M+ biomedical records. Cross-platform (Claude Code / Codex / Gemini CLI) with zero external SDK dependencies.
license: MIT
---

# pubmed-eutils · NCBI E-utilities 原子封装

## 一句话定义
把 NCBI E-utilities (`esearch` / `efetch` / `esummary` / `elink`) 封装成医学证据检索流水线里**唯一的 PubMed 召回入口**。只负责"把 PMID 列表 + 结构化元数据拿回来"，不做相关性重排、不抽全文、不评证据等级。

---

## 何时调用
- 用户提到 **PubMed、文献检索、pmid、医学文献、NCBI、MeSH、Clinical Queries**
- 任务需要 **召回 PMID 列表**（系统综述起点、市场调研证据池、疾病机制文献池）
- 需要 **PMID → PMCID 映射**（给 `bioc-fulltext-fetch` 取全文）
- 需要 **批量摘要 + MeSH 标签**（给 `medical-evidence-grading` 排序、给 `pubtator-entity-search` 实体标注）
- 需要 **Clinical Queries 内置过滤器**（therapy / diagnosis / etiology / prognosis / clinical_prediction_guides / systematic_reviews + narrow / broad）

## 何时不调用
- 取**全文 XML/JATS** → 用 `bioc-fulltext-fetch`（PMC OAI / BioC API）
- 取 **Europe PMC 特有字段**（如 preprint、欧洲灰色文献）→ 用 `europepmc-search`（互补召回）
- 取 **临床试验注册信息** → 用 `clinical-trials-v2` + `aact-bulk-trials`
- 做 **基因/疾病/药物实体标注** → 用 `pubtator-entity-search`
- 做 **GRADE/Cochrane RoB 证据评级** → 用 `medical-evidence-grading`
- 做 **语义重排 / 相关度排序** → 本 skill 输出后由 `medical-evidence-grading` 或 reranker 处理

---

## 与其他 skill 的协作关系

```
                    ┌─ pubmed-eutils（本 skill · 召回主力 · PMID + 元数据）
                    │
召回层 (recall)  ───┼─ europepmc-search（互补 · preprint / 欧洲文献）
                    │
                    └─ clinical-trials-v2 / aact-bulk-trials（试验注册）

                                │
                                ▼ PMID list
全文层 (fulltext) ─── bioc-fulltext-fetch（PMC 全文 JATS / BioC）
                                │
                                ▼ entity-rich text
标注层 (annotate) ─── pubtator-entity-search（gene/disease/drug NER）
                                │
                                ▼
排序层 (rank)     ─── medical-evidence-grading（GRADE / RoB / 证据等级）
                                │
                                ▼
终下游           ─── evidence-appendix-sync（市场调研附录 C 同步）
```

**显式 skill 引用路径**（同 `~/.claude/skills/` 下）:
- `~/.claude/skills/europepmc-search/SKILL.md` — 互补召回(preprint / 欧洲灰文献)
- `~/.claude/skills/bioc-fulltext-fetch/SKILL.md` — 下游全文获取(PMID/PMCID → JATS/BioC)
- `~/.claude/skills/pubtator-entity-search/SKILL.md` — 互补实体级关系挖掘(疾病-药物-基因)
- `~/.claude/skills/medical-evidence-grading/SKILL.md` — 上层证据排序(GRADE / OCEBM / RoB)
- `~/.claude/skills/evidence-appendix-sync/SKILL.md` — 终下游附录 C 同步
- `~/.claude/skills/clinical-trials-v2/SKILL.md` — 试验注册(非文献)互补

**协作规则**：本 skill **永远先跑**,输出 PMID + 摘要 + MeSH,让下游 skill 决策"取哪些做全文 / 哪些进证据矩阵"。

---

## 5 个核心函数签名

```python
from typing import Literal
from dataclasses import dataclass

@dataclass
class PubMedRecord:
    pmid: str
    title: str
    abstract: str | None
    authors_first: str | None
    authors_count: int
    journal: str | None
    year: int | None
    mesh_terms: list[str]
    publication_types: list[str]
    doi: str | None = None
    pmcid: str | None = None
    cited_count: int | None = None  # 通过 elink pubmed_pubmed_citedin 获取，可选

# 1) 检索 → PMID 列表
def esearch_pubmed(
    query: str,
    max_results: int = 200,
    filters: dict | None = None,   # {"pubdate_from": "2020/01/01", "pubdate_to": "2025/12/31",
                                    #  "pub_types": ["Randomized Controlled Trial"],
                                    #  "species": "humans", "language": "english"}
    sort: Literal["relevance", "pub_date", "first_author", "journal"] = "relevance",
) -> list[str]: ...

# 2) 批量取摘要 + MeSH（XML 解析）
def efetch_abstracts(pmid_list: list[str]) -> list[PubMedRecord]: ...

# 3) 简表（标题 + 第一作者 + 年份 + 期刊，比 efetch 快 5-10x）
def esummary_pubmed(pmid_list: list[str]) -> list[dict]: ...

# 4) PMID → PMCID 映射（给 bioc-fulltext-fetch 用）
def elink_pubmed_to_pmc(pmid_list: list[str]) -> dict[str, str]:
    """返回 {pmid: pmcid} · 没有全文的 PMID 不出现在结果里"""
    ...

# 5) Clinical Queries 内置过滤器
def pubmed_clinical_queries(
    query: str,
    category: Literal[
        "therapy", "diagnosis", "etiology", "prognosis",
        "clinical_prediction_guides", "systematic_reviews"
    ],
    scope: Literal["narrow", "broad"] = "narrow",
    max_results: int = 200,
) -> list[str]: ...
```

---

## API 配置加载逻辑（按优先级）

```python
def load_ncbi_config() -> dict:
    # 1. 项目本地（最高优先级）
    project_yaml = Path.cwd() / ".config" / "ncbi.local.yaml"
    if project_yaml.exists():
        return yaml.safe_load(project_yaml.read_text())

    # 2. 用户全局
    user_yaml = Path.home() / ".config" / "ncbi.yaml"
    if user_yaml.exists():
        return yaml.safe_load(user_yaml.read_text())

    # 3. 环境变量
    if os.getenv("NCBI_API_KEY"):
        return {
            "api_key": os.environ["NCBI_API_KEY"],
            "email": os.getenv("NCBI_EMAIL", "anonymous@example.com"),
            "tool":  os.getenv("NCBI_TOOL",  "claude-code-pubmed-eutils"),
        }

    # 4. 降级：无 key 模式（NCBI 允许 3 RPS）
    return {"api_key": None, "email": "anonymous@example.com",
            "tool": "claude-code-pubmed-eutils", "rps": 3}
```

**配置文件示例 `~/.config/ncbi.yaml`**:
```yaml
api_key: "your_36char_ncbi_api_key"
email:   "you@example.com"      # 必传，NCBI 礼貌要求
tool:    "your-project-name"    # 必传，便于 NCBI 联系
rps:     10                     # 有 key 上限 10
```

> **关键**：每次请求都要带 `email` + `tool` + `api_key`(如有)，否则 NCBI 可能 ban IP。

---

## 检索式构造模板 + 跨疾病移植清单

7 个 ready-to-use 医学场景检索式(系统综述 / RCT / Clinical Queries / 流行病学 / RWE / 中国人群 / 指南)和疾病迁移指引详见参考文件,以保持主文件精简:

→ **`references/query-templates.md`**(同目录 `~/.claude/skills/pubmed-eutils/references/query-templates.md`)

---

## 速率限制 + endpoint 速查

完整 endpoint 表 / dbfrom-db 组合 / 速率限制详见:

→ **`references/endpoint-table.md`**

主文件保留要点:

| 模式      | RPS | 单批 PMID 上限 | 超时 |
| --------- | --- | -------------- | ---- |
| 有 API key | 10  | 200            | 30s  |
| 无 key     | 3   | 200            | 30s  |

实现要求:令牌桶限流 + 429/503 指数退避(1s→2s→4s,3 次) + 单批超 200 自动切片 + 长 query (>2000 字符) 切 POST。

---

## 失败模式速查表

| # | 失败模式                  | 根因                                      | 修复                                                              |
|---|---------------------------|-------------------------------------------|-------------------------------------------------------------------|
| 1 | 无 key 限速被 ban         | HTTP 429 持续 / 缺 `email`+`tool`        | 检查是否传 `email` + `tool` + `api_key`;申请 API key(免费)        |
| 2 | 429 / 5xx 暂时性错误      | 限速触发 / NCBI 服务器抖动                | 指数退避重试 3 次(1s→2s→4s);仍失败抛 `EUtilsTransientError`      |
| 3 | XML 解析错误              | `<ERROR>...</ERROR>` 节点                 | 单条 PMID 失效 → 跳过该条 + log warning,不 raise 中断整批         |
| 4 | PMID 不存在 / 已撤稿(404) | efetch 返回空 `<PubmedArticle>`           | 在 `PubMedRecord.title` 标 `[RETRACTED]` 或 `[NOT FOUND]`         |
| 5 | MeSH term 不规范返 0 结果 | preferred term 拼写 / 已被合并            | 用 `einfo` 查 MeSH 树;退化为 `[tiab]` 自由词 + 同义词扩展         |
| 6 | email 未传被 NCBI 警告    | 请求缺 `email` 参数                       | 强制配置加载层校验 email,缺失则用 `anonymous@example.com` 兜底    |
| 7 | 网络超时                  | `httpx.ReadTimeout`                       | 退避重试 3 次仍失败 → 抛 `EUtilsTimeout`(上游可降级到 europepmc) |
| 8 | 长 query GET 414          | URL too long                              | 自动切到 POST(E-utilities 支持)                                   |
| 9 | 日期格式错                | NCBI 返回 `<ERROR>Empty term</ERROR>`     | 强制 `YYYY/MM/DD`;过滤器 builder 入口校验                         |
| 10| `WebEnv` 失效             | history server 过期(8h)                   | 重新 esearch 而非缓存 history                                     |

---

## 证据等级提示（本 skill 不排序）
本 skill **只给原始召回结果**，不做证据等级判断。证据等级排序由 `medical-evidence-grading` 完成，依据：
- Publication type（meta-analysis > RCT > cohort > case-control > case report）
- 期刊影响因子（可选 · 需配 IF 数据源）
- 引用数（本 skill 通过 `elink pubmed_pubmed_citedin` 选配输出 `cited_count`）
- 样本量（需 `bioc-fulltext-fetch` 取全文后正则抽取）

输出 `PubMedRecord` 时**保留 `publication_types` 原始列表**，让下游 skill 自行映射 GRADE / OCEBM / 牛津等级。

---

## 跨平台兼容（Claude Code / Codex / Gemini CLI）

| 平台         | 触发方式                          | 备注                                                |
| ------------ | --------------------------------- | --------------------------------------------------- |
| Claude Code  | 自动 (description 包含触发词)     | SKILL.md frontmatter 已优化                         |
| Codex CLI    | `codex skill use pubmed-eutils`   | 全部函数签名是纯 Python type hint，可直接 import   |
| Gemini CLI   | `/skill pubmed-eutils <query>`    | description 用关键词 + 自然语言双语，通用触发      |

**实现层兼容要求**：
- 函数实现层**不依赖任何平台特定 SDK**（不用 `anthropic` / `openai` / `google.genai`）
- 仅依赖：`httpx` / `lxml`（XML 解析）/ `pydantic` 或 `dataclasses` / `pyyaml` / `aiolimiter`
- 同步 + 异步双版本（`esearch_pubmed` + `aesearch_pubmed`），让 agent 编排器自由选用

---

## 必含章节自检
1. frontmatter(中英双语 + 推式触发词)✅
2. 一句话定义 ✅
3. 何时调用 / 不调用 ✅
4. 与其他 skill 协作关系(显式相对路径)✅
5. 5 个核心函数签名(标准 Python type hint)✅
6. API 配置加载逻辑 ✅
7. 检索式模板(放 references/query-templates.md)✅
8. 速率限制摘要(完整表放 references/endpoint-table.md)✅
9. 失败模式速查表(10 条 · 标准化 # | 模式 | 根因 | 修复 格式)✅
10. 证据等级提示 ✅
11. 跨平台兼容 ✅

---

## 参考资料

**项目内 references**(progressive disclosure):
- `~/.claude/skills/pubmed-eutils/references/query-templates.md` — 7 个医学场景检索式 + 跨疾病移植清单
- `~/.claude/skills/pubmed-eutils/references/endpoint-table.md` — endpoint 速查 / dbfrom-db 组合 / 速率限制详情

**外部官方文档**:
- E-utilities 完整文档: https://www.ncbi.nlm.nih.gov/books/NBK25500/
- E-utilities In Depth: https://www.ncbi.nlm.nih.gov/books/NBK25497/
- Clinical Queries 过滤器: https://pubmed.ncbi.nlm.nih.gov/help/#clinical-queries-filters
- API key 申请: https://www.ncbi.nlm.nih.gov/account/settings/
- MeSH 浏览器: https://www.ncbi.nlm.nih.gov/mesh/
- 速率限制官方说明: https://www.ncbi.nlm.nih.gov/books/NBK25497/#chapter2.Usage_Guidelines_and_Requiremen
