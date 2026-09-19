---
name: clinical-trials-v2
description: Use this skill whenever the user asks about clinical trial status, recruitment, trial phases (1-4), outcomes, trial registries, NCT IDs, or any query on ClinicalTrials.gov data. Real-time lookup of trial protocols, results, enrollment status, sponsors, and interventions via ClinicalTrials.gov API v2. Handles: 'What is the latest status of NCT04368728?', 'Find Phase 3 BTK inhibitor trials currently recruiting', 'Show primary outcomes for this trial', 'Which trials use Pembrolizumab?', 'Recruiting trials for Acute Myeloid Leukemia'. Real-time, single-query ≤1000 records. Delegates to: aact-bulk-trials (bulk >10k), pubmed-eutils (PubMed literature), medical-evidence-grading (GRADE rating), evidence-appendix-sync (reference formatting).
keywords:
  - clinical-trials
  - clinicaltrials-gov
  - clinicaltrials.gov
  - 临床试验
  - 试验注册
  - 招募状态
  - nct
  - nct-id
  - trial-registry
  - recruitment-status
  - recruiting
  - phase-1
  - phase-2
  - phase-3
  - phase-4
  - rct-lookup
  - sponsor-search
  - interventional
  - observational
  - primary-outcome
  - secondary-outcome
  - real-time-api
license: MIT
---

# ClinicalTrials.gov API v2 实时检索

封装 ClinicalTrials.gov 官方 API v2,为医学证据检索体系提供"实时官方源"原子能力。

## 0. Auto-Trigger 示例

| 用户 prompt | 应触发 | 原因 |
|---|---|---|
| "我要查血液科 IFI 相关的招募中临床试验" | ✅ clinical-trials-v2 | 实时招募状态查询 |
| "BTK 抑制剂的 Phase 3 试验有哪些" | ✅ clinical-trials-v2 | intervention + phase 过滤 |
| "给我所有近 5 年完成的曲霉病试验的 results 数据" | ✅ clinical-trials-v2 (`get_study_outcomes`) | 主次终点 + 已发布结果 |
| "NCT04368728 现在到哪一阶段了" | ✅ clinical-trials-v2 (`get_study_details`) | 单 NCT 详情 |
| "我要批量分析过去 10 年血液病所有试验" | ❌ → aact-bulk-trials | 全量 SQL,本地镜像 |
| "找 PubMed 上 RCT 文献" | ❌ → pubmed-eutils | 文献库非试验注册 |
| "这条 RCT 的证据等级是 A 还是 B" | ❌ → medical-evidence-grading (上层调用本 skill) | GRADE 评级编排 |

## 1. 定位与边界

### 只做
- 通过 `https://clinicaltrials.gov/api/v2/studies` 实时检索单个/批量试验
- 单次请求 ≤ 1000 条记录
- 返回完整 protocol + results 模块结构化数据

### 不做(显式委托)
| 任务 | 委托给 | 关系 |
|---|---|---|
| 大批量历史分析 (>10k / 全库 SQL) | `aact-bulk-trials` | 互补:批量·SQL·历史全量 vs 本 skill 实时·单查·≤1000 |
| 关联 PubMed 文献 / NCT→PMID | `pubmed-eutils` | 上游:文献检索后取 NCT 详情 |
| RCT 证据等级 GRADE A/B/C/D | `medical-evidence-grading` | 上层:它编排本 skill 提取 RCT 元数据后评级 |
| 引文落入报告附录 C | `evidence-appendix-sync` | 终下游:`source_url` + NCT 直接落参考文献表 |
| 全文 XML 解析 | `bioc-fulltext-fetch` | 不重叠 |
| 系统综述 PRISMA 编排 | `systematic-review` | 不重叠 |

### 与 aact-bulk-trials 详细对比
| 维度 | clinical-trials-v2 (本 skill) | aact-bulk-trials |
|---|---|---|
| 数据源 | 实时 API | 每日同步的 PostgreSQL 镜像 |
| 单次规模 | ≤1000 条 | 无限(SQL JOIN 全表) |
| 延迟 | 实时 (T+0) | T-1 |
| 查询能力 | REST query DSL | 完整 SQL |
| 适用场景 | 单试验最新状态 / 小批量招募检索 | 全库统计 / 历史趋势 / 多表 JOIN |
| 速率限制 | 建议 ≤5 RPS | 仅本地 IO |

