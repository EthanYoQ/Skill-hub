# PubTator3 实体类型完整参考

PubTator3 支持 7 类生物医学实体的自动标注 (NER + entity normalization)。本表为完整定义、标识体系、查询前缀与典型 ID 示例。

## 实体类型总览

| concept (查询参数) | 查询前缀 | 标识体系 | 描述 |
|---|---|---|---|
| `gene` | `@GENE_` | NCBI Gene ID | 蛋白编码基因 / 非编码 RNA 基因 |
| `disease` | `@DISEASE_MESH:` | MeSH / OMIM / DO | 疾病、综合征、表型 |
| `chemical` | `@CHEMICAL_MESH:` | MeSH / DrugBank / ChEBI | 化学品、药物、代谢物 |
| `variant` | `@VARIANT_` | dbSNP rs# / tmVar / ClinVar | SNP / 多态位点 |
| `mutation` | `@VARIANT_` (合并) | tmVar 表达式 | HGVS 蛋白/核酸级具体突变 |
| `species` | `@SPECIES_` | NCBI Taxonomy | 物种 (人 / 鼠 / 病原体) |
| `cellline` | `@CELLLINE_` | Cellosaurus | 细胞系 |

> **注意**：PubTator3 在内部把 `Mutation` 与 `Variant` 合并为 `Variant`，查询时统一用 `concept=variant`。

---

## 1. Gene (基因)

- **标识体系**：NCBI Gene ID (`https://www.ncbi.nlm.nih.gov/gene/<id>`)
- **示例**：
  - `695` → BTK (Bruton tyrosine kinase)
  - `1956` → EGFR
  - `7157` → TP53
  - `4609` → MYC
- **查询语法**：`text=@GENE_695` 或 `text=@GENE_BTK`
- **常见陷阱**：基因符号高度多义 (e.g. `BTK` 也是 "Brain Tumor Kinase" / 缩写)，应优先用 NCBI Gene ID 而非 symbol。

## 2. Disease (疾病)

- **标识体系**：主用 MeSH (Medical Subject Headings)，少量 OMIM
- **示例**：
  - `MESH:D055744` → Invasive Pulmonary Aspergillosis (侵袭性肺曲霉病)
  - `MESH:D015464` → Leukemia, Lymphocytic, Chronic, B-Cell (CLL)
  - `MESH:D008175` → Lung Neoplasms
  - `MESH:D003920` → Diabetes Mellitus
- **查询语法**：`text=@DISEASE_MESH:D055744`
- **数据来源**：`TaggerOne` + 字典扩展，覆盖 MeSH C 类 (Diseases)。

## 3. Chemical (化学品/药物)

- **标识体系**：主用 MeSH，部分映射到 DrugBank / ChEBI / CAS
- **示例**：
  - `MESH:D000077594` → ibrutinib
  - `MESH:D000077180` → Bruton Tyrosine Kinase Inhibitors (类)
  - `MESH:D014750` → voriconazole
  - `MESH:D015735` → cyclosporine
- **查询语法**：`text=@CHEMICAL_MESH:D000077594`
- **DrugBank 交叉引用**：autocomplete 端点偶有 `DrugBank:DB09053` 字段；不保证。

## 4. Variant (变异 / SNP)

- **标识体系**：dbSNP rs#、ClinVar、tmVar 表达式
- **示例**：
  - `rs113488022` → BRAF V600E 对应 SNP
  - `rs28934578` → TP53 R175H
  - `RS#:113488022` (PubTator 内部格式)
- **查询语法**：`text=@VARIANT_rs113488022`

## 5. Mutation (突变 — HGVS)

- **标识体系**：tmVar 输出的 HGVS 风格表达式
- **示例**：
  - `p.V600E` (BRAF V600E)
  - `c.35G>A` (KRAS G12D 核酸级)
  - `p.L858R` (EGFR L858R)
- **查询语法**：在自由文本中混合：`text=BRAF AND p.V600E`
- **PubTator3 已合并为 `concept=variant`**。

## 6. Species (物种)

- **标识体系**：NCBI Taxonomy ID
- **示例**：
  - `9606` → Homo sapiens
  - `10090` → Mus musculus
  - `746128` → Aspergillus fumigatus Af293
- **查询语法**：`text=@SPECIES_9606`
- **用途**：过滤模型生物 (排除/筛选鼠源研究)。

## 7. CellLine (细胞系)

- **标识体系**：Cellosaurus ID
- **示例**：
  - `CVCL_0030` → HeLa
  - `CVCL_0023` → A549
  - `CVCL_0291` → MCF-7
- **查询语法**：`text=@CELLLINE_CVCL_0030`

---

## Identifier 格式速查

```
GENE      → 纯数字 NCBI Gene ID            e.g. 695
DISEASE   → MESH:D###### / OMIM:######    e.g. MESH:D055744
CHEMICAL  → MESH:D###### / MESH:C######   e.g. MESH:D000077594
VARIANT   → rs######### / RS#:######      e.g. rs113488022
SPECIES   → 纯数字 Taxonomy ID            e.g. 9606
CELLLINE  → CVCL_####                     e.g. CVCL_0030
```

## BioC-JSON 中标注字段

每个 annotation 节点结构：

```json
{
  "id": "0",
  "infons": {
    "type": "Disease",                 // Gene / Disease / Chemical / Variant / Species / CellLine
    "identifier": "MESH:D055744",      // 标准 ID
    "ncbi_homologene": "..."           // 可选,基因有
  },
  "text": "invasive pulmonary aspergillosis",
  "locations": [{ "offset": 47, "length": 32 }]
}
```

## 解析最佳实践

1. **永远用 `infons.identifier` 做去重**，不要用 `text` (大小写/形态变体多)。
2. **基因 symbol 多义性**：`infons.identifier` 缺失或 `-1` 时，跳过 (NER 命中但未规范化)。
3. **物种过滤**：默认保留 `9606` (人) 与无 species 注释的 passage；如做药理研究保留 `10090`。
4. **置信度**：PubTator3 不在 BioC 标准字段中给 confidence，需用 `/relations` 端点的 `score`。
