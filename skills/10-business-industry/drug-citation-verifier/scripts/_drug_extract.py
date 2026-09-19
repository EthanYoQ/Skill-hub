"""药品提及抽取(基于命名学,而非字典)。

**P0 守护**:本模块**不**包含任何具体药品名 / 商品名 / 英文药品名。
只识别"中文医药命名后缀"和"上下文关键词"。

允许的规则(命名学):
- 中文药名后缀:"替尼"/"单抗"/"阿克"/"沙星"/"霉素"/"他汀"/"西布"/"洛尔"/...
- 英文药名后缀:"-tinib"/"-mab"/"-statin"/"-ciclib"/"-parib"/...
- 上下文关键词:"商品名"/"剂量"/"治疗"/"推荐"/"批准"/...

抽取出的"疑似药名"必须由调用方(verifier)拿去**核对源**,
源里有 = 真实药提及,源里没 = LLM 编造或不属于本指南。
"""

from __future__ import annotations

import re
from dataclasses import dataclass

# ---------------------------------------------------------------------------
# 命名学规则(NOT a drug dictionary — these are linguistic suffixes)
# ---------------------------------------------------------------------------

# 中文药名后缀:中国药典 / WHO INN 中译规则中的常见后缀
# 这是"中文药名构词法",符合后缀的字符串都视为疑似药名
DRUG_NAME_SUFFIXES_CN: tuple[str, ...] = (
    # 小分子靶向药
    "替尼",
    "西尼布",
    "西布",
    "拉尼布",
    "拉非尼",
    "格列汀",
    "列汀",
    "格列净",
    "列净",
    # 抗体类
    "单抗",
    "双抗",
    "抗体偶联物",
    # 化疗 / 抗生素类
    "霉素",
    "沙星",
    "西林",
    "头孢",
    "环素",
    "硝唑",
    "嘧啶",
    "他赛",
    # 心血管 / 代谢类
    "他汀",
    "洛尔",
    "普利",
    "沙坦",
    "地平",
    # 神经精神类
    "西汀",
    "西泮",
    "巴比妥",
    # 其他通用后缀
    "阿克",
    "司他",
    "鲁单",
    "伐他",
    "膦酸",
)

# 英文药名后缀(WHO INN stems):用于识别报告中混排的英文药名
DRUG_NAME_SUFFIXES_EN: tuple[str, ...] = (
    "tinib",
    "ciclib",
    "parib",
    "rafenib",
    "lisib",
    "degib",
    "fenib",
    "mab",
    "ximab",
    "zumab",
    "tuzumab",
    "lumab",
    "olimumab",
    "statin",
    "vastatin",
    "sartan",
    "pril",
    "olol",
    "dipine",
    "azole",
    "mycin",
    "floxacin",
    "cillin",
    "cycline",
    "navir",
    "tegravir",
    "ciclovir",
)

# 上下文关键词:出现在药名附近时,可"关联"出商品名/剂量
DRUG_CONTEXT_KEYWORDS: tuple[str, ...] = (
    "商品名",
    "通用名",
    "原研",
    "仿制",
    "剂量",
    "推荐剂量",
    "治疗",
    "I 级推荐",
    "Ⅰ级推荐",
    "II 级推荐",
    "Ⅱ级推荐",
    "首选",
    "一线",
    "二线",
    "批准",
    "获批",
    "上市",
)

# 中文药名上限长度(INN 中译名通常 3-6 字,极少超过 8)
_MAX_CN_NAME_LEN = 8
# 中文药名下限长度
_MIN_CN_NAME_LEN = 3

# 中文药名字符集:汉字
_CN_DRUG_CHAR = r"[一-鿿]"


def _build_cn_suffix_pattern() -> re.Pattern[str]:
    """匹配后缀本身的正则,用于"suffix-first"扫描。

    扫到后缀位置后,由 ``_walk_back_drug_name`` 向左走,
    取连续的汉字直到长度 N-1 / 遇到非汉字 / 已知句首词。
    这样避免 lazy 量词在长前缀(如"一线推荐")上越界。
    """
    suffix_alt = "|".join(re.escape(s) for s in DRUG_NAME_SUFFIXES_CN)
    return re.compile(rf"(?:{suffix_alt})")


def _build_en_drug_pattern() -> re.Pattern[str]:
    suffix_alt = "|".join(re.escape(s) for s in DRUG_NAME_SUFFIXES_EN)
    # 英文药名:小写为主,首字母可大写,3-30 chars,以后缀结尾(单词边界)
    pat = rf"\b([A-Za-z]{{2,28}}(?:{suffix_alt}))\b"
    return re.compile(pat)


_CN_SUFFIX_RE = _build_cn_suffix_pattern()
_EN_DRUG_RE = _build_en_drug_pattern()

# 用于"向左走"边界判断:汉字字符
_CN_CHAR_RE = re.compile(r"[一-鿿]")