### 跨平台无锁声明
本 skill 仅依赖标准 HTTP + Python stdlib + httpx,**无任何 Claude Code / Codex / Cursor 平台特定 API**。可直接在三平台间迁移。

## 2. 认证与速率

### 无需 API key
ClinicalTrials.gov API v2 是开放 API,无需注册或 API key。

### 建议 User-Agent
```python
HEADERS = {
    "User-Agent": "ClinicalTrialsV2-Skill/1.0 (medical-evidence-retrieval; contact@example.com)",
    "Accept": "application/json",
}
```

### 速率限制
- 官方未强制 RPS 限制,但建议自约束 ≤5 RPS
- 实现指数退避: 429/503 → 退避 2^n * 0.5s, 最多 5 次重试

## 3. 安装与依赖

```bash
pip install httpx tenacity pydantic
```

仅依赖标准 HTTP 客户端,无需特殊 SDK。

## 4. 核心 API 设计

### 统一返回 dataclass

```python
from dataclasses import dataclass, field
from typing import Optional

@dataclass
class TrialRecord:
    nct_id: str
    title: dict                      # {"brief": str, "official": str}
    status: str                      # RECRUITING / ACTIVE_NOT_RECRUITING / COMPLETED / ...
    phase: list[str]                 # ["PHASE2", "PHASE3"]
    study_type: str                  # INTERVENTIONAL / OBSERVATIONAL / EXPANDED_ACCESS
    condition: list[str]
    intervention: list[dict]         # [{"type": "DRUG", "name": "Pembrolizumab"}]
    sponsor: dict                    # {"lead": str, "class": "INDUSTRY"|"NIH"|...}
    enrollment: Optional[int]
    enrollment_type: Optional[str]   # ACTUAL / ESTIMATED
    start_date: Optional[str]
    completion_date: Optional[str]
    primary_outcomes: list[dict]     # [{"measure": str, "time_frame": str}]
    locations: list[dict]            # [{"facility": str, "city": str, "country": str, "status": str}]
    has_results: bool
    last_update_posted: Optional[str]
    source_url: str = field(init=False)

    def __post_init__(self):
        self.source_url = f"https://clinicaltrials.gov/study/{self.nct_id}"
```

### 5 个核心检索函数

#### 4.1 `search_studies(query, filters)`
综合检索入口,支持自由文本 + 结构化过滤器组合。

```python
def search_studies(
    query: str,
    *,
    recruitment_status: list[str] | None = None,    # ["RECRUITING", "ACTIVE_NOT_RECRUITING"]
    phase: list[str] | None = None,                  # ["PHASE2", "PHASE3"]
    study_type: str | None = None,                   # "INTERVENTIONAL"
    country: str | None = None,
    sponsor: str | None = None,
    date_from: str | None = None,                    # "2023-01-01"
    date_to: str | None = None,
    page_size: int = 100,                            # ≤1000
    max_results: int = 500,
) -> list[TrialRecord]:
    """组合查询。query 走 query.term,过滤器映射到 filter.* 参数。"""
```

#### 4.2 `get_study_details(nct_id)`
按 NCT ID 获取完整 protocol + results。

```python
def get_study_details(nct_id: str) -> TrialRecord:
    """GET /api/v2/studies/{nct_id}?format=json"""
```

#### 4.3 `search_by_condition(condition_term, ...)`
疾病专项检索,内部映射到 `query.cond`。

```python
def search_by_condition(
    condition_term: str,                  # "Multiple Myeloma" / "AML"
    *,
    status: list[str] | None = None,
    phase: list[str] | None = None,
    country: str | None = None,
    max_results: int = 200,
) -> list[TrialRecord]:
```

#### 4.4 `search_by_intervention(intervention_term, intervention_type)`
干预专项检索,映射到 `query.intr`。

```python
def search_by_intervention(
    intervention_term: str,                          # "Pembrolizumab" / "CAR-T"
    intervention_type: str | None = None,            # "DRUG"|"DEVICE"|"BEHAVIORAL"|"BIOLOGICAL"
    *,
    status: list[str] | None = None,
    max_results: int = 200,
) -> list[TrialRecord]:
```

