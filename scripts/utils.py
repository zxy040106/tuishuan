#!/usr/bin/env python3
"""推算 Skill — 共享工具模块"""

import sys; sys.stdout.reconfigure(encoding='utf-8')  # Windows GBK 修复

from datetime import datetime, date, timedelta
from typing import Tuple, Optional, Dict, List
import math

# =============================================================================
# 天干地支基础
# =============================================================================

TIANGAN = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
DIZHI = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]

# 六十甲子表（0=甲子, 1=乙丑, ..., 59=癸亥）
SEXAGENARY = [
    "甲子","乙丑","丙寅","丁卯","戊辰","己巳","庚午","辛未","壬申","癸酉",
    "甲戌","乙亥","丙子","丁丑","戊寅","己卯","庚辰","辛巳","壬午","癸未",
    "甲申","乙酉","丙戌","丁亥","戊子","己丑","庚寅","辛卯","壬辰","癸巳",
    "甲午","乙未","丙申","丁酉","戊戌","己亥","庚子","辛丑","壬寅","癸卯",
    "甲辰","乙巳","丙午","丁未","戊申","己酉","庚戌","辛亥","壬子","癸丑",
    "甲寅","乙卯","丙辰","丁巳","戊午","己未","庚申","辛酉","壬戌","癸亥",
]

# 生肖
SHENGXIAO = ["鼠","牛","虎","兔","龙","蛇","马","羊","猴","鸡","狗","猪"]


def gan_index(g: str) -> int:
    """Return 0-based index of a heavenly stem."""
    return TIANGAN.index(g)


def zhi_index(z: str) -> int:
    """Return 0-based index of an earthly branch."""
    return DIZHI.index(z)


def ganzhi_to_index(gz: str) -> int:
    """Convert a 干支 string (e.g. '甲子') to its 0-59 index."""
    return SEXAGENARY.index(gz)


def index_to_ganzhi(i: int) -> str:
    """Convert a 0-59 index to 干支 string."""
    return SEXAGENARY[i % 60]


def split_ganzhi(gz: str) -> Tuple[str, str]:
    """Split '甲子' -> ('甲', '子')."""
    return gz[0], gz[1]


def join_ganzhi(gan: str, zhi: str) -> str:
    """Join ('甲', '子') -> '甲子'."""
    return gan + zhi


def shengxiao_from_year_zhi(zhi: str) -> str:
    """Get zodiac animal from year branch."""
    return SHENGXIAO[DIZHI.index(zhi)]


# =============================================================================
# 五行系统
# =============================================================================

WUXING_LIST = ["木", "火", "土", "金", "水"]

# 天干五行
TIANGAN_WUXING = {
    "甲": "木", "乙": "木",
    "丙": "火", "丁": "火",
    "戊": "土", "己": "土",
    "庚": "金", "辛": "金",
    "壬": "水", "癸": "水",
}

# 天干阴阳（甲丙戊庚壬=阳, 乙丁己辛癸=阴）
TIANGAN_YINYANG = {
    "甲": "阳", "乙": "阴",
    "丙": "阳", "丁": "阴",
    "戊": "阳", "己": "阴",
    "庚": "阳", "辛": "阴",
    "壬": "阳", "癸": "阴",
}

# 地支五行
DIZHI_WUXING = {
    "寅": "木", "卯": "木",
    "巳": "火", "午": "火",
    "申": "金", "酉": "金",
    "亥": "水", "子": "水",
    "辰": "土", "戌": "土", "丑": "土", "未": "土",
}

# 地支藏干表（本气/中气/余气）
DIZHI_CANGGAN = {
    "子": ["癸"],
    "丑": ["己", "癸", "辛"],
    "寅": ["甲", "丙", "戊"],
    "卯": ["乙"],
    "辰": ["戊", "乙", "癸"],
    "巳": ["丙", "庚", "戊"],
    "午": ["丁", "己"],
    "未": ["己", "丁", "乙"],
    "申": ["庚", "壬", "戊"],
    "酉": ["辛"],
    "戌": ["戊", "辛", "丁"],
    "亥": ["壬", "甲"],
}

# =============================================================================
# 纳音五行（六十甲子纳音）
# =============================================================================

