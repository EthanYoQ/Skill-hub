# ClinicalTrials.gov API v2 — 完整枚举与端点参考

本文件是主 SKILL.md 的补充参考。仅在需要完整字段/枚举时加载。

## 1. recruitment_status (filter.overallStatus) 完整 9 值

| 值 | 含义 |
|---|---|
| `NOT_YET_RECRUITING` | 已注册但尚未开始招募 |
| `RECRUITING` | 正在招募 |
| `ENROLLING_BY_INVITATION` | 仅邀请入组,不公开招募 |
| `ACTIVE_NOT_RECRUITING` | 已停止招募但试验继续 |
| `COMPLETED` | 试验完成 |
| `SUSPENDED` | 暂停(可能恢复) |
| `TERMINATED` | 提前终止(不会恢复) |
| `WITHDRAWN` | 启动前撤回 |
| `UNKNOWN` | 长期未更新,状态未知 |

## 2. phase 完整枚举

| 值 | 含义 |
|---|---|
| `EARLY_PHASE1` | 早期 1 期(原 Phase 0) |
| `PHASE1` | 1 期 |
| `PHASE2` | 2 期 |
| `PHASE3` | 3 期 |
| `PHASE4` | 4 期(上市后) |
| `NA` | 不适用(常见于器械/行为干预) |

## 3. study_type

| 值 | 含义 |
|---|---|
| `INTERVENTIONAL` | 干预性试验(RCT 主体) |
| `OBSERVATIONAL` | 观察性研究 |
| `EXPANDED_ACCESS` | 扩展使用(同情用药) |

## 4. intervention_type 完整 11 值

| 值 | 含义 |
|---|---|
| `DRUG` | 药物 |
| `DEVICE` | 器械 |
| `BIOLOGICAL` | 生物制剂(疫苗/单抗) |
| `PROCEDURE` | 手术/操作 |
| `RADIATION` | 放射治疗 |
| `BEHAVIORAL` | 行为干预 |
| `GENETIC` | 基因治疗 |
| `DIETARY_SUPPLEMENT` | 膳食补充 |
| `COMBINATION_PRODUCT` | 组合产品 |
| `DIAGNOSTIC_TEST` | 诊断检测 |
| `OTHER` | 其他 |

## 5. sponsor_class

| 值 | 含义 |
|---|---|
| `NIH` | 美国 NIH |
| `FED` | 其他联邦机构 |
| `INDUSTRY` | 工业界(药企) |
| `NETWORK` | 研究网络 |
| `OTHER_GOV` | 其他政府 |
| `OTHER` | 其他(学术等) |

## 6. 日期字段

| 字段 | 含义 |
|---|---|
| `study_first_posted` | 首次注册时间 |
| `last_update_posted` | 最近更新 |
| `results_first_posted` | 结果首次发布 |
| `start_date` | 试验开始日期 |
| `completion_date` | 试验完成日期 |
| `primary_completion_date` | 主要终点完成日期 |

日期 filter 语法: `filter.advanced=AREA[StartDate]RANGE[2023-01-01,2024-12-31]`

## 7. 端点完整字段映射

### 7.1 GET /api/v2/studies (检索)

| Query 参数 | 说明 |
|---|---|
| `query.term` | 自由文本(全字段) |
| `query.cond` | 仅条件(疾病) |
| `query.intr` | 仅干预 |
| `query.titles` | 仅标题 |
| `query.outc` | 仅结局指标 |
| `query.spons` | 仅 sponsor |
| `query.lead` | lead sponsor |
| `query.id` | NCT ID 列表 |
| `query.locn` | 地点(自由文本) |
| `query.patient` | 患者标签 |
| `filter.overallStatus` | 招募状态(逗号分隔) |
| `filter.phase` | 阶段 |
| `filter.studyType` | 类型 |
| `filter.geo` | 地理 distance(`distance(lat,lng,radius_km)`) |
| `filter.advanced` | 复杂 AREA 表达式 |
| `pageSize` | 每页(≤1000) |
| `pageToken` | 游标分页 |
| `fields` | 字段裁剪(逗号分隔模块路径) |
| `format` | `json` / `csv` |
| `countTotal` | true 时返回总数(性能差,慎用) |

### 7.2 GET /api/v2/studies/{nctId} (详情)

支持 `fields=` 裁剪,常用值:
- `protocolSection.identificationModule`
- `protocolSection.statusModule`
- `protocolSection.designModule`
- `protocolSection.conditionsModule`
- `protocolSection.armsInterventionsModule`
- `protocolSection.outcomesModule`
- `protocolSection.eligibilityModule`
- `protocolSection.contactsLocationsModule`
- `protocolSection.sponsorCollaboratorsModule`
- `derivedSection`
- `resultsSection`
- `hasResults`

### 7.3 分页(pageToken 游标)

```python
all_records = []
token = None
while True:
    params = {"pageSize": 100, "format": "json"}
    if token:
        params["pageToken"] = token
    data = _fetch(params)
    all_records.extend(data.get("studies", []))
    token = data.get("nextPageToken")
    if not token:
        break
```

## 8. 高级 query DSL (filter.advanced)

格式: `AREA[FieldName]EXPR`

常用 AREA:
- `AREA[ConditionSearch]` — 条件
- `AREA[InterventionName]` — 干预名
- `AREA[OverallStatus]` — 状态
- `AREA[Phase]` — 阶段
- `AREA[LocationCountry]` — 国家(ISO)
- `AREA[LocationCity]` — 城市
- `AREA[LeadSponsorName]` — lead sponsor

布尔: `AND` / `OR` / `NOT`,优先级用括号。

例:
```
AREA[ConditionSearch]"Multiple Myeloma" AND (AREA[Phase]PHASE3 OR AREA[Phase]PHASE2) AND AREA[OverallStatus]RECRUITING
```

## 9. 国家/地点同义词处理

ClinicalTrials.gov `locStr` 模糊匹配常漏值。建议:

| 用户输入 | 实际可能值(全部加 OR) |
|---|---|
| 中国 / China | `China`, `People's Republic of China`, `Hong Kong`, `Taiwan`(若需含) |
| 美国 / US | `United States`, `USA`, `U.S.A.` |
| 北京 / Beijing | `Beijing`, `Peking`, `Beijing, China` |
| 上海 / Shanghai | `Shanghai`, `Shanghai, China` |
| 韩国 / Korea | `Korea, Republic of`, `South Korea` |

推荐统一使用 `query.locn` 自由文本 + 后端再做规范化,或用 `filter.geo=distance(lat,lng,radius_km)` 替代字符串匹配。

## 10. results section 子模块清单

`hasResults=True` 时,`resultsSection` 含:
- `participantFlowModule` — 入组/完成/退出流程
- `baselineCharacteristicsModule` — 基线
- `outcomeMeasuresModule` — 主次终点结果(数值)
- `adverseEventsModule` — 不良事件
- `moreInfoModule` — 限制 / 协议偏离

注意: `hasResults=True` 不保证所有子模块都有内容。访问前需逐一检查 key 是否存在。
