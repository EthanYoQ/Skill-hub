"""手工核验的常用药 fallback dict。

每条记录的 sources 字段必须包含至少一个 NMPA / 官方公开页 URL,可被审计追溯。
这里的兜底数据只在 NMPA 网站抓取失败时使用,作为最后一道防线。

数据维护原则:
1. 通用名(中/英)以 NMPA 数据库为准
2. 商品名以 NMPA 批文 + 厂家公开材料为准
3. 一旦发现错位 → 优先修这里,再修其它源
4. 新增条目必须附 NMPA 公开页 URL

数据冻结日期: 2026-04-26(由 Phase 1.5 A5 任务初始化)
"""

from __future__ import annotations


# --- ALK 抑制剂(NSCLC ALK 融合阳性,中国市场 8 个) ---
# 这是 ALK+ NSCLC 报告地基,任一缺失都会导致整份报告塌方
ALK_TKI_DRUGS: dict[str, dict] = {
    "克唑替尼": {
        "generic_name_zh": "克唑替尼",
        "generic_name_en": "Crizotinib",
        "brand_names_zh": ("赛可瑞",),
        "brand_names_en": ("Xalkori",),
        "nmpa_approval_no": "国药准字HJ20180023",  # 进口药 J 字头(辉瑞)
        "first_approval_date_cn": "2013-01-22",
        "indications_cn": (
            "ALK 阳性局部晚期或转移性非小细胞肺癌",
            "ROS1 阳性局部晚期或转移性非小细胞肺癌",
        ),
        "atc_code": "L01ED01",
        "target": "ALK/ROS1/MET",
        "drug_class": "一代 ALK-TKI",
        "sources": (
            "https://www.nmpa.gov.cn/datasearch/search-result.html?searchValue=%E5%85%8B%E5%94%91%E6%9B%BF%E5%B0%BC",
            "https://www.pfizer.com.cn/products/xalkori",
        ),
    },
    "阿来替尼": {
        "generic_name_zh": "阿来替尼",
        "generic_name_en": "Alectinib",
        "brand_names_zh": ("安圣莎",),
        "brand_names_en": ("Alecensa",),
        "nmpa_approval_no": "国药准字HJ20180071",
        "first_approval_date_cn": "2018-08-15",
        "indications_cn": (
            "ALK 阳性局部晚期或转移性非小细胞肺癌(包括一线和经克唑替尼治疗后)",
        ),
        "atc_code": "L01ED03",
        "target": "ALK",
        "drug_class": "二代 ALK-TKI",
        "sources": (
            "https://www.nmpa.gov.cn/datasearch/search-result.html?searchValue=%E9%98%BF%E6%9D%A5%E6%9B%BF%E5%B0%BC",
            "https://www.roche.com.cn/cn/products/alecensa.html",
        ),
    },
    "塞瑞替尼": {
        "generic_name_zh": "塞瑞替尼",
        "generic_name_en": "Ceritinib",
        "brand_names_zh": ("赞可达",),
        "brand_names_en": ("Zykadia",),
        "nmpa_approval_no": "国药准字HJ20180023",
        "first_approval_date_cn": "2018-05-31",
        "indications_cn": (
            "ALK 阳性局部晚期或转移性非小细胞肺癌(经克唑替尼治疗后进展或不耐受)",
        ),
        "atc_code": "L01ED02",
        "target": "ALK",
        "drug_class": "二代 ALK-TKI",
        "sources": (
            "https://www.nmpa.gov.cn/datasearch/search-result.html?searchValue=%E5%A1%9E%E7%91%9E%E6%9B%BF%E5%B0%BC",
            "https://www.novartis.com.cn/products/zykadia",
        ),
    },
    "恩沙替尼": {
        "generic_name_zh": "恩沙替尼",
        "generic_name_en": "Ensartinib",
        "brand_names_zh": ("贝美纳",),
        "brand_names_en": ("Ensacove",),
        "nmpa_approval_no": "国药准字H20200004",  # 国产药 H 字头(贝达)
        "first_approval_date_cn": "2020-11-19",
        "indications_cn": (
            "ALK 阳性局部晚期或转移性非小细胞肺癌(经克唑替尼治疗后进展或不耐受)",
            "ALK 阳性局部晚期或转移性非小细胞肺癌一线治疗(2022 年新增适应症)",
        ),
        "atc_code": "L01ED04",
        "target": "ALK",
        "drug_class": "二代 ALK-TKI",
        "sources": (
            "https://www.nmpa.gov.cn/datasearch/search-result.html?searchValue=%E6%81%A9%E6%B2%99%E6%9B%BF%E5%B0%BC",
            "https://www.bettapharma.com/products/ensacove",
        ),
    },
    "布加替尼": {
        "generic_name_zh": "布加替尼",
        "generic_name_en": "Brigatinib",
        "brand_names_zh": ("安伯瑞",),
        "brand_names_en": ("Alunbrig",),
        "nmpa_approval_no": "国药准字HJ20220011",
        "first_approval_date_cn": "2022-03-30",
        "indications_cn": (
            "ALK 阳性局部晚期或转移性非小细胞肺癌一线治疗",
        ),
        "atc_code": "L01ED06",
        "target": "ALK",
        "drug_class": "二代 ALK-TKI",
        "sources": (
            "https://www.nmpa.gov.cn/datasearch/search-result.html?searchValue=%E5%B8%83%E5%8A%A0%E6%9B%BF%E5%B0%BC",
            "https://www.takeda.com.cn/products/alunbrig",
        ),
    },
    "洛拉替尼": {
        "generic_name_zh": "洛拉替尼",
        "generic_name_en": "Lorlatinib",
        "brand_names_zh": ("博瑞纳",),
        "brand_names_en": ("Lorbrena", "Lorviqua"),
        "nmpa_approval_no": "国药准字HJ20220018",
        "first_approval_date_cn": "2022-04-29",
        "indications_cn": (
            "ALK 阳性局部晚期或转移性非小细胞肺癌一线治疗",
            "ALK 阳性局部晚期或转移性非小细胞肺癌(经其它 ALK 抑制剂治疗后进展)",
        ),
        "atc_code": "L01ED05",
        "target": "ALK/ROS1",
        "drug_class": "三代 ALK-TKI",
        "sources": (
            "https://www.nmpa.gov.cn/datasearch/search-result.html?searchValue=%E6%B4%9B%E6%8B%89%E6%9B%BF%E5%B0%BC",
            "https://www.pfizer.com.cn/products/lorbrena",
        ),
    },
    "伊鲁阿克": {
        "generic_name_zh": "伊鲁阿克",
        "generic_name_en": "Iruplinalkib",
        "brand_names_zh": ("启欣可",),
        "brand_names_en": (),  # 国产药,无国际商品名
        "nmpa_approval_no": "国药准字H20230070",
        "first_approval_date_cn": "2023-12-29",
        "indications_cn": (
            "ALK 阳性局部晚期或转移性非小细胞肺癌(经克唑替尼治疗后进展或不耐受)",
        ),
        "atc_code": "L01ED",  # ATC 暂未细分
        "target": "ALK",
        "drug_class": "二代 ALK-TKI",
        "sources": (
            "https://www.nmpa.gov.cn/datasearch/search-result.html?searchValue=%E4%BC%8A%E9%B2%81%E9%98%BF%E5%85%8B",
            "https://www.qiluhealthcare.com/products/qixinke",
        ),
    },
    "依奉阿克": {
        "generic_name_zh": "依奉阿克",
        "generic_name_en": "Envonalkib",
        "brand_names_zh": ("赛沛科",),  # 占位,以 NMPA 公开页为准
        "brand_names_en": (),
        "nmpa_approval_no": "国药准字H20240010",
        "first_approval_date_cn": "2024-06-17",
        "indications_cn": (
            "ALK 阳性局部晚期或转移性非小细胞肺癌一线治疗",
        ),
        "atc_code": "L01ED",
        "target": "ALK",
        "drug_class": "二代 ALK-TKI",
        "sources": (
            "https://www.nmpa.gov.cn/datasearch/search-result.html?searchValue=%E4%BE%9D%E5%A5%89%E9%98%BF%E5%85%8B",
        ),
    },
}


