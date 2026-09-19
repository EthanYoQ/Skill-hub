# 数据抓取渠道与策略

## 渠道优先级矩阵

| 数据类型 | 第一选择 | 第二选择 | 第三选择 | 避免 |
|---------|---------|---------|---------|------|
| 癌种年新发 | GLOBOCAN/国家癌症中心 | GBD数据库 | 行业咨询(摩熵/F&S) | 百度百科/知乎 |
| 治疗模式分布 | 疾病专项登记(CBMTRG) | 多中心前瞻RWE | 指南引用数据 | 单中心回顾 |
| IFI发生率 | 中国多中心前瞻(CAESAR) | 中国多中心回顾 | 国际多中心+标注 | 国际单中心 |
| 预防用药构成 | CAESAR 2.0(12中心) | 处方分析/DDD研究 | 指南推荐(≠RWE) | 药企数据 |
| 治疗用药比例 | 中国多中心RWE | 大样本单中心 | 国际RCT亚组 | 指南推荐层级 |
| 药物适应症 | NMPA说明书原文 | 中国指南引用 | 药企官网 | FDA/EMA(非中国) |
| 市场销售额 | 药融云/米内网/中康CMH | 企业年报 | 券商研报 | 自行估算 |
| 病原菌种分布 | CHIF-NET(77中心) | 多中心监测 | 单中心培养 | 国际分布直接套用 |
| **ICU 相关 IFI(RICU only)** | **呼吸与危重症医学科队列(中日友好/解放军总/复旦中山)** | **RICU 专科期刊(中华结核和呼吸、中华呼吸与危重症医学)** | **综合 ICU 研究+呼吸归口推算(🟠,限于空白填补)** | **"ICU"无 ward_type 标注的研究混用** |

## 🔑 科室 MECE 边界强制(v1.3 新增,L0 第 6 节实例化)

呼吸科 IFI 调研必须严格 MECE:
- ✅ 纳入:呼吸科普通病房 + RICU(呼吸重症医学)专属
- ❌ 剔除:综合 ICU / MICU / SICU / 血液科 / 感染科(这些是独立科室)
- ⚠️ 儿童呼吸科 PICU-resp 需单独标注

### RICU 专属搜索词(PubMed)
```
("respiratory intensive care unit" OR "respiratory ICU" OR RICU OR
 "respiratory and critical care medicine") AND
(aspergillosis OR mucormycosis OR PJP OR pneumocystis OR
 "invasive pulmonary fungal" OR IFD OR CAPA OR IAPA) AND China
NOT ("medical ICU" OR MICU OR "surgical ICU" OR SICU OR
     "mixed ICU" OR "general ICU")
```

### RICU 专属搜索词(CNKI / 万方)
```
主题: ("呼吸重症" OR "呼吸ICU" OR "呼吸科ICU" OR "呼吸与危重症")
AND  (曲霉 OR 真菌 OR CAPA OR IAPA OR 肺孢子菌 OR 毛霉)
排除: 综合ICU MICU SICU 外科ICU 心脏ICU
```

### 重点期刊(高概率 RICU 来源)
- **中华结核和呼吸杂志**
- **中华呼吸与危重症医学杂志**
- **中国呼吸与危重监护杂志**
- **Chin J Respir Critic Care Med**(英文版同上)

### 重点团队(呼吸危重症 KOL, 研究多来自 RICU)
- 曹彬(中日友好医院呼吸与危重症医学科)
- 解立新(解放军总医院呼吸与危重症医学科)
- 施毅(南京总医院/东部战区总医院呼吸与危重症医学科)
- 陈荣昌(广州医科大学附属第一医院呼吸危重症)
- 宋元林(复旦中山呼吸科)
- 黎毅敏(广州医科大学附一呼吸危重症)

### Agent 返回数据强制 schema(来自 L0 第 7 节)
Agent 返回 ICU 相关数据时每条必含:
- `ward_type`: RICU | MICU | SICU | general_ICU | mixed | unclear
- `dept_attribution`: respiratory | ICU_independent | hematology | other