NAYIN = {
    "甲子": "海中金", "乙丑": "海中金",
    "丙寅": "炉中火", "丁卯": "炉中火",
    "戊辰": "大林木", "己巳": "大林木",
    "庚午": "路旁土", "辛未": "路旁土",
    "壬申": "剑锋金", "癸酉": "剑锋金",
    "甲戌": "山头火", "乙亥": "山头火",
    "丙子": "涧下水", "丁丑": "涧下水",
    "戊寅": "城头土", "己卯": "城头土",
    "庚辰": "白蜡金", "辛巳": "白蜡金",
    "壬午": "杨柳木", "癸未": "杨柳木",
    "甲申": "泉中水", "乙酉": "泉中水",
    "丙戌": "屋上土", "丁亥": "屋上土",
    "戊子": "霹雳火", "己丑": "霹雳火",
    "庚寅": "松柏木", "辛卯": "松柏木",
    "壬辰": "长流水", "癸巳": "长流水",
    "甲午": "砂中金", "乙未": "砂中金",
    "丙申": "山下火", "丁酉": "山下火",
    "戊戌": "平地木", "己亥": "平地木",
    "庚子": "壁上土", "辛丑": "壁上土",
    "壬寅": "金箔金", "癸卯": "金箔金",
    "甲辰": "覆灯火", "乙巳": "覆灯火",
    "丙午": "天河水", "丁未": "天河水",
    "戊申": "大驿土", "己酉": "大驿土",
    "庚戌": "钗钏金", "辛亥": "钗钏金",
    "壬子": "桑柘木", "癸丑": "桑柘木",
    "甲寅": "大溪水", "乙卯": "大溪水",
    "丙辰": "沙中土", "丁巳": "沙中土",
    "戊午": "天上火", "己未": "天上火",
    "庚申": "石榴木", "辛酉": "石榴木",
    "壬戌": "大海水", "癸亥": "大海水",
}

# 纳音五行（简化，只取五行）
NAYIN_WUXING = {gz: full[-1] for gz, full in NAYIN.items()}  # e.g. '海中金' -> '金'


# =============================================================================
# 五行生克
# =============================================================================

def wuxing_sheng(wx: str) -> str:
    """返回被生者: 木生火 -> 返回'火'."""
    order = {"木": "火", "火": "土", "土": "金", "金": "水", "水": "木"}
    return order[wx]


def wuxing_ke(wx: str) -> str:
    """返回被克者: 木克土 -> 返回'土'."""
    order = {"木": "土", "土": "水", "水": "火", "火": "金", "金": "木"}
    return order[wx]


def wuxing_sheng_wo(wx: str) -> str:
    """返回生我者: 水生木 -> 返回'水'."""
    order = {"木": "水", "水": "金", "金": "土", "土": "火", "火": "木"}
    return order[wx]


def wuxing_ke_wo(wx: str) -> str:
    """返回克我者: 金克木 -> 返回'金'."""
    order = {"木": "金", "金": "火", "火": "水", "水": "土", "土": "木"}
    return order[wx]


def wuxing_relation(a_wx: str, b_wx: str) -> str:
    """a对b的五行关系: 生/克/被生/被克/同."""
    if a_wx == b_wx:
        return "同"
    if wuxing_sheng(a_wx) == b_wx:
        return "a生b"
    if wuxing_ke(a_wx) == b_wx:
        return "a克b"
    if wuxing_sheng_wo(a_wx) == b_wx:
        return "a被b生"
    if wuxing_ke_wo(a_wx) == b_wx:
        return "a被b克"
    return "未知"


# =============================================================================
# 四时旺衰表 — 月支五行对爻支五行的旺衰状态
# =============================================================================

# 月份地支 → 当令五行
MONTH_DIZHI_WANG_WUXING = {
    "寅": "木", "卯": "木",
    "巳": "火", "午": "火",
    "申": "金", "酉": "金",
    "亥": "水", "子": "水",
    "辰": "土", "戌": "土", "丑": "土", "未": "土",
}

# 每个当令五行下，其他五行的旺衰状态
# 旺=当令, 相=被当令生, 休=生当令, 囚=克当令, 死=被当令克
_WANG_SHUAI_BY_LING = {
    "木": {"木": "旺", "火": "相", "水": "休", "金": "囚", "土": "死"},
    "火": {"火": "旺", "土": "相", "木": "休", "水": "囚", "金": "死"},
    "土": {"土": "旺", "金": "相", "火": "休", "木": "囚", "水": "死"},
    "金": {"金": "旺", "水": "相", "土": "休", "火": "囚", "木": "死"},
    "水": {"水": "旺", "木": "相", "金": "休", "土": "囚", "火": "死"},
}


