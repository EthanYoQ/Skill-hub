# 8 失败模式详解

## #1 lookup 返回 None(药品不在权威数据库)

**症状**: `lookup_drug("XYZ-2026")` → `None`

**可能原因**:
1. 真的是新药,fallback dict 还没更新
2. 仿制名(如"伊马替尼"的某个仿制品牌)
3. 拼写错(如把"奥希替尼"写成"奥西替尼")
4. 进口未上市(临床试验阶段)

**修复**:
- 调用方 **必须 raise UnverifiedDrugError**,不允许 LLM 凭记忆补
- 通知用户该药未验证,确认是否仍写入(标 `unverified: true`)
- 若确认是新药,补到 `_known_drugs_fallback.py` 并附 NMPA URL

## #2 同一通用名多个商品名(多厂家)

**症状**: 阿仑膦酸钠在中国有 5+ 厂家(默沙东、普利、华润等)

**修复**:
- `brand_names_zh` 必须列**全部**已知商品名,不要任选一个
- 报告里写时建议用通用名 + (商品名: A / B / C / 等)格式

## #3 通用名↔商品名错位(LLM 偷偷脑补)

**症状**: 报告写"洛拉替尼(商品名:赛可瑞)" — 但赛可瑞实际是克唑替尼商品名

**根因**: LLM 训练数据老化,凭记忆拼凑出错位

**修复**:
- 报告生成完毕跑 `cross_check_drug_mentions(html)`
- 任何 `name_mismatches` 非空 → severity=critical → raise
- 重生成时显式注入 drug_registry.json 让 LLM 必须从中取

## #4 NMPA 网站抓取失败(反爬 / 改版)

**症状**: HTTP 5xx / 验证码 / 空骨架

**修复**:
1. 降级到 `<cache_dir>/drug_registry.json` 上次缓存
2. 仍无 → 用 `_known_drugs_fallback` 兜底
3. 仍无 → raise(报告生成阻断)
4. 不要在 CI 自动重试网站,容易触发更严反爬

## #5 同一英文名对应多个中文音译

**症状**: "Imatinib" 早期翻译有"伊马替尼"和"伊马提尼"两版

**修复**:
- NMPA **当前**通用名是唯一权威(以最新版数据库为准)
- 旧译名作 alias 收录但不作为 canonical
- alias_to_generic_index 兼容查询

## #6 DrugBank 拒绝学术抓取

**症状**: 403 / Captcha

**修复**:
- 不阻塞主流程: ATC code / 英文名 / 靶点 字段标空
- NMPA 字段(通用名/批文号/适应症/上市日期)是必需字段,已在 fallback 兜底

## #7 LLM 在 prompt 里"脑补"通用名

**症状**: orchestration 调 LLM 写决策树,LLM 自己拼了个"塞瑞替尼商品名为 XYZ"

**修复**:
- 任何 grade_evidence / LP / 内容生成阶段都强制 `lookup_drug()`
- LLM 输出后跑 `cross_check_drug_mentions` 全文扫描
- 不接受 LLM 直出的药名对应

## #8 进口药批文号格式 vs 国产不同

**症状**: 进口药批文号是 `国药准字HJ20180071`,国产是 `国药准字H20200004`

**修复**:
- 不要在代码里拆解前缀分类
- 作为 opaque string 存储 + 渲染
- 如需区分国产/进口,看 `nmpa_approval_no` 第 5 字符是 J 还是无 J
