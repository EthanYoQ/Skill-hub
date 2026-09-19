# Failure Modes

> 本 skill 在哪些情况会触发 critical violation,如何修复。

## 1. 报告写药名但无 citation

### 现象

```text
一线推荐 XX 替尼治疗 ALK 阳性 NSCLC。
```

(整段没有 `[...]` 锚点)

### 触发原因

`find_nearest_citation` 跨段无法匹配 → 返回 None。

### 输出

```json
{
  "text": "<药名>",
  "citation": null,
  "verified": false,
  "missing_in_source": ["<药名>", ...],
  "reason": "no citation near drug mention",
  "severity": "critical"
}
```

### 修复

LLM 在该药提及附近添加 citation 锚点,如:
`一线推荐 XX 替尼。[guideline:CSCO-2024-NSCLC:§5.5.2]`

---

## 2. citation 解析不到源

### 现象

```text
一线推荐 XX 替尼。[guideline:CSCO-9999-XX:§99.99]
```

(锚点指向不存在的指南 / 不存在的章节)

### 触发原因

A11 `resolve_citation` 返回 None → A11 `verify_claim_against_source` 返回
`verified=False, reason="anchor unresolvable: ..."`。

### 输出

```json
{
  "citation": "[guideline:CSCO-9999-XX:§99.99]",
  "verified": false,
  "reason": "anchor unresolvable: ...",
  "severity": "critical"
}
```

### 修复

1. 确认源材料是否真的下载到了 `.cache/<slug>/sources/`
2. 确认锚点 source_id / locator 是否拼写错误
3. 若是 Step 0 抓取阶段漏抓,补抓后重试
4. **不允许**:为了让锚点"看起来能解析"而硬编码 fallback 答案

---

## 3. 源里只有通用名没商品名,但报告写了商品名

### 现象

报告:`一线推荐 XX 替尼(商品名:某某品牌)。[guideline:CSCO-2024-NSCLC:§5.5.2]`

源里只写了:`I 级推荐 XX 替尼`(没提"某某品牌")

### 触发原因

A11 严格 substring 核对,"某某品牌"不在源里 → missing_keywords 非空。

### 输出

```json
{
  "text": "<药名>",
  "brand_in_context": "商品名:某某品牌",
  "verified": false,
  "missing_in_source": ["某某品牌"],
  "reason": "source missing: 某某品牌",
  "severity": "critical"
}
```

### 修复

二选一:
- **选 A(去掉商品名)**:报告改为"一线推荐 XX 替尼。",不带商品名
- **选 B(找到正确出处)**:换一个真的提到"某某品牌"的源(如 NMPA 批准文号),
  然后用相应锚点(如 `[nmpa-page:批准文号:title]`)

不允许:为了通过审计而修改源材料 / 加 fallback 字典。

---

## 4. LLM 编造的药名(符合命名学但源里没)

### 现象

报告:`新批的某某替尼用于 EGFR 阳性 NSCLC。[guideline:CSCO-2024-NSCLC:§5.5.2]`

但 CSCO §5.5.2 里根本没"某某替尼"(LLM 编造,因为符合 `*替尼` 后缀被抽出)。

### 触发原因

A11 严格 substring 核对,"某某替尼"不在源里 → missing_keywords=["某某替尼"]。

### 输出

```json
{
  "text": "某某替尼",
  "verified": false,
  "missing_in_source": ["某某替尼"],
  "reason": "source missing: 某某替尼",
  "severity": "critical"
}
```

### 修复

1. 确认这个药真的存在(去 NMPA 官网查批准文号)
2. 若存在 → 抓取相应源材料,用对应锚点
3. 若不存在 → 删除该段(LLM 编造)
4. **不允许**:加到"已知药品列表"里绕过审计

---

## 5. 命名学漏抽(False Negative)

### 现象

报告写了"卡铂 + 紫杉醇"等不在后缀表中的药名,本 skill 抽不出来。

### 影响

不会触发 critical violation(因为压根没识别为药提及)。

### 缓解

- 上层 A6' `content-verification-layer` 会做"语义级"全段校验
- 如果发现长期遗漏的命名规律,**仅扩 `DRUG_NAME_SUFFIXES_CN` 后缀表**,
  **绝不**加入具体药名到代码

### 关键约束

扩后缀时,新加的项目必须是"中文医药构词法的通用后缀",
不允许像 "卡铂"/"紫杉醇" 这类单个具体药名。

如需进一步捕获非后缀类传统药名,正确做法是:
- 上层用 LLM 做语义抽取(联网召回时)
- 或扩展 `_drug_extract.py` 接受额外的"已知化疗类后缀模式"
  (但这些后缀必须能匹配 ≥ 2 个独立的药,不能是单药)
