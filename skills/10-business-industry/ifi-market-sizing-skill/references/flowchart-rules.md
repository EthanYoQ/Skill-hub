# 流程图构建硬性规则（v1.1 · 12条）

> 本文档随 SKILL.md v1.1 升级。新增规则 11-12 来自呼吸科肺真菌病项目的复盘教训。

## 规则详解与正误对比

### 规则1：每层分流加和=100%

**错误示例：**
```
HSCT 21,714 → Allo 15,056(69%) → ...
                Auto 6,658(31%) → ...
                其他 → ...   ← 多出一个分支，加和超过100%
```

**正确示例：**
```
HSCT 21,714 → Allo 15,056(69%)
              Auto 6,658(31%)
              69% + 31% = 100% ✓
```

**检查方法：** 画完每个分叉后，把所有子分支百分比相加。不等于100%就是错的。

---

### 规则2：每个分支走完直至●终止

**错误（截断）：**
```
非HSCT低危 135,000
  └── IFI <2% → IFI <2,700例   ← 到这里就断了！这些IFI患者后续呢？
```

**正确（完整）：**
```
非HSCT低危 135,000
  ├── 无IFI >98% → >132,300例 ●终止
  └── IFI <2% → <2,700例
      └── 进入治疗策略 → 经验/DD/目标 → 诊断分级 → 病原 → 药物 → 疗效评估
          ├── 有效 → 完成疗程 ●终止
          └── 失败 → 挽救 → 再评估
              ├── 有效 → ●终止
              └── 失败 → 死亡/姑息 ●终止
```

**检查方法：** 找到图中所有叶子节点。每个叶子节点要么标"●终止"，要么继续向下连接。如果叶子节点既没有●也没有向下箭头，就是截断。

---

### 规则3：病种拆分是节点属性，不是分支

**错误（层级归类错误）：**
```
Allo-HSCT 15,056
  ├── AML 5,838 (38%)       ← 病种变成了和预防平行的分支
  ├── ALL 3,311 (21%)
  ├── AA 2,000 (13%)
  ├── MDS 1,505 (10%)
  ├── 地贫 753 (5%)
  ├── 其他 1,649 (13%)
  └── 抗真菌预防 15,056     ← 预防和病种平级了！
```

**正确（病种是属性）：**
```
Allo-HSCT 15,056例
  [属性：AML38% ALL21% AA13% MDS10% 地贫5% 其他13%]
  └── 100%接受抗真菌预防 → 15,056例
      ├── 未突破 93.7% → 14,107例 ●终止
      └── IFD 6.3% → 949例 → 进入治疗...
```

**为什么这很重要：** 病种拆分告诉你"这15,056个患者是谁"（属性），但他们后续的真菌治疗flow是统一的——100%都接受预防。如果把病种做成分支，视觉上暗示AML患者走一条路、ALL患者走另一条路，而事实上他们在真菌预防这一步走的是同一条路。

---

### 规则4：以目标疾病的flow为主轴

**错误（以基础疾病为主轴）：**
```
AML患者 → 化疗 → HSCT → 维持 → 复发 → 再治疗...
                                    ↓
                              中间某个节点提一下IFI
```

**正确（以IFI为主轴）：**
```
血液科患者 → [按IFI风险分层] → 高危 → 预防 → IFI发生？
                                              ├── 否 ●终止
                                              └── 是 → 治疗策略 → ...
```

**核心原则：** 我们做的是IFI市场调研，不是血液病诊疗指南。所有的基础疾病信息（AML/ALL/NHL等）都是为了回答"这个IFI市场有多大"，不是为了回答"AML怎么治"。

---

### 规则5：药物出现位置受NMPA适应症约束

**必须在画流程图之前完成NMPA适应症查询。**

**错误：**
```
预防节点：伏立康唑、泊沙康唑、艾沙康唑、卡泊芬净...
← 艾沙康唑在中国没有预防适应症！不应出现在预防节点
```

**正确：**
```
预防节点：
  NMPA获批：伏立康唑(次级预防)、泊沙康唑(≥13岁)、氟康唑(粒缺预防)
  超说明书：卡泊芬净、米卡芬净、伊曲康唑、L-AmB
  ⚠ 艾沙康唑无预防适应症，不出现
```

**标注规则：**
- `NMPA` = 说明书获批适应症
- `超说明书` = 指南推荐但说明书无该适应症
- `⚠不出现` = 既无适应症也无指南推荐，或明确无活性