def get_wang_shuai(month_zhi: str, yao_wuxing: str) -> str:
    """
    返回爻支五行在月建下的旺衰状态。
    返回: 旺/相/休/囚/死
    """
    ling = MONTH_DIZHI_WANG_WUXING.get(month_zhi, "")
    if not ling:
        return "平"
    return _WANG_SHUAI_BY_LING.get(ling, {}).get(yao_wuxing, "平")


# =============================================================================
# 合冲刑害
# =============================================================================

# 天干五合
TIANGAN_HE = {
    ("甲", "己"): "土",
    ("乙", "庚"): "金",
    ("丙", "辛"): "水",
    ("丁", "壬"): "木",
    ("戊", "癸"): "火",
}

# 地支六合
DIZHI_LIUHE = {
    ("子", "丑"): "土",
    ("寅", "亥"): "木",
    ("卯", "戌"): "火",
    ("辰", "酉"): "金",
    ("巳", "申"): "水",
    ("午", "未"): "土",
}

# 地支六冲
DIZHI_LIUCHONG = {
    ("子", "午"), ("丑", "未"), ("寅", "申"),
    ("卯", "酉"), ("辰", "戌"), ("巳", "亥"),
}

# 地支三合 (frozenset 键 — 避免Unicode排序导致匹配失败)
DIZHI_SANHE = {
    frozenset(["申","子","辰"]): "水",
    frozenset(["亥","卯","未"]): "木",
    frozenset(["寅","午","戌"]): "火",
    frozenset(["巳","酉","丑"]): "金",
}

# 地支六害
DIZHI_LIUHAI = {
    ("子", "未"), ("丑", "午"), ("寅", "巳"),
    ("卯", "辰"), ("申", "亥"), ("酉", "戌"),
}

# 地支三刑
DIZHI_SANXING = {
    ("寅", "巳", "申"): "无恩之刑",
    ("丑", "戌", "未"): "持势之刑",
    ("子", "卯"): "无礼之刑",
}

# 地支自刑
DIZHI_ZIXING = {"辰", "午", "酉", "亥"}


def get_tiangan_he(g1: str, g2: str) -> Optional[str]:
    """如果两个天干合, 返回化气五行, 否则None."""
    return TIANGAN_HE.get((g1, g2)) or TIANGAN_HE.get((g2, g1))


def get_dizhi_liuhe(z1: str, z2: str) -> Optional[str]:
    """如果两个地支六合, 返回化气五行, 否则None."""
    return DIZHI_LIUHE.get((z1, z2)) or DIZHI_LIUHE.get((z2, z1))


def get_dizhi_liuchong(z1: str, z2: str) -> bool:
    """两个地支是否六冲."""
    return (z1, z2) in DIZHI_LIUCHONG or (z2, z1) in DIZHI_LIUCHONG


def get_dizhi_liuhai(z1: str, z2: str) -> bool:
    """两个地支是否六害."""
    return (z1, z2) in DIZHI_LIUHAI or (z2, z1) in DIZHI_LIUHAI


def get_dizhi_sanhe(z1: str, z2: str, z3: str) -> Optional[str]:
    """三个地支是否三合局, 返回化气五行."""
    return DIZHI_SANHE.get(frozenset([z1, z2, z3]))


# =============================================================================
# 时辰转换
# =============================================================================

# 时辰对应表（23:00-00:59 = 子时, 依此类推）
HOUR_TO_SHICHEN = {
    0: "子", 1: "丑", 2: "丑", 3: "寅", 4: "寅", 5: "卯", 6: "卯",
    7: "辰", 8: "辰", 9: "巳", 10: "巳", 11: "午", 12: "午",
    13: "未", 14: "未", 15: "申", 16: "申", 17: "酉", 18: "酉",
    19: "戌", 20: "戌", 21: "亥", 22: "亥", 23: "子",
}

SHICHEN_TO_HOUR = {
    "子": (23, 0),
    "丑": (1, 2),
    "寅": (3, 4),
    "卯": (5, 6),
    "辰": (7, 8),
    "巳": (9, 10),
    "午": (11, 12),
    "未": (13, 14),
    "申": (15, 16),
    "酉": (17, 18),
    "戌": (19, 20),
    "亥": (21, 22),
}

SHICHEN_ORDER = ["子","丑","寅","卯","辰","巳","午","未","申","酉","戌","亥"]


def hour_to_shichen(hour: int) -> str:
    """Convert a 0-23 hour to 时辰 branch string."""
    return HOUR_TO_SHICHEN.get(hour % 24, "子")


