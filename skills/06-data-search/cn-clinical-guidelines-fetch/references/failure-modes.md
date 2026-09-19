# 失败模式

| 症状 | 原因 | 处置 |
|------|------|------|
| CSCO 远程不可达 (网络 / 5xx) | 公网偶发 | fall back 到 `cache_dir/csco_<slug>.json` |
| 反爬 (403 / 验证码) | CSCO 改版加了反爬 | fall back 到 hardcoded fixture（仅 ALK+ NSCLC 等 ground truth 病种） |
| PDF 解析失败 | pypdf 不识别该版本 PDF 嵌入字体 | 退回 HTML，再退回章节标题拼接 |
| `cache_dir` 提供但 miss + 远程 fail | 用户首次跑 + 离线 | 抛 RuntimeError，`sources_succeeded` 不含该源 |
| `fetch_chinese_guidelines` 全部源都失败 | 全网络故障 | manifest 标 `guideline_fetch_failed: True`，报告 §0 红色警告 + 流水线不阻塞但产物 = draft |
| cross-check 返回 critical | LLM 生成的治疗方案完全没命中 I 级药 | orchestration 重生成 1 次，仍违规 → 把 §"治疗方案" 改为 placeholder + warning |
| cross-check 返回 warning | LLM 生成部分命中 | 报告 §0 黄色警告 + 不阻塞 |
| LLM "脑补" 通用名 | 训练数据过时 | A5 nmpa-drug-registry-lookup 强制 lookup_drug 验证 |
| disease 不在 fixture 覆盖 | 还没扩展该病种 | TODO 加 fixture，或抛 `RuntimeError` 让上层降级 |

## 调用方降级矩阵

| `sources_succeeded` 状态 | 报告处置 |
|-------------------------|---------|
| 含 `csco` | 正常生成，治疗章节以 CSCO 为锚 |
| 不含 `csco`，含 `nccn_zh` | 正常生成，§0 标 "未抓到 CSCO，使用 NCCN 中文版" |
| 仅 `nmpa_drug_status` | §"治疗方案" 标 placeholder + 红色警告 |
| 全空 | 流水线产物标 draft，强制要求人工补指南 |

## fixture vs 远程的语义区别

`cache_dir is None`（开发 / 测试默认）：
- 远程失败 → fixture 兜底（保证 8 药全在）
- 适合：测试、开发环境、无网络环境

`cache_dir` 提供（生产模式）：
- 远程失败 + cache miss → 抛 RuntimeError
- 适合：生产流水线，要求"明确知道源是否成功"
- 调用方应在第一次成功抓取后 _cache.save() 把数据写到 cache_dir
