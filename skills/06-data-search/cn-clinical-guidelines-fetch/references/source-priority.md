# 数据源优先级

按降序优先级，市场调研流水线 Step 0 调用本 skill 时按此顺序聚合。

## 1. CSCO 指南（中国临床肿瘤学会）—— 最高优先级

- **域名**：csco.org.cn / www.csco.org.cn
- **覆盖**：肿瘤精准医疗（NSCLC、乳腺癌、淋巴瘤、结直肠癌、肝癌等几十个瘤种）
- **更新频率**：每年 4-5 月发布新版（2024 版、2025 版）
- **格式**：公开 PDF（首选）+ HTML 摘要 + 部分章节官网公开
- **证据等级**：I / II / III 级（I 级 = 一致推荐 / 高级别证据）
- **抓取方式**：
  1. 优先 WebFetch HTML 摘要页
  2. 退回 PDF 全文 + pypdf 解析
  3. 反爬时用本仓 hardcoded fixture（基于年度官方公开发布版）

**为什么优先**：
- CSCO 是中国肿瘤诊疗的事实标准，国家医保目录与 CSCO 一致
- 含国产药（伊鲁阿克 / 依奉阿克 / 恩沙替尼），NCCN 不含
- 治疗等级 I/II/III 划分清晰，结构化抓取友好

## 2. NCCN 中文版

- **域名**：nccn.org（中文版部分公开）
- **覆盖**：全球肿瘤指南本地化
- **抓取**：HTML（P2 task 实现）

## 3. NMPA（国家药监局）

- **域名**：nmpa.gov.cn
- **覆盖**：药品注册批件、适应症、批准日期
- **抓取**：REST 风格数据库查询（A5 nmpa-drug-registry-lookup 实现）
- **本 skill**：minimal hardcoded（ALK+ NSCLC 八种 ALK-TKI 的 NMPA 上市状态）

## 4. CDE（药品审评中心）

- **域名**：cde.org.cn
- **覆盖**：临床试验技术审评、新药审评结论
- **抓取**：HTML（P2 stub）

## 5. NHC（国家卫健委）诊疗规范

- **域名**：nhc.gov.cn
- **覆盖**：恶性肿瘤诊疗规范（部分瘤种）、罕见病诊疗指南
- **抓取**：HTML（P2 stub）

## 全球市场 fallback（market_geo != CN）

切换到：
- NCCN（英文）
- ESMO Guidelines
- WHO Essential Medicines List
- ASCO Guidelines

P2 task：在 fetcher.py 加 `market_geo` 参数路由到不同 fetcher set。
