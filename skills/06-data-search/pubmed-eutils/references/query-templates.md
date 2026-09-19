# PubMed 检索式构造模板（医学专属 · ready-to-use）

主 SKILL.md 的扩展参考。覆盖 7 个高频医学检索场景。

## 1. 系统综述 / Meta 分析（金字塔顶端）
```
("disease X"[MeSH] OR "disease X"[tiab])
  AND (systematic[sb] OR meta-analysis[pt] OR "systematic review"[pt])
  AND ("2020/01/01"[PDAT] : "3000"[PDAT])
```

## 2. RCT（高质量原始证据）
```
("drug Y"[MeSH] OR "drug Y"[tiab])
  AND (randomized controlled trial[pt] OR "randomized"[tiab])
  AND humans[Filter] AND english[lang]
```

## 3. 治疗效果 - Clinical Queries narrow
```python
pubmed_clinical_queries("CAR-T multiple myeloma", category="therapy", scope="narrow")
# 自动加: ((randomized controlled trial[pt]) OR (controlled clinical trial[pt])
#          OR (randomized[tiab] AND placebo[tiab]) ...)
```

## 4. 流行病学 / 发病率
```
("disease X"[MeSH]) AND (incidence[MeSH] OR prevalence[MeSH] OR epidemiology[sh])
  AND ("2018"[PDAT] : "3000"[PDAT])
```

## 5. 真实世界研究 (RWE)
```
("drug Y") AND (real-world[tiab] OR registry[tiab] OR observational[tiab]
               OR "cohort studies"[MeSH])
```

## 6. 中国人群证据
```
("disease X") AND (China[MeSH] OR Chinese[tiab] OR China[ad])
```

## 7. 指南
```
("disease X") AND (practice guideline[pt] OR guideline[pt] OR consensus[tiab])
  AND ("2020"[PDAT] : "3000"[PDAT])
```

## 跨疾病移植清单

把本 skill 用到新疾病只需替换 3 处：
1. **疾病主词**：MeSH preferred term + 同义词 + 缩写（如 `"Multiple Myeloma"[MeSH]` + `"MM"[tiab]` + `"plasma cell myeloma"[tiab]`）
2. **干预词**：药物 / 器械 / 术式 MeSH + 通用名 + 商品名
3. **时间窗**：通常 5-10 年；指南类放宽到 10 年；机制类不限

**禁止移植的部分**：Clinical Queries 过滤器是 NCBI 官方语料训练的,所有疾病通用,**不要改**。