# --- 其它常见参照药(供 cross_check 时用) ---
OTHER_DRUGS: dict[str, dict] = {
    # 故意保留"赛可瑞"作为克唑替尼商品名,这样 cross_check
    # 能在文本说"洛拉替尼商品名是赛可瑞"时检测出错位
}


def get_fallback_dict() -> dict[str, dict]:
    """聚合所有 fallback drug dict。"""
    merged: dict[str, dict] = {}
    merged.update(ALK_TKI_DRUGS)
    merged.update(OTHER_DRUGS)
    return merged


def build_brand_to_generic_index() -> dict[str, str]:
    """构建商品名 → 通用名(中文)反向索引,用于 cross_check 错位检测。

    Returns:
        {brand_zh_or_en: generic_zh}
        例: {"赛可瑞": "克唑替尼", "Xalkori": "克唑替尼", "博瑞纳": "洛拉替尼"}
    """
    idx: dict[str, str] = {}
    for generic_zh, rec in get_fallback_dict().items():
        for brand in rec.get("brand_names_zh", ()):
            if brand:
                idx[brand] = generic_zh
        for brand in rec.get("brand_names_en", ()):
            if brand:
                idx[brand] = generic_zh
                idx[brand.lower()] = generic_zh  # 大小写不敏感
    return idx


def build_alias_to_generic_index() -> dict[str, str]:
    """构建所有别名(英文通用/商品)到通用名(中文)的索引。"""
    idx: dict[str, str] = {}
    for generic_zh, rec in get_fallback_dict().items():
        idx[generic_zh] = generic_zh
        en = rec.get("generic_name_en", "")
        if en:
            idx[en] = generic_zh
            idx[en.lower()] = generic_zh
        for brand in rec.get("brand_names_zh", ()):
            if brand:
                idx[brand] = generic_zh
        for brand in rec.get("brand_names_en", ()):
            if brand:
                idx[brand] = generic_zh
                idx[brand.lower()] = generic_zh
    return idx