def shichen_index(zhi: str) -> int:
    """Get the 0-based ordinal of a 时辰 (子=0, 丑=1, ...)."""
    return SHICHEN_ORDER.index(zhi)


# =============================================================================
# 月柱推算（年上起月 / 五虎遁）
# =============================================================================

# 年干 → 正月（寅月）天干
YEAR_GAN_TO_MONTH1_GAN = {
    "甲": "丙", "己": "丙",  # 甲己之年丙作首
    "乙": "戊", "庚": "戊",  # 乙庚之岁戊为头
    "丙": "庚", "辛": "庚",  # 丙辛必定寻庚起
    "丁": "壬", "壬": "壬",  # 丁壬壬位顺行流
    "戊": "甲", "癸": "甲",  # 戊癸何方发，甲寅之上好追求
}


def month_ganzhi(year_gan: str, month_num: int) -> str:
    """
    返回指定农历月份的干支。
    month_num: 1=寅月(正月), 2=卯月, ..., 12=丑月.
    """
    base_gan = YEAR_GAN_TO_MONTH1_GAN[year_gan]
    gan_idx = (TIANGAN.index(base_gan) + (month_num - 1)) % 10
    zhi_idx = (2 + (month_num - 1)) % 12  # 寅=2
    return TIANGAN[gan_idx] + DIZHI[zhi_idx]


# =============================================================================
# 时柱推算（日上起时 / 五鼠遁）
# =============================================================================

# 日干 → 子时天干
DAY_GAN_TO_ZISHI_GAN = {
    "甲": "甲", "己": "甲",  # 甲己还加甲
    "乙": "丙", "庚": "丙",  # 乙庚丙作初
    "丙": "戊", "辛": "戊",  # 丙辛从戊起
    "丁": "庚", "壬": "庚",  # 丁壬庚子居
    "戊": "壬", "癸": "壬",  # 戊癸何方发，壬子是真途
}


def hour_ganzhi(day_gan: str, shichen_zhi: str) -> str:
    """返回时柱干支."""
    base_gan = DAY_GAN_TO_ZISHI_GAN[day_gan]
    zhi_idx = SHICHEN_ORDER.index(shichen_zhi)
    gan_idx = (TIANGAN.index(base_gan) + zhi_idx) % 10
    return TIANGAN[gan_idx] + shichen_zhi


# =============================================================================
# 六十甲子 循环运算
# =============================================================================

def sexagenary_add(gz: str, n: int) -> str:
    """六十甲子循环加: 甲子+1=乙丑, 甲子+60=甲子."""
    idx = (SEXAGENARY.index(gz) + n) % 60
    return SEXAGENARY[idx]


def sexagenary_diff(gz1: str, gz2: str) -> int:
    """返回 gz2 - gz1 (mod 60), 结果为0-59."""
    i1 = SEXAGENARY.index(gz1)
    i2 = SEXAGENARY.index(gz2)
    return (i2 - i1) % 60


# =============================================================================
# 地支顺逆排
# =============================================================================

def dizhi_step(zhi: str, n: int) -> str:
    """地支顺推n步(n可为负)."""
    return DIZHI[(DIZHI.index(zhi) + n) % 12]


# =============================================================================
# 中国农历年（以立春为界）
# =============================================================================

# =============================================================================
# 节气天文算法（替代硬编码表，无年份范围限制）
# =============================================================================

# 节气名称和对应太阳视黄经
_SOLAR_TERM_LON = {
    "立春": 315, "雨水": 330, "惊蛰": 345, "春分": 0,
    "清明": 15,  "谷雨": 30,  "立夏": 45,  "小满": 60,
    "芒种": 75,  "夏至": 90,  "小暑": 105, "大暑": 120,
    "立秋": 135, "处暑": 150, "白露": 165, "秋分": 180,
    "寒露": 195, "霜降": 210, "立冬": 225, "小雪": 240,
    "大雪": 255, "冬至": 270, "小寒": 285, "大寒": 300,
}

# 12个"节"（月柱换月点），按农历月顺序
SOLAR_TERM_MONTH = [
    "立春", "惊蛰", "清明", "立夏", "芒种",
    "小暑", "立秋", "白露", "寒露", "立冬",
    "大雪", "小寒",
]


def _jd_from_date(dt: datetime) -> float:
    """公历日期 → 儒略日（Julian Day）."""
    y, m = dt.year, dt.month
    d = dt.day + dt.hour / 24.0 + dt.minute / 1440.0 + dt.second / 86400.0
    if m <= 2:
        y -= 1
        m += 12
    a = y // 100
    b = 2 - a + a // 4
    return int(365.25 * (y + 4716)) + int(30.6001 * (m + 1)) + d + b - 1524.5