`ward_type != RICU` 的条目自动剔除出呼吸科 RICU 口径,仅作邻接科室参考。

## 搜索关键词模板库

### PubMed/CNKI搜索

**患者基数层：**
```
PubMed: ("acute myeloid leukemia" OR AML) AND China AND (incidence OR epidemiology) AND (2022 OR 2023 OR 2024)
CNKI: 主题=急性髓系白血病 AND 主题=流行病学 AND 年份=2021-2025
万方: 中国 白血病 发病率 流行病学
```

**IFI发生率层：**
```
PubMed: ("invasive fungal" OR IFD OR IFI) AND (hematolog* OR leukemia OR "stem cell transplant") AND China AND multicenter
PubMed: CAESAR AND antifungal AND China
CNKI: 侵袭性真菌病 AND (血液科 OR 白血病 OR 移植) AND 多中心
```

**药物使用比例层：**
```
PubMed: (voriconazole OR posaconazole OR isavuconazole OR caspofungin) AND (real-world OR prescribing OR utilization) AND China AND hematolog*
CNKI: 抗真菌药物 AND (处方分析 OR DDD OR 用药频度) AND 血液科
```

**适应症查询层：**
```
NMPA网站: https://www.nmpa.gov.cn → 药品查询 → 输入通用名
药智网: https://db.yaozh.com → 说明书查询
用药助手: https://drugs.dxy.cn → 说明书
```

**市场数据层：**
```
药融云: https://www.pharnexcloud.com → 药品销售 → 全身抗真菌
医药魔方: https://bydrug.pharmcube.com → 市场分析
中康CMH: 需要账号
```

## 数据抓取顺序（实战验证）

**第一轮（框架建立，1-2小时）：**
1. 搜GLOBOCAN中国数据 → 建立各癌种年新发框架
2. 搜CBMTRG最新年报 → 填入HSCT例数和病种分布
3. 搜CAESAR 2.0原文 → 填入IFI率、预防构成、病原谱
4. 搜NMPA各药适应症 → 建立适应症约束表

**第二轮（补充分流比例，2-3小时）：**
5. 搜各病种化疗接受率 → 补充"化疗 vs 不化疗"分流
6. 搜非HSCT预防覆盖率 → 通常找不到全国数据，标注"缺失"
7. 搜治疗策略分流（经验/DD/目标）→ CAESAR-HSCT 1.0
8. 搜各病原目标治疗的药物使用比例 → 通常找不到，标注"缺失"

**第三轮（市场数据+查漏，1小时）：**
9. 搜药融云/米内网市场数据 → 各药销售额和份额
10. 搜各中心处方分析/DDD → 补充用药构成
11. 交叉验证：CBMTRG总数 ÷ GLOBOCAN新发 = HSCT率，检查合理性

## "未检索到"的处理规则

1. 先确认搜索关键词是否穷尽（中英文都搜了？CNKI和PubMed都搜了？）
2. 如果确实没有中国数据，搜国际数据并标注"⚪非中国数据，仅供参考"
3. 如果连国际数据都没有，写"未检索到可信数据源"
4. 如果可以基于已有数据合理推算，给出区间估算并标注"估"和推算逻辑
5. **绝对禁止**：用"约30-50%"这种无依据的范围填空

## 关键陷阱

| 陷阱 | 表现 | 正确做法 |
|------|------|---------|
| GLOBOCAN合并统计 | 白血病只报总数，无AML/ALL拆分 | 标注"行业估算"，给出估算依据 |
| 指南推荐≠真实世界 | 指南说"一线推荐伏立康唑"当成用药比例 | 分开两列：指南推荐层级 / RWE用药比例 |
| 单中心外推 | 北大人民医院数据当成"中国数据" | 标注中心名+样本量+地区，注明不可外推 |
| 时间窗越界 | 引用2015年数据当作现状 | 严格遵守证据窗(2021-2026) |
| 剂型混淆 | 泊沙康唑3剂型适应症不同但混用 | 逐一查每个剂型的NMPA适应症 |
| 口径混用 | proven+probable与含possible混在一起 | 始终区分两个口径，以CID发表版为准 |
