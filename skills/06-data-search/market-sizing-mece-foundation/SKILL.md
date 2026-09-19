---
name: market-sizing-mece-foundation
compatibility:
  upstream: medical-evidence-grading
  downstream: ifi-market-sizing-skill, oncology-sizing-skill, cv-sizing-skill
description: >
  L0 foundation for all medical market-sizing tasks. Use this skill whenever a
  task involves MECE department/age/region/indication slicing, evidence grading,
  drug-target three-state activity matrix, or cross-department patient-flow sizing.
  Trigger phrases: "市场多大", "market sizing", "用药占比", "竞品格局", "患者流". Disease-specific
  L1 skills (ifi-market-sizing-skill, etc.) must reference this first.
---

# Medical Market Sizing — MECE Foundation (L0)

**一句话定义:** 所有医药市场调研 market sizing 任务的跨疾病共性骨架 — 包括 MECE 切分原则、证据分级、药物-靶点三态活性矩阵、Phase 0 通用澄清问题库、Agent 输出 schema 契约。疾病特化 skill (L1) 继承本 skill 后再加专属内容。

> **定位**:本 skill 是 L0 Foundation。疾病特化 skill 是 L1(如 `ifi-market-sizing-skill` 抗真菌、`oncology-sizing-skill` 肿瘤、`cv-sizing-skill` 心血管)。L1 必须在开头引用本 skill,并只维护本疾病专属部分(锚点文献、NMPA 药物清单、专家团队、专属诊疗路径)。

---

## 1. MECE 切分原则(核心 Iron Law)

**MECE = Mutually Exclusive, Collectively Exhaustive**(互斥 + 穷尽)

做医药市场调研时,常见的 4 个切分维度必须分别保证 MECE:

| 维度 | 切分示例 | MECE 陷阱 |
|------|---------|---------|
| **科室** | 血液科 / 呼吸科(含 RICU)/ 综合 ICU / 感染科 / 肿瘤科 / 器官移植 | ❌ 综合 ICU 里的呼吸相关患者被重复算到"呼吸科" |
| **年龄** | 成人 / 儿童(0-17)— 或更细分新生儿/婴幼/青少年 | ❌ "成人"默认包含儿童但没标注 |
| **地理** | 华北/华东/华南/西南/西北/东北 — 或省级 | ❌ 国家级数据不能按科室再拆 |
| **适应症** | 预防 / 经验性治疗 / 诊断驱动 / 目标治疗 / 挽救治疗 | ❌ "一线治疗"同时包含经验+目标模糊 |

### MECE 违反的工程根源

MECE 错误通常不在方法论层,而在 **Phase 2 数据抓取层**。以下三个漏洞必须在 L2 data-agent-template 中堵住:

1. **搜索词模糊**:"ICU" 搜出综合 ICU + RICU 混杂
2. **数据 schema 不强制**:返回数据无 `ward_type` 字段,下游无法过滤
3. **数据不足时默认顶替**:综合 ICU 数据被无声填入呼吸科空白

### MECE 修复三件套(L0 强制)

所有 L1 疾病 skill 必须实施:

**A. Phase 0 强制 MECE 提问**(见第 4 节模板库)
```
Q: 按科室切分时是否走 MECE 互斥?
   A-1 严格互斥(推荐默认):呼吸科 ∩ 综合 ICU = ∅,综合 ICU 数据剔除
   A-2 包含归口:呼吸科 + X% 归口的综合 ICU 患者(标注系数)
   A-3 不区分:仅在单一科室独立调研时使用
```

**B. Phase 2 搜索词模板按 MECE 模式过滤**(见第 6 节)

**C. Agent 输出强制 schema**(见第 7 节)每条证据含 `dept_attribution` + `ward_type` / `age_group` / `region` / `indication_stage` 必要字段

---

## 2. 证据分级标准(跨疾病统一)

| 等级 | 符号 | 定义 | 市场分析可用性 |
|------|------|------|-------------|
| 最高 | 🟢 | 中国多中心 RWE(≥5 中心或 n≥200)或国家级指南/登记 | 可直接用于市场分析 |
| 重要 | 🔵 | 中国单中心 RWE n≥50 或区域多中心 | 可谨慎参考,标注局限 |
| 参考 | 🟡 | 单中心 n<50 / 摘要 / 学位论文 / 行业咨询估算 | 仅作补充参考 |
| 国际 | ⚪ | 国际多中心 / 指南(非中国数据) | 标注"非中国数据"后可参考 |
| 估算 | 🟠 | 基于数据的合理推算 | 必须标注推算逻辑和假设 |

**特殊规则**:
- 指南推荐 ≠ 真实世界比例,两者分列
- 企业赞助但经同行评审 → 正常分级 + 标注赞助方
- 会议摘要 vs 期刊全文 → 以期刊版为准
- 处方分析 / DDD → 等级随中心数和样本量判定

---

## 3. 药物-靶点 三态活性矩阵(跨疾病通用)

**不得用二态(✅/✗)描述药物 × 靶点关系**。必须三态:

| 符号 | 含义 | 判断标准 | 处方含义 |
|------|------|---------|---------|
| 🟢 **说明书适应症** | 药监局(NMPA/FDA/EMA)说明书明确列出 | 查药监官网说明书原文 | 可正常处方,医保支付顺畅 |
| 🟡 **超说明书(off-label)** | 药理学有活性,说明书未列 | 有证据源之一:指南推荐 / RWE / 体外/体内药理学 | 依据指南/共识处方,须告知患者+留档 |
| ❌ **无活性** | 固有耐药 / 无靶点 / 药代不可达 | 有药理学证据(MIC/靶点缺失/PK 失败) | 绝对不应使用 |
| — | 不适用 | 该场景与该药无交集 | N/A |

### 证据码系统(每个 🟡 和 ❌ 必须附)

