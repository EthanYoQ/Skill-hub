---
name: ifi-market-sizing-skill
description: >
  Use when user requests medical/pharmaceutical market sizing, Chinese clinical
  pathway reconstruction, patient flow waterfall charts, drug usage composition
  analysis, unmet need quantification, prescription share estimation, competitive
  landscape for antifungals/oncology/ICU drugs, or says things like "估算某市场多大",
  "画个诊疗路径图", "做个 market sizing", "分析用药占比". Also triggers on
  disease×department×drug class combinations (血液科 IFI, 呼吸科真菌, ICU真菌,
  肿瘤免疫). Works for 中立第三方 or 特定产品策略 stances. Supports Agent Teams
  as the foundation for market research sub-agents.
  [Domain reference] Generic flow now lives in `disease-market-sizing-orchestration` + 7 retrieval skills.
---

# 临床路径Market Sizing Skill (L1 · 侵袭性真菌感染特化 · v1.6)

> **v1.6 (2026-04-25 · IFI 侵袭性真菌感染特化 · 血液科基准 · v2.5.1 修正后)**:新增 3 条 Iron Law(失败模式 #29-31)防 v2.5.1 暴露的问题再次复现:#29 主图与 LP 图分离(一图一主题,主图禁嵌 LP_BADGE) · #30 LP 决策图必须基于双分支(或多分支)模型,单分支会低估 30-50%+ 旁支 unmet need · #31 evidence/ ↔ 报告附录 C 强制双向同步,禁止"手写附录 C 取舍",必须 grep evidence/ 全量列出。
>
> **v1.5 (2026-04-25 血液科 v2.5 第 6 次迭代)**:新增 §5.3 HTML 报告完整性清单 Iron Law(防 LP 决策图 + 决策树节点级 LP 标注复现遗漏);LP 嵌入规范拆出为 L2 skill `decision-tree-with-lp-embedding`,HTML 模板拆出为 L2 skill `disease-market-sizing-html-template`,跨疾病编排升级为 L3 skill `disease-market-sizing-orchestration`(可移植至呼吸科 ICU)。
>
> **依赖 L0 Foundation**:本 skill 是 L1 疾病特化,继承 `market-sizing-mece-foundation` (L0)。
> **使用本 skill 前必须先读 L0**,其中包含:
> - MECE 切分原则(科室/年龄/地理/适应症 4 维)
> - 证据分级 🟢🔵🟡⚪🟠 通用标准
> - 药物-靶点 三态活性矩阵(🟢/🟡/❌)+ 证据码系统 [G#/R#/P#]
> - Phase 0 通用 12 维度澄清问题库
> - Phase 2 数据抓取 MECE 模式搜索词模板
> - Agent 输出 schema 契约(ward_type/dept_attribution 等)
> - 跨疾病通用 Red Flags + 失败模式
>
> **本 L1 skill 只维护**:侵袭性真菌感染(IFI)专属的锚点文献、NMPA 药物清单、专家团队、诊疗路径。跨疾病共性规则请查阅 L0。

**一句话定义:** 从公开循证文献中还原**侵袭性真菌感染**在中国真实世界的诊疗路径,在每个决策节点量化患者分流比例和药物使用构成,生成可直接驱动 market size 测算的患者流瀑布图和 PDF 报告。

---

## Phase 0：需求对齐（执行前必须完成 · 强制触发）

> ⚠️ **Iron Law(违反即返工)**:无论用户是否已给出"研究规划摘要",**执行前必须输出至少 3–5 条澄清问题并等待用户回复**。已给摘要的情况下,审视摘要中未覆盖/有歧义的维度,就这些维度提问;**绝对禁止**以"用户已给摘要"为由跳过对齐环节,直接执行。

### 🛑 Red Flags — 这些念头意味着你正在违反 Phase 0,必须停下重来

| 自我辩护的念头 | 现实 |
|-------------|------|
| "用户已经给了研究规划摘要,可以直接执行" | 摘要不等于所有维度都对齐。儿童/RICU边界/分母口径等常被遗漏。**必须提问** |
| "任务明确,不需要澄清" | "明确"是你的感觉,不是事实。总有 3-5 个维度你没确认过 |
| "先执行,发现问题再追问" | 一旦启动 agent teams,返工成本极高。**提问在先** |
| "提问显得不够主动" | Phase 0 澄清 = 专业,不是懒惰。用户更怕错了方向 |
| "我有合理默认值" | 默认值要在摘要中明示+让用户确认,不是你自己填完就算 |
| "报告可以事后修正" | 流程图一旦画定,基数就锁死。事后改 = 重跑 agent teams |
| "节省时间优先" | Phase 0 漏触发导致的返工时间 >> 提问时间 10-100 倍 |

**全部都是返工信号:看到任何一条,立即停止执行,回到 Phase 0 提问。**

### IFI 专属 Phase 0 问题(L0 通用 12 维度基础上补充)

除 L0 通用 12 维度外,IFI 任务还必须问:
- **儿童限制**:泊沙康唑 ≥2/13 岁、艾沙康唑仅 ≥18 岁 → 儿童口径严重受限
- **RICU vs 综合 ICU**(本 skill v1.3 核心教训):呼吸科 IFI 必须严格 RICU,综合 ICU 另立
- **COVID-19 期隔离**:CAPA 数据偏离基线,默认 2020-2022 单列
- **非抗真菌关键药**:TMP-SMX(PJP)+ 奥马珠单抗(ABPA)是否纳入

### Phase 0 违反速查:典型失败案例(呼吸科肺真菌病项目,v1.0 → v1.3 复盘)

> 用户给了"目标 / 疾病×科室 / 药物范围 / 患者范围 / 证据窗口 / 输出物 / 已知锚点"7 项摘要
> Skill v1.0 直接执行,事后用户反馈:
> - "儿童范围没界定" — 泊沙康唑 ≥13 岁限制遗漏
> - "RICU 边界没明确" — 综合 ICU 转呼吸科患者是否计入未问
> - "市场分母口径" — 院内 62 亿 vs 全口径 220 亿差异巨大,未确认
> - "COVID-19 期处理" — CAPA 数据是否按特殊期隔离,未问
> - "非抗真菌关键药" — TMP-SMX / 奥马珠单抗是否纳入,未问
>
> 教训:即使 7 项看似完整的摘要,仍有 5+ 核心维度被漏问。
> **从此 Phase 0 成为 Iron Law,无例外。**

> **v1.3 新增教训(MECE 违反案例)**:
> 本次呼吸科任务 8 条 ICU 数据中有 6 条为综合 ICU 被无声混入呼吸科口径。
> 根因:Phase 2 data-agent 的搜索词用了"ICU"而非"RICU",且返回数据无 `ward_type` schema。
> **修复(v1.3)**:
> - Phase 0 对 11 维度"科室归属边界"强制提问(L0 第 4 节)
> - Phase 2 使用 L0 第 6 节的 RICU 专属搜索词模板
> - Agent 输出强制 L0 第 7 节 schema,含 `ward_type` 必填字段
> - 综合 ICU 数据 **剔除**,不以其顶替 RICU 空白;RICU 数据不足时 🟠 推算 + 空白清单

> **IFI 专属 RICU 锚点(v1.3 修正后标准参考)**:
> - **温州医大一院 PMID 40281478 / DOI 10.1186/s12890-025-03671-4** — 目前中国**最好的** RICU vs 综合 ICU MECE 证据:同队列 n=871 分层 RICU CAPA 30.8% vs PCCM 病房 13.4% vs 其他 ICU 6.8%(RICU 是综合 ICU 4.5 倍)
> - **中日友好医院 RICU(49 床)** — 全国 RICU 最大单中心数据源:CAPA n=123, 29.3%, 死亡 66.7% + IAPA n=221, 19% + 抗真菌药 RWE
> - **7 中心 RICU PJP 多中心** — DOI 10.3389/fcimb.2022.872813,上海/杭州/南京/深圳 n=198
> - **华西 RICU 20 床 / 千佛山 RICU 15 床** — RICU 床位规模锚点
> - **RICU 床位占全国 ICU 床位 12-15%(最可能 13%)** — 推算逻辑:PCCM 规建 409 家 + 国际对标 + 单中心外推;对应 2023 年约 10,900 张 RICU 床位
>
> **v1.3.1/v1.3.2 报告侧教训(LP 决策图 + 视觉 + 中立立场)**:
> 用户明确反馈 3 条设计错误(见失败模式 #18-20):LP 标签不够醒目需独立 badge · 7.2 冗余"瀑布图位置"列 · 建议偏向具体产品。已在 L0 第 10-13 节写入规范。

> **v1.3.3 视觉规范(字体/配色 MRR 对齐)**:
> 用户要求报告"参照 market-research-reports skill"的字体。从 MRR `market_research.sty` 提取:
> - Primary Navy `#003366` / Secondary Blue `#336699` / Accent Blue `#0078D7`
> - 正文 11pt · 表格 10pt · h1 22pt · 行距 1.65
> - 字体堆栈 `Source Han Sans CN → PingFang SC → Microsoft YaHei`
> - Callout/Warning/DataHint 四色 box 环境对齐 MRR tcolorbox
> 详见 L0 第 11 节完整规范。

### 对齐清单

**A. 目标定义（必须明确）**
- 调研目标是什么？（market sizing / 竞品格局 / unmet need / 全部）
- 目标疾病×科室是什么？（如：血液科IFI / 呼吸科肺曲霉 / ICU真菌感染）
- 目标药物组合是什么？（如：Cresemba+Vfend / 全品类中立）
- 报告立场是什么？（中立第三方 / 特定产品策略导向）

**B. 范围定义（容易遗漏）**
- 患者人群范围？（成人/儿童/两者？住院/门诊？三级/所有？）
- 地理范围？（中国大陆 / 含港澳台？是否分省市梯度？）
- 证据时间窗？（如2021-2026；COVID-19 期是否隔离？）
- 需要覆盖的药物清单是否完整？（用户可能遗漏某些竞品）
- 非抗真菌关键药物是否纳入？（如 PJP 的 TMP-SMX、ABPA 的奥马珠单抗/Mepolizumab）

**C. 输出定义(影响工作量)**
- 输出物是什么?(PDF 报告 / 流程图 / 数据表 / 全部)
- 流程图格式?(Mermaid HTML / 嵌入 PDF / 两者)
- 是否需要药监局适应症约束?(通常需要,**且必须区分三态:说明书内 / 超说明书 / 药理学无活性**,详见 Phase 2)
- 是否需要市场销售额数据?
- 市场分母口径?(院内 vs 全口径含外用/零售;选一作为主分母)
- 目标读者?(药企策略 / 医院 KOL / 投资方 / 政策制定者 — 影响叙事深浅)
- **报告输出语言?(中文 / 英文 / 双语)** — v1.2 新增
- **报告呈现顺序是否参照咨询式排版?(TOC+图表索引+附录式方法论/证据表)** — v1.2 新增(默认采纳)

**D. 已有资源（避免重复劳动）**
- 用户是否已有咨询公司数据？（如IQVIA/米内网账号）
- 是否有已知的锚点文献？（如CAESAR 2.0）
- 是否有上一版报告需要迭代？

### 对齐方式

**步骤 1：先列问题清单**（无论用户是否给摘要，都要做）
- 从 A/B/C/D 四类中挑选 3–5 个**最可能影响测算结果**的维度
- 按如下格式输出：

```
=== Phase 0 澄清问题（请回复后再执行）===
1. [维度]：[具体问题]
   - 默认建议：[如用户不回复，采用什么默认值]
2. [维度]：[具体问题]
   - 默认建议：…
…
```

**步骤 2：等待用户回复**
- 回复可以是"全部采用默认"或逐条修正
- 收到回复后，再输出**研究规划摘要**让用户二次确认

**步骤 3：输出规划摘要**

```
=== 研究规划摘要 ===
目标：[一句话]
疾病×科室：[X]
药物范围：[列出]
患者范围：[X]
证据窗口：[X]
输出物：[X]
已知锚点：[X]
Phase 0 澄清回复要点：[用户对澄清问题的关键回复]
确认后开始执行。
```

### Phase 0 常见被漏问的维度（至少覆盖其中 2 个）

| 维度 | 为什么重要 | 典型默认 |
|------|-----------|---------|
| 儿童范围 | 多数新药有年龄限制（泊沙康唑≥13岁 / 艾沙康唑仅成人） | 默认成人为主，标注儿童限制 |
| RICU 边界 | 综合 ICU vs 呼吸专属 RICU 患者谱不同 | 默认 RICU + 普通呼吸病房分列 |
| COVID-19 期隔离 | CAPA 数据偏离基线 | 默认把 2020-2022 单列并与其他年份对比 |
| 市场分母口径 | 院内 62 亿 vs 全口径 220+ 亿差异巨大 | 默认院内,全口径为补充 |
| 非抗真菌关键药 | TMP-SMX/奥马珠单抗影响 PJP/ABPA 完整性 | 默认纳入 |
| 目标读者 | 影响叙事深浅与策略建议取向 | 默认中立药企/KOL 可读 |
| 地理分层 | 马尔尼菲西南/东南 vs 华北华东差异显著 | 默认全国,重大差异单列 |
| **输出语言** | 英文触达国际药企,中文触达国内 KOL | 默认中文(国内任务),Phase 0 必须问一次确认 |
| **呈现顺序** | 咨询式(TOC/图表索引/附录)vs 学术式(线性) | 默认咨询式(参照 market-research-reports 排版) |

---

## Phase 1-5：执行流程

### Phase 1：定义参数包
读 references/quality-checklist.md 底部的参数包YAML模板，基于Phase 0结果填写。

### Phase 2:数据抓取(读 references/data-acquisition.md + nmpa-antifungal-table.md)
按渠道优先级搜索:患者池基数 → 分流比例 → **药物-靶点 三态矩阵** → 市场数据。
证据等级:🟢多中心/国家登记 > 🔵单中心 n≥50 > 🟡小样本/摘要 > ⚪国际参考。
搜索关键词模板见 reference 文件。

**🔑 药物-靶点 活性三态矩阵(v1.2 强制 · 疾病领域无关)**

> 本规则通用于任何"药物 × 病原/靶点/适应症"关系,不仅限于抗真菌药。
> 肿瘤(靶向药 × 驱动基因)、慢病(降压药 × 合并症场景)、感染(抗生素 × 菌种)均适用。

不得用二态(✅ / ✗)描述药物 × 靶点关系。必须用三态:

| 符号 | 含义 | 含义细节 |
|------|------|---------|
| 🟢 **说明书适应症** | 药监局批件有此适应症 | 可正常处方 |
| 🟡 **超说明书(off-label)** | 药理学有活性,说明书未列 | 依据国际指南/专家共识/RWE 处方,须告知患者并留档 |
| ❌ **无活性** | 固有耐药 / 无靶点 / 药代不可达 | 绝对不应使用 |
| — | 不适用 | 该场景与该药无交集 |

**每个 🟡 超说明书 + 每个 ❌ 无活性 都必须附证据码**(在报告中维护"超说明书 / 活性判断 证据索引"表):
- `[G#]` 指南来源(如 G2 = ESCMID/ECMM/ERS CPA 2016)
- `[R#]` RWE 文献(如 R1 = 武汉 220 例 CPA)
- `[P#]` 药理学证据(如 P1 = 伏立康唑 MIC90 对 C. neoformans 0.12-0.25 μg/mL)
- `[#]` 说明书批件(如 1 = 伏立康唑 NMPA 2005 版)

**填完矩阵后必须自问**:"每个 ✗ 是因为**无适应症**还是**无活性**?"如分不清,标 🟡 并查指南+药理学。

**典型误区对照表**(呼吸科肺真菌病 v1.1 → v1.2 复盘):

| 药物 × 靶点 | 二态误判 | 三态正解 | 根因 |
|-----------|---------|--------|------|
| 伏立康唑 × 肺隐球菌 | ❌ 无活性 | 🟡 超说明书 | MIC≤0.5,IDSA 2010 备选,中国说明书未列 |
| 伊曲康唑 × 肺毛霉 | 🟡 超说明书 | ❌ 无活性 | 毛霉对伊曲康唑固有耐药(MIC>8) |
| 米卡芬净 × PJP | ❌ 无 | 🟡 超说明书 | 体外对 Pneumocystis 包囊细胞壁有活性,中国无 PJP 适应症 |

**泛化到其他领域**:
- 肿瘤:奥希替尼 × EGFR Exon20ins → 🟡 超说明书(部分活性,新版 NCCN 列为二线,中国未获批该亚型)
- 心内:SGLT2i × 射血分数保留 HFpEF → 视 FDA/NMPA 批件状态而定
- 抗菌:头孢他啶 × 铜绿假单胞菌 → 🟢 NMPA 适应症

### Phase 3：构建患者流瀑布图（读 references/flowchart-rules.md）
**核心交付物。** 12 条硬性规则：
1. 每层分流加和=100%
2. 每个分支走完直至●终止
3. 病种拆分是节点属性不是分支
4. 以目标疾病flow为主轴
5. 药物出现位置受NMPA约束
6. 绝对数字+百分比双标注
7. 估算值必须标注依据
8. 证据来源标注在图下方
9. 用Mermaid flowchart TD语法，**复杂树状图强制使用 ELK 布局引擎**（dagre 默认布局箭头交叉严重）
10. 色彩编码（蓝=患者池 绿=预防 红=IFI/死亡 橙=治疗 紫=病原特异）
11. **消除跨分支共用节点**：多个入口指向同一分型节点（如 PJP/肺隐球菌）时，必须为每个入口独立复制一套节点（A_PJP/B_PJP/D_PJP），避免箭头回折交叉；宁可节点重复也不可箭头交叉
12. **使用 subgraph 为每个入口划分 swim-lane**，配合 `linkStyle` 为每条主路径着色，让读者一眼分清流向

**Mermaid 布局骨架模板（所有复杂诊疗路径套用）**
```
---
config:
  layout: elk
  flowchart:
    nodeSpacing: 70
    rankSpacing: 90
    curve: basis
---
flowchart TD
  POOL --> SCREEN --> ROUTER
  ROUTER --> ENT_A & ENT_B & ENT_C & ENT_D
  subgraph GRP_A ["入口 A"]
    direction TB
    ENT_A --> DX_A --> A_IPA --> A_TX_IPA --> A_END
  end
  subgraph GRP_B ["入口 B"]
    direction TB
    …
  end
  linkStyle 0,1,2,3 stroke:#1A5490,stroke-width:2.5px
```

### Phase 4：质量审核（读 references/quality-checklist.md）
逐条检查：分流加和、分支完整、层级正确、NMPA约束、术语规范、证据排序。

### Phase 5：生成最终报告

#### 5.1 报告呈现顺序(v1.2 · 参照 market-research-reports 咨询式排版)

> **仅参照"呈现顺序",不强制加入商业战略板块(Porter / PESTLE / SWOT 等)**。
> 这些板块属于业务咨询专属工具,与临床路径 market sizing 的证据基线不直接对应。
> TAM/SAM/SOM 例外 — 它是市场 sizing 的核心测算分层,予以保留。

**咨询式呈现骨架**(默认采纳):

```
Front Matter:
  1. 封面(Cover) — 含标题/立场/署名
  2. 目录(TOC)
  3. 图表索引(List of Figures + List of Tables)

Core Analysis(论述正文,结论先行):
  4. 执行摘要(8-12 条结论按证据等级排序)
  5. 研究方法概要(详细挪附录 A)
  6. 诊疗路径框架【核心交付物】
     - 6.1 患者流瀑布图(渲染 PNG 嵌入)
     - 6.2 文字树状路径
     - 6.3 关键分流比例总表
     - 6.4 药物-靶点 三态矩阵
     - 6.5 超说明书证据索引
     - 6.6 测算原则
  7. 分层分析(按亚人群)
  8. 市场规模
     - 8.1 总市场规模
     - 8.2 分药物销售额 / 份额
     - 8.3 TAM / SAM / SOM 分层测算
     - 8.4 子市场份额估算方法
     - 8.5 医保与集采影响
     - 8.6 增长驱动
  9. 研究结论与策略切入点
     - 9.1 可直接用于市场分析(🟢+🔵)
     - 9.2 仅可谨慎参考(🟡+🟠)
     - 9.3 不可用于市场分析(⚪/空白)
     - 9.4 策略切入点建议

Back Matter(附录:细节支撑):
  附录 A:完整研究方法论(证据分级/核心锚点/术语规范)
  附录 B:详细证据表(表 1-7)
  附录 C:参考文献清单(按证据等级分组)
```

**关键设计原则**:
- **结论先行**:执行摘要在第 4 节,核心结论在第 9 节,细节数据挪到附录
- **TOC + 图表索引**:提供全文导航,符合咨询式报告习惯
- **方法论双层**:正文只放"方法概要",完整方法论放附录 A
- **证据表分离**:核心叙事靠精选插图/小表,详细 7 张证据表移至附录 B
- **不强制商业战略框架**:Porter 五力 / PESTLE / SWOT / 风险热图 / 机会矩阵 / 实施路线图 **不默认加入**;如任务明确需要,Phase 0 确认后再酌情补

#### 5.2 PDF生成流水线 (v1.6 工作流 · 防止流程图缺失 + 强制高清)

Mermaid是HTML/JS渲染技术，**不能直接嵌入PDF**。必须走以下流水线。本节为"清晰度驱动"升级版：

**路径 A（推荐 · 无需 LibreOffice）—— HTML+Chrome Headless**
```
Step 1: 写 Mermaid .mmd 文件
        - 复杂树状图必须用 ELK layout(frontmatter `layout: elk`)
        - 每个入口独立 subgraph，消除跨分支共用节点
Step 2: mmdc -i flowchart.mmd -o flowchart.png -w 5000 --scale 2 \
              -b white -p puppeteer-config.json
        要求:输出 PNG 短边 ≥ 3000px,文件 ≥ 800KB。低于此值视为不达标。
Step 3: 构造 HTML 报告,PNG 以 base64 嵌入 <img style="width:100%">
Step 4: chrome.exe --headless --disable-gpu --no-sandbox \
              --print-to-pdf=report.pdf --no-pdf-header-footer \
              file:///.../report.html
Step 5: 用 pypdf 验证 PDF 页数 ≥ 12、封面关键元素 ≥ 5 项
```

**路径 B（传统 · LibreOffice 可用时）—— docx+LibreOffice**
```
Step 1+2: 同上(Mermaid→PNG)
Step 3: docx-js(Node.js) 生成 .docx,ImageRun 嵌入 PNG
Step 4: soffice --headless --convert-to pdf report.docx
Step 5: 验证完整性
```

**绝对禁止**：
- PDF 中写"见附件 HTML"而不嵌入流程图图片。流程图是核心交付物,必须 PDF 内可见
- 使用 mmdc 默认 `-w 2400` 低分辨率渲染 — **复杂诊疗路径图必须 `-w 5000 --scale 2` 或更高**
- 不设置 ELK 布局直接用 dagre,对多分支树状图产生大量箭头交叉

**中文渲染方案优先级**：
1. Chrome headless 打印 HTML → PDF(最稳,无需额外安装)
2. docx-js → LibreOffice soffice(需安装 LibreOffice)
3. ❌ reportlab + CFF 字体(中文乱码,禁用)

#### 5.3 HTML 报告完整性清单(v1.5 强制 · 不可缺失)

> **v1.5 核心防复现**:LP 决策图与决策树节点级 LP 标注**反复在 v2.1-v2.5 各版本中遗漏**(失败模式 #28)。
> 本清单为 Iron Law,主页 / 子页 / 流程图三层资产**必须全过**才可交付。
> 任意一项失败 = 报告未完成,禁止提交"已交付"。

**层 1 · 主页报告资产清单(必含)**:

- [ ] §7.0(或对应 LP 章节)**必含 LP 全景决策图 PNG**`<img src="flowchart_lp.png">` — Iron Law,失败模式 #28 直接来源
- [ ] §3 必含主图 `flowchart_main_v??.png`(疾病分流图)
- [ ] §4(或子页跳转区)必含 N 张 disease-card 跳转卡片(N = 子页数)
- [ ] 每张 disease-card 链接到对应子页 HTML
- [ ] §7 LP 总览 `lp-callout` × 全部 LP(典型 8 个,允许 ±2)
- [ ] §7 LP 排序表(按 Impact 中位数)
- [ ] footer 含全部子页快速跳转链
- [ ] sticky topnav 含 8-12 个章节锚点
- [ ] 全文署名 `Skill Presented by:YongQi, SimonSu, RuiYu, YingJi`

**层 2 · 子页报告资产清单(每个子页必含)**:

- [ ] hero 区(渐变色按市场分级:⭐⭐⭐ 金 / ⭐⭐ 橙 / ⭐ 蓝)
- [ ] hero 含返回主页 back 链接 + tier-tag
- [ ] sticky topnav 含 4 个章节锚点(决策树 / 测算 / TOP 3 LP / 证据)
- [ ] §1 决策树 PNG(子页对应的 flowchart_<sub>_v??.png)
- [ ] §2 双分支患者流量表 + 阶段 × 主药表
- [ ] §3 TOP 3 LP `lp-callout`(其中 1 个 lp-crown 金边)
- [ ] §3 末尾 `recommendation` 区块解释 LP 选择逻辑 + 链回主页 §7
- [ ] §4 关键证据 PMID 表(≥4 行)
- [ ] footer 含返回主页链 + 署名

**层 3 · 流程图节点级 LP 标注资产清单(每张 .mmd 必含 · v1.5 新增 Iron Law)**:

- [ ] 每张子页决策树 .mmd 末尾**必含 LP_BADGE 节点定义**(参考 L2 skill `decision-tree-with-lp-embedding`)
- [ ] LP_BADGE 数量 = 该子页 TOP 3 LP(典型 2-3 个)
- [ ] LP_BADGE 与对应业务节点用**虚线 `-.->` 连接**(不打断主流)
- [ ] LP_BADGE 用 stadium 形状 `(["..."])` 不与决策方块/菱形混淆
- [ ] LP_BADGE 用 `lpcrown`(金 #FEF3C7/#F59E0B)+ `lpstd`(红 #FEE2E2/#DC2626)classDef
- [ ] 每张 LP_BADGE 内含 `Impact xxx-xxx/yr` 量化数字
- [ ] 主图 `flowchart_main_v??.mmd` 必含全部 LP(典型 8 个),按 Tier 层级连接
- [ ] 渲染后 PNG 短边 ≥ 3000 px,文件 ≥ 750 KB

**层 4 · 链接互联完整性**:

- [ ] 主页 → 子页:每张 disease-card / 跳转表 / footer 链接全部就位且文件存在
- [ ] 子页 → 主页:每子页至少 4 个反向链接(hero back / topnav home / recommendation / footer)
- [ ] 子页 → PNG:每子页正确引用其专属 flowchart_<sub>_v??.png
- [ ] 主页 → flowchart_lp.png(本身的 LP 全景图)+ flowchart_main_v??.png(主图)

**复现历史(惨痛教训 · v2.1-v2.5)**:

| 版本 | LP 决策图嵌入 | 决策树节点级 LP 标注 | 根因 |
|------|------------|------------------|-----|
| v2.1 | ✅ 早期模板含 | ❌ 仅 SUMMARY 文字 | 早期约束完整,后期遗漏 |
| v2.2 | ❌ | ❌ | 全手写 HTML,无清单 |
| v2.3 | ❌ | ❌ | skill 未硬约束 |
| v2.4 | ❌ | ❌ | 子页拆出,主页 LP 章被简化 |
| v2.5 (修复前) | ❌ | ❌ | 用户第三次反馈才发现 |
| **v2.5 (修复后)** | **✅** | **✅** | **本清单强制** |

> **未来项目执行此清单时若任何 ☐ 未打勾,禁止用"已完成"措辞向用户汇报**。

#### 5.4 PDF完整性清单（交付前必须逐项核验）

- [ ] 封面含署名 `Skill Presented by:YongQi, SimonSu, RuiYu, YingJi`（位置:方法依据下一行）
- [ ] 执行摘要 8-12 条结论完整
- [ ] 研究口径与方法（含证据分级说明、术语规范）
- [ ] **流程图图片已嵌入**（非"见附件"文字引用）
- [ ] 流程图 PNG 短边 ≥ 3000 px(打印不糊)
- [ ] 流程图无跨分支箭头交叉(ELK 布局 + 独立节点)
- [ ] 文字树状路径完整（每个分支到 ● 终止）
- [ ] NMPA 适应症对比表（≥10 种药物 × ≥5 个场景）
- [ ] 表1:基础疾病/人群规模（≥8 行）
- [ ] 表2:病原类型构成（≥6 行）
- [ ] 表3:诊断方法（≥8 行）
- [ ] 表4:关键分流比例（≥10 行）
- [ ] 表5:各阶段药物用药比例（≥15 行,所有药物平等）
- [ ] 表6:基础疾病贡献（≥6 行）
- [ ] 表7:证据空白（≥5 行）
- [ ] 分层分析（≥3 个亚人群详细展开）
- [ ] 市场规模数据
- [ ] 研究结论含三级分类（可用/谨慎/不可用）
- [ ] 参考文献按等级分组
- [ ] 全文无"靶向治疗"（应为"目标治疗"，规范对照表中的反例举例除外）
- [ ] 全文无"确诊分级"（应为"诊断分级"，规范对照表中的反例举例除外）
- [ ] PDF 页数 ≥ 12 页（内容密度合理的情况下）
- [ ] Phase 0 澄清问题记录留痕（放在"研究口径与方法"章节或附录）

---

## 署名规则（所有输出物强制执行）

所有生成的流程图（Mermaid HTML）和 PDF 报告，必须在首页/封面包含署名：

```
Skill Presented by:YongQi, SimonSu, RuiYu, YingJi
```

**格式规范（v1.1 更新）：**
- 文字完整串：`Skill Presented by:YongQi, SimonSu, RuiYu, YingJi`（注意冒号后无空格、名字之间用 `·` 分隔）
- **位置**：在"方法依据:ifi-market-sizing-skill v1.x"这一行的**下一行**(不再占据 hero 区主视觉位置)
- **字色**：与"方法依据"同色(建议灰色 `#888888` / CSS var `--gray-500`)
- **字号**：比"方法依据"再小一号(若方法依据 18pt → 署名 16pt;HTML 若方法依据 10pt → 署名 9pt)
- **对齐**：与"方法依据"对齐(通常 center)

**具体位置：**
- PDF 报告:封面页,标题/副标题/立场横幅下方 → 证据窗口日期 → 方法依据 → 署名(末行)
- Mermaid HTML 流程图:页面顶部标题区域,"方法依据"小字下方一行
- 任何导出的图片/幻灯片:右下角或底部

**为什么改为 "Skill Presented by:"(而非原 "Presented by:"):**
本 skill 的本质是方法论呈现框架,署名指的是 skill 作者而非报告作者本人。
用户可能会用同一 skill 重复生成不同报告,但 skill 作者永远是 YongQi, SimonSu, RuiYu, YingJi。
用 "Skill Presented by:" 让读者一眼知道这是 skill 默认署名,而非报告实际作者。

---

## 失败模式速查表（迭代至 v1.1）

| # | 失败模式 | 根因 | 修复规则 |
|---|--------|------|---------|
| 1 | 全是"未检索到" | 学术标准套用市场调研 | 最佳可得证据分层呈现 |
| 2 | 隐性品牌偏向 | 指令结构先写自家产品 | 按路径阶段而非药物组织 |
| 3 | 只有文字无图 | 未定义 Mermaid 为硬性交付物 | 瀑布图 = 硬性交付物 |
| 4 | 分支截断 | 低危分支无后续 flow | 规则 2：走完直至 ● 终止 |
| 5 | 层级归类错误 | 病种做成独立分支 | 规则 3：病种是属性 |
| 6 | 药物位置错误 | 没查 NMPA 适应症 | 规则 5：先查适应症再画图 |
| 7 | PDF 流程图缺失 | Mermaid 是 HTML/JS 渲染,不能直接嵌入 PDF | 必须先用 mmdc 渲染为 PNG 再嵌入 docx→PDF 或 HTML→Chrome→PDF |
| 8 | PDF 内容不完整 | 生成脚本遗漏表格/分层分析 | 用 PDF 完整性清单逐项核验后再交付 |
| 9 | **Phase 0 漏触发** | 用户给了"研究规划摘要"就直接执行,未主动追问遗漏维度 | Phase 0 强制规则:**无论用户是否给摘要,执行前必须输出 3-5 条澄清问题并等待回复**。典型漏问:儿童限制/RICU 边界/市场分母口径/COVID-19 隔离/非抗真菌关键药 |
| 10 | **流程图线条交叉严重** | dagre 默认布局 + 多个入口指向同一共用分型节点(PJP/肺隐球菌等),导致箭头回折交叉 | 复杂树状图强制 `layout: elk`;每个入口独立复制分型节点(A_PJP/B_PJP/D_PJP)而非共用;subgraph + linkStyle 着色区分流向 |
| 11 | **流程图清晰度低(打印糊)** | mmdc 默认 `-w 2400` 宽度偏低 | 复杂路径图必须 `-w 5000 --scale 2`,输出 PNG 短边 ≥ 3000 px,文件 ≥ 800 KB;HTML 嵌入用 `width:100%` |
| 12 | 署名占据 hero 视觉 | 封面主视觉被署名喧宾夺主 | 署名移到"方法依据"下,字号比方法依据再小一号,同灰色 |
| 13 | "无适应症"被误标为"无活性" | 二态表达不足 | 三态矩阵 + 证据码(详见 L0 第 3 节) |
| 14 | 超说明书条目无证据来源 | 缺证据码系统 | L0 [G#/R#/P#] 索引 |
| 15 | 把商业战略板块塞进临床 market sizing | 误以为 MRR 全套都要加 | L0 报告结构只参考呈现顺序,不强推 Porter/PESTLE/SWOT |
| 16 | Phase 0 漏问语言 | 默认中文 | L0 Phase 0 第 7 维度强制 |
| **17** | **综合 ICU 数据混入呼吸科口径(MECE 违反)** | **Phase 2 搜索词不严格,数据无 ward_type schema,综合 ICU 无声顶替 RICU** | **v1.3**:Phase 0 问 MECE 边界(L0 第 11 维度)+ Phase 2 用 RICU 专属搜索词(L0 第 6 节)+ Agent 返回强制 ward_type schema(L0 第 7 节)+ 数据不足留空 🟠 推算不以邻接顶替 |
| **18** | **LP 标签混在业务节点文字内,视觉淹没** | 用 `"🏆 LP1 ... 正文内容"` 前缀,被正文稀释 | **v1.3.2**:LP 用独立 stadium badge + 虚线连接,红/金配色粗边 classDef(详见 L0 第 10 节) |
| **19** | **LP 建议偏袒具体药物(产品化语言)** | 如"通过伊曲康唑 TDM 普及..."——中立报告立场污染 | **v1.3.1**:去产品化改写为"长程 TDM 工具普及 → 整个三唑类赛道扩容"(详见 L0 第 12 节) |
| **20** | **Chrome headless 不支持 CSS target-counter,TOC 无页码** | `leader(dotted) " " target-counter(...)` 两者均不支持,Paged.js polyfill 渲染超时 | **v1.3.1**:Python 两遍渲染法——先渲染 PDF 测页码、再注入 HTML、再渲染最终 PDF(详见 L0 第 13 节) |
| **21** | **WPS/Adobe 锁定输出 PDF** | 用户打开 PDF 阅读器 → Python 写入 PermissionError | **v1.3.1**:fallback 到 `report_v131.pdf`,避免渲染失败(详见 L0 第 13.4 节) |
| **22** | **Mermaid YAML frontmatter 前有注释 → 10.9+ 解析失败** | 子 agent 在 `---` 前加 `%% Skill Presented by...` 注释 | **v1.2 Iron Law**:flowchart-rules 规则 13(首行 `---`)+ L0 §14 validator 自动拦截 + L1 flowchart-rules 规则 13 例证(详见 `flowchart-validator.py`) |
| **23** | **流程图无 ● 终止,所有分支悬空** | ICU LP 决策图 `●=0`,叶子节点无终止标记 | **v1.2 Iron Law**:flowchart-rules 规则 2 + 规则 14 validator 自动扫描叶子节点(非明确 `END_` 前缀或 `●` 关键字的叶子报硬错误) |
| **24** | **疾病/亚人群合并成单一池** | 血液科 v1.2 前 — AML/HSCT/MDS 合并为"高危合并池",失去各自 IFI 发生率/药物比例 | **v1.2 Iron Law**:L0 Phase 0 第 11 维度"科室内疾病/病因细分"强制问,含 5 科室默认粒度表(血液 14 亚人群 / 呼吸 4 入口 × 7 分型 / ICU 6 宿主 × 5 病原 等) |
| **25** | **多源汇聚共用节点产生跨分支交叉** | ICU LP — `HOSTS` 广播到 5 个分型,然后各分型 `--> DIAG` 再次汇聚,ELK 布局中 DIAG 4 入度从不同方向拉过来 | **v1.2 Iron Law**:flowchart-rules 规则 15 禁止非评估/路由节点入度 ≥3,必须拆成 `DIAG_A/DIAG_B/DIAG_C` |
| **26** | **简化三态矩阵误降级**(血液科 v2.1 发现) | HTML agent 从 5 阶段原始矩阵缩减为"每药 × 每病原 1 格"时,将 NMPA 明确批件(如伏立康唑 × IC 非粒缺念珠菌血症、卡泊芬净 × IA 经验+难治挽救)误读为"不是一线 = 🟡 超说明书"。根因:简化时把"条件限定(非粒缺/经验/难治)"当"超说明书",但这些**均在 NMPA 批件原文内**,应为 🟢 | **v1.4**:遵守 L0 §3.1 三态核查自问表(5 问 Iron Law · "是否原文含<病原名>+感染/治疗/预防/耐药/难治")+ L0 §3.2 NMPA 批件原文强制引用;简化规则:≥3 阶段 🟢 → 整格 🟢;混合则注脚"🟢(条件)"不降级 |
| **27** | **医学术语误译:breakthrough IFI → "IFI 爆发"**(血液科 v2.1 发现) | HTML agent 将 "breakthrough infection" 直译为 "爆发",但**"爆发"=outbreak 公共卫生疫情**含义,与个体"突破性感染"完全不同 | **v1.4**:遵守 L0 §16 医学术语规范对照表(22 条英→中);**IFI 专属必译**:breakthrough IFI = "突破性 IFI" · breakthrough mucormycosis = "突破性毛霉病" · breakthrough candidemia = "突破性念珠菌血症";Phase 4 质量审核强制 `grep "爆发\|确诊分级\|靶向治疗"` 零命中 |
| 13 | **"无适应症"被误标为"无活性"** | 二态(✅/✗)无法区分"超说明书"与"真正无活性" | v1.2 强制三态:🟢 说明书 / 🟡 超说明书 / ❌ 无活性;每个 🟡 和 ❌ 附证据码 |
| 14 | **超说明书条目无证据来源** | 只写"超说明书"不注来源,读者无法追溯 | 强制维护"证据索引"表,采用 [G#]/[R#]/[P#]/[#] 引用 |
| 15 | **把商业战略板块塞进临床 market sizing** | 误以为 MRR 全套(Porter/PESTLE/SWOT)都要加,稀释临床证据密度 | v1.2 只参照 MRR 的**呈现顺序**(TOC/附录),不默认加商业战略框架;TAM/SAM/SOM 例外(核心测算) |
| 16 | **Phase 0 漏问语言** | 默认中文输出,用户要英文时须重做 | Phase 0 必须问"输出报告语言?(中文/英文/双语)" |
| **28** | **🔥 高频复现:LP 决策图遗漏 + 决策树节点级 LP 标注缺失**(血液科 v2.1-v2.5 反复出现 5 次) | 全手写 HTML 无 build pipeline → 无"必含资产清单"约束 → skill 未硬约束 → 子页拆出后主页 LP 章被简化为纯文字 → 用户第三次反馈才发现 | **v1.5 Iron Law**:Phase 5.3 HTML 报告完整性清单(本节)四层资产清单 · LP 决策图必含 §7.0 · 7 张 .mmd 必含 LP_BADGE 节点 · 渲染前用 L2 skill `decision-tree-with-lp-embedding` 模板;**未来执行此清单时若任何 ☐ 未打勾,禁止用"已完成"措辞向用户汇报** |
| **29** | **⚠️ 主图嵌入 LP 标注(违反一图一主题)**(血液科 v2.5 发现) | 主图(疾病分流总览)与 LP 全景图(战略切入点)被混合为一张图。主图视觉负载过重,LP 又不够聚焦 | **v1.6 Iron Law**:**主图(disease-flow-map)禁止嵌入 LP_BADGE**,只承载"疾病分流总览 + 市场分级";LP 全景图(lp-decision-map)是**独立的战略切入点决策图**,8 LP 集中在此;子页决策树**可在节点级嵌入 TOP 3 LP_BADGE**(L2 `decision-tree-with-lp-embedding` 已规范);**Why**:一图一主题,各司其职,读者认知负担可控;**How**:Phase 5 渲染前 grep 主图 .mmd 不含 `LP_BADGE` / `lpcrown` / `lpstd` classDef;**历史复现证据**:v2.5(2026-04-25)主图嵌入 8 LP,被用户立即指出违反一图一主题原则 |
| **30** | **⚠️ LP 决策图基于单分支(只看主流路径)模型**(血液科 v2.5 发现) | LP 图沿用早期(v2.1)单分支(只看预防)模型,忽略占总池 ~50% 的非预防分支(MDS 60% / NHL 68% / AML 50% 不启用预防);LP1/LP3/LP8 Impact 严重低估(旧 15k-30k → 新 47k-128k,3-4 倍跃升) | **v1.6 Iron Law**:任何疾病的 LP 决策图必须先建立"完整诊疗路径多分支模型",再连接 LP;**单分支会忽略 unmet need 最大的旁支(常占 30-50%+)**;LP 连接节点必须横跨所有分支(决策点 + 维持期 + 经验治疗主战场);**Why**:旁支常是 unmet need 最大的市场窗口;**How to apply**:LP 图渲染前验收必须可见至少 2 条主分支(预防/非预防 / 一线/二线 / 早筛/晚发等);**历史复现证据**:v2.5 LP 图沿用 v2.1 单分支,LP1/LP3/LP8 Impact 低估 3-4 倍(旧 15k-30k → 新 47k-128k) |
| **31** | **⚠️ evidence/ ↔ 报告附录 C 不同步,附录欠缺 75%**(血液科 v2.5 发现) | evidence/ 文件夹累积 44 条 PMID,报告附录 C 只列 11 条(欠 75%);根因:手写附录 C 时凭印象取舍,未与 evidence/ 强制对账 | **v1.6 Iron Law**:任何报告交付前,必须运行 `evidence-appendix-sync` 验证(L2 skill 待建);**每个 evidence/*.md 中出现的 PMID 必须出现在报告附录 C(允许 ±0 偏差)**;反之每个附录 C 列出的 PMID 必须有 evidence 来源;**禁止"手写附录 C 取舍"** — 必须 grep evidence/ 全量列出;**Why**:可追溯性是医学市场报告基线,缺失 PMID = 证据链断裂;**How to apply 验收命令**:`grep -roh "PMID:[0-9]\+" evidence/ \| sort -u \| wc -l` 应 ≤ 报告附录 C 中 PMID 数;**历史复现证据**:v2.5 evidence 44 条 vs 附录 C 11 条(欠 75%),用户反馈后才补全 |

---

## 术语规范（强制）

| 正确 | 错误 | 原因 |
|------|------|------|
| 目标治疗 | 靶向治疗 | "靶向"易混淆分子靶向药 |
| 诊断分级 | 确诊分级 | 分级含probable/possible |
| 超说明书 | off-label | 中文报告用中文术语 |

---

## 领域适配指南

Phase 0-5和10条规则是疾病无关的。切换新领域只需修改参数包：

| 领域 | 路径主轴 | 关键差异 |
|------|---------|---------|
| 血液科IFI | 预防→经验→DD→目标→挽救 | 线性流 |
| 呼吸科真菌 | 疑似→诊断分型→按型治疗 | 树状分支 |
| ICU真菌 | 高危→经验→DD→目标 | 联合治疗多 |
| 肿瘤免疫 | 筛查→一线→二线→三线 | RCT数据丰富 |

---

## 参考文件索引

| 文件 | 何时读 |
|------|-------|
| references/flowchart-rules.md | Phase 3 画图前 |
| references/data-acquisition.md | Phase 2 搜数据时 |
| references/nmpa-antifungal-table.md | Phase 2.3 查适应症时 |
| references/quality-checklist.md | Phase 4 审核 + Phase 1 参数包模板 |
| references/iteration-log.md | 方法论学习 |