#### 4.5 `get_study_outcomes(nct_id)`
专取主/次要终点 + 已发布结果(若 hasResults=True)。

```python
def get_study_outcomes(nct_id: str) -> dict:
    """
    返回:
    {
      "primary_outcomes": [...],
      "secondary_outcomes": [...],
      "has_results": bool,
      "results": {...} | None,         # outcomeMeasuresModule + adverseEventsModule
    }
    """
```

## 5. 参数化过滤器枚举(精简)

最常用的 4 类枚举值速查;**完整枚举 + 端点字段清单 + DSL 语法见 [references/enums-and-endpoints.md](references/enums-and-endpoints.md)**。

| 类型 | 常用值 |
|---|---|
| recruitment_status | `RECRUITING` · `ACTIVE_NOT_RECRUITING` · `COMPLETED` · `TERMINATED` (完整 9 值见 references) |
| phase | `PHASE1` · `PHASE2` · `PHASE3` · `PHASE4` (+ `EARLY_PHASE1` / `NA`) |
| study_type | `INTERVENTIONAL` · `OBSERVATIONAL` · `EXPANDED_ACCESS` |
| intervention_type | `DRUG` · `DEVICE` · `BIOLOGICAL` · `BEHAVIORAL` (完整 11 值见 references) |

## 6. API v2 端点映射(精简)

| 函数 | HTTP | 关键参数 |
|---|---|---|
| search_studies | GET /api/v2/studies | query.term + filter.* |
| get_study_details | GET /api/v2/studies/{nct_id} | format=json |
| search_by_condition | GET /api/v2/studies | query.cond |
| search_by_intervention | GET /api/v2/studies | query.intr |
| get_study_outcomes | GET /api/v2/studies/{nct_id} | fields=outcomesModule,resultsSection |

完整字段映射 + 分页 (`pageToken`) + `fields=` 裁剪语法详见 references。

## 7. 标准请求示例

```python
import httpx

BASE = "https://clinicaltrials.gov/api/v2/studies"

def _fetch(params: dict) -> dict:
    with httpx.Client(headers=HEADERS, timeout=30.0) as client:
        r = client.get(BASE, params=params)
        r.raise_for_status()
        return r.json()

# 示例: 检索"多发性骨髓瘤 + PHASE3 + RECRUITING"
data = _fetch({
    "query.cond": "Multiple Myeloma",
    "filter.overallStatus": "RECRUITING",
    "filter.phase": "PHASE3",
    "pageSize": 100,
    "format": "json",
})
```

## 8. 失败模式与处理(必读)

| # | 失败模式 | 触发条件 | 处理策略 |
|---|---|---|---|
| 1 | **API rate limit** | 单 IP > 5 RPS,返回 429/503 | tenacity 指数退避 (0.5s × 2^n,上限 8s,最多 5 次);批量任务建议 sleep(0.25) 节流 |
| 2 | **NCT ID 格式错误** | 非 `^NCT\d{8}$` (例如 `NCT123` / `nct04368728`) | `validate_nct_id()` 上游校验,直接抛 `InvalidNCTIdError`,不发请求 |
| 3 | **试验未发布 results** | `hasResults=False` 或 `resultsSection` 缺失子模块 | `get_study_outcomes` 优雅降级,返回 `{"has_results": False, "results": None}`,不抛错 |
| 4 | **query DSL 解析错** | `query.term` 含未转义括号/AND-OR 优先级错,API 返回 400 | 抛 `InvalidQueryError`,记录原 query,提示用户使用 `search_by_condition` / `search_by_intervention` 而非 raw query |
| 5 | **国家/地点过滤模糊匹配失败** | `filter.locStr=Beijing` 漏掉 "Peking"/"Beijing, China" | 文档说明使用 ISO 国家码或 `query.locn`,提供常见城市同义词表(见 references) |
| 6 | **NCT 不存在 (404)** | 已撤回或拼写错 | 抛 `TrialNotFoundError`,不重试 |
| 7 | **status 字段滞后真实情况** | sponsor 自报,可能仍标 RECRUITING 但实际已停 | 严肃决策需交叉验证 `last_update_posted` 并提示用户 |

