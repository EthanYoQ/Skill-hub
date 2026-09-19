---
name: evidence-appendix-sync
description: >
  Use when finalizing market research report appendix C (参考文献清单) before
  delivery; Use when verifying evidence/ folder PMID coverage matches the
  report's reference list; Use when generating 附录 C / Appendix C from a
  populated evidence/ directory; Use when reviewing a delivered report for
  PMID 漏列 / 幻觉 / 等级缺失. Trigger keywords: 市场调研报告交付前 / 附录 C
  生成 / 参考文献清单 / evidence 同步 / PMID 双向校验 / 文献附录核对.
  Library-agnostic — works for hematology IFI, respiratory ICU 真菌, oncology,
  cardiology, ICU sepsis, any evidence-driven medical/pharmaceutical market
  research report where evidence/*.md and 报告附录 C must stay bidirectionally
  synchronized. Inherits L0 market-sizing-mece-foundation §evidence-driven
  pattern.
  v1.1 (2026-04-25):基于血液科 v2.5.2 复盘,新增 Iron Law 5(每条 PMID 必含 5 项元数据,
  零裸数字)与 Iron Law 6(PMID 主题相关性核查,防关键词污染),配套 SOP Step 6/7/8
  与失败模式 #9/#10。
  v1.2 (2026-04-25):基于血液科 v2.5.3 复盘,新增 Iron Law 7(evidence/ 内部标注 vs
  PubMed 真实文献冲突时,信 PubMed 删 evidence/ 错误,禁止"保留 + 警告"妥协),
  确立数据源信任优先级链(PubMed > 期刊官网 > NMPA > evidence 笔记 > LLM 推断),
  配套 SOP Step 9(PMID 内外冲突核查)与失败模式 #11(zombie warnings)。
  PMID source of truth: `pubmed-eutils.efetch_abstracts()` cache; do NOT use `pubmed-search` (Valyu, deprecated).
---

# Evidence ↔ 附录 C 双向同步 Skill (L2 · 复用组件)

> **L2 工具组件**:本 skill 强制执行"evidence/ 文件夹 PMID 集合"与"报告附录 C PMID 清单"的**双向零差集同步**。
> 设计目标:杜绝"作者凭印象手写附录 C 致 75% PMID 缺失"的反复失败模式。
> 上游依赖:`market-sizing-mece-foundation` (L0 evidence-driven pattern) + 任意 L1 疾病 skill (IFI / ICU 真菌 / 等)

> **诞生背景 (2026-04-25)** · 血液科 IFI v2.5 项目交付后,用户审计发现:`evidence/*.md` 累积 **44 条 PMID**,但报告附录 C 仅列 **11 条**,缺失率 **75%**。根因不是数据丢失,而是"报告作者凭印象写附录 C,没有完整列出 evidence 中所有 PMID"。本 skill 将该校验流程标准化、可移植化。

---

## 一句话定义

报告交付前,**机械地**对齐 `evidence/` 文件夹中所有 PMID 与报告附录 C 中所有 PMID,确保两个集合**完全相等**(双向零差集),并按"证据等级 × 研究类型"分组呈现。

---

## 何时调用本 skill

| 场景 | 触发动作 |
|---|---|
| 任何医学市场调研报告**交付前最后一道关** | 强制调用,作为质控终点 |
| 附录 C / 参考文献清单第一次起草 | 直接用本 skill 生成,而非手写 |
| 报告迭代到 v2.x / v3.x 等大版本 | 每个大版本都要重跑同步,evidence 增量必须反映在附录 C |
| 用户提出"参考文献是否完整" / "附录 C 看起来太少" | 立即用本 skill 做双向校验 |
| 跨疾病移植项目(IFI → 呼吸科 真菌 → ICU 脓毒症) | 新项目第一次交付前必跑 |

## 何时**不**调用本 skill

| 场景 | 原因 |
|---|---|
| 报告还在数据收集阶段(evidence/ 还没稳定) | 同步无意义,evidence 还在变 |
| 内部草稿、未交付版本 | 可延后到正式交付前再跑 |
| 不基于 evidence/ 模式的报告(纯定性、纯访谈) | 没有 PMID 集合可对齐 |
| 单纯改报告排版/UI,未触动文献 | evidence 与附录 C 都未变,无需重跑 |

---

## 核心规范 · Iron Law(违反即不通过)

### Rule 1 · evidence/ → 附录 C 零遗漏

`evidence/` 中**所有** PMID 必须出现在附录 C。不允许"作者觉得不重要就不列"。

> 反例(血液科 v2.5 复现):evidence/ 有 44 条 PMID,附录 C 只列 11 条。33 条 evidence 中实际引用但附录未列 → 读者无法追溯。

```bash
# 校验脚本(必须返回空)
diff <(grep -roh "PMID:[0-9]\+" evidence/ | sort -u) \
     <(grep -oh "PMID:[0-9]\+" 报告_附录C.html | sort -u)
```

### Rule 2 · 附录 C → evidence/ 零幻觉

附录 C 中**所有** PMID 必须能在 `evidence/` 找到来源文件。不允许"凭记忆补一个 PubMed 号"。

> 反例:附录 C 列 PMID:34567890,但 grep 整个 evidence/ 找不到 → 幻觉,必须删除或补充对应 evidence/{PMID}.md 文件。

### Rule 3 · 双维度分组(证据等级 × 研究类型)

附录 C 必须按以下分组层级展示:

```
附录 C · 参考文献清单(共 N 条)
├── 🟢 A 级证据(指南 / Meta 分析 / Cochrane)
├── 🔵 B 级证据(RCT / 大样本前瞻队列)
├── 🟡 C 级证据(回顾性研究 / 单中心队列 / 病例系列)
├── ⚪ 参考性资料(综述 / 述评 / 流行病学背景)
└── 🟠 待标注(评级未定的 PMID,必须在交付前清零)
```

**禁止** 把 PMID 平铺一个长列表 — 读者无法判断证据强度。

### Rule 4 · 每条 PMID 四要素必含

| 要素 | 示例 |
|---|---|
| 第一作者 + 年份 | `Maertens J, 2024` |
| 研究类型 | `RCT` / `Meta-analysis` / `Retrospective cohort` |
| 核心数据(1-2 句话) | `泊沙康唑 vs. 氟康唑预防 IFI,IFD 率从 8% → 2.3% (HR=0.28)` |
| 应用领域(指向报告章节) | `用于 §3.2 高危预防策略 Sankey 图` |

缺任一要素 → 阻塞交付。

### Rule 5 · 每条 PMID 必含 5 项元数据(零裸数字)· v1.1 新增

附录 C 中**每条** PMID 必须同时包含以下 **5 项元数据**,缺一即视为"占位式补录"(zombie PMID),禁止交付:

| # | 元数据 | 示例 | 缺失后果 |
|---|---|---|---|
| 1 | 标题(简化) | `泊沙康唑预防造血干细胞移植后 IFD 的 III 期 RCT` | 读者无法判断主题 |
| 2 | 第一作者 + 年份 | `Maertens J, 2024` | 无法追溯/引用/同行讨论 |
| 3 | 期刊名 | `N Engl J Med` / `Blood` / `J Clin Oncol` | 无法判断证据权威性 |
| 4 | n=受试者数(或 study type) | `n=575` 或 `Phase III RCT, multi-center` | 无法判断证据强度 |
| 5 | 核心数据一行(关键百分比/OR/HR) | `IFD 率 2.3% vs 8% (HR=0.28, p<0.001)` | 无法判断结果显著性 |

> **历史复现证据(血液科 v2.5.1)**:附录 C 子分组 C.5 / C.6 共 **15 条 PMID 仅列裸数字**,无标题、无作者、无期刊、无 n、无核心数据。用户立即指出"这些文献仍处于不明确/缺失状态"。根因:v1.0 skill 只规定 evidence/ ↔ 附录 C 集合差为零,但**未强制每条 PMID 必含元数据**。Sub-agent 把 evidence/ 中 grep 出的孤立 PMID 直接列入附录 C,留空元数据字段。

> **如何应用**:发现 evidence/ 有 PMID 但缺元数据时,**必须**调用以下任一通道拉取元数据,再写入附录 C:
> - `medical-research` skill
> - `pubmed-search` skill
> - `WebFetch https://pubmed.ncbi.nlm.nih.gov/{PMID}/`
>
> **禁止**:在元数据缺失时强行交付,或用"待补充"占位。

### Rule 6 · PMID 主题相关性核查(防关键词污染)· v1.1 新增

每条进入附录 C 的 PMID,必须用 PubMed 元数据验证标题与项目主题相关。**关键词污染**(早期 evidence 采集时关键词模糊匹配混入主题无关 PMID)是一类隐蔽但严重的失败模式。

**项目领域 → 标题关键词相关性矩阵**:

```
血液科 IFI 项目  → 标题应含: hematolog* / leukemia / lymphoma / myeloma /
                            HSCT / CAR-T / fungal / aspergillus / candida /
                            mucor / pneumocystis / antifungal / IFD / IFI /
                            真菌 / 血液 / 移植

呼吸科真菌项目  → 标题应含: respirator* / pulmonar* / RICU / CAPA / CPA /
                            ABPA / aspergill* / pneumon* / 呼吸 / 肺

肿瘤免疫项目    → 标题应含: tumor / oncology / immune* / checkpoint / CAR /
                            antibody
```

> **历史复现证据(血液科 v2.5.2)**:经 PubMed 核查发现 **4 条主题完全无关 PMID** 混入血液科 IFI 附录 C:
> - `PMID:10793555` → 日本老年社会医学(2000)
> - `PMID:37293262` → 茶尺蠖昆虫学
> - `PMID:39034762` → 钙钛矿太阳能电池
> - `PMID:39039587` → 脊柱外科麻醉
>
> 根因:v2.4 evidence 采集 sub-agent 关键词搜索时模糊匹配混入(搜 "hematology fungal" 返回邻近数字段落中无关文献),v1.0 skill 没有"PMID 主题相关性核查"步骤。zombie PMID 不仅占位,还可能让读者**误以为有支撑数据**。

> **如何应用**:`evidence-appendix-sync` 阶段用 grep + PubMed 拉每条 PMID 的标题,与项目关键词矩阵 fuzzy match。无关项 → **从 evidence/ 删除**并在附录 C 中**透明披露**(不要静默删除,留痕展示根因)。透明披露格式见 Step 8 模板。

### Rule 7 · evidence/ 内部标注 vs PubMed 真实文献冲突时,信 PubMed · v1.2 新增

当 evidence/ 中的 PMID 标注(主题/作者/期刊)与 PubMed 实际返回的文献元数据**直接冲突**时,**唯一正确处理**是:**信任 PubMed,删除 evidence 错误条目,留 TODO 让人类后续重找正确 PMID**。**禁止**"保留 + ⚠️ 警告"的妥协式呈现。

**数据源信任优先级链(物理真理 → 易错笔记)**:

```
PubMed (PMID → 文献的物理映射 · 不可争议)
  > 期刊官网 / DOI 映射
  > NMPA 批件原文
  > 项目 evidence/ 笔记 (可错 · 输入错误/OCR 错误/复制粘贴移位)
  > LLM 推断 / 印象 (最不可信)
```

**Why 不能"保留 + 警告"**:
- PubMed 是 PMID → 文献的**物理映射**,绝对可靠;evidence/ 只是项目笔记,可能因人类输入错误 / OCR 错误 / 复制粘贴时数字移位导致 PMID 数字与标注不符
- "保留 + ⚠️ 警告"是**最差妥协** — 读者扫描附录 C 时仍会**误以为是真文献**(警告框易被忽略),且警告框反而让报告显得不专业
- 正确做法是**信 PubMed 删 evidence**,在 evidence/ 原引用位置留 HTML TODO 注释("此处原引 X 研究,但 PMID:XXX 在 PubMed 上是 Y 主题,请人工重找正确 PMID"),并在附录 C 删除披露区透明列出

> **历史复现证据(血液科 v2.5.3)**:经 PubMed 复核发现 **3 条 evidence/ 标注与 PubMed 真实文献直接冲突**:
> - `PMID:37293262` · evidence/ 标 "Xu Y 2023 · DLBCL PJP 病例系列 · SAGE Open Med" / PubMed 实为 "Yang F 2023 · 茶尺蠖 CXE14 羧酯酶基因表达 · Front Physiol"
> - `PMID:39034762` · evidence/ 标"中华血液学杂志推断" / PubMed 实为钙钛矿太阳能电池
> - `PMID:39039587` · evidence/ 标"中华血液学杂志推断" / PubMed 实为脊柱外科麻醉
>
> v2.5.2 错误处理:把这 3 条"保留在附录 C C.5 + 加 ⚠️ 警告框"。v2.5.3 用户立即指出这是**最差妥协** — 应该信 PubMed 物理真理,直接删除。

> **如何应用(6 步流程)**:
> - **Step 1**:用 `WebFetch https://pubmed.ncbi.nlm.nih.gov/{PMID}/` 或 `pubmed-search` skill 拉每条 evidence/ 中 PMID 的真实标题
> - **Step 2**:与 evidence/ 中标注做标题关键词 fuzzy match(同主题词共现 ≥1 即可)
> - **Step 3**:不匹配 → 标记为"内外冲突"
> - **Step 4**:从附录 C **直接删除**该 PMID(不可"保留 + 警告")
> - **Step 5**:在 evidence/ 原引用位置追加 HTML 注释:
>   ```html
>   <!-- TODO v2.5.3: PMID:37293262 evidence 笔记标注 DLBCL PJP 病例系列,
>        但 PubMed 真实为茶尺蠖昆虫学(Yang F 2023 Front Physiol),内外冲突。
>        请人工重找正确 PMID 并替换。-->
>   ```
> - **Step 6**:在附录 C "C.6 已删除条目"区块,新建"类型 B · 内外冲突"子表格透明披露(区别于 v1.1 的"类型 A · 关键词污染")

---

## 执行流程 · SOP(9 步)

### Step 1 · 提取 evidence/ 中全部 PMID

```bash
# Bash(Git Bash / WSL / macOS)
grep -roh "PMID:[0-9]\+" evidence/ | sort -u > /tmp/evidence_pmids.txt
wc -l /tmp/evidence_pmids.txt
```

```powershell
# PowerShell 5.1 等价命令
Select-String -Path "evidence\*.md" -Pattern "PMID:\d+" -AllMatches |
  ForEach-Object { $_.Matches.Value } | Sort-Object -Unique |
  Out-File -Encoding utf8 evidence_pmids.txt
(Get-Content evidence_pmids.txt).Count
```

**预期输出**:每行一个 `PMID:XXXXXXXX`,总数应等于 evidence 文件夹独立 PMID 数。

### Step 2 · 按证据等级分组

打开每个 evidence/{PMID}.md,读取 frontmatter 中的 `evidence_level: A|B|C|D` 字段,按 5 个分组桶整理:

```yaml
# evidence/PMID_38381437.md 头部示例
---
pmid: "PMID:38381437"
first_author: "Maertens J"
year: 2024
study_type: "Phase III RCT"
evidence_level: "B"   # ← 核心字段
key_finding: "泊沙康唑 vs 氟康唑 IFD 率 2.3% vs 8%"
applies_to: "§3.2 高危预防策略"
---
```

若 evidence/ 文件没有 `evidence_level` 字段 → 进入 🟠 待标注桶,同时回到 evidence 补齐。

### Step 3 · 每条 PMID 收集四要素元数据

可用 Python / 手工 / Bash 拼接,生成中间 JSON:

```json
{
  "PMID:38381437": {
    "first_author": "Maertens J",
    "year": 2024,
    "study_type": "Phase III RCT",
    "level": "B",
    "key_finding": "泊沙康唑 vs 氟康唑预防 IFD 率 2.3% vs 8% (HR=0.28)",
    "applies_to": "§3.2 高危预防 / Sankey 图"
  },
  ...
}
```

### Step 4 · 生成附录 C HTML 块

用下方"完整模板"直接替换报告中旧的附录 C `<section>`。

### Step 5 · 双向数量校验

```bash
# 必须返回完全一致的差集为空
EVIDENCE_COUNT=$(grep -roh "PMID:[0-9]\+" evidence/ | sort -u | wc -l)
APPENDIX_COUNT=$(grep -oh "PMID:[0-9]\+" 报告_附录C.html | sort -u | wc -l)
echo "evidence: $EVIDENCE_COUNT  appendix: $APPENDIX_COUNT"
# 两者必须相等
diff <(grep -roh "PMID:[0-9]\+" evidence/ | sort -u) \
     <(grep -oh "PMID:[0-9]\+" 报告_附录C.html | sort -u)
# 期望:无任何输出(空 diff = 通过)
```

差集非空 → 回到 Step 1 排查;**严禁**强行交付。

### Step 6 · 用 PubMed 拉每条 PMID 元数据(v1.1 新增)

对每条 PMID,**逐条**确认 5 项元数据(Rule 5)是否齐全。任一缺失 → 调用以下通道补齐:

```bash
# 通道 A:WebFetch(单条 PMID)
WebFetch https://pubmed.ncbi.nlm.nih.gov/{PMID}/
# 解析返回 HTML:<title>(标题) · authors · journal · year · abstract(找 n / OR / HR)

# 通道 B:medical-research / pubmed-search skill(批量更优)
# 输入 PMID 列表,返回结构化元数据 JSON
```

**执行清单(对每条 PMID)**:
- [ ] 标题(简化):去掉冗余副标题,保留主诊断 + 干预 + 设计
- [ ] 第一作者 + 年份:`Maertens J, 2024`
- [ ] 期刊名:`N Engl J Med`(用标准 ISO 缩写)
- [ ] n(受试者数)或 study type:`n=575` 或 `Phase III RCT`
- [ ] 核心数据一行:关键百分比 / OR / HR / p 值

写入对应 `evidence/{PMID}.md` frontmatter,**同步**更新附录 C 条目。

### Step 7 · 主题相关性核查(v1.1 新增)

对每条 PMID,把标题与"项目领域关键词矩阵"(见 Rule 6)做 fuzzy match:

```bash
# 示例:血液科 IFI 项目核查
for pmid in $(cat /tmp/evidence_pmids.txt); do
  TITLE=$(curl -s "https://pubmed.ncbi.nlm.nih.gov/${pmid#PMID:}/" | \
          grep -oP '<title>\K[^<]+' | head -1)
  echo "$pmid: $TITLE" | \
    grep -iE "hematolog|leukemia|lymphoma|myeloma|HSCT|CAR-T|fungal|aspergillus|candida|mucor|pneumocystis|antifungal|IFD|IFI|真菌|血液|移植" || \
    echo "⚠️ OFF-TOPIC: $pmid - $TITLE"
done
```

**判定规则**:
| 情况 | 处理 |
|---|---|
| 标题命中 ≥1 个领域关键词 | 通过 ✅ |
| 标题完全不命中 | 标记为"主题无关",进入 Step 8 透明披露 |
| 标题部分命中(交叉学科) | 人工复核摘要,有疑问保守保留 + 标注 |

### Step 8 · 无关项透明删除 + 披露区块(v1.1 新增)

发现的无关 PMID,**禁止静默删除**(读者审计时无法追溯根因)。必须从 evidence/ 删除并在附录 C 末尾追加"删除披露区块":

```html
<!-- 附录 C 末尾追加 -->
<details class="ref-group level-removed">
  <summary>⚠️ 已删除条目透明披露(v1.1 引入,共 <strong>4</strong> 条) ·
    <em>因主题无关 / 关键词污染 / 重复幻觉,从 evidence/ 与附录 C 同步删除</em>
  </summary>
  <table class="removed-table">
    <thead>
      <tr><th>已删 PMID</th><th>实际主题</th><th>删除原因</th><th>检测时间</th></tr>
    </thead>
    <tbody>
      <tr>
        <td><span class="pmid">PMID:10793555</span></td>
        <td>日本老年社会医学(2000)</td>
        <td>关键词污染 — 与血液科 IFI 主题完全无关</td>
        <td>2026-04-25</td>
      </tr>
      <tr>
        <td><span class="pmid">PMID:37293262</span></td>
        <td>茶尺蠖昆虫学</td>
        <td>关键词污染 — 模糊匹配混入</td>
        <td>2026-04-25</td>
      </tr>
      <tr>
        <td><span class="pmid">PMID:39034762</span></td>
        <td>钙钛矿太阳能电池</td>
        <td>关键词污染 — PubMed 邻近号段误抓</td>
        <td>2026-04-25</td>
      </tr>
      <tr>
        <td><span class="pmid">PMID:39039587</span></td>
        <td>脊柱外科麻醉</td>
        <td>关键词污染 — 非血液科文献</td>
        <td>2026-04-25</td>
      </tr>
    </tbody>
  </table>
  <p class="meta">
    根因分析:v2.4 evidence 采集 sub-agent 关键词搜索时模糊匹配混入。
    v1.1 起强制 Iron Law 6(主题相关性核查)防止再发生。
  </p>
</details>
```

**重要**:删除披露区块**必须**保留至所有后续版本(v2.6 / v3.0 等),让审计链路完整可见。

### Step 9 · PMID 内外冲突核查(v1.2 新增)

Step 7 解决"evidence/ + PubMed 都无关"(关键词污染)。Step 9 解决**更隐蔽**的"evidence/ 标对题 + PubMed 显示无关"(内外冲突)— 即 evidence/ 笔记记录的主题/作者/期刊与 PubMed 真实文献元数据**直接冲突**。

**为什么 Step 7 不够**:Step 7 只比对 PubMed 标题与项目领域关键词。如果 evidence/ 笔记自身写得"看起来对题"(例:写"DLBCL PJP 病例系列"),Step 7 会通过领域关键词核查,但 PubMed 真实文献可能完全是另一篇(例:茶尺蠖昆虫学)。这种"内外冲突"必须独立核查。

**执行流程**:

```bash
# 对每条 PMID,逐条比对 evidence/ 标注 vs PubMed 真实标题
for pmid in $(cat /tmp/evidence_pmids.txt); do
  # Step 9.1:从 evidence/{PMID}.md 提取笔记中的标注主题
  EVIDENCE_TITLE=$(grep -A1 "^title:" evidence/${pmid#PMID:}.md | head -1)

  # Step 9.2:从 PubMed 拉真实标题
  PUBMED_TITLE=$(curl -s "https://pubmed.ncbi.nlm.nih.gov/${pmid#PMID:}/" | \
                 grep -oP '<title>\K[^<]+' | head -1)

  # Step 9.3:fuzzy match(关键名词共现 ≥1 即认为一致)
  echo "=== $pmid ==="
  echo "Evidence: $EVIDENCE_TITLE"
  echo "PubMed:   $PUBMED_TITLE"
  # 人工核对 / LLM 判断关键词共现
done
```

**判定 + 处理**:

| 比对结果 | 处理 |
|---|---|
| evidence/ 标题与 PubMed 标题主题词共现 ≥1 | 通过 ✅(PMID 正确) |
| 主题词完全不共现(内外冲突) | **删除该 PMID + evidence/ 留 TODO + 附录 C 透明披露** |
| 部分共现(交叉学科 / 模糊) | 人工复核摘要,有疑问保守删除 |

**evidence/ TODO 注释模板**:

```html
<!-- TODO v2.5.3: PMID:{pmid} evidence 笔记标注 "{evidence_title}",
     但 PubMed 真实文献为 "{pubmed_title}",内外冲突。
     疑似输入错误 / OCR 错误 / 复制粘贴时 PMID 数字移位。
     请人工重新查找正确 PMID 并替换;原 evidence 内容暂保留供参考。-->
```

**附录 C 透明披露(类型 B 内外冲突)**— 在 Step 8 的"已删除条目透明披露"区块中追加新表格:

```html
<details class="ref-group level-removed">
  <summary>⚠️ 已删除条目透明披露 · 类型 B · 内外冲突(v1.2 引入,共 <strong>3</strong> 条)</summary>
  <p class="meta">
    <strong>定义</strong>:evidence/ 笔记标注主题与 PubMed 真实文献主题直接冲突。
    <strong>处理原则</strong>(Iron Law 7):信任 PubMed 物理真理,删除 evidence 错误条目。
  </p>
  <table class="removed-table">
    <thead>
      <tr><th>已删 PMID</th><th>evidence/ 笔记标注</th><th>PubMed 真实主题</th><th>检测时间</th></tr>
    </thead>
    <tbody>
      <tr>
        <td><span class="pmid">PMID:37293262</span></td>
        <td>Xu Y 2023 · DLBCL PJP 病例系列 · SAGE Open Med</td>
        <td>Yang F 2023 · 茶尺蠖 CXE14 羧酯酶基因表达 · Front Physiol</td>
        <td>2026-04-25</td>
      </tr>
      <tr>
        <td><span class="pmid">PMID:39034762</span></td>
        <td>(笔记推断为)中华血液学杂志</td>
        <td>钙钛矿太阳能电池</td>
        <td>2026-04-25</td>
      </tr>
      <tr>
        <td><span class="pmid">PMID:39039587</span></td>
        <td>(笔记推断为)中华血液学杂志</td>
        <td>脊柱外科麻醉</td>
        <td>2026-04-25</td>
      </tr>
    </tbody>
  </table>
  <p class="meta">
    根因分析:疑似 evidence 录入时人类输入错误 / OCR 错误 / 复制粘贴时 PMID 数字移位。
    v1.2 起强制 Iron Law 7 + Step 9 PMID 内外冲突核查防止再发生。
    evidence/ 原引用位置已留 TODO 注释,待人工重找正确 PMID。
  </p>
</details>
```

**Why 必须删除而非"保留 + 警告"**(再次强调,这是 v2.5.2 → v2.5.3 最重要的修正):
- 读者扫描附录 C 时**警告框易被忽略**,仍会误以为是真文献 → 引用错误传播
- "保留 + 警告"反而让报告显得不专业(读者疑问:为什么把已知有问题的文献仍然展示?)
- PubMed 是**物理真理**,evidence/ 笔记可错;遵循信任优先级链,应该信 PubMed
- 删除后留 TODO 是**唯一正确的渐进修复**:先去除错误信息,再让人类后续补正确 PMID

---

## 完整模板(直接复制粘贴)

```html
<section id="appendix-c" class="appendix">
  <h2>附录 C · 参考文献清单(共 <span id="ref-total">44</span> 条)</h2>
  <p class="meta">PMID 与 evidence/ 文件夹双向同步 · 最后校验:2026-04-25</p>

  <!-- 🟢 A 级:指南 / Meta 分析 / Cochrane -->
  <details open class="ref-group level-a">
    <summary>🟢 A 级证据(指南 / Meta 分析 / Cochrane) · <strong>N 条</strong></summary>
    <ol>
      <li>
        <span class="pmid">PMID:38381437</span> · Maertens J, 2024 ·
        <em>Phase III RCT</em> ·
        泊沙康唑 vs 氟康唑预防 IFD 率 2.3% vs 8% (HR=0.28) ·
        <a href="#sec-3-2">用于 §3.2 高危预防策略</a>
      </li>
      <!-- ...依次列出 A 级所有 PMID... -->
    </ol>
  </details>

  <!-- 🔵 B 级:RCT / 大样本前瞻队列 -->
  <details open class="ref-group level-b">
    <summary>🔵 B 级证据(RCT / 大样本前瞻队列) · <strong>N 条</strong></summary>
    <ol>
      <!-- ...所有 B 级 PMID,四要素齐全... -->
    </ol>
  </details>

  <!-- 🟡 C 级:回顾性 / 单中心 / 病例系列 -->
  <details class="ref-group level-c">
    <summary>🟡 C 级证据(回顾性 / 单中心 / 病例系列) · <strong>N 条</strong></summary>
    <ol>
      <!-- ... -->
    </ol>
  </details>

  <!-- ⚪ 参考性资料 -->
  <details class="ref-group level-ref">
    <summary>⚪ 参考性资料(综述 / 述评 / 流行病学背景) · <strong>N 条</strong></summary>
    <ol>
      <!-- ... -->
    </ol>
  </details>

  <!-- 🟠 待标注:交付前必须清零 -->
  <details class="ref-group level-pending">
    <summary>🟠 待标注(交付前清零) · <strong>0 条</strong></summary>
    <ol>
      <!-- 空数组 = 通过 -->
    </ol>
  </details>

  <!-- 证据等级说明表 -->
  <table class="evidence-legend">
    <thead>
      <tr><th>等级</th><th>含义</th><th>典型来源</th></tr>
    </thead>
    <tbody>
      <tr><td>🟢 A</td><td>最强证据</td><td>系统综述 / Meta / Cochrane / 一线指南</td></tr>
      <tr><td>🔵 B</td><td>较强证据</td><td>多中心 RCT / 大样本前瞻队列</td></tr>
      <tr><td>🟡 C</td><td>中等证据</td><td>回顾性研究 / 单中心 / 病例系列</td></tr>
      <tr><td>⚪ 参考</td><td>背景参考</td><td>综述 / 述评 / 流行病学统计</td></tr>
      <tr><td>🟠 待定</td><td>评级未完成</td><td>交付前必须清零</td></tr>
    </tbody>
  </table>
</section>
```

配套 CSS(可选,放 `<style>` 中):

```css
.appendix .ref-group { margin: 1rem 0; padding: 0.5rem 1rem; border-left: 4px solid; border-radius: 4px; }
.appendix .level-a { border-color: #16a34a; background: #f0fdf4; }
.appendix .level-b { border-color: #2563eb; background: #eff6ff; }
.appendix .level-c { border-color: #ca8a04; background: #fefce8; }
.appendix .level-ref { border-color: #94a3b8; background: #f8fafc; }
.appendix .level-pending { border-color: #ea580c; background: #fff7ed; }
.appendix .level-removed { border-color: #dc2626; background: #fef2f2; }  /* v1.1 删除披露区块 */
.appendix .removed-table { width: 100%; border-collapse: collapse; margin-top: 0.5rem; }
.appendix .removed-table th, .appendix .removed-table td { padding: 0.4rem 0.8rem; border: 1px solid #fecaca; text-align: left; }
.appendix .pmid { font-family: monospace; font-weight: 600; }
.evidence-legend { margin-top: 2rem; border-collapse: collapse; }
.evidence-legend th, .evidence-legend td { padding: 0.5rem 1rem; border: 1px solid #cbd5e1; }
```

---

## 跨疾病移植清单(下次"呼吸科 ICU 真菌"项目如何用)

下次启动新疾病项目(例:呼吸科 ICU 侵袭性曲霉),**完整复制**以下流程,无需重新设计:

1. **目录结构沿用**
   ```
   output/呼吸科ICU真菌/
   ├── evidence/        ← 沿用,每个 PMID 一个 .md,头部 frontmatter 必有 evidence_level
   ├── 报告_主体.html
   └── 报告_附录C.html  ← 由本 skill 生成
   ```
2. **frontmatter 字段**完全沿用(`pmid` / `first_author` / `year` / `study_type` / `evidence_level` / `key_finding` / `applies_to`)— 不要改字段名,改了下游脚本就坏。
3. **5 个分组桶**沿用(🟢A / 🔵B / 🟡C / ⚪参考 / 🟠待标注)— 不要新增"D 级",会破坏读者已建立的色码心智模型。
4. **校验脚本**直接复用 Step 1 + Step 5 的 bash/powershell 命令,只改 evidence 路径与附录 HTML 文件名。
5. **完整模板**直接复制,只把 `appendix-c` 的标题、`#sec-3-2` 锚点、PMID 列表替换为新疾病数据。
6. **不要"省略 evidence_level 字段先交付,后面再补"** — 这是血液科 v2.5 失败的最直接根因。
7. **不要"附录 C 只列代表性 11 条,完整 44 条放后面"** — 没有"代表性",必须全列。

---

## 失败模式速查(至少 5 条)

| # | 失败模式 | 真实案例 | 预防措施 |
|---|---|---|---|
| 1 | **凭印象手写附录 C 致大面积缺失** | 血液科 IFI v2.5:evidence/ 44 条,附录 C 仅 11 条,缺失 **75%** | 强制 Step 5 双向 diff,差集非空禁止交付 |
| 2 | **附录 C 列出 evidence 中没有的 PMID(幻觉)** | 早期草稿曾出现 PMID 数字记错位,grep evidence/ 找不到 | Rule 2 反向校验,补 evidence/{PMID}.md 或删除该条 |
| 3 | **缺等级分组,PMID 平铺成长列表** | 读者无法快速判断"哪些是 A 级强证据" | Rule 3 强制 5 桶分组 + 色码 |
| 4 | **缺第一作者+年份,只给 PMID** | 读者无法快速搜索 / 引用 / 与同行讨论 | Rule 4 四要素必含,缺一项即阻塞 |
| 5 | **不同疾病版本附录 C 不一致(混入旧文献)** | 跨疾病移植时,把血液科 PMID 留在呼吸科附录中 | 跨疾病每次重跑 Step 1,基于**当前疾病** evidence/ 重新生成 |
| 6 | **"代表性引用"借口** | 作者说"挑 11 条最重要的,完整在 evidence 文件夹" | 报告读者不会去翻 evidence/,附录就是唯一入口,必须全列 |
| 7 | **evidence_level 字段缺失/为空** | frontmatter 没填 → 默认进 🟠 待标注桶 | 交付前 🟠 桶必须清零 |
| 8 | **applies_to 字段缺失致读者无法回溯报告章节** | PMID 列出来但不知道用在哪个图/段 | Rule 4 强制四要素之一,锚点链接到报告对应章节 |
| 9 | **占位式补录(zombie PMIDs)· v1.1 新增** | 血液科 v2.5.1 附录 C C.5/C.6 共 **15 条** PMID 仅列裸数字,无标题/作者/年份/期刊/n;用户反馈"仍处于不明确状态" | **Rule 5** 强制每条 PMID 必含 5 项元数据,缺一即阻塞;Step 6 用 PubMed 拉元数据补齐 |
| 10 | **关键词污染(主题无关 PMID)· v1.1 新增** | 血液科 v2.5.2 发现 4 条无关 PMID 混入:`10793555`(老年社会医学)/ `37293262`(茶尺蠖昆虫学)/ `39034762`(钙钛矿太阳能电池)/ `39039587`(脊柱外科麻醉);根因 v2.4 evidence 采集模糊匹配 | **Rule 6** 强制 PMID 主题相关性核查,Step 7 用关键词矩阵 fuzzy match;Step 8 透明披露删除条目 |
| 11 | **内外冲突的"保留 + 警告"妥协(zombie warnings)· v1.2 新增** | 血液科 v2.5.3 发现 3 条 evidence/ 标注与 PubMed 真实文献直接冲突:`37293262` evidence 标 DLBCL PJP 病例 / PubMed 实为茶尺蠖昆虫学;`39034762` evidence 标中华血液学杂志推断 / PubMed 实为太阳能电池;`39039587` evidence 标中华血液学杂志推断 / PubMed 实为脊柱麻醉。v2.5.2 错误处理为"保留在附录 C + 加 ⚠️ 警告框",读者扫描时易误以为是真文献 | **Rule 7** 数据源信任优先级链(PubMed > 期刊官网 > NMPA > evidence 笔记 > LLM),冲突时**信 PubMed 删 evidence**,禁止"保留 + 警告";Step 9 PMID 内外冲突核查,evidence/ 留 TODO 注释,附录 C "类型 B 内外冲突"子表格透明披露 |

**根因(LLM 心智模型缺陷)**:LLM 不知道 evidence/ vs PubMed 该信谁时,默认选择"都展示 + 警告"的折中。v1.2 显式建立**数据源信任优先级链**消除该折中倾向 — PubMed 是 PMID 的物理映射,evidence 只是项目笔记可错。

---

## 验收清单(交付前自检)

交付前**逐项打钩**,全打钩才能发版:

- [ ] `grep -roh "PMID:[0-9]\+" evidence/ | sort -u | wc -l` 数量已记录
- [ ] `grep -oh "PMID:[0-9]\+" 报告_附录C.html | sort -u | wc -l` 数量已记录
- [ ] 两个数量**完全相等**
- [ ] `diff` 命令输出**为空**(双向零差集)
- [ ] 附录 C 按 5 个等级桶分组(🟢A / 🔵B / 🟡C / ⚪参考 / 🟠待标注)
- [ ] 🟠 待标注桶**为空**(N=0)
- [ ] 每条 PMID 含**四要素**:第一作者+年份 / 研究类型 / 核心数据 / 应用领域
- [ ] 每条 PMID 的 "应用领域" 链接到报告对应章节锚点(`#sec-3-2` 等)
- [ ] 证据等级说明表已附在附录 C 末尾
- [ ] 跨疾病移植场景:确认 evidence/ 不含其他疾病的 PMID(纯净校验)
- [ ] 报告页脚标注"附录 C 最后校验时间:YYYY-MM-DD"

### v1.1 新增验收项

- [ ] **每条 PMID 含 5 项元数据**(标题 / 第一作者+年份 / 期刊名 / n 或 study type / 核心数据一行),无裸数字
- [ ] **每条 PMID 标题含项目领域关键词**(对照 Rule 6 关键词矩阵 fuzzy match);未命中条目已从 evidence/ 删除并在删除披露区列出
- [ ] **透明披露区**已列出所有删除条目 + 根因(关键词污染 / 幻觉 / 重复),并记录检测时间
- [ ] Step 6 已对**所有** PMID 执行 PubMed 元数据拉取(WebFetch / medical-research / pubmed-search)
- [ ] Step 7 主题相关性核查日志已留档(便于审计)

### v1.2 新增验收项

- [ ] 附录 C 中**无任何"保留 + ⚠️ 警告"的 zombie 文献** — 检测到 evidence/ vs PubMed 内外冲突的条目,**应删除而非保留**(Iron Law 7)
- [ ] evidence/ 中所有删除的冲突条目都有 **HTML TODO 注释留痕**(`<!-- TODO v2.5.3: PMID:XXX 与 PubMed 实际文献冲突,需重找正确 PMID -->`)
- [ ] Step 9 PMID 内外冲突核查已对**每条** PMID 执行(evidence/ 标注 vs PubMed 真实标题 fuzzy match)
- [ ] 附录 C 删除披露区块按**两种类型**分列子表格:**类型 A · 关键词污染**(Step 8 / v1.1)+ **类型 B · 内外冲突**(Step 9 / v1.2)
- [ ] 数据源信任优先级链已落实:遇 PubMed vs evidence 冲突时,信 PubMed,删 evidence/

---

## 版本历史

| 版本 | 日期 | 变更 |
|---|---|---|
| v1.0 | 2026-04-25 | 初始版本。基于血液科 IFI v2.5 交付时发现的"附录 C 缺失 75% PMID"失败模式标准化 |
| v1.1 | 2026-04-25 | 基于血液科 v2.5.2 复盘新增:**Iron Law 5**(每条 PMID 必含 5 项元数据,零裸数字,堵 v2.5.1 C.5/C.6 共 15 条占位 PMID 漏洞)+ **Iron Law 6**(PMID 主题相关性核查 + 透明披露,堵 v2.5.2 发现的 4 条主题无关 PMID 关键词污染漏洞)。配套 SOP **Step 6/7/8**(PubMed 元数据拉取 / 主题核查 / 透明删除披露)、**失败模式 #9/#10**、5 项验收清单升级、**level-removed** CSS 区块样式 |
| v1.2 | 2026-04-25 | 基于血液科 v2.5.3 复盘新增:**Iron Law 7**(evidence/ 内部标注 vs PubMed 真实文献冲突时,信 PubMed 删 evidence,禁止"保留 + 警告"妥协),确立**数据源信任优先级链**(PubMed > 期刊官网 > NMPA > evidence 笔记 > LLM 推断),堵 v2.5.2 → v2.5.3 发现的 3 条 zombie warning 文献(`37293262`/`39034762`/`39039587` evidence 标注与 PubMed 真实文献直接冲突)。配套 SOP **Step 9**(PMID 内外冲突核查)、**失败模式 #11**(zombie warnings)、5 项验收清单升级、附录 C 删除披露区按"类型 A 关键词污染 / 类型 B 内外冲突"双子表格分列 |

---

Skill Presented by:YongQi, SimonSu, RuiYu, YingJi