def _jd_to_date(jd: float) -> date:
    """儒略日 → 公历 date."""
    jd += 0.5
    z = int(jd)
    f = jd - z
    if z < 2299161:
        a = z
    else:
        alpha = int((z - 1867216.25) / 36524.25)
        a = z + 1 + alpha - alpha // 4
    b = a + 1524
    c = int((b - 122.1) / 365.25)
    d = int(365.25 * c)
    e = int((b - d) / 30.6001)
    day = int(b - d - int(30.6001 * e) + f)
    if e < 14:
        month = e - 1
    else:
        month = e - 13
    year = c - 4716 if month > 2 else c - 4715
    return date(year, month, day)


def _jd_to_datetime(jd: float) -> datetime:
    """儒略日 → 公历 datetime（精度到分钟级）."""
    jd += 0.5
    z = int(jd)
    f = jd - z
    if z < 2299161:
        a = z
    else:
        alpha = int((z - 1867216.25) / 36524.25)
        a = z + 1 + alpha - alpha // 4
    b = a + 1524
    c = int((b - 122.1) / 365.25)
    d = int(365.25 * c)
    e = int((b - d) / 30.6001)
    day_frac = b - d - int(30.6001 * e) + f
    day = int(day_frac)
    frac = day_frac - day
    hour = int(frac * 24)
    minute = int((frac * 24 - hour) * 60)
    second = int(((frac * 24 - hour) * 60 - minute) * 60)
    if e < 14:
        month = e - 1
    else:
        month = e - 13
    year = c - 4716 if month > 2 else c - 4715
    return datetime(year, month, day, hour, minute, second)


def _sun_ecliptic_lon(jd: float) -> float:
    """太阳视黄经（度, 0-360）. Meeus 低精度公式, 误差 ~0.01° → 时间误差 ~15分钟."""
    T = (jd - 2451545.0) / 36525.0
    T2 = T * T
    L0 = (280.46646 + 36000.76983 * T + 0.0003032 * T2) % 360
    M = (357.52911 + 35999.05029 * T - 0.0001537 * T2) % 360
    Mr = math.radians(M)
    C = ((1.914602 - 0.004817 * T - 0.000014 * T2) * math.sin(Mr) +
         (0.019993 - 0.000101 * T) * math.sin(2 * Mr) +
         0.000289 * math.sin(3 * Mr))
    lon = L0 + C - 0.00569 - 0.00478 * math.sin(math.radians(125.04 - 1934.136 * T))
    return lon % 360


def get_solar_term_date(year: int, term_name: str) -> date:
    """
    计算某年某个节气的准确公历日期。
    term_name: 节气名，如 '立春', '冬至', '惊蛰'
    精度: 时间误差 ~15分钟，年份范围不限。
    注意：返回 date 对象（日级别精度），节气时刻可能在该日任意时分。
    对于年柱/月柱的节气换月判定，当日精度对绝大多数情况足够。
    """
    target = _SOLAR_TERM_LON.get(term_name)
    if target is None:
        return date(year, 2, 4)
    # 初值：从立春(315°)起算偏移天数
    effective = target if target >= 315 else target + 360
    offset_days = (effective - 315) / 360.0 * 365.2422
    jd = _jd_from_date(datetime(year, 2, 4, 12, 0, 0)) + offset_days
    # Newton 迭代求解
    for _ in range(6):
        lon = _sun_ecliptic_lon(jd)
        diff = (target - lon) % 360
        if diff > 180:
            diff -= 360
        if abs(diff) < 0.00001:
            break
        jd += diff / 0.98564736
    return _jd_to_date(jd + 8.0 / 24.0)  # UTC → 北京时间 (UTC+8)


def get_solar_term_datetime(year: int, term_name: str) -> Optional[datetime]:
    """
    计算某年某个节气的准确公历日期时间（精确到分钟级）。
    用于年柱/月柱在节气当天的精确换月判定。
    精度: 时间误差 ~15分钟。
    """
    target = _SOLAR_TERM_LON.get(term_name)
    if target is None:
        return None
    effective = target if target >= 315 else target + 360
    offset_days = (effective - 315) / 360.0 * 365.2422
    jd = _jd_from_date(datetime(year, 2, 4, 12, 0, 0)) + offset_days
    for _ in range(6):
        lon = _sun_ecliptic_lon(jd)
        diff = (target - lon) % 360
        if diff > 180:
            diff -= 360
        if abs(diff) < 0.00001:
            break
        jd += diff / 0.98564736
    return _jd_to_datetime(jd + 8.0 / 24.0)


