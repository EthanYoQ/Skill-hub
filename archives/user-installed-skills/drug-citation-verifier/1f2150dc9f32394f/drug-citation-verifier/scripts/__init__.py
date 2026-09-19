"""drug-citation-verifier 内部脚本包。

公开入口:``verifier.verify_drug_mentions_in_text``。

P0 守护:本包**不**维护任何药品字典 / 商品名映射 / 已知药品列表。
唯一允许的"内置规则"是中文/英文药名后缀(命名学,非药品库)。
"""
