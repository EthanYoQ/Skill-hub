# DrugBank 学术免费用法

## 概述

DrugBank 是全球最大开源药物数据库,提供:
- INN 通用名(英文)
- ATC 分类码
- 商品名(全球各市场)
- 化学结构 / 分子式
- 靶点 / 机制
- 适应症 / 禁忌症
- 药物相互作用

## 免费层限制

| 用途 | 是否允许 |
|-----|---------|
| 个人学术查询(单次) | ✅ |
| 网页直接访问搜索结果 | ✅ |
| 课程/论文引用(标 source) | ✅ |
| 商业产品集成 | ❌ 需付费 license |
| 大规模爬取 | ❌ 反爬 + ToS 禁止 |
| 转售数据 | ❌ |

## 抓取入口

- 主搜索: <https://go.drugbank.com/drugs/search?query=lorlatinib>
- 详情页: `https://go.drugbank.com/drugs/DB12130`(DBID)

## HTML 解析重点字段

| 字段 | 选择器(粗略) |
|-----|---------------|
| Generic name | `dt:contains("Generic Name") + dd` |
| Brand names | `dt:contains("Brand Names") + dd` |
| ATC code | `dt:contains("ATC code") + dd` |
| Drug class | `dt:contains("Categories") + dd a` |
| Targets | `#drug-targets table tbody tr` |

## 本 skill 集成方式

1. 默认: **不联网**,所有 DrugBank 字段已编入 fallback dict
2. 调用方显式 `force_online=True` 才尝试抓取
3. 抓取失败不阻塞主流程: ATC/英文/靶点字段标空,但 NMPA 字段正常
4. 抓到的 DrugBank 字段必须与 fallback dict 一致;不一致时优先信 fallback

## 替代

如 DrugBank 不可达:
- **PubChem** (NIH 公开): 通用名 + 同义词 + 分子式
- **ChEMBL** (EMBL-EBI): 完整化学/生物活性数据
- **Wikidata**: 部分药物有 Q 号,可拿到多语言名
