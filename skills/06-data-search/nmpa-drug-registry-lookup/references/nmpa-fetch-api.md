# NMPA 网站结构 + 抓取策略

## 入口

- **公开搜索**: <https://www.nmpa.gov.cn/datasearch/search-result.html>
- **数据库分类**:
  - 国产药品(`searchValue` + 国产 tab)
  - 进口药品(`searchValue` + 进口 tab)
  - 国家基本药物
  - 化学药品
  - 中药
  - 生物制品

## 抓取参数

| 参数 | 含义 | 示例 |
|-----|------|------|
| `searchValue` | 通用名 / 商品名 / 批文号关键词 | `阿来替尼` |
| `searchType` | 默认全文 | `0` |

## 返回结构(粗略)

实际返回是 JS 渲染的列表页,直接 GET 拿到的 HTML 通常为空骨架。
真实抓取需要:

1. 模拟 XHR 调用 NMPA 的 JSON API(若发现)
2. 或者用 Playwright/Selenium 等渲染引擎
3. **不要**短时间高频请求(会触发反爬验证码)

## 批文号编码规则(opaque,不要拆解)

| 前缀 | 含义 |
|-----|------|
| `H` | 国产化学药 |
| `J` | 进口药 |
| `Z` | 中药 |
| `S` | 生物制品 |

例: `国药准字HJ20180071` = 进口化学药,2018 年批,序号 71

## 推荐做法(本 skill 默认)

1. **不主动联网**: 用预录制 fixture + 手工核验 fallback dict
2. 真实抓取由调用方传 `force_online=True` 启用,且要做:
   - 单线程顺序请求(QPS ≤ 0.5)
   - 失败重试 ≤ 2 次
   - 失败 fallback 到 cache → fallback dict → 报错
3. 抓到的数据**必须**与 fallback dict 交叉核验,有冲突时优先信 fallback(因 fallback 是手工 NMPA-validated)

## 替代源

NMPA 抓取困难时优先用:
- **米内网** (menet.com.cn): 部分公开数据,有 NMPA 同步
- **insight 数据库** (insight.pharmcube.com): 学术免费层
- **DrugBank** (drugbank.com): 英文名 / ATC / 靶点
- **PubChem** (NIH): 化学结构 / 同义词

## 法律边界

NMPA 数据库为公开信息,允许个人查阅。
- **可以**: 学术/调研用途的低频查询
- **不允许**: 大规模爬取、商业转售、伪造来源
- **本 skill** 的兜底数据全部基于公开页面,每条都附 `sources` URL 可审计