```python
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import re

NCT_PATTERN = re.compile(r"^NCT\d{8}$")

def validate_nct_id(nct_id: str) -> str:
    if not NCT_PATTERN.match(nct_id):
        raise InvalidNCTIdError(f"非法 NCT ID: {nct_id!r},应为 NCT + 8 位数字")
    return nct_id

@retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=0.5, min=0.5, max=8),
    retry=retry_if_exception_type((httpx.HTTPStatusError, httpx.TimeoutException)),
    reraise=True,
)
def _fetch_with_retry(params: dict) -> dict:
    ...
```

## 9. 输出规范

- **永远返回结构化 dataclass**,不返回 raw JSON
- `source_url` 字段供下游引文用
- list 字段空值用 `[]` 而非 `None`
- 日期统一 `YYYY-MM-DD` 字符串(原始 API 可能返回 `YYYY-MM`,前端补 `-01`)

## 10. 跨 Skill 协作链(显式)

```
[pubmed-eutils]               (上游: 文献找到 PMID, elink 拿到 NCT)
        │
        ▼
[clinical-trials-v2]  ←─ 本 skill (单查 ≤1000 / 实时)
        │
        ├──→ [aact-bulk-trials]      (互补: 大批量历史时切换)
        │
        ├──→ [medical-evidence-grading]  (上层: RCT 自动评 GRADE A)
        │           │
        │           ▼
        └──→ [evidence-appendix-sync]    (终下游: 落 NCT 到附录 C)
```

### 与 medical-evidence-grading 集成
```python
# medical-evidence-grading 调用本 skill 提取 RCT 元数据
trial = get_study_details("NCT04368728")
grade_input = {
    "study_type": trial.study_type,           # INTERVENTIONAL
    "phase": trial.phase,                      # ["PHASE3"]
    "enrollment": trial.enrollment,            # 样本量
    "has_results": trial.has_results,
    "primary_outcomes": trial.primary_outcomes,
}
# → grading skill 判定 RCT + Phase 3 + 样本 ≥1000 → GRADE A
```

### 与 evidence-appendix-sync 集成
```python
for trial in search_studies("CAR-T", recruitment_status=["RECRUITING"]):
    appendix.add_reference({
        "type": "clinical_trial",
        "id": trial.nct_id,                    # NCT04368728
        "title": trial.title["official"] or trial.title["brief"],
        "url": trial.source_url,               # https://clinicaltrials.gov/study/NCT...
        "accessed": today_iso(),
    })
```

### 与 pubmed-eutils 上游集成
```python
# 1) PubMed 文献 → NCT
nct_ids = pubmed_eutils.elink(pmids=["38123456"], db="clinicaltrials")
# 2) 取试验详情
trials = [get_study_details(nct) for nct in nct_ids]
```

## 11. 测试清单

- [ ] `get_study_details("NCT04368728")` 返回 BNT162b2 完整 protocol
- [ ] `search_by_condition("Acute Myeloid Leukemia", status=["RECRUITING"])` ≥10 条
- [ ] `search_by_intervention("Pembrolizumab", "DRUG")` 返回 KEYNOTE 系列
- [ ] `get_study_outcomes("NCT00000000")` 对未发布结果试验返回 `has_results=False`
- [ ] 不存在的 NCT 触发 `TrialNotFoundError`
- [ ] 5 次连续 429 后正确退避并最终返回结果
- [ ] 分页超过 1000 条时使用 pageToken 自动续取

## 12. 限制与注意

- API v2 已替代 v1(2024-06 起 v1 deprecated),本 skill 仅使用 v2
- `hasResults=True` 不代表所有 endpoint 已发布;需检查 `resultsSection` 各子模块
- `locations` 数组可能极大(国际多中心试验 >500 站点),按需用 `fields` 参数裁剪
- 单次 ≥1000 条请用 `aact-bulk-trials` 改走本地镜像
- 试验 status 字段可能滞后真实招募情况(由 sponsor 自报),严肃决策需交叉验证
- 不要把本 skill 用于"导出全库做统计"——会被识别为滥用模式