def get_lichun_date(year: int) -> tuple:
    """返回 (月, 日) 立春日期."""
    d = get_solar_term_date(year, "立春")
    return (d.month, d.day)


# 向后兼容：动态生成的 LICHUN_DATES（懒加载，支持 .get() 调用）
class _LichunDict(dict):
    """自动计算立春日期的字典，兼容原有 LICHUN_DATES.get(year, default) 调用."""
    def __missing__(self, year):
        d = get_solar_term_date(year, "立春")
        val = (d.month, d.day)
        self[year] = val
        return val

    def get(self, year, default=None):
        try:
            return self[year]  # 触发 __missing__ 进行懒计算
        except (KeyError, TypeError):
            return default

LICHUN_DATES = _LichunDict()


# =============================================================================
# 天文朔日（新月）计算 — 农历月精确长度
# =============================================================================

def _new_moon_jd(k: int) -> float:
    """
    计算第 k 个朔日（日月合朔）的儒略日 (Universal Time)。
    k=0 对应 2000-01-06 附近的新月。
    使用 Meeus《Astronomical Algorithms》第49章算法。
    精度: ~2分钟，足够精确到日历日。
    """
    T = k / 1236.85
    T2 = T * T
    T3 = T2 * T
    T4 = T3 * T

    # 平朔 (Mean conjunction, JDE in dynamical time)
    JDE = (2451550.09765 + 29.530588853 * k +
           0.0001337 * T2 - 0.000000150 * T3 +
           0.00000000073 * T4)

    # 地球轨道偏心率修正
    E = 1 - 0.002516 * T - 0.0000074 * T2

    # 太阳平近点角 (degrees)
    M = (2.5534 + 29.10535669 * k - 0.0000218 * T2 - 0.00000011 * T3) % 360
    Mr = math.radians(M)

    # 月球平近点角
    Mp = (201.5643 + 385.81693528 * k + 0.0107438 * T2 +
          0.00001239 * T3 - 0.000000058 * T4) % 360
    Mpr = math.radians(Mp)

    # 月球纬度参数
    F = (160.7108 + 390.67050274 * k - 0.0016341 * T2 -
         0.00000227 * T3 + 0.000000011 * T4) % 360
    Fr = math.radians(F)

    # 升交点黄经
    Omega = (124.7746 - 1.56375580 * k + 0.0020691 * T2 +
             0.00000215 * T3) % 360
    Omegar = math.radians(Omega)

    # 14个主要周期项 (Meeus Table 49.A)
    corr = (-0.40720 * math.sin(Mpr) +
            0.17241 * E * math.sin(Mr) +
            0.01608 * math.sin(2.0 * Mpr) +
            0.01039 * math.sin(2.0 * Fr) +
            0.00739 * E * math.sin(Mpr - Mr) +
            -0.00514 * E * math.sin(Mpr + Mr) +
            0.00208 * E * E * math.sin(2.0 * Fr - Mpr) +
            -0.00111 * math.sin(Fr - Mpr) +
            -0.00057 * math.sin(Mpr + 2.0 * Fr) +
            0.00056 * E * math.sin(Fr + Mpr) +
            -0.00042 * math.sin(2.0 * Mpr + Mr) +
            0.00042 * E * math.sin(Omegar) +
            0.00038 * E * math.sin(Mr - Omegar) +
            -0.00024 * E * math.sin(2.0 * Mpr - Mr))

    # 行星摄动项
    plan_args = [
        (299.77 + 0.107408 * k - 0.009173 * T2),
        (251.88 + 0.016321 * k),
        (251.83 + 26.651886 * k),
        (349.42 + 36.412478 * k),
        (84.66 + 18.206239 * k),
        (141.74 + 53.303771 * k),
        (207.14 + 2.453732 * k),
        (154.84 + 7.306860 * k),
        (34.52 + 27.261239 * k),
        (207.19 + 0.121824 * k),
        (291.34 + 1.844379 * k),
        (161.72 + 24.198154 * k),
        (239.56 + 25.513099 * k),
        (331.55 + 3.592518 * k),
    ]
    plan_coeff = [0.000325, 0.000165, 0.000164, 0.000126, 0.000110,
                  0.000062, 0.000060, 0.000056, 0.000047, 0.000042,
                  0.000040, 0.000037, 0.000035, 0.000023]

    for i in range(14):
        corr += plan_coeff[i] * math.sin(math.radians(plan_args[i] % 360))

    # 力学时→世界时 (ΔT对日历日精度可忽略, 但保留框架)
    return JDE + corr