| 证据码 | 来源类型 | 示例 |
|--------|---------|------|
| `[数字]` | 药监说明书 | `[1]` = 伏立康唑 NMPA 2005 说明书 |
| `[G#]` | 指南/共识 | `[G2]` = ESCMID/ECMM/ERS CPA 2016 |
| `[R#]` | RWE 文献 | `[R1]` = 武汉 220 例 CPA PMC12864492 |
| `[P#]` | 药理学 | `[P1]` = 伏立康唑 MIC90 对 C. neoformans 0.12-0.25 μg/mL |

### 填写步骤(通用于任何疾病)

1. 查药监说明书原文 → 有 → 🟢 + `[数字]`
2. 无说明书 → 查指南 → 推荐 → 🟡 + `[G#]`
3. 查 RWE → 有临床实践 → 🟡 + `[R#]`
4. 查 PK/MIC → 药理学支持 → 🟡 + `[P#]`
5. 均否定 → ❌ 无活性 + `[P#]`(需耐药机制证据)

### 典型误区(任何领域都会犯)

| 药物 × 靶点 | 二态误判 | 三态正解 |
|-----------|---------|--------|
| 伏立康唑 × 隐球菌 | ❌ | 🟡 (IDSA 备选, MIC 低) |
| 奥希替尼 × EGFR Exon20ins | 🟢 | 🟡 (部分活性, NCCN 二线, NMPA 未批亚型) |
| SGLT2i × HFpEF | 因国而异 | 视药监批件状态三态 |

### 3.1 三态核查自问表(v1.2 新增 · Iron Law · 防止简化误判)

> **背景**:v2.0 → v2.1 审阅发现 HTML agent 在"简化三态矩阵(每药 × 每病原 1 格)"时,将原文 🟢[批件号] 错误简化成 🟡(超说明书)。根因:**从多阶段原始矩阵简化到单格视图时,agent 未把"NMPA 批件是否明确列出该病原"作为独立判断维度**,而是误以为"不是一线 = 超说明书"。
>
> **v1.2 补丁**:**每填一格三态前,强制回答以下 5 问;任何 1 问答 Yes,必须 🟢 · 不得降级**:

```
Q1. 该药 NMPA 说明书「适应症」章节是否原文提到该病原 / 靶点?
    (不是"作用机制"或"药理学",而是具体适应症原文)
Q2. 原文是否含以下关键词之一:
    "<病原名>感染" / "对<病原>的治疗" / "<病原>的预防" / 
    "对<药物 A>耐药的<病原>" / "难治性<病原>" / "挽救治疗"?
Q3. 若 Q1/Q2 为 Yes 但限定在"某亚场景"(如粒缺 vs 非粒缺 / 儿童 vs 成人 / 
    一线 vs 挽救),该亚场景在本报告 MECE 范围内是否占主流(≥50%)?
Q4. 若 Q3 为 No (主流场景超出批件),那一格是否应该标 🟢(预防)+ 🟡(治疗)
    双态,而非一刀切 🟡?
Q5. 若所有批件都无,查指南(中国指南 2A 级/2B 级推荐)— 有 → 🟡 · 无 → ❌

简化规则(从 5 阶段 × N 病原 × M 药 缩减到 1 格 × N 病原 × M 药):
  - 5 阶段中 ≥3 阶段 🟢 → 单格 🟢
  - 1-2 阶段 🟢 + 其他 🟡 → 单格 🟢(预防/治疗)注脚区分
  - 全部 🟡 → 单格 🟡
  - 全部 ❌ → 单格 ❌
  - 混合 🟢+🟡+❌ → 单格 🟢(若主流场景内 🟢)· 不可降级为 🟡
```

**违反时的典型信号**:
- 看到"药物 A 在 XX 场景算超说明书"就直接降级整个 🟢 → 🟡
- 忘了"NMPA 批件"与"指南首选"是两个维度 — 批件 🟢 ≠ 一线
- 简化时把"条件限定"(如"13 岁以上")当作"超说明书"—— 不对,只要批件列出,仍是 🟢

### 3.2 NMPA 批件查证清单(v1.2 新增 · 医药类强制)

填三态前,每个药物必须先完成以下两步查证:

**Step A:NMPA 说明书原文查证**
- 官方渠道:https://www.nmpa.gov.cn/ 搜索药品名 → 打开药品说明书 PDF
- 第二渠道:https://www.yaozh.com/ 药智网(国内镜像)
- 第三渠道:丁香园专业版 drugs.dxy.cn
- **必须摘抄**"适应症"章节原文(不是产品介绍/药理学章节)