# 边界字符集:常见**中文语法词**(非药名)的字符。当向左走时若当前字属于此集,
# 视为边界,停止扩展药名。
#
# 这是**中文语法**,不是**药品字典**:这些字出现在所有医学/非医学中文里都
# 表示动词/介词/连词/副词/数词,与药名构词无关。
_CN_BOUNDARY_CHARS: frozenset[str] = frozenset(
    # 动作/状态动词
    "推荐治疗使用应用采用建议批准获批准予允许包括含有具有给予服用口服注射"
    # 关系/介词/连词
    "用为是与和及或而对于关于相对则在由从到至向且但被及"
    # 数词/序数
    "一二三四五六七八九十首末初终全各每某其本该这那此些"
    # 量级/分类
    "线级期型类组组别群项次度组合方案"
    # 临床通用词
    "病患者人群儿成年老幼孕妇男女岁周月年日时分秒次毫克片粒支袋"
    # 高频虚词
    "的了着过吗呢吧呀啊么也都还又再才就只仍便却均"
    # 结构词
    "新原老旧前后上下里外中内左右大小高低多少长短"
)


def _walk_back_drug_name(text: str, suffix_start: int, suffix_end: int) -> tuple[int, int] | None:
    """从后缀位置向左走,取连续汉字作为药名核心。

    Returns:
        (name_start, name_end) 或 None(无足够前缀)。

    策略:
    - 向左走最多 (_MAX_CN_NAME_LEN - len(suffix)) 个汉字,直到遇到非汉字
    - 必须有至少 (_MIN_CN_NAME_LEN - len(suffix)) 个前缀汉字 *或* 前缀汉字
      之后形成的总长 >= _MIN_CN_NAME_LEN
    """
    suffix_len = suffix_end - suffix_start
    max_prefix = _MAX_CN_NAME_LEN - suffix_len
    min_prefix = max(0, _MIN_CN_NAME_LEN - suffix_len)

    name_start = suffix_start
    for i in range(suffix_start - 1, suffix_start - 1 - max_prefix, -1):
        if i < 0:
            break
        ch = text[i]
        if not _CN_CHAR_RE.fullmatch(ch):
            break
        if ch in _CN_BOUNDARY_CHARS:
            # 撞到中文语法词字符 → 停下,不吞此字
            break
        name_start = i

    prefix_len = suffix_start - name_start
    if prefix_len < min_prefix:
        return None
    return (name_start, suffix_end)

# 商品名/英文括注:在药名后紧跟的"(...)"或"(...)"括号
_BRAND_PAREN_RE = re.compile(r"[\(\(]([^\)\)]{1,40})[\)\)]")

# 上下文取词窗口(字符)
_CONTEXT_WINDOW = 60


@dataclass(frozen=True)
class DrugMention:
    """单个药品提及(数据类)。"""

    text: str
    brand_in_context: str
    context: str
    position: int


def _extract_brand_after(text: str, end_pos: int) -> str:
    """在药名末位置之后立即查找括号注释。"""
    if end_pos >= len(text):
        return ""

    tail = text[end_pos : end_pos + 80]
    m = _BRAND_PAREN_RE.search(tail)
    if not m:
        return ""
    if m.start() > 30:
        return ""
    return m.group(1).strip()


def _context_around(text: str, start: int, end: int) -> str:
    left = max(0, start - _CONTEXT_WINDOW)
    right = min(len(text), end + _CONTEXT_WINDOW)
    return text[left:right].strip()


def extract_drug_mentions_with_context(text: str) -> list[dict]:
    """从文本中抽取所有"疑似药品提及"(命名学规则)。

    Returns:
        [
            {
                "text": "<通用名>",
                "brand_in_context": "<括号内容>",
                "context": "<上下文 ±60 字>",
                "position": <int>,
            },
            ...
        ]

    P0 守护:本函数**只识别命名后缀**,不验证"这个药真的存在";
    调用方必须拿 mention.text(+ brand_in_context)去**核对源**。
    """
    if not text:
        return []

    out: list[dict] = []
    seen_positions: set[int] = set()

    # 中文药名:suffix-first 扫描,然后向左走取核心
    for m in _CN_SUFFIX_RE.finditer(text):
        suffix_start, suffix_end = m.start(), m.end()
        span = _walk_back_drug_name(text, suffix_start, suffix_end)
        if span is None:
            continue
        start, end = span
        if start in seen_positions:
            continue
        seen_positions.add(start)
        name = text[start:end].strip()
        if any(ch in name for ch in "[](){}〔〕,。;:、 "):
            continue
        brand = _extract_brand_after(text, end)
        out.append(
            {
                "text": name,
                "brand_in_context": brand,
                "context": _context_around(text, start, end),
                "position": start,
            }
        )

    for m in _EN_DRUG_RE.finditer(text):
        start, end = m.start(), m.end()
        if start in seen_positions:
            continue
        seen_positions.add(start)
        name = m.group(1).strip()
        out.append(
            {
                "text": name,
                "brand_in_context": _extract_brand_after(text, end),
                "context": _context_around(text, start, end),
                "position": start,
            }
        )

    out.sort(key=lambda x: x["position"])
    return out