---

### 规则6：绝对数字+百分比双标注

**仅有百分比（不够用）：**
```
经验性治疗 82.3%  ← 82.3%是多少人？无法计算市场规模
```

**绝对数字+百分比（可直接计算）：**
```
经验性治疗 82.3% → ~781例/年  ← 可以乘以单价算出市场值
```

---

### 规则7：估算值必须标注依据

**错误（无依据猜测）：**
```
非HSCT高危预防覆盖率 ~50%
← 这个50%从哪来的？猜的？
```

**正确（标注依据）：**
```
非HSCT高危预防覆盖率 30-70%估
测算依据：无全国数据，30%为基层医院单中心经验下限(Liu 2021 n=128)，
70%为顶级移植中心上限(PUMCH 2022 AML队列)，取区间而非点估计
```

---

### 规则 8-10：证据来源集中标注 / Mermaid 语法 / 色彩编码

详见 SKILL.md 主文件对应规则。

---

### 规则 11:消除跨分支共用节点（v1.1 新增）

**错误（共用节点导致箭头交叉）:**
```
ENT_A --> T_PJP
ENT_B --> T_PJP   ← 3 条箭头汇聚到同一个 T_PJP,导致跨 swim-lane 回折
ENT_D --> T_PJP
T_PJP --> TX_PJP
```

**正确（每个入口独立一套节点）:**
```
subgraph A[入口A]
  ENT_A --> A_PJP --> A_TX_PJP --> A_END
end
subgraph B[入口B]
  ENT_B --> B_PJP --> B_TX_PJP --> B_END
end
subgraph D[入口D]
  ENT_D --> D_PJP --> D_TX_PJP --> D_END
end
```

**为什么宁可节点重复?**
- 视觉清晰度 > 节点数量最小化
- 每个入口的 PJP 治疗路径实际有差异(ICU PJP 三联 vs 非 ICU TMP-SMX 单药),本来就需要独立节点承载不同信息
- 便于 linkStyle 为每个入口分配专属颜色

**检查方法:** 数流程图中有多少条箭头跨越 2 个 rank(纵向层级)之上而不在同一条主路径上。超过 3 条就说明有共用节点问题。

---

### 规则 12:复杂树状图强制 ELK 布局（v1.1 新增）

Mermaid 的默认 `dagre` 引擎在复杂树状分支(4+ 入口 × 7+ 分型)下会出现大量交叉。必须切换 ELK:

**Mermaid frontmatter 写法:**
```yaml
---
config:
  layout: elk
  flowchart:
    nodeSpacing: 70
    rankSpacing: 90
    curve: basis
---
flowchart TD
…
```

**渲染命令:**
```bash
mmdc -i flowchart.mmd -o flowchart.png \
     -w 5000 --scale 2 \
     -b white -p puppeteer-config.json
```

**高清要求:**
- `-w 5000`:输出 PNG 宽度至少 5000px(默认 2400 偏低)
- `--scale 2`:渲染时再 2x 超采样,打印不糊
- 验证结果:PNG 短边 ≥ 3000px,文件 ≥ 800 KB
- HTML 嵌入用 `<img style="width:100%">`,让浏览器根据容器自适应缩放

**为什么 ELK 更好?**
- ELK(Eclipse Layout Kernel)是 Eclipse 项目组提供的层次图布局引擎,专门优化多层分支树状图
- 支持 subgraph 感知布局(同 subgraph 内节点聚拢,不同 subgraph 间留白)
- 边路由算法避免跨层级回折
- 2024+ 版 mermaid-js/mermaid-cli 原生支持

---

### 规则 13:YAML frontmatter 必须首行(v1.2 新增 · 硬约束)

**背景**:ICU 项目 v1.2 前复盘 — agent 把 `%% Skill Presented by...` 注释放在 `---` frontmatter 之前,导致 Mermaid 10.9+ 报错 `Parse error on line 1: ---config`,整个瀑布图未渲染。

**硬约束**:如果 .mmd 使用 `---` YAML frontmatter,**第 1 行必须是 `---`**。前面不得有任何内容(注释 `%%`、空行、BOM 等均不允许)。

**错误示范**:
```mermaid
%% Skill Presented by: YongQi, SimonSu, RuiYu, YingJi    ← 删掉
%% 文件:综合 ICU IFI 患者流瀑布图                         ← 删掉
                                                          ← 删掉空行
---
config:
  layout: elk
---
```