**Step B:批件证据码系统化归档**
- 每个 🟢 必须附批件号 + 年份 + 适应症原文摘抄
- 每个 🟡 必须附 [G#]/[R#]/[P#] 证据码(L0 第 3 节)
- 每个 ❌ 必须附 [P#] 耐药机制证据

**不得使用"推测"或"国际外推"代替 NMPA 查证**。国际 FDA/EMA 批件在中国任务中仅作 ⚪ 参考,不能自动等价中国 🟢。

---

## 4. Phase 0 通用澄清问题库(强制触发)

> **Iron Law**:无论用户是否给"研究规划摘要",执行前必须输出 3-5 条澄清问题。已给摘要时,审视摘要中未覆盖/有歧义的维度。

### 通用 13 维度检查清单(v1.2 从 12 → 13 维度)

| # | 维度 | 必问情景 | 默认建议 |
|---|------|--------|--------|
| 1 | **MECE 边界** | 跨科室/跨人群时必问 | 严格互斥(剔除邻接科室) |
| 2 | **年龄范围** | 有儿童年龄限制药物时必问 | 成人为主,儿童限制标注 |
| 3 | **地理范围** | 有地域差异病原时必问 | 中国大陆全国,重大差异单列 |
| 4 | **证据窗口** | 有 COVID-19 影响时必问 | 默认隔离 2020-2022 |
| 5 | **市场分母口径** | 任何市场调研必问 | 院内 vs 全口径选一 |
| 6 | **药物范围** | 是否含非抗真菌/邻接治疗药? | 明确列清 |
| 7 | **输出语言** | 中/英/双语 | 中文(国内任务) |
| 8 | **目标读者** | 药企/KOL/投资方/政策 | 中立多方可读 |
| 9 | **报告呈现顺序** | 咨询式 vs 学术式 | 咨询式(TOC+图表索引+附录) |
| 10 | **立场** | 中立第三方 vs 特定产品 | 中立 |
| 11 | **科室归属边界(MECE 跨科室)** | 科室切分时必问(关键) | 严格 MECE(剔除综合 ICU 等邻接独立科室) |
| **12** | **科室内疾病/病因细分(v1.2 新增 Iron Law)** | **每次做科室 market sizing 必问** | **见下方"科室内细分粒度参考表"**;不同疾病的 IFI 发生率/治疗方案/药物比例差异极大,严禁合并为单一"高危池" |
| 13 | **MRR 骨架** | 是否加 TAM/SAM/SOM | 加(sizing 核心) |

### 科室内疾病/病因细分粒度参考表(v1.2 新增)

> **血液科 v1.2 前复盘**:新版报告把 AML/HSCT/MDS 合并为"高危层单一池",完全丢失了每种疾病的 IFI 发生率/预防用药比例。
> **Iron Law**:Phase 0 必须问"科室内按什么疾病/病因拆分",每个亚人群必须在瀑布图中作为**独立分支**(不可合并)。

| 科室 | 疾病/病因最小拆分粒度 | 说明 |
|------|-------------------|------|
| **血液科** | allo-HSCT · auto-HSCT · AML诱导 · AML维持 · ALL · NHL · HL · MM · MDS-IST · CML · CLL · 再障ATG · CAR-T · 非恶性血液病 | 参照 CAESAR 2.0 亚人群分层 |
| **呼吸科** | 4 大入口(免疫缺陷/RICU/慢性肺病/免疫正常)× 7 分型(IPA/CPA/ABPA/隐球菌/毛霉/PJP/念珠菌) | 树状分支已在 ifi-market-sizing-skill 验证 |
| **综合 ICU** | 高危宿主 swim-lane(免疫抑制 · 长期激素 · COPD · DKA · CTD · SICU术后)× 5 病原(念珠菌 · 曲霉 · PJP · 毛霉 · 隐球菌)× 病毒叠加(IAPA/CAPA) | MECE 剔除 RICU;**每个病原必须独立分支,不共用诊断/治疗节点** |
| **SOT 器官移植** | 肝 · 肾 · 心 · 肺 · 胰 · 小肠 | 各器官 IFI 风险与预防用药差异大 |
| **实体肿瘤** | 按癌种(肺 · 消化道 · 血液转移)× 治疗线(化疗/靶向/免疫) | — |

数据不足时 🟠 推算填空,**但分支结构必须保留**。

### Phase 0 输出模板

```
=== Phase 0 澄清问题(请回复后再执行)===
1. [维度]:[具体问题]
   - 默认建议:[值]
2. …
=== 等用户回复 ===
=== 收到回复后输出研究规划摘要 ===
```

---

## 5. Red Flags — 违反 Phase 0 或 MECE 的警示信号

看到这些念头立即停下来:

| 念头 | 为什么是违规信号 |
|------|---------------|
| "用户已给摘要,直接执行" | 摘要不等于 12 维度对齐,须审视缺口 |
| "科室就是 X 科室,不用区分" | 科室内部有亚专业(RICU vs 病房),必须区分 |
| "数据不够,用邻接科室顶替" | MECE 违反,宁可留空 🟠 推算 |
| "ICU 就是 ICU" | 综合 ICU vs 专科 ICU(RICU/CCU/NICU/SICU)完全不同 |
| "成人和儿童差不多" | 药物年龄限制严格,必须分层 |
| "先干再说,有问题再改" | MECE 一旦污染,返工成本 10x |

---

## 6. Phase 2 数据抓取 · MECE 模式搜索词模板

### 科室 MECE 切分(以本骨架覆盖的常见科室)

**呼吸科(RICU only,严格互斥)**
```
PubMed: ("respiratory intensive care unit" OR "respiratory ICU" OR RICU OR
         "respiratory ward") AND <disease keywords> AND China
        NOT ("medical ICU" OR MICU OR "surgical ICU" OR SICU OR
             "mixed ICU" OR "general ICU")
CNKI:  "呼吸重症" OR "呼吸ICU" OR "呼吸科ICU" -综合ICU -MICU -SICU
期刊:  中华结核和呼吸杂志 / 中华呼吸与危重症医学杂志
团队:  呼吸与危重症医学科 KOL(如曹彬/解立新/施毅)
```

**综合 ICU(不含 RICU)**
```
PubMed: ("medical ICU" OR "surgical ICU" OR "mixed ICU" OR "general ICU" OR
         MICU OR SICU) AND <disease> NOT respiratory
```

**血液科(不含其他)**
```
PubMed: ("hematology ward" OR "HSCT unit" OR "bone marrow transplant" OR
         "leukemia ward") AND <disease>
```

**儿科(不含成人)**
```
PubMed: (pediatric OR paediatric OR "children" OR neonatal OR NICU OR PICU)
        AND <disease>
```

### 科室归属过滤关键词

搜索完成后,对每条返回的文献用以下关键词判断科室归属:

- RICU / 呼吸 ICU / 呼吸重症 / 呼吸与危重症 → `ward_type: RICU`
- MICU / 内科 ICU / 医学 ICU → `ward_type: MICU`
- SICU / 外科 ICU → `ward_type: SICU`
- 综合 ICU / 中心 ICU / mixed ICU / general ICU → `ward_type: general_ICU`
- ICU(无限定) → `ward_type: unclear`(默认剔除)

---

## 7. Agent 输出 Schema 契约(文档级,Phase 1 软约束)

> Phase 1 只在文档层写清楚约定（当前状态）。**升级条件**：L2 data-agent 上线后，
> 将本 schema 移至 `scripts/validate_schema.py` 并在 pipeline 中硬阻塞。
> 主 agent 在启动 Phase 2 data-agent 时,必须将本 schema 嵌入 agent prompt。

### 证据条目 schema

```yaml
evidence_item:
  study_name: string            # 研究名或作者+年份
  sample_size: int
  evidence_grade: 🟢|🔵|🟡|⚪|🟠
  pmid_doi: string              # 必须有,否则降级为 🟡
  ward_type: RICU|MICU|SICU|general_ICU|mixed|unclear  # 必填
  dept_attribution: respiratory|ICU_independent|hematology|oncology|other  # 必填
  age_group: adult|pediatric|mixed|unclear
  region: national|province|municipal|single_center
  indication_stage: prevention|empirical|DD|target|salvage|maintenance
  time_window: YYYY-YYYY
```

### schema 违反时的处理

- 缺 `ward_type` 或为 `unclear` → 该条从"目标口径基线"剔除,降级到"参考"
- 缺 `dept_attribution` → 同上
- `ward_type` 与目标科室不匹配(如做呼吸科但 ward_type = MICU)→ **强制剔除**,可放入"邻接科室对照"附录
- 数据不足无法填目标口径 → 留空 + 🟠 推算,**绝不以邻接科室数据顶替**

---

## 8. L1 疾病特化 skill 的编写规范

### L1 应该维护什么

✅ **专属内容**(L1 必有):
- 疾病 NMPA 药物清单(如抗真菌 14 药 / 肿瘤靶向药组 / 降压药组)
- 疾病锚点文献(如 Zhou EID 2020 真菌负担 / CAESAR 血液 IFI)
- 疾病专家团队(如抗真菌的施毅/曹彬 vs 肿瘤的孙燕/吴一龙)
- 疾病专属诊疗路径(如真菌 4 入口 vs 肿瘤 5 线治疗)
- 疾病专属的 NMPA 适应症表(通用三态规则来自 L0,具体药-病原映射是 L1 专属)

### L1 不应该维护什么

❌ **应在 L0 的内容**(L1 不重复):
- MECE 原则(抽象)
- 证据分级 🟢🔵🟡⚪🟠
- 三态活性矩阵 规则
- Phase 0 通用 12 维度
- Phase 2 通用搜索词模板
- Agent schema 契约
- Red Flags 通用列表

### L1 引用 L0 的方式

L1 SKILL.md 开头:
```markdown
> **依赖**:本 skill 是 L1 疾病特化,继承 L0 `market-sizing-mece-foundation`。
> 使用本 skill 前请先读 L0 的 MECE 原则、证据分级、三态矩阵、Phase 0 问题库、
> Phase 2 搜索词模板、Agent schema 契约。
```

---

## 9. 已知失败模式(跨疾病通用)

| # | 失败模式 | 根因 | 修复规则 |
|---|--------|------|---------|
| 1 | MECE 违反 - 邻接科室混入 | Phase 2 搜索词不严格 + 无 ward_type schema | 第 6-7 节 |
| 2 | 无适应症被误标为无活性 | 二态表达不足 | 第 3 节三态 |
| 3 | 超说明书无证据来源 | 缺证据码系统 | 第 3 节 [G#/R#/P#] |
| 4 | Phase 0 漏触发 | 用户给摘要就跳过 | 第 4 节 Iron Law |
| 5 | 数据不足以邻接科室顶替 | 缺 schema 强制 | 第 7 节"强制剔除"规则 |
| 6 | 成人药物套用儿童 | 年龄维度漏 MECE | 第 1 节 + 第 4 节 |

---

## 10. LP 决策图(Leverage Points)呈现规范

> v1.1 新增。**LP 决策图**是基于 market sizing 结论**按 Impact 排序的策略切入点可视化**,在最终报告作为独立章节(通常第 7 章)呈现。

### 10.1 LP 定义
- LP = Leverage Point,指"该杠杆点改进后可直接受益的年度患者数"
- **MECE 原则**:LP 之间不重叠,覆盖市场主要未满足需求
- 通常 5-10 个 LP 为宜,按 Impact 中位数从大到小排列

### 10.2 LP Impact 三列量化
| 字段 | 含义 |
|------|------|
| Impact low | 保守估算(最低识别率/最小可及率) |
| Impact mid | **排序基准**(仅作优先级参考,非精确值) |
| Impact high | 乐观估算(最高识别率/最大可及率) |

### 10.3 LP 在瀑布图上的标注(Mermaid 实现)

**关键原则**:LP 标签必须是**独立于业务节点的视觉元素**,而非混在节点文字内。

**错误示范**(节点内前缀,视觉淹没):
```
C_CPA["🏆 <b>LP1</b> CPA 长程未满足 · Impact 127-345k<br/>CPA 20-30%..."]
```

**正确示范**(独立 stadium badge + 虚线连接):
```mermaid
C_CPA["<b>CPA</b> 20-30% 🟢<br/>Zhou 2020 现患 48.9万..."]
LP1(["🏆 LP1"]):::lpBadgeCrown
LP1 -.- C_CPA

classDef lpBadge fill:#DC2626,stroke:#7F1D1D,stroke-width:3px,color:#FFFFFF,font-weight:bold
classDef lpBadgeCrown fill:#F59E0B,stroke:#78350F,stroke-width:4px,color:#FFFFFF,font-weight:bold
```

### 10.4 LP Badge 视觉分层(三态)

| Tier | 配色 | 粗边 | 适用 |
|------|------|------|------|
| 🏆 Crown(最大杠杆点) | 金底 `#F59E0B` / 深棕边 `#78350F` | 4px | **Impact 最大的 1 个 LP** |
| 🔴 Standard(标准) | 红底 `#DC2626` / 深红边 `#7F1D1D` | 3px | 其他可嵌入瀑布图的 LP |
| ⬜ Cross-entry(跨入口) | 灰底 · 虚线边 | 2px dashed | 跨多入口亚组的 LP(如儿童、年龄分层),**无法嵌入瀑布图时用灰虚线,报告另附亚组图** |

### 10.5 LP 跨入口情况

当一个 LP 在**多个入口/分支**都有作用点时,在每个 subgraph 内各放一个 badge(用后缀区分):

```
LP3_A(["🔬 LP3"]):::lpBadge
LP3_A -.- DX_A   %% 入口 A 的 LP3

LP3_B(["🔬 LP3"]):::lpBadge
LP3_B -.- DX_B   %% 入口 B 的 LP3
```

这让瀑布图中同一 LP 的多个作用点都被标注,避免"挂哪个好"的取舍。

### 10.6 LP Icon 语义建议(emoji)

| Icon | 语义 | 示例 |
|------|------|------|
| 🏆 | Champion / 最大杠杆 | LP1 必用 |
| 🎯 | Target / 识别精准 | 如"门诊识别率提升" |
| 🔬 | Lab / 诊断基建 | 如"mNGS 协同检测" |
| 🌿 | Long-tail / 长尾稳定 | 如"免疫正常长程用药" |
| ⚙️ | Gear / 规范化治理 | 如"指南化/AFS 规范" |
| 💊 | Drug / 药物窗口 | 如"新药独家窗口" |
| 👶 | Baby / 儿童亚组 | LP 跨入口儿童专属 |
| 🌍 | Globe / 地域差异 | LP 跨地区 |

Icon 可自定义,但必须**每个 LP 专属不重复**。

### 10.7 报告章节结构(7. LP 决策图)

```
七、LP 决策图(Leverage Points)
 ├ 7.1 LP 在患者流瀑布图上的具体位置
 │      └ 图 7.1(含独立 LP badge + 虚线连接)
 │      └ 阅读指南 callout(说明 badge 配色分层 / 跨入口处理)
 ├ 7.2 LP 排序表(按 Impact 中位数)
 │      └ 字段:LP# | 策略切入点 | Impact 区间 | 中位数 | 关键依据 | 原编号
 │      └ ⚠️ 不要有"瀑布图位置"列(已在图上标,冗余)
 ├ 7.3 跨入口 LP 单独说明(如有)
 └ 7.4 LP 量化方法说明
```

### 10.8 LP 立场规范(中立第三方)

**严禁**在 LP 策略建议中出现**具体药物/产品推荐**。
- ❌ 错:"可通过伊曲康唑 TDM 普及 + 医保长疗程支付破局"
- ✅ 对:"需解决三大摩擦——长程 TDM 工具普及、医保长疗程支付机制、基层诊疗路径教育。属于全市场结构性机会,不偏向任何单一产品"

同样语言的正/反对照见第 12 节"去产品化语言规范"。

---

## 11. 报告呈现:字体与配色规范(参照 market-research-reports)

> v1.1 新增。所有 market sizing 报告的 HTML/PDF 渲染参照 `market-research-reports` skill 的 `market_research.sty` 调色板和字号,以保证咨询公司级专业度。

### 11.1 调色板(与 MRR 对齐)

| 角色 | Hex | RGB | 用途 |
|------|-----|-----|------|
| Primary Navy | `#003366` | 0,51,102 | h1 标题、表头色 |
| Secondary Blue | `#336699` | 51,102,153 | h2/h3、强调文字 |
| Accent Blue | `#0078D7` | 0,120,215 | callout box / 链接 |
| Accent Green | `#008060` | 0,128,96 | data hint box、🟢 A 级证据 |
| Warning Orange | `#FF8C00` | 255,140,0 | 🟡 C 级 / 🟠 估算 |
| Alert Red | `#C62828` | 198,40,40 | warning box / 🔴 风险 |

### 11.2 字号(MRR LaTeX 11pt 正文对齐)

| 层级 | HTML PDF | 备注 |
|------|---------|------|
| 正文 | **11pt** | 对齐 MRR 11pt(非 10.5pt) |
| 表格 | 10pt | 含 `font-variant-numeric: tabular-nums` 对齐数字 |
| h1 | 22pt / 700 | 章节标题,navy · 2.5pt 下边框 |
| h2 | 15pt / 700 | 小节,navy · 4pt 左边框(blue) |
| h3 | 12pt / 600 | blue |
| h4 | 11pt / 600 | gray-700 |
| caption | 9pt italic | 图表注释 |
| 行距 | 1.65 | 正文;表格 1.5 |

### 11.3 字体家族(中英混排)

```css
:root {
  --font-sans: 'Source Han Sans CN', 'Noto Sans SC', 'PingFang SC',
               'Microsoft YaHei', -apple-system, 'Helvetica Neue', Arial, sans-serif;
  --font-mono: 'JetBrains Mono', 'Consolas', 'Menlo', monospace;
}
```

优先级理由:**思源黑体 SC(Source Han Sans CN)→ 苹方(PingFang SC)→ 微软雅黑**,覆盖 macOS/Windows,视觉最一致。

### 11.4 Box 环境(对齐 MRR 四色系)

| 类型 | 边色 · 背景 | 用途 |
|------|-----------|------|
| `.callout` | 蓝 #0078D7 · 浅蓝 #E6F1FB | **Key Insight / 说明** |
| `.warning` | 红 #C62828 · 浅红 #FFEBEE | **Critical Risk** |
| `.datahint` | 绿 #008060 · 浅绿 #C8E6C9 | **Market Data Box** |
| (可选) `.recommendation` | 紫 #6A1B9A · 浅紫 | 策略建议(但 market sizing 立场通常用 callout) |

---

## 12. 去产品化语言规范(中立第三方 Iron Law)

> v1.1 新增。所有 market sizing 报告默认"中立第三方"立场时,LP 建议 / 策略切入点 / 结论章节**严禁偏袒具体药物/产品**。

### 12.1 禁语示例

| ❌ 错(偏袒单一产品) | ✅ 对(中立市场视角) |
|---------------------|-------------------|
| "可通过**伊曲康唑 TDM** 破局" | "需解决**长程 TDM 工具普及**摩擦" |
| "**单伊曲康唑长程处方**即增量 2-3 亿元" | "**长程抗真菌处方扩量** → 整个三唑类赛道扩容" |
| "**艾沙康唑毛霉独家**窗口" | "**毛霉识别与精准用药闭环** → 多烯类+口服序贯市场同步扩容" |
| "对**某药企**的决策工具有临床教育价值" | "规范化 AFS 决策 → 整体降低资源浪费" |

### 12.2 通用模式

**结构**:
- "【痛点规模】 → 【解决摩擦】 → 【带动整个赛道/子市场】"

**动词选择**:
- ✅ 扩容 / 规范 / 普及 / 识别 / 基建 / 教育 / 闭环
- ❌ 首选 / 最佳 / 优于 / 碾压 / 主导 / 独占

**主体措辞**:
- ✅ "整个 [赛道/品类] 规模性扩容"
- ✅ "结构性机会,不偏向任何单一产品"
- ✅ "市场基建 / 行业共建"
- ❌ "【某药】 市场份额提升 X%"(除非明确是该药企定制报告)

### 12.3 例外:特定产品策略导向报告

如 Phase 0 明确 `report_stance: 特定产品策略导向(如 XXX 药企委托)`,则 LP 建议可包含该产品推荐。**但必须在封面和执行摘要明确标注立场**,避免读者误解为中立第三方观点。

---

## 13. 工程:两遍渲染 PDF 生成页码(Chrome headless)

> v1.1 新增。Chrome headless 不支持 CSS `target-counter(attr(href url), page)` 和 `leader()`,直接用失效。
> Paged.js polyfill 在 Chrome headless 中渲染超时不稳。
> **推荐方案:Python 两遍渲染法**(可靠 · 零外部依赖)。

### 13.1 流程

```
Pass 1: 渲染 HTML → PDF (TOC 页码占位空)
         ↓
Pass 2: pypdf 扫描每页文本,搜章节标题关键字首次出现的页 → 得到 {anchor: page_num}
         ↓
Pass 3: 正则替换 HTML 中的 <span class="page"></span> 为 <span class="page">N</span>
         ↓
Pass 4: 再次渲染 HTML → PDF(最终带页码)
```

### 13.2 HTML TOC 结构契约

```html
<div class="toc">
  <ol>
    <li><a href="#ch1">
         <span class="title">一、执行摘要</span>
         <span class="dots"></span>
         <span class="page"></span>     <!-- 占位,两遍渲染脚本注入 -->
       </a></li>
    ...
  </ol>
</div>
```

CSS:
```css
.toc a { display: flex; align-items: baseline; gap: 6pt; }
.toc a .title { white-space: nowrap; }
.toc a .dots  { flex: 1; border-bottom: 1pt dotted #ccc; transform: translateY(-2pt); }
.toc a .page  { white-space: nowrap; font-variant-numeric: tabular-nums; color: #666; }
```

### 13.3 Python 参考脚本

见仓库 `output/build_pdf_two_pass.py`。核心逻辑:

```python
TOC_ANCHORS = [('#ch1', '一、执行摘要'), ('#ch2', '二、研究方法'), ...]

def measure_page_numbers(pdf_path):
    reader = PdfReader(str(pdf_path))
    pages = [(p.extract_text() or '') for p in reader.pages]
    result = {}
    for href, keyword in TOC_ANCHORS:
        # 从第 4 页开始搜(跳过 TOC 本身)
        for i in range(2, len(pages)):
            if keyword in pages[i]:
                result[href] = i + 1  # 1-indexed
                break
        else:
            result[href] = None
    return result

def inject_page_numbers(html_path, page_map):
    html = html_path.read_text(encoding='utf-8')
    for href, page_num in page_map.items():
        pattern = (
            r'(<a href="' + re.escape(href) + r'">'
            r'<span class="title">[^<]+</span>'
            r'<span class="dots"></span>'
            r'<span class="page">)(</span></a>)'
        )
        html = re.sub(pattern, r'\g<1>' + str(page_num or '—') + r'\g<2>', html)
    html_path.write_text(html, encoding='utf-8')
```

### 13.4 WPS/Adobe 占用 PDF 文件的 fallback

```python
def pick_pdf_path():
    try:
        if PRIMARY.exists():
            PRIMARY.rename(PRIMARY)  # 测试可写
        return PRIMARY
    except PermissionError:
        print(f'⚠ {PRIMARY.name} 被其他程序占用, fallback 到 {FALLBACK.name}')
        return FALLBACK
```

---

## 14. 署名规则(强制规范 · 所有输出物)

> v1.1 新增。所有 market sizing 报告、流程图、交付物封面必须包含 skill 署名。

### 14.1 标准文字(精确匹配)

```
Skill Presented by:YongQi, SimonSu, RuiYu, YingJi
```

**格式要点**:
- 冒号后**无空格** (`by:YongQi`)
- 姓名之间用英文**逗号+空格** (`, `)
- 4 人顺序固定:**YongQi, SimonSu, RuiYu, YingJi**
- 禁止使用中点分隔符 `·`(v1.0 用过,v1.1 起废弃)
- 禁止使用中文顿号 `、`

### 14.2 出现位置

| 载体 | 位置 | 字号/样式 |
|------|------|----------|
| PDF/HTML 报告 | 封面 · 最后一行(方法依据下方) | 小字灰色 9pt · `color: var(--gray-500)` |
| Mermaid HTML 流程图 | header 底部 credit 行 | 11px 半透明 · `opacity: .65` |
| Mermaid .mmd 源文件 | 文件顶部 comment 区 | `%% Skill Presented by: YongQi, SimonSu, RuiYu, YingJi` |
| docx 封面 | 最末段 | 16pt 灰色 · `color: '888888'` |
| 参数包 yaml | 文件头注释 | `# 署名: Presented by YongQi, SimonSu, RuiYu, YingJi` |

### 14.3 替换脚本(跨项目迁移时用)

```python
import re
from pathlib import Path

# 统一替换各种旧格式为新标准
PATTERNS = [
    (r'YongQi\s*·\s*SimonSu\s*·\s*RuiYu(?!\s*,?\s*YingJi)',
     'YongQi, SimonSu, RuiYu, YingJi'),
    (r'YongQi,\s*SimonSu,\s*RuiYu(?!\s*,?\s*YingJi)',
     'YongQi, SimonSu, RuiYu, YingJi'),
    (r'YongQi、SimonSu、RuiYu(?!.*YingJi)',
     'YongQi, SimonSu, RuiYu, YingJi'),
]

for fp in Path('.').rglob('*'):
    if fp.suffix in ('.md', '.mmd', '.js', '.yaml', '.yml', '.html'):
        content = fp.read_text(encoding='utf-8')
        for pat, repl in PATTERNS:
            content = re.sub(pat, repl, content)
        fp.write_text(content, encoding='utf-8')
```

---

## 15. 流程图验证 Iron Law(v1.2 新增 · 强制机器约束)

> **背景**:v1.2 前三次复盘发现同类流程图缺陷跨项目复现 —— Mermaid 语法错误、分支无终点、多源汇聚交叉。
> 根因:规则在文档里,但子 agent 生成 .mmd 后**无机器验证**,直接嵌入 PDF 才暴露。
> **Iron Law**:所有 `.mmd` 文件在渲染 PNG/嵌入 PDF 之前,**必须运行 `references/flowchart-validator.py` 通过**。
> return code = 2 阻塞渲染流水线,return code = 1 软警告。

### 15.1 标准流水线(L1 报告生成器必须遵守)

```bash
# Step 1: 结构 + 语法验证(硬约束)
python references/flowchart-validator.py output/flowchart.mmd
if return_code == 2: 停止,根据错误信息修复 .mmd,重跑
if return_code == 1: 软警告,记录但可继续

# Step 2: 验证通过后才渲染 PNG
mmdc -i output/flowchart.mmd -o output/flowchart.png -w 5000 --scale 2 ...

# Step 3: 嵌入 HTML/PDF
```

### 15.2 Validator 覆盖的 7 项自动检查

| # | 检查项 | 类型 | v1.2 前真实错误 |
|---|-------|------|----------------|
| 1 | `mmdc` 渲染测试 | **硬错误** | ICU `Parse error on line 1: ---config` |
| 2 | YAML frontmatter 首行位置 | **硬错误** | ICU `%% 注释` 放在 `---` 前 → mermaid 10.9+ 失败 |
| 3 | 每个叶子 `●` 终止(规则 2) | **硬错误** | ICU LP `●=0` 所有分支悬空;血液科 3 个 `_PROPH` 叶子无终止 |
| 4 | 复杂图 ≥3 subgraph(规则 4) | 软警告 | ICU `subgraph=0` swim-lane 丢失 |
| 5 | 无多入度 ≥3 共用节点(规则 15) | 软警告 | ICU `HOSTS --> A&B&C&D&E`, 然后 `A/B/C/D/E --> DIAG` 多源汇聚 |
| 6 | 必须含诊断层 | 软警告 | 纯流行病图会触发 |
| 7 | 必须含治疗层 | 软警告 | 纯路由图会触发 |

### 15.3 flowchart-rules 同步新增(规则 13-15,写入 L1 flowchart-rules.md)

- **规则 13 · YAML frontmatter 首行**:若使用 `---` frontmatter,**第 1 行必须是 `---`**。前面不得有注释/空行/任何字符。
- **规则 14 · validator 必须通过**:所有 `.mmd` 必须通过 validator 才能渲染 PNG。
- **规则 15 · 禁止多源汇聚共用节点**:非明确评估/路由/汇聚节点(`EVAL_ / ROUTER / SCREEN / END_ / DIAG / RETURN`),**入度不得 ≥ 3**。多分支需要经过相同诊断/治疗节点时,**必须拆成独立节点**(如 `DIAG_CAND / DIAG_ASP / DIAG_PJP`),即使文字相同。

### 15.4 合规率统计(自检)

本 skill 发布时,对历史 3 个项目的 `.mmd` 文件做合规回溯:

| 项目 | .mmd 文件 | 硬错误数 | 软警告数 | 修复后 |
|------|---------|---------|---------|-------|
| 呼吸科(v1.3.3) | flowchart.mmd + flowchart_lp.mmd | 0 | 0-1 | ✅ |
| ICU(v1.0) | patient_flow_normal.mmd | 2(frontmatter + ●终止) | 1 | ❌ → 需重跑 |
| ICU(v1.0) | lp_decision_map.mmd | 2(同上) | 2(subgraph=0 + 多入度) | ❌ → 需重跑 |
| 血液科(v2.0) | flowchart.mmd | 1(3 叶子无 ●) | 1(H_MAINT 多入度) | ❌ → 需重跑 |

**Iron Law 效果**:如果 validator 在 v1.2 前就存在,三个项目都会在渲染阶段被拦截,不会进入用户可见的 PDF。

---

## 16. 医学术语规范对照表(v1.3 新增 · 跨疾病通用)

> **背景**:v2.1 审阅发现 HTML agent 把 "breakthrough IFI"(预防期感染)中文化为"**IFI 爆发**",这是**严重医学术语错误**。"爆发"(outbreak)是公共卫生疫情暴发含义,与个体患者"突破性感染"(breakthrough infection)完全不同。
>
> **Iron Law**:所有 medical market sizing 报告必须严格遵守以下中英医学术语对照表,禁止任意意译。

### 16.1 常见英→中医学术语(任何领域通用)

| English | ✅ 正确中文 | ❌ 错误中文(常见误译) | 注释 |
|---------|----------|---------------------|------|
| breakthrough infection | **突破性感染** / **突破** | ❌ 爆发(爆发=outbreak 疫情含义) | 特指预防/治疗期间仍发生的感染 |
| outbreak | **暴发** / **疫情暴发** | ❌ 爆发 | "暴"字正,群体性 |
| prophylaxis | **预防** / **预防治疗** | ❌ 先期治疗 | 一级预防 = 未感染时预防 |
| empirical therapy | **经验治疗** / **经验性治疗** | ❌ 经验主义治疗 | FN 无真菌证据时 |
| diagnostic-driven therapy (DD) | **诊断驱动治疗** | ❌ 诊断指导治疗(不推荐)/ 先发治疗(错误) | 有微生物阳性但未 proven |
| targeted therapy (IFI 领域) | **目标治疗** | ❌ 靶向治疗(=molecular targeted 分子靶向) | 区别于肿瘤"靶向治疗" |
| salvage therapy | **挽救治疗** | ❌ 营救治疗 | 一线失败后 |
| refractory | **难治 / 难治性** | ❌ 耐药(耐药=resistant) | 治疗无应答 |
| relapse | **复发** | ❌ 爆发 / 再发(不精准) | 缓解后再发 |
| persistence | **持续感染** | ❌ 持续性 | |
| colonization | **定植** | ❌ 殖民化 | 无感染征象 |
| proven | **确诊(级)** | ❌ 确定 / 验证 | EORTC/MSG 定义 |
| probable | **临床诊断(级)** | ❌ 可能诊断 | EORTC/MSG 定义 |
| possible | **拟诊(级)** | ❌ 可能 / 疑诊(部分场景可) | EORTC/MSG 定义 |
| incidence | **发病率** | ❌ 发生率(语境敏感) | 新发/时间单位 |
| prevalence | **患病率** / **现患率** | ❌ 流行率(不精准) | 某时点已有病例 |
| cumulative incidence | **累积发生率** | ❌ 累积发病率(可混用) | 某时间窗内新发 |
| attributable mortality | **归因死亡率** | ❌ 相关死亡率 | 该病直接导致 |
| all-cause mortality | **全因死亡率** | ❌ 总死亡率 | 各原因死亡合计 |
| off-label | **超说明书** / **超适应症** | ❌ 标签外(不专业) | 中文正式报告 |
| on-label | **说明书内** / **适应症内** | ❌ 批件内(可混用) | |
| TDM (therapeutic drug monitoring) | **治疗药物监测** | ❌ 药物浓度监测(不精准) | 含浓度+疗效评估 |
| GVHD (graft-versus-host disease) | **移植物抗宿主病** | ❌ 宿主抗移植物病(倒置) | 免疫学术语 |
| CRS (cytokine release syndrome) | **细胞因子释放综合征** | ❌ 细胞因子风暴(colloquial · 不规范) | CAR-T 后 |
| ICANS | **免疫效应细胞相关神经毒性综合征** | ❌ CAR-T 神经毒性(不规范) | CAR-T 后 |
| high-dose methotrexate (HD-MTX) | **大剂量甲氨蝶呤** | ❌ 高剂量 MTX(直译) | ALL 化疗 |

### 16.2 使用规则

- **报告正文/流程图/表格/图注**:全部使用"✅ 正确中文"
- **引用原文献/共识名称**:可保留原词不变(如 "2025 免疫/靶向治疗感染共识" 是官方名)
- **英文缩写**:首次出现附中文全称 + 英文缩写,之后可仅用缩写
- **Phase 4 质量审核必查**:grep 以下关键词必须零命中:
  ```bash
  grep -n "爆发\|确诊分级\|标签外\|营救治疗\|先期治疗" output/**/*.md evidence/**/*.md
  ```
  命中即阻塞交付。

### 16.3 跨领域等价术语(肿瘤/心血管等)

肿瘤领域"靶向治疗"合法(特指分子靶向 molecular targeted therapy),但**在抗感染语境必须用"目标治疗"**。疾病领域切换时必须重新校准术语表。

---

## 17. 版本

- **v1.0**:从 ifi-market-sizing-skill v1.2 提取共性骨架
- **v1.1**:LP 决策图规范(§10) + MRR 字体对齐(§11) + 去产品化语言(§12) + 两遍渲染 PDF 工程(§13)
- **v1.2**:Iron Law §15 流程图验证器 + Phase 0 从 12 → 13 维度 + flowchart-rules.md 新增规则 13-15
- **v1.3(本版)**:
  - §3.1 三态核查自问表(5 问 Iron Law)+ §3.2 NMPA 批件查证清单
  - §16 医学术语规范对照表(22 条英→中对照 · 防止 "breakthrough → 爆发" 类误译)
  - 根因:v2.0 → v2.1 审阅发现 HTML agent 简化三态矩阵时误判 · 术语"爆发"医学语境错误
- 计划 v1.4:补充肿瘤/心血管科疾病细分粒度表 + flowchart-templates/ 样板库
- 计划 Phase 2:L2 agent prompt schema 硬验证 + L3 跨报告一致性 meta skill
