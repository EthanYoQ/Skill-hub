# 按能力域索引

共 59 个技能，按 7 个能力域 + projects（项目私有）分组。

## 目录

- [01 Agent 工程](#01-agent-工程)（4）
- [02 编程语言](#02-编程语言)（1）
- [03 框架与技术栈](#03-框架与技术栈)（1）
- [06 数据与检索](#06-数据与检索)（15）
- [07 媒体与内容制作](#07-媒体与内容制作)（10）
- [08 写作与营销](#08-写作与营销)（2）
- [10 行业与业务](#10-行业与业务)（17）
- [Projects 项目私有](#projects-项目私有)（9）

## 01 Agent 工程（4）

| 技能名 | 路径 | 中文简介 |
|---|---|---|
| **deep-research** | [skills/01-agent-engineering/deep-research/](../skills/01-agent-engineering/deep-research/) | 多源深度研究，使用 firecrawl/exa 搜索并综合发现。 |
| **find-skills** | [skills/01-agent-engineering/find-skills/](../skills/01-agent-engineering/find-skills/) | 自动发现与推荐可用 Agent 技能，回答"有没有能做 X 的技能"。 |
| **santa-method** | [skills/01-agent-engineering/santa-method/](../skills/01-agent-engineering/santa-method/) | 多 Agent 对抗验证收敛循环，两个独立审查都通过后才出交付。 |
| **skill-creator** | [skills/01-agent-engineering/skill-creator/](../skills/01-agent-engineering/skill-creator/) | 创建、修改和优化 skill，并可跑 eval 衡量触发准确率与性能。 |

## 02 编程语言（1）

| 技能名 | 路径 | 中文简介 |
|---|---|---|
| **liquid-glass-design** | [skills/02-coding-languages/swift/liquid-glass-design/](../skills/02-coding-languages/swift/liquid-glass-design/) | iOS 26 Liquid Glass 设计系统：SwiftUI/UIKit/WidgetKit 的玻璃材质与交互。 |

## 03 框架与技术栈（1）

| 技能名 | 路径 | 中文简介 |
|---|---|---|
| **frontend-design** | [skills/03-frameworks/frontend-design/](../skills/03-frameworks/frontend-design/) | 创建具有高设计质量的生产级前端界面。 |

## 06 数据与检索（15）

| 技能名 | 路径 | 中文简介 |
|---|---|---|
| **bioc-fulltext-fetch** | [skills/06-data-search/bioc-fulltext-fetch/](../skills/06-data-search/bioc-fulltext-fetch/) | 从 PubMed/PMC 获取结构化全文并按章节切分为 RAG 友好的 chunk。 |
| **clinical-trials-v2** | [skills/06-data-search/clinical-trials-v2/](../skills/06-data-search/clinical-trials-v2/) | 实时查询 ClinicalTrials.gov 试验协议、结果和招募状态。 |
| **cn-clinical-guidelines-fetch** | [skills/06-data-search/cn-clinical-guidelines-fetch/](../skills/06-data-search/cn-clinical-guidelines-fetch/) | 抓取中国权威医学指南（CSCO/NCCN 中文版/NMPA/CDE/NHC）。 |
| **data-scraper-agent** | [skills/06-data-search/data-scraper-agent/](../skills/06-data-search/data-scraper-agent/) | 构建全自动 AI 数据采集 Agent：按计划抓取公开源并用 LLM 富化入库。 |
| **europepmc-search** | [skills/06-data-search/europepmc-search/](../skills/06-data-search/europepmc-search/) | 多源文献聚合检索：PubMed + PMC + 预印本 + NCBI Bookshelf + 专利。 |
| **evidence-appendix-sync** | [skills/06-data-search/evidence-appendix-sync/](../skills/06-data-search/evidence-appendix-sync/) | 最终确定市场研究报告附录 C（参考文献清单）。 |
| **market-research-reports** | [skills/06-data-search/market-research-reports/](../skills/06-data-search/market-research-reports/) | 生成 50+ 页专业市场研究报告，McKinsey/BCG/Gartner 质量。 |
| **market-sizing-mece-foundation** | [skills/06-data-search/market-sizing-mece-foundation/](../skills/06-data-search/market-sizing-mece-foundation/) | 所有医学市场规模任务的 MECE 基础。 |
| **medical-evidence-grading** | [skills/06-data-search/medical-evidence-grading/](../skills/06-data-search/medical-evidence-grading/) | 医学证据分级：按证据金字塔自动分级 A/B/C/D。 |
| **medical-research** | [skills/06-data-search/medical-research/](../skills/06-data-search/medical-research/) | 从 PubMed 获取论文并生成通俗易懂的研究摘要，覆盖医学/临床/科研主题。 |
| **nmpa-drug-registry-lookup** | [skills/06-data-search/nmpa-drug-registry-lookup/](../skills/06-data-search/nmpa-drug-registry-lookup/) | 中国药品权威数据库：NMPA + CDE + DrugBank + PubChem 融合查询。 |
| **pubmed-eutils** | [skills/06-data-search/pubmed-eutils/](../skills/06-data-search/pubmed-eutils/) | 通过 NCBI E-utilities 搜索 PubMed 并获取结构化生物医学文献。 |
| **pubmed-search** | [skills/06-data-search/pubmed-search/](../skills/06-data-search/pubmed-search/) | 通过 Valyu 语义搜索以自然语言检索 PubMed 生物医学文献，支持全文。 |
| **pubtator-entity-search** | [skills/06-data-search/pubtator-entity-search/](../skills/06-data-search/pubtator-entity-search/) | NLM PubTator3 实体级关系挖掘：疾病-药物-基因-化学品关联。 |
| **report-bundle-builder** | [skills/06-data-search/report-bundle-builder/](../skills/06-data-search/report-bundle-builder/) | 将多页 HTML 报告合并为单一独立 HTML/PDF/XLSX 交付物。 |

## 07 媒体与内容制作（10）

| 技能名 | 路径 | 中文简介 |
|---|---|---|
| **docx** | [skills/07-media-content/docx/](../skills/07-media-content/docx/) | 全面处理 .docx：创建、编辑、修订跟踪、评论、格式保留与文本提取。 |
| **editorial-presentation-html** | [skills/07-media-content/editorial-presentation-html/](../skills/07-media-content/editorial-presentation-html/) | Anthropic 暖色编辑设计语言，用于演示/case sharing/战略汇报。 |
| **imagegen** | [skills/07-media-content/imagegen/](../skills/07-media-content/imagegen/) | 生成或编辑光栅图像（照片、插画、纹理、UI 模型等）。 |
| **jianying-editor** | [skills/07-media-content/jianying-editor/](../skills/07-media-content/jianying-editor/) | 剪映 AI 自动剪辑高级封装 API（JyWrapper）：录屏、素材、字幕、Web 动效。 |
| **pdf** | [skills/07-media-content/pdf/](../skills/07-media-content/pdf/) | "Use when tasks involve reading, creating, or reviewing PDF files where rendering and layout matter; prefer visual checks by rendering pages (Poppler) and use Python tools such as `reportlab`, `pdfplumber`, and `pypdf` for generation and extraction." |
| **ppt-nano** | [skills/07-media-content/ppt-nano/](../skills/07-media-content/ppt-nano/) | 白板板书风格 PPT 生成，适合教学、汇报、头脑风暴。 |
| **pptx** | [skills/07-media-content/pptx/](../skills/07-media-content/pptx/) | 演示文稿 .pptx 的创建、编辑、布局、评论与演讲者备注。 |
| **remotion-video-creation** | [skills/07-media-content/remotion-video-creation/](../skills/07-media-content/remotion-video-creation/) | Remotion 在 React 中做视频创作的 29 条领域规则（3D、动画、字幕、过渡）。 |
| **wechat-article** | [skills/07-media-content/wechat-article/](../skills/07-media-content/wechat-article/) | 傅盛风格的公众号文章创作：对话式、故事驱动、有观点。 |
| **xlsx** | [skills/07-media-content/xlsx/](../skills/07-media-content/xlsx/) | 电子表格 .xlsx/.csv 等创建、编辑、公式、格式、数据分析与可视化。 |

## 08 写作与营销（2）

| 技能名 | 路径 | 中文简介 |
|---|---|---|
| **decision-tree-with-lp-embedding** | [skills/08-writing-marketing/decision-tree-with-lp-embedding/](../skills/08-writing-marketing/decision-tree-with-lp-embedding/) | 生成包含 LP 嵌入的 Mermaid 临床决策树。 |
| **yq-article-style-imitation** | [skills/08-writing-marketing/yq-article-style-imitation/](../skills/08-writing-marketing/yq-article-style-imitation/) | 任意作家文章风格仿写：验证作者原文、拆解表达 DNA、生成并修复公众号/小红书稿。 |

## 10 行业与业务（17）

| 技能名 | 路径 | 中文简介 |
|---|---|---|
| **citation-anchor-resolver** | [skills/10-business-industry/citation-anchor-resolver/](../skills/10-business-industry/citation-anchor-resolver/) | Cite-or-Block 架构基石：解析报告中引用锚点。 |
| **cite-bound-content-generator** | [skills/10-business-industry/cite-bound-content-generator/](../skills/10-business-industry/cite-bound-content-generator/) | 生成带强制引用锚点的报告 HTML。 |
| **content-verification-layer** | [skills/10-business-industry/content-verification-layer/](../skills/10-business-industry/content-verification-layer/) | 审核 compose 输出，确保每个引用锚点可逆解析到源文件。 |
| **contract-elicitor** | [skills/10-business-industry/contract-elicitor/](../skills/10-business-industry/contract-elicitor/) | 疾病市场规模调研的合同引导阶段，输出启动问题。 |
| **contract-review** | [skills/10-business-industry/contract-review/](../skills/10-business-industry/contract-review/) | 合同审核：三层审查（基础/业务/法律）、结构化注释、摘要与 Mermaid 流程图。 |
| **creating-financial-models** | [skills/10-business-industry/creating-financial-models/](../skills/10-business-industry/creating-financial-models/) | 高级财务建模套件，含 DCF 估值、敏感性分析、蒙特卡洛模拟。 |
| **design-system-injector** | [skills/10-business-industry/design-system-injector/](../skills/10-business-industry/design-system-injector/) | 向报告 HTML 注入咨询公司配色（navy/gold/blue）+ 基础 CSS。 |
| **disease-market-sizing-html-template** | [skills/10-business-industry/disease-market-sizing-html-template/](../skills/10-business-industry/disease-market-sizing-html-template/) | 多页 HTML 市场研究报告模板，含主页和 N 个子页。 |
| **disease-market-sizing-orchestration** | [skills/10-business-industry/disease-market-sizing-orchestration/](../skills/10-business-industry/disease-market-sizing-orchestration/) | 跨疾病市场规模入口 skill，自动运行 5 阶段管线。 |
| **disease-stratifier** | [skills/10-business-industry/disease-stratifier/](../skills/10-business-industry/disease-stratifier/) | 发现疾病特异性分层维度，输出 staging.json。 |
| **drug-citation-verifier** | [skills/10-business-industry/drug-citation-verifier/](../skills/10-business-industry/drug-citation-verifier/) | 药品名交叉验证：检查药品提及与引用源的一致性。 |
| **healthcare-cdss-patterns** | [skills/10-business-industry/healthcare-cdss-patterns/](../skills/10-business-industry/healthcare-cdss-patterns/) | 临床决策支持系统开发：药物互作、剂量校验、临床评分、告警分级与 EMR 集成。 |
| **healthcare-emr-patterns** | [skills/10-business-industry/healthcare-emr-patterns/](../skills/10-business-industry/healthcare-emr-patterns/) | 医疗 EMR/EHR 开发模式：临床安全、就诊流程、处方生成、CDSS 集成、无障碍 UI。 |
| **healthcare-eval-harness** | [skills/10-business-industry/healthcare-eval-harness/](../skills/10-business-industry/healthcare-eval-harness/) | 医疗发布的病人安全评测 harness：CDSS、PHI、临床流程与集成合规，失败阻断上线。 |
| **healthcare-phi-compliance** | [skills/10-business-industry/healthcare-phi-compliance/](../skills/10-business-industry/healthcare-phi-compliance/) | 医疗应用 PHI/PII 合规：数据分级、访问控制、审计、加密、常见泄漏路径。 |
| **ifi-market-sizing-skill** | [skills/10-business-industry/ifi-market-sizing-skill/](../skills/10-business-industry/ifi-market-sizing-skill/) | 用于医学/制药市场规模的临床路径重建与患者流瀑布图。 |
| **session-resume** | [skills/10-business-industry/session-resume/](../skills/10-business-industry/session-resume/) | disease-market-sizing 管线中断后恢复，无需从头开始。 |

## Projects 项目私有（9）

### ai-seed-project（2）

| 技能名 | 路径 | 中文简介 |
|---|---|---|
| **aliyun-openapi-mcp-ops** | [projects/ai-seed-project/aliyun-openapi-mcp-ops/](../projects/ai-seed-project/aliyun-openapi-mcp-ops/) | 通过自建 OpenAPI MCP 运维阿里云，聚焦 SWAS 部署：OAuth、选择器更新、诊断、预发验证。 |
| **feishu-automation** | [projects/ai-seed-project/feishu-automation/](../projects/ai-seed-project/feishu-automation/) | 飞书自动化能力，优先用官方 OpenAPI MCP/CLI，不把后台配置动作误判为 MCP 能力。 |

### ai-seed-project-phase-one-feishu（2）

| 技能名 | 路径 | 中文简介 |
|---|---|---|
| **aliyun-swas-manage** | [projects/ai-seed-project-phase-one-feishu/aliyun-swas-manage/](../projects/ai-seed-project-phase-one-feishu/aliyun-swas-manage/) | 端到端管理阿里云 SWAS：实例、命令、磁盘快照、防火墙、监控与轻量数据库。 |
| **feishu-card-ws** | [projects/ai-seed-project-phase-one-feishu/feishu-card-ws/](../projects/ai-seed-project-phase-one-feishu/feishu-card-ws/) | 飞书交互式卡片在 WebSocket 长连接模式下的配置指南与回调处理。 |

### alk-plus-tracker（1）

| 技能名 | 路径 | 中文简介 |
|---|---|---|
| **hui-rui-lan** | [projects/alk-plus-tracker/hui-rui-lan/](../projects/alk-plus-tracker/hui-rui-lan/) | 重建或扩展 ALK+ Tracker UI 时保留原始品牌蓝视觉体系、区块顺序、玻璃卡片布局。 |

### codex-invoice（4）

| 技能名 | 路径 | 中文简介 |
|---|---|---|
| **163-email-ground-truth** | [projects/codex-invoice/163-email-ground-truth/](../projects/codex-invoice/163-email-ground-truth/) | 163/网易邮箱真值集构建、审计与跑批，含 IMAP ID 命令等特殊处理。 |
| **controlled-lockcheck-autofix** | [projects/codex-invoice/controlled-lockcheck-autofix/](../projects/codex-invoice/controlled-lockcheck-autofix/) | QQ 受控前端 lockcheck 自动化：失败分类、受限自动修复、打包门的证据留存。 |
| **email-batch-test** | [projects/codex-invoice/email-batch-test/](../projects/codex-invoice/email-batch-test/) | 跑批测试标准与双邮箱回归门禁：P0/P1/P2 标准与保护区改动的双邮箱验证。 |
| **qq-email-ground-truth** | [projects/codex-invoice/qq-email-ground-truth/](../projects/codex-invoice/qq-email-ground-truth/) | 构建/重建/审计/比对 QQ 邮箱发票真值集，验证跑批输出。 |