**正确示范**:
```mermaid
---
config:
  layout: elk
---
flowchart TD
%% Skill Presented by: YongQi, SimonSu, RuiYu, YingJi    ← 注释移到 flowchart TD 之后
%% 文件:综合 ICU IFI 患者流瀑布图
POOL["..."]
```

**验证方法**:`python flowchart-validator.py your.mmd` 会报"YAML frontmatter 前 N 行含非空内容"。

---

### 规则 14:validator 必须通过(v1.2 新增 · 硬约束)

**背景**:v1.2 前,flowchart-rules 规则在文档里,但子 agent 生成 .mmd 后**无机器验证**,直接嵌入 PDF,渲染错误或结构缺陷在终版 PDF 才暴露。

**硬约束**:任何 `.mmd` 文件在**渲染 PNG 之前**,必须通过 L0 skill 的 `references/flowchart-validator.py`(return code ≤ 1)。return code = 2 硬错误阻塞渲染流水线。

**7 项自动检查**:
1. Mermaid 渲染测试(mmdc)
2. YAML frontmatter 位置(规则 13)
3. 每个叶子节点是 `●` 终止(规则 2)
4. 复杂图 ≥ 3 subgraph(规则 4)
5. 无多源汇聚共用节点(规则 15)
6. 诊断层存在(患者流专项)
7. 治疗层存在(患者流专项)

---

### 规则 15:禁止多源汇聚共用节点(v1.2 新增)

**背景**:ICU LP 决策图 v1.2 前 — agent 写成 `CAND --> DIAG`, `ASP --> DIAG`, `PJP --> DIAG`, `MUC --> DIAG`(4 条入边汇聚到 DIAG),然后 `CAND --> TDM`, `ASP --> TDM` 再次汇聚。ELK 布局把 DIAG/TDM 放在图中间,**4 条入边从不同方向拉过来,产生严重跨分支交叉**。

**硬约束**:非明确的评估/路由/汇聚节点(关键词白名单:`EVAL_` · `ROUTER` · `SCREEN` · `END_` · `DIAG` 仅作为评估节点时 · `RETURN`),**入度不得 ≥ 3**。如果多个分支需要经过相同诊断/治疗节点,**必须拆成多份独立节点**(如 `DIAG_CAND` / `DIAG_ASP` / `DIAG_PJP`),即使节点文字完全相同。

**错误示范**:
```mermaid
HOSTS --> CAND & ASP & PJP & MUC & CRY    %% 星型广播 OK
CAND --> DIAG                              %% ❌ 多源汇聚(4 入度)
ASP --> DIAG
PJP --> DIAG
MUC --> DIAG
CAND --> TDM_NODE                          %% ❌ 再次多源汇聚
ASP --> TDM_NODE
```

**正确示范**:
```mermaid
%% 每个分支独立诊断节点,即使文字相同
CAND --> DIAG_CAND["诊断:BDG + mNGS"] --> TX_CAND --> END_CAND(["● 完成"])
ASP  --> DIAG_ASP ["诊断:GM + BALF + mNGS"] --> TX_ASP --> END_ASP(["● 完成"])
PJP  --> DIAG_PJP ["诊断:BDG + mNGS"] --> TX_PJP --> END_PJP(["● 完成"])

%% 或者在 subgraph 内保留汇聚,但每个 subgraph 是独立 swim-lane
subgraph 曲霉分支
  ASP --> DIAG_ASP --> TX_ASP --> END_ASP
end
subgraph 念珠菌分支
  CAND --> DIAG_CAND --> TX_CAND --> END_CAND
end
```

**Exception**:明确标注 `EVAL_`(疗效评估)/ `ROUTER`(分流路由)/ `SCREEN`(筛查)/ `END_`(终止)前缀的节点,允许多入度(这些是明确的评估/分流点,不会造成"共用困惑")。

---

## Mermaid语法速查

```mermaid
flowchart TD
  A["矩形节点<br/>可以换行"]        %% 普通流程节点
  B{"菱形决策节点"}                  %% 分叉判断
  C(["圆角节点"])                    %% 起止节点
  A -->|"标签文字"| B               %% 带标签的箭头
  B -->|"分支1 60%"| D["节点D"]
  B -->|"分支2 40%"| E["节点E"]
  style A fill:#e6f1fb,stroke:#378add  %% 蓝色=患者池
  style D fill:#e1f5ee,stroke:#1d9e75  %% 绿色=预防
```
