# Query Matrix

Use these query classes and rotate them to avoid overfitting to one wording. Search broad single company, alias, and pharma-specific role terms first, then run paired terms as precision probes. Do not rely only on bundled terms such as `诺华 MSL`, because that narrows recall and can over-represent recruiting/role-introduction posts.

## Pharma Context Gate

Do not run these cross-industry terms as standalone searches: `市场部`, `报销`, `背调`, `外企`, `裁员`, `离职`, `合规`, `薪资`, `KPI`.

Use them only when paired with at least one pharma context anchor:

- Company or alias anchor: `辉瑞`, `P司`, `诺华`, `N司`, `诺和诺德`, `Novo`, `礼来`, `LL司`, `赛诺菲`, `SNY`, `罗氏`, `Roche`, `阿斯利康`, `AZ`, `默沙东`, `MSD`, `强生`, `J&J`, `拜耳`, `GSK`, `葛兰素史克`, `BMS`, `安进`, `武田`, `勃林格`, `BI`, `默克`, `默克雪兰诺`, `外资药企`.
- Pharma role or industry anchor: `药企`, `外资药企`, `医药代表`, `药代`, `MSL`, `MA`, `医学部`, `CRA`, `临床`, `RWE`, `准入`, `市场准入`, `医学事务`, `科会`, `医院`, `医生`, `药品`, `产品线`.

A result from a generic pain query can enter the dataset only if the title, description, extracted text, or comments contain at least one pharma context anchor.

## Broad Recall Seeds

- 辉瑞
- 诺华
- 诺和诺德
- 礼来
- 阿斯利康
- 罗氏
- 赛诺菲
- 默沙东
- 强生
- GSK
- P司
- N司
- NN司
- LL司
- AZ
- R司
- S司
- 药代
- 医药代表
- MSL
- MA
- 医学部
- 药企
- 外资药企

## Generic Pharma Work

- 外资药企
- 药企打工人
- 外企医药代表
- 医药代表 外企
- 药代 外企
- 药企 裁员
- 药企 离职
- 药企 待遇
- 药企 奖金
- 药企 面试
- 药企 内推
- 药企 背调
- 外资药企 背调
- 药企 PIP
- 药企 薪资
- 外资药企 薪资
- 医药代表 KPI
- 医药代表 合规
- 药企 合规
- 药企 会议 新规
- 药企 报销
- 药企 垫付

## Medical Affairs / AI / Clinical

- 医学部 AI 药企
- 药企 AI
- 药代 AI
- MSL 药企
- MA MSL 药企
- 医学部 药企
- CRA 药企 AI
- RWE 药企
- 药企 数据 AI
- 药企 临床 数据
- 药企 市场部 mkt
- 外资药企 市场部
- 药企 市场部
- 外企 mkt 药企

## Company Names And Aliases

- 诺华 药企
- N司 药企
- 诺和诺德 药企
- NN司 药企
- 辉瑞 P司
- P司 药企
- 礼来 药企
- LL司 药企
- L司 药企
- 阿斯利康 AZ 药企
- AZ 药企
- 罗氏 R司
- R司 药企
- 赛诺菲 S司
- S司 药企
- 默沙东 药企
- M司 药企
- 强生 J司 药企
- GSK 药企
- 武田 T司 药企
- 拜耳 药企
- B司 药企
- 安进 药企
- 艾伯维 药企
- 百时美施贵宝 药企
- BMS 药企
- 吉利德 药企

## Alias + Pain

- P司 裁员
- P司 背调
- P司 薪资
- N司 裁员
- N司 背调
- N司 薪资
- NN司 裁员
- LL司 裁员
- LL司 薪资
- AZ 合规
- AZ 薪资
- AZ 会议
- R司 大瓜
- R司 裁员
- S司 裁员
- 外资药企 裁员
- 外资药企 合规
