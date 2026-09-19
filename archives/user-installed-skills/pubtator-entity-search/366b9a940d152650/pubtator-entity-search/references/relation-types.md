# PubTator3 关系类型完整参考

PubTator3 在 `/relations` 端点上提供 8 类核心生物医学关系标签。本表为完整定义、典型主-宾语组合、置信度阈值与查询示例。

## 关系类型总览

| 关系标签 | 含义 | 典型主语 → 宾语 | 方向性 |
|---|---|---|---|
| `treat` / `treats` | 治疗 / 适应症 | Chemical → Disease | 有向 |
| `cause` / `causes` | 致病 / 引发 | Chemical/Variant → Disease | 有向 |
| `inhibit` / `inhibits` | 抑制 (药理) | Chemical → Gene/Protein | 有向 |
| `interact_with` | 蛋白-蛋白 / 药物-基因相互作用 | Gene ↔ Gene 或 Chemical ↔ Gene | 无向 |
| `regulate` / `regulates` | 调控 (上下游) | Gene → Gene | 有向 |
| `associate` / `associated_with` | 关联 (弱因果) | Gene ↔ Disease / Variant ↔ Disease | 无向 |
| `compare` | 比较 (临床/疗效) | Chemical vs Chemical → Disease | 无向 |
| `co-occur` | 共现 (无语义方向) | 任意 ↔ 任意 | 无向 |

> 不确定关系语义时,优先用 `co-occur` 做共现挖掘,再人工二次核对方向。

---

## 1. `treat` — 治疗 / 适应症

- **典型组合**: Chemical → Disease
- **示例**:
  - ibrutinib (`MESH:D000077594`) → CLL (`MESH:D015464`)
  - voriconazole (`MESH:D014750`) → invasive aspergillosis (`MESH:D055744`)
- **查询**: `GET /relations?e1=MESH:D000077594&e2=MESH:D015464&type=treat`
- **置信度建议**: ≥ 0.7 才进入证据表;< 0.5 多为提及而非肯定治疗。

## 2. `cause` — 致病 / 引发

- **典型组合**: Chemical → Disease (药物副作用) / Variant → Disease (致病变异)
- **示例**:
  - cyclophosphamide → hemorrhagic cystitis
  - BRCA1 c.5266dupC → breast cancer
- **查询**: `GET /relations?e1=<chemical>&e2=<disease>&type=cause`
- **注意**: 包含因果关系与"引起 (induce)"语义,需二次区分剂量/时间关系。

## 3. `inhibit` — 抑制 (药理)

- **典型组合**: Chemical → Gene/Protein
- **示例**:
  - ibrutinib → BTK (`695`)
  - sotorasib → KRAS G12C
- **查询**: `GET /relations?e1=MESH:D000077594&e2=695&type=inhibit`
- **用途**: 找靶向药物-靶点对,做 drug repositioning。

## 4. `interact_with` — 相互作用

- **典型组合**: Gene ↔ Gene (PPI) / Chemical ↔ Gene (DGI)
- **示例**:
  - voriconazole ↔ CYP2C19 (代谢相互作用)
  - BTK ↔ PLCG2 (信号通路)
- **查询**: `GET /relations?e1=695&e2=5336&type=interact_with`
- **方向性**: 无向,主-宾语可互换。

## 5. `regulate` — 调控 (上下游)

- **典型组合**: Gene → Gene
- **示例**:
  - MYC → CCND1 (上调)
  - p53 → MDM2 (反馈)
- **查询**: `GET /relations?e1=4609&e2=595&type=regulate`
- **变体**: 部分文献返回 `positive_regulation` / `negative_regulation`,需二次解析。

## 6. `associate` — 关联 (弱因果)

- **典型组合**: Gene ↔ Disease / Variant ↔ Disease (GWAS 风格)
- **示例**:
  - APOE ɛ4 ↔ Alzheimer disease
  - HLA-B*57:01 ↔ abacavir hypersensitivity
- **查询**: `GET /relations?e1=348&e2=MESH:D000544&type=associate`
- **置信度建议**: 多 < 0.6,需配合 GWAS catalog / ClinVar 二次核实。

## 7. `compare` — 比较

- **典型组合**: Chemical vs Chemical → Disease (临床头对头)
- **示例**:
  - ibrutinib vs chlorambucil → CLL
- **用途**: 找头对头随机对照试验。
- **置信度建议**: 较稀疏,通常需 fallback `co-occur` + 出版类型筛选 RCT。

## 8. `co-occur` — 共现

- **任意类型**;无语义方向
- **用途**: 探索性挖掘 — 当 `treat`/`cause`/`inhibit` 都没命中时退化使用。
- **查询**: `GET /relations?e1=<id1>&e2=<id2>&type=co-occur`
- **注意**: 共现 ≠ 关联,需人工核对句级证据。

---

## 关系输出格式

```json
{
  "pmid": "12345678",
  "subject":   { "text": "ibrutinib", "type": "Chemical", "id": "MESH:D000077594" },
  "predicate": "inhibits",
  "object":    { "text": "BTK",       "type": "Gene",     "id": "695" },
  "score": 0.92,
  "evidence_sentence": "Ibrutinib irreversibly inhibits BTK by covalent binding to Cys481.",
  "section": "Abstract"
}
```

## 置信度阈值规则

| `score` 区间 | 处理 |
|---|---|
| ≥ 0.8 | 高可信,直接采纳 |
| 0.5 – 0.8 | 中等,人工或 LLM 二次核对句级证据 |
| < 0.5 | **过滤丢弃** (假阳性高) |

## 关系语义陷阱

1. **同义谓词**：`treat` 与 `treats` 在不同 PMID 上可能并存,合并为同一谓词。
2. **方向反转**：BioRED 数据集存在主-宾语反转的标注 — 在跨 PMID 聚合时按 `(min_id, max_id)` 排序去重。
3. **隐含关系**：`co-occur` 不等于因果;只用作召回扩展,不作为证据。
4. **语义重叠**：`inhibit` ⊂ `interact_with`,但 PubTator3 通常只返回最具体的标签。
5. **临床否定**：评估时关注 `evidence_sentence` 是否含 "not", "fail to", "no association" 等否定语。

## 关系到证据的折叠流程

```text
1. /relations → 拿候选 PMID + score + evidence_sentence
2. 过滤 score < 0.5
3. 按 evidence_sentence 检测否定语 (LLM 或正则)
4. 用 pubmed-eutils.efetch 拉 PubDate / PublicationType
5. 按出版类型加权 (Meta-Analysis > RCT > Cohort > Case Report)
6. 输出三元组证据表
```