def _new_moon_date(k: int) -> date:
    """返回第k个朔日对应的北京日期 (UTC+8)."""
    jd_ut = _new_moon_jd(k)
    jd_bj = jd_ut + 8.0 / 24.0  # 北京时间
    return _jd_to_date(jd_bj)


# 朔日缓存（懒加载）
_new_moon_cache: Dict[int, date] = {}


def _get_new_moon_date(k: int) -> date:
    """取第k个朔日的北京日期（带缓存）."""
    if k not in _new_moon_cache:
        _new_moon_cache[k] = _new_moon_date(k)
    return _new_moon_cache[k]


# 中气名（用于闰月判断）
_ZHONGQI_NAMES = [
    "冬至", "大寒", "雨水", "春分", "谷雨", "小满",
    "夏至", "大暑", "处暑", "秋分", "霜降", "小雪",
]


# 每个月份对应的节气: (节, 气)
# 立春寅月, 惊蛰卯月, 清明辰月, 立夏巳月, 芒种午月, 小暑未月,
# 立秋申月, 白露酉月, 寒露戌月, 立冬亥月, 大雪子月, 小寒丑月
# 以下给出各月"节"气的大致日期（每月两个节气，这里只记录换月的节）
MONTH_START_JIEQI = {
    1: "立春", 2: "惊蛰", 3: "清明", 4: "立夏", 5: "芒种",
    6: "小暑", 7: "立秋", 8: "白露", 9: "寒露", 10: "立冬",
    11: "大雪", 12: "小寒",
}

# 节气对应农历月
JIEQI_TO_NONGLI_MONTH = {
    "立春": 1, "惊蛰": 2, "清明": 3, "立夏": 4, "芒种": 5,
    "小暑": 6, "立秋": 7, "白露": 8, "寒露": 9, "立冬": 10,
    "大雪": 11, "小寒": 12,
}

# 节气近似日期（动态生成，无年份限制）— 需要节气日期时请用 get_solar_term_date(year, name)


# =============================================================================
# 已知干支的参考日期（用于日柱推算）
# =============================================================================

# 1900年1月1日 = 甲戌日（第10日，索引9，这是确定的参考点）
# 来源：多个万年历交叉验证
REFERENCE_DATE = date(1900, 1, 1)
REFERENCE_GANZHI_INDEX = 10  # 甲戌在六十甲子中的索引


def day_ganzhi_index(d: date) -> int:
    """返回某日的干支索引（0-59），基于1900-01-01=甲戌（索引10）."""
    delta = (d - REFERENCE_DATE).days
    return (REFERENCE_GANZHI_INDEX + delta) % 60


def day_ganzhi(d: date) -> str:
    """返回某日的干支字符串."""
    return SEXAGENARY[day_ganzhi_index(d)]


# =============================================================================
# 小六壬 掌诀
# =============================================================================

XIAOLIUREN_STATIONS = ["大安", "留连", "速喜", "赤口", "小吉", "空亡"]

XIAOLIUREN_ATTRS = {
    "大安": {"wu_xing": "木", "direction": "东方", "timing": "1/5/7日", "meaning": "平安稳定，诸事顺遂"},
    "留连": {"wu_xing": "水", "direction": "北方", "timing": "2/8/10日", "meaning": "纠缠拖延，事难速决"},
    "速喜": {"wu_xing": "火", "direction": "南方", "timing": "3/6/9日", "meaning": "喜庆迅速，求谋有成"},
    "赤口": {"wu_xing": "金", "direction": "西方", "timing": "4/7/10日", "meaning": "口舌是非，破财官讼"},
    "小吉": {"wu_xing": "水", "direction": "北方", "timing": "1/4/7日", "meaning": "行人喜至，凡事和合"},
    "空亡": {"wu_xing": "土", "direction": "中", "timing": "3/6/9日", "meaning": "谋事落空，劳而无成"},
}


def xiaoliuren(lunar_month: int, lunar_day: int, lunar_hour_zhi: str = None) -> dict:
    """
    小六壬掌诀推算。
    lunar_month: 农历月 (1-12)
    lunar_day: 农历日 (1-30)
    lunar_hour_zhi: 时辰地支 (可选)
    返回: 最终落位及中间步骤
    """
    # 输入验证
    if not (1 <= lunar_month <= 12):
        return {"error": f"农历月超出范围: {lunar_month}（应为1-12）"}
    if not (1 <= lunar_day <= 30):
        return {"error": f"农历日超出范围: {lunar_day}（应为1-30）"}
    if lunar_hour_zhi is not None and lunar_hour_zhi not in DIZHI:
        return {"error": f"时辰无效: {lunar_hour_zhi}（应为十二地支之一）"}

    # 第一步: 从寅位起月（定月位）
    # 从大安(寅位, index=0)起正月，顺数至月
    # 正月=大安(0), 二月=留连(1), ...
    month_pos = (lunar_month - 1) % 6

    # 第二步: 月上起日 — 从月落位起初一，顺数至日
    day_pos = (month_pos + lunar_day - 1) % 6

    result = {
        "month_station": XIAOLIUREN_STATIONS[month_pos],
        "day_station": XIAOLIUREN_STATIONS[day_pos],
        "final_station": XIAOLIUREN_STATIONS[day_pos],
    }

    # 第三步: 日上起时 — 从日落位起子时，顺数至时辰
    if lunar_hour_zhi:
        hour_idx = SHICHEN_ORDER.index(lunar_hour_zhi)
        final_pos = (day_pos + hour_idx) % 6
        result["final_station"] = XIAOLIUREN_STATIONS[final_pos]

    result["attrs"] = XIAOLIUREN_ATTRS[result["final_station"]]

    # 掌诀间五行生克分析
    wx_relations = []
    stations = [
        ("月", result["month_station"]),
        ("日", result["day_station"]),
        ("时", result["final_station"]),
    ]
    wx_desc = {
        "同": "两两比和，力量叠加，加强最终掌诀的吉凶",
        "a生b": "前生后，前因推动后果，顺势而为",
        "a被b生": "后被前生，后劲充足，说明事情有后续支撑",
        "a克b": "前克后，前因压制后果，期间有阻力需要克服",
        "a被b克": "后被前克，后劲被前因制约，需调整方向",
    }
    for i in range(len(stations) - 1):
        a_label, a_name = stations[i]
        b_label, b_name = stations[i + 1]
        a_wx = XIAOLIUREN_ATTRS[a_name]["wu_xing"]
        b_wx = XIAOLIUREN_ATTRS[b_name]["wu_xing"]
        rel = wuxing_relation(a_wx, b_wx)
        wx_relations.append({
            "从": f"{a_label}上({a_name},{a_wx})",
            "到": f"{b_label}上({b_name},{b_wx})",
            "关系": rel,
            "解读": wx_desc.get(rel, ""),
        })
    result["五行生克"] = wx_relations

    return result


# =============================================================================
# 八卦基础（梅花易数 & 六爻 共用）
# =============================================================================

# 先天八卦数: 乾1 兑2 离3 震4 巽5 坎6 艮7 坤8
XIANTIAN_BAGUA = {
    1: "乾", 2: "兑", 3: "离", 4: "震",
    5: "巽", 6: "坎", 7: "艮", 8: "坤",
}

XIANTIAN_BAGUA_NUM = {name: num for num, name in XIANTIAN_BAGUA.items()}

# 八卦属性
BAGUA_ATTRS = {
    "乾": {"nature": "天", "family": "父", "wu_xing": "金", "direction": "西北", "body": "首"},
    "兑": {"nature": "泽", "family": "少女", "wu_xing": "金", "direction": "西", "body": "口"},
    "离": {"nature": "火", "family": "中女", "wu_xing": "火", "direction": "南", "body": "目"},
    "震": {"nature": "雷", "family": "长男", "wu_xing": "木", "direction": "东", "body": "足"},
    "巽": {"nature": "风", "family": "长女", "wu_xing": "木", "direction": "东南", "body": "股"},
    "坎": {"nature": "水", "family": "中男", "wu_xing": "水", "direction": "北", "body": "耳"},
    "艮": {"nature": "山", "family": "少男", "wu_xing": "土", "direction": "东北", "body": "手"},
    "坤": {"nature": "地", "family": "母", "wu_xing": "土", "direction": "西南", "body": "腹"},
}


def number_to_bagua(num: int) -> str:
    """先天八卦取数: 任意整数 → 八卦（除以8取余，余0为坤）."""
    r = num % 8
    if r == 0:
        r = 8
    return XIANTIAN_BAGUA[r]


def number_to_yao(num: int) -> int:
    """任意整数 → 动爻（除以6取余，余0为第6爻）."""
    r = num % 6
    if r == 0:
        r = 6
    return r
