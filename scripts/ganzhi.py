#!/usr/bin/env python3
"""推算 Skill — 干支历法模块"""

import sys; sys.stdout.reconfigure(encoding='utf-8')  # Windows GBK 修复

from datetime import datetime, date
from typing import Tuple, Dict, List, Optional
import os

# Allow running standalone or from parent
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from utils import (
    TIANGAN, DIZHI, SEXAGENARY,
    gan_index, zhi_index, ganzhi_to_index, index_to_ganzhi,
    split_ganzhi, join_ganzhi,
    TIANGAN_WUXING, DIZHI_WUXING, TIANGAN_YINYANG, DIZHI_CANGGAN,
    LICHUN_DATES, MONTH_START_JIEQI, JIEQI_TO_NONGLI_MONTH,
    YEAR_GAN_TO_MONTH1_GAN, DAY_GAN_TO_ZISHI_GAN,
    HOUR_TO_SHICHEN, SHICHEN_ORDER,
    month_ganzhi, hour_ganzhi,
    day_ganzhi_index, day_ganzhi,
    sexagenary_add, sexagenary_diff,
    wuxing_sheng, wuxing_ke, wuxing_sheng_wo, wuxing_ke_wo,
    wuxing_relation,
    NAYIN, NAYIN_WUXING,
    REFERENCE_DATE, REFERENCE_GANZHI_INDEX,
    dizhi_step,
    get_solar_term_date, get_lichun_date, get_solar_term_datetime,
)


# =============================================================================
# 排四柱
# =============================================================================

def get_year_ganzhi(dt: datetime) -> str:
    """
    返回年柱干支（以立春为界，精确到分钟）。
    节气当天如立春时刻晚于出生时间则仍属上一年。
    """
    y = dt.year
    lichun_dt = get_solar_term_datetime(y, "立春")
    if lichun_dt is not None and dt < lichun_dt:
        y -= 1
    elif lichun_dt is None:
        # 兜底：用旧逻辑（日期级近似）
        lichun = LICHUN_DATES.get(y, (2, 4))
        if dt.month < lichun[0] or (dt.month == lichun[0] and dt.day < lichun[1]):
            y -= 1
    # 年干支: 1864 = 甲子年 (index 0)
    idx = (y - 1864) % 60
    return SEXAGENARY[idx]


def lunar_year_for_date(dt: datetime) -> int:
    """返回农历年（以立春为界）."""
    y = dt.year
    m, d = dt.month, dt.day
    lichun = LICHUN_DATES.get(y, (2, 4))
    if m < lichun[0] or (m == lichun[0] and d < lichun[1]):
        return y - 1
    return y


def get_year_ganzhi_by_chunjie(dt: datetime) -> str:
    """返回年柱干支（以正月初一为界，紫微斗数使用）."""
    y = dt.year
    m, d = dt.month, dt.day
    cny = _CHINESE_NEW_YEAR.get(y, (2, 1))
    if m < cny[0] or (m == cny[0] and d < cny[1]):
        y -= 1
    idx = (y - 1864) % 60
    return SEXAGENARY[idx]


def get_month_ganzhi(year_gan: str, dt: datetime) -> str:
    """
    返回月柱干支（以节气为界）。
    节气对应月: 立春=寅月1, 惊蛰=卯月2, 清明=辰月3, 立夏=巳月4,
               芒种=午月5, 小暑=未月6, 立秋=申月7, 白露=酉月8,
               寒露=戌月9, 立冬=亥月10, 大雪=子月11, 小寒=丑月12
    """
    # 简化判断: 通过节气近似日期确定月份
    month_num = determine_nongli_month(dt)
    return month_ganzhi(year_gan, month_num)


def determine_nongli_month(dt: datetime) -> int:
    """
    根据公历日期时间（精确到分钟）和节气判断农历月（以节为界）。
    返回1-12: 1=寅月, 2=卯月, ..., 12=丑月
    使用天文算法动态计算节气时刻，无年份限制。
    """
    y = dt.year
    target = dt

    # 12个"节"及对应月号，使用精确到分钟的节气时刻
    jie_list = [
        (get_solar_term_datetime(y - 1, "小寒"), 12),   # y年1月小寒
        (get_solar_term_datetime(y, "立春"), 1),
        (get_solar_term_datetime(y, "惊蛰"), 2),
        (get_solar_term_datetime(y, "清明"), 3),
        (get_solar_term_datetime(y, "立夏"), 4),
        (get_solar_term_datetime(y, "芒种"), 5),
        (get_solar_term_datetime(y, "小暑"), 6),
        (get_solar_term_datetime(y, "立秋"), 7),
        (get_solar_term_datetime(y, "白露"), 8),
        (get_solar_term_datetime(y, "寒露"), 9),
        (get_solar_term_datetime(y, "立冬"), 10),
        (get_solar_term_datetime(y, "大雪"), 11),
        (get_solar_term_datetime(y, "小寒"), 12),        # y+1年1月小寒
    ]

    # 过滤掉 None（天文计算失败），按时间排序
    jie_list = [(d, m) for d, m in jie_list if d is not None]
    jie_list.sort()

    for i, (d, month_num) in enumerate(jie_list):
        if target < d:
            if i == 0:
                return 11  # 大雪之后 = 子月11
            return jie_list[i - 1][1]

    return 12


# =============================================================================
# 农历日转换（公历 → 农历日）
# =============================================================================

# 农历正月初一对应的公历日期 (month, day)
# 数据来源: 香港天文台 + 万年历交叉验证, 覆盖 1900-2100
_CHINESE_NEW_YEAR = {
    1900: (1, 31), 1901: (2, 19), 1902: (2, 8), 1903: (1, 29),
    1904: (2, 16), 1905: (2, 4), 1906: (1, 25), 1907: (2, 13),
    1908: (2, 2), 1909: (1, 22), 1910: (2, 10), 1911: (1, 30),
    1912: (2, 18), 1913: (2, 6), 1914: (1, 26), 1915: (2, 14),
    1916: (2, 3), 1917: (1, 23), 1918: (2, 11), 1919: (2, 1),
    1920: (2, 20), 1921: (2, 8), 1922: (1, 28), 1923: (2, 16),
    1924: (2, 5), 1925: (1, 24), 1926: (2, 13), 1927: (2, 2),
    1928: (1, 23), 1929: (2, 10), 1930: (1, 30), 1931: (2, 17),
    1932: (2, 6), 1933: (1, 26), 1934: (2, 14), 1935: (2, 4),
    1936: (1, 24), 1937: (2, 11), 1938: (1, 31), 1939: (2, 19),
    1940: (2, 8), 1941: (1, 27), 1942: (2, 15), 1943: (2, 5),
    1944: (1, 25), 1945: (2, 13), 1946: (2, 2), 1947: (1, 22),
    1948: (2, 10), 1949: (1, 29), 1950: (2, 17), 1951: (2, 6),
    1952: (1, 27), 1953: (2, 14), 1954: (2, 3), 1955: (1, 24),
    1956: (2, 12), 1957: (1, 31), 1958: (2, 18), 1959: (2, 8),
    1960: (1, 28), 1961: (2, 15), 1962: (2, 5), 1963: (1, 25),
    1964: (2, 13), 1965: (2, 2), 1966: (1, 21), 1967: (2, 9),
    1968: (1, 30), 1969: (2, 17), 1970: (2, 6), 1971: (1, 27),
    1972: (2, 15), 1973: (2, 3), 1974: (1, 23), 1975: (2, 11),
    1976: (1, 31), 1977: (2, 18), 1978: (2, 7), 1979: (1, 28),
    1980: (2, 16), 1981: (2, 5), 1982: (1, 25), 1983: (2, 13),
    1984: (2, 2), 1985: (2, 20), 1986: (2, 9), 1987: (1, 29),
    1988: (2, 17), 1989: (2, 6), 1990: (1, 27), 1991: (2, 15),
    1992: (2, 4), 1993: (1, 23), 1994: (2, 10), 1995: (1, 31),
    1996: (2, 19), 1997: (2, 7), 1998: (1, 28), 1999: (2, 16),
    2000: (2, 5), 2001: (1, 24), 2002: (2, 12), 2003: (2, 1),
    2004: (1, 22), 2005: (2, 9), 2006: (1, 29), 2007: (2, 18),
    2008: (2, 7), 2009: (1, 26), 2010: (2, 14), 2011: (2, 3),
    2012: (1, 23), 2013: (2, 10), 2014: (1, 31), 2015: (2, 19),
    2016: (2, 8), 2017: (1, 28), 2018: (2, 16), 2019: (2, 5),
    2020: (1, 25), 2021: (2, 12), 2022: (2, 1), 2023: (1, 22),
    2024: (2, 10), 2025: (1, 29), 2026: (2, 17), 2027: (2, 6),
    2028: (1, 26), 2029: (2, 13), 2030: (2, 3), 2031: (1, 23),
    2032: (2, 11), 2033: (1, 31), 2034: (2, 19), 2035: (2, 8),
    2036: (1, 28), 2037: (2, 15), 2038: (2, 4), 2039: (1, 24),
    2040: (2, 12), 2041: (2, 1), 2042: (1, 22), 2043: (2, 10),
    2044: (1, 30), 2045: (2, 17), 2046: (2, 6), 2047: (1, 26),
    2048: (2, 14), 2049: (2, 2), 2050: (1, 23), 2051: (2, 11),
    2052: (2, 1), 2053: (2, 19), 2054: (2, 8), 2055: (1, 28),
    2056: (2, 15), 2057: (2, 4), 2058: (1, 24), 2059: (2, 12),
    2060: (2, 2), 2061: (1, 21), 2062: (2, 9), 2063: (1, 29),
    2064: (2, 17), 2065: (2, 5), 2066: (1, 26), 2067: (2, 14),
    2068: (2, 3), 2069: (1, 23), 2070: (2, 11), 2071: (1, 31),
    2072: (2, 19), 2073: (2, 7), 2074: (1, 27), 2075: (2, 15),
    2076: (2, 5), 2077: (1, 24), 2078: (2, 12), 2079: (2, 2),
    2080: (1, 22), 2081: (2, 9), 2082: (1, 29), 2083: (2, 17),
    2084: (2, 6), 2085: (1, 26), 2086: (2, 14), 2087: (2, 3),
    2088: (1, 24), 2089: (2, 10), 2090: (1, 30), 2091: (2, 18),
    2092: (2, 7), 2093: (1, 27), 2094: (2, 15), 2095: (2, 5),
    2096: (1, 25), 2097: (2, 12), 2098: (2, 1), 2099: (1, 21),
    2100: (2, 9),
}

# 农历月长度数据（由天文朔日计算，替换固定交替模式）
# {农历年(int): {"lengths": [29,30,...], "leap_after": None|int}}
_LUNAR_DATA = {}


def _init_lunar_data():
    """
    使用天文朔日计算精确的农历月长度。
    在首次调用 determine_nongli_day / determine_calendar_lunar_month 时懒初始化。
    """
    global _LUNAR_DATA
    if _LUNAR_DATA:
        return

    from utils import _new_moon_date, _jd_from_date, _jd_to_date, get_solar_term_date
    from utils import math as _math

    zhongqi_names = [
        "冬至", "大寒", "雨水", "春分", "谷雨", "小满",
        "夏至", "大暑", "处暑", "秋分", "霜降", "小雪",
    ]

    years = sorted(_CHINESE_NEW_YEAR.keys())

    for idx, year in enumerate(years):
        cny_m, cny_d = _CHINESE_NEW_YEAR[year]
        cny_date = date(year, cny_m, cny_d)

        # 找最接近正月初一的天文朔日 k 值
        cny_jd = _jd_from_date(datetime(year, cny_m, cny_d, 12, 0, 0))
        k_approx = int((cny_jd - 2451550.1) / 29.530588853)
        best_k = k_approx
        best_diff = 999
        for dk in range(-4, 5):
            nm = _new_moon_date(k_approx + dk)
            diff = abs((nm - cny_date).days)
            if diff < best_diff:
                best_diff = diff
                best_k = k_approx + dk

        # 以正月初一表值为锚点，用朔日差得出各月长度
        next_year = year + 1
        next_cny = None
        if next_year in _CHINESE_NEW_YEAR:
            ncy = _CHINESE_NEW_YEAR[next_year]
            next_cny = date(next_year, ncy[0], ncy[1])

        lengths = []
        leap_after = None
        month_num = 1
        prev_nm = cny_date

        for mi in range(1, 15):
            next_nm = _new_moon_date(best_k + mi)
            month_len = (next_nm - prev_nm).days
            # 容错: 朔日计算偶尔可能偏差导致极端值
            if month_len < 28:
                month_len = 29
            if month_len > 31:
                month_len = 30

            # 中气检测（闰月判断）
            has_zq = False
            for zq_name in zhongqi_names:
                for dy in [-1, 0, 1]:
                    zq_d = get_solar_term_date(prev_nm.year + dy, zq_name)
                    if prev_nm <= zq_d < next_nm:
                        has_zq = True
                        break
                if has_zq:
                    break

            if not has_zq and len(lengths) > 0 and len(lengths) < 12:
                leap_after = month_num - 1
                lengths.append(month_len)
            else:
                lengths.append(month_len)
                month_num += 1

            prev_nm = next_nm
            if next_cny and next_nm >= next_cny:
                break

        # 补齐不足12月的数据
        while len(lengths) < 12:
            last_len = lengths[-1] if lengths else 30
            lengths.append(59 - last_len)  # 互补一个月
        if len(lengths) > 13:
            lengths = lengths[:13]

        _LUNAR_DATA[year] = {
            "lengths": lengths,
            "leap_after": leap_after,
        }


def _get_lunar_month_lengths(lunar_year: int) -> list:
    """获取某农历年各月长度（含闰月，若有）."""
    _init_lunar_data()
    d = _LUNAR_DATA.get(lunar_year)
    if d:
        return d["lengths"]
    # 回退
    return [30, 29, 30, 29, 30, 29, 30, 29, 30, 29, 30, 29]


def _get_lunar_leap(lunar_year: int) -> int:
    """获取闰月位置（闰几月后），无闰月返回 None."""
    _init_lunar_data()
    d = _LUNAR_DATA.get(lunar_year)
    if d:
        return d["leap_after"]
    return None


def determine_nongli_day(dt: datetime) -> int:
    """
    根据公历日期推算农历日（1-30）。

    算法: 通过天文朔日计算各月精确长度，从正月初一逐月累加。
    精度: 0天误差（日历日级别精确）。

    返回: 农历日（1-30）
    """
    y = dt.year
    m, d = dt.month, dt.day

    cny = _CHINESE_NEW_YEAR.get(y)
    if cny is None:
        return d

    cny_m, cny_d = cny
    cny_date = date(y, cny_m, cny_d)
    target_date = date(y, m, d)

    # 确定农历年
    if target_date < cny_date:
        lunar_year = y - 1
        prev_cny = _CHINESE_NEW_YEAR.get(lunar_year)
        if prev_cny is None:
            return d
        cny_date = date(lunar_year, prev_cny[0], prev_cny[1])
    else:
        lunar_year = y

    elapsed = (target_date - cny_date).days
    month_lengths = _get_lunar_month_lengths(lunar_year)

    for month_len in month_lengths:
        if elapsed < month_len:
            return elapsed + 1
        elapsed -= month_len

    # 超12/13月仍溢出：返回剩余天数+1
    return min(elapsed + 1, 30) if elapsed >= 0 else d


def determine_calendar_lunar_month(dt: datetime) -> int:
    """
    根据公历日期确定日历农历月（以正月初一为界，紫微斗数安命宫使用）。
    返回 1-12: 1=正月, 2=二月, ..., 12=腊月
    与 determine_nongli_month 不同：后者以节气为界（八字月柱用）。
    """
    y = dt.year
    target = dt.date() if isinstance(dt, datetime) else dt
    if isinstance(target, datetime):
        target = target.date()

    cny = _CHINESE_NEW_YEAR.get(y)
    if cny is None:
        return dt.month if isinstance(dt, datetime) else target.month

    cny_date = date(y, cny[0], cny[1])

    if target < cny_date:
        lunar_year = y - 1
        prev_cny = _CHINESE_NEW_YEAR.get(lunar_year)
        if prev_cny is None:
            return 12
        cny_date = date(lunar_year, prev_cny[0], prev_cny[1])
    else:
        lunar_year = y

    elapsed = (target - cny_date).days
    month_lengths = _get_lunar_month_lengths(lunar_year)
    leap_after = _get_lunar_leap(lunar_year)

    month_num = 1
    for idx, month_len in enumerate(month_lengths):
        if elapsed < month_len:
            return month_num
        elapsed -= month_len
        # 闰月处理：若下一项是闰月则不递增月号
        if leap_after is not None and idx == leap_after - 1:
            pass  # 下个entry是闰月，月号保持不变
        else:
            month_num += 1

    return 12


def get_hour_ganzhi(day_gan: str, hour: int) -> str:
    """返回时柱干支."""
    shichen = HOUR_TO_SHICHEN.get(hour, "子")
    return hour_ganzhi(day_gan, shichen)


def pai_sizhu(year: int, month: int, day: int, hour: int) -> dict:
    """
    排八字四柱。
    返回: {年柱, 月柱, 日柱, 时柱, 年干, 年支, ...}
    """
    # 晚子时(23:00-23:59): 日柱按传统规则属次日
    # 但年柱和月柱必须用出生原始时间，不能因为子时换日而移动
    # 否则跨节气/立春的23时生人年柱月柱会错
    birth_dt = datetime(year, month, day, hour)
    if hour == 23:
        from datetime import timedelta
        adj = birth_dt + timedelta(days=1)
        ri = adj.date()
    else:
        ri = date(year, month, day)

    # 年柱（以立春为界，用出生原始时间）
    nian_zhu = get_year_ganzhi(birth_dt)
    nian_gan, nian_zhi = split_ganzhi(nian_zhu)

    # 月柱（以节气为界，用出生原始时间，精确到分钟）
    yue_num = determine_nongli_month(birth_dt)
    yue_zhu = month_ganzhi(nian_gan, yue_num)
    yue_gan, yue_zhi = split_ganzhi(yue_zhu)

    # 日柱（子时换日后用修正后的日期）
    ri_zhu = day_ganzhi(ri)
    ri_gan, ri_zhi = split_ganzhi(ri_zhu)

    # 时柱（时柱用修正后的日干排五鼠遁，时辰仍是23点=子时）
    shi_zhu = get_hour_ganzhi(ri_gan, hour)
    shi_gan, shi_zhi = split_ganzhi(shi_zhu)

    # 纳音
    nayin_list = {
        "年": NAYIN[nian_zhu],
        "月": NAYIN[yue_zhu],
        "日": NAYIN[ri_zhu],
        "时": NAYIN[shi_zhu],
    }

    # 地支藏干
    canggan = {
        "年": DIZHI_CANGGAN[nian_zhi],
        "月": DIZHI_CANGGAN[yue_zhi],
        "日": DIZHI_CANGGAN[ri_zhi],
        "时": DIZHI_CANGGAN[shi_zhi],
    }

    return {
        "年柱": nian_zhu, "月柱": yue_zhu, "日柱": ri_zhu, "时柱": shi_zhu,
        "年干": nian_gan, "年支": nian_zhi,
        "月干": yue_gan, "月支": yue_zhi,
        "日干": ri_gan, "日支": ri_zhi,
        "时干": shi_gan, "时支": shi_zhi,
        "纳音": nayin_list,
        "藏干": canggan,
        "日主五行": TIANGAN_WUXING[ri_gan],
    }


# =============================================================================
# 十神
# =============================================================================

# 十神关系（以日干为"我"）
# 同我且阴阳同 = 比肩, 同我且阴阳异 = 劫财
# 生我且阴阳同 = 偏印, 生我且阴阳异 = 正印
# 我生且阴阳同 = 食神, 我生且阴阳异 = 伤官
# 克我且阴阳同 = 七杀, 克我且阴阳异 = 正官
# 我克且阴阳同 = 偏财, 我克且阴阳异 = 正财

def get_shishen(day_gan: str, other_gan: str) -> str:
    """返回日干对另一个天干的十神关系."""
    day_wx = TIANGAN_WUXING[day_gan]
    other_wx = TIANGAN_WUXING[other_gan]

    day_yy = TIANGAN_YINYANG[day_gan]
    other_yy = TIANGAN_YINYANG[other_gan]
    tong_yinyang = (day_yy == other_yy)

    if day_wx == other_wx:
        return "比肩" if tong_yinyang else "劫财"

    rel = wuxing_relation(day_wx, other_wx)

    if rel == "a被b生":  # other生我
        return "偏印" if tong_yinyang else "正印"
    elif rel == "a生b":  # 我生other
        return "食神" if tong_yinyang else "伤官"
    elif rel == "a被b克":  # other克我
        return "七杀" if tong_yinyang else "正官"
    elif rel == "a克b":  # 我克other
        return "偏财" if tong_yinyang else "正财"

    return "未知"


def pai_shishen(sizhu: dict) -> dict:
    """根据四柱排出所有天干的十神."""
    day_gan = sizhu["日干"]

    result = {}
    for pillar in ["年", "月", "日", "时"]:
        gan = sizhu[f"{pillar}干"]
        shen = get_shishen(day_gan, gan)
        result[pillar] = shen

    # 地支藏干的十神
    canggan_shishen = {}
    for pillar in ["年", "月", "日", "时"]:
        cang = sizhu["藏干"][pillar]
        canggan_shishen[pillar] = {g: get_shishen(day_gan, g) for g in cang}

    result["藏干十神"] = canggan_shishen
    return result


# =============================================================================
# 大运推算
# =============================================================================

def pai_dayun(nian_gan: str, nian_zhi: str, yue_zhi: str,
              gender: str, birth_dt: datetime, ri_gan: str = "") -> dict:
    """
    排大运。
    gender: '男' or '女'

    规则:
    - 阳年(年干阳)男 + 阴年(年干阴)女 → 顺排（月柱之后顺推）
    - 阴年男 + 阳年女 → 逆排（月柱之前逆推）

    起运岁数: 从出生日到下一个（或上一个）"节"的天数 ÷ 3
    """
    nian_yinyang = TIANGAN_YINYANG[nian_gan]

    is_shun = False
    if nian_yinyang == "阳" and gender == "男":
        is_shun = True
    elif nian_yinyang == "阴" and gender == "女":
        is_shun = True

    # 计算起运岁数（精确到月: 3天=1岁, 余1天=4个月, 余2天=8个月）
    qiyun_result = _calc_qiyun_age(birth_dt, is_shun)
    qiyun_age = qiyun_result["岁数"]
    qiyun_months = qiyun_result["月数"]

    # 排大运列表
    yue_ganzhi = month_ganzhi(nian_gan, determine_nongli_month(birth_dt))

    dayun_list = []
    for i in range(8):  # 排8步大运
        if is_shun:
            gz = sexagenary_add(yue_ganzhi, i + 1)
        else:
            gz = sexagenary_add(yue_ganzhi, -(i + 1))

        start_age = qiyun_age + i * 10
        dy_gan, dy_zhi = split_ganzhi(gz)
        dy_gan_shishen = get_shishen(ri_gan, dy_gan) if ri_gan else ""
        dayun_list.append({
            "干支": gz,
            "年龄": f"{start_age}-{start_age + 9}岁",
            "起运": start_age,
            "大运十神": dy_gan_shishen,
        })

    return {
        "顺逆": "顺排" if is_shun else "逆排",
        "起运岁数": qiyun_age,
        "起运月数": qiyun_months,
        "起运": qiyun_result["文字"],
        "大运列表": dayun_list,
    }


def _calc_qiyun_age(birth_dt: datetime, is_shun: bool) -> dict:
    """
    计算起运岁数（精确到月）。
    标准: 3天 = 1岁, 余1天 = 4个月, 余2天 = 8个月。
    使用精确节气时刻计算出生到最近"节"的天数，精确到日期级。
    返回: {"岁数": int, "月数": int, "文字": "X岁Y个月"}
    """
    from utils import get_solar_term_datetime
    y = birth_dt.year

    # 所有"节"名（顺序）
    jie_names = ["小寒","立春","惊蛰","清明","立夏","芒种",
                 "小暑","立秋","白露","寒露","立冬","大雪"]

    # 收集本年、上年、下年的节时刻（精确到分钟）
    all_jie = []
    for name in jie_names:
        dt_jie = get_solar_term_datetime(y, name)
        if dt_jie is not None:
            all_jie.append(dt_jie)
    for name in ["大雪", "小寒"]:
        dt_jie = get_solar_term_datetime(y - 1, name)
        if dt_jie is not None:
            all_jie.append(dt_jie)
    dt_jie = get_solar_term_datetime(y, "小寒")  # 下年小寒
    if dt_jie is not None:
        all_jie.append(dt_jie)
    all_jie = sorted(set(all_jie))

    days = 0
    if is_shun:
        for d in all_jie:
            if d > birth_dt:
                days = (d - birth_dt).days
                break
    else:
        for d in reversed(all_jie):
            if d < birth_dt:
                days = (birth_dt - d).days
                break

    # 3天 = 1岁 = 12个月 → 1天 = 4个月
    total_months = days * 4
    years = total_months // 12
    months = total_months % 12
    # 起运岁数可为0岁X个月（出生在节气附近）
    if years == 0:
        text = f"{months}个月"
    elif months > 0:
        text = f"{years}岁{months}个月"
    else:
        text = f"{years}岁"
    return {
        "岁数": max(years, 0),
        "月数": months,
        "文字": text,
    }


# =============================================================================
# 流年（当前年运势）
# =============================================================================

def get_liunian(year: int, month: int = 6, day: int = 15) -> str:
    """
    返回某年的流年干支（以立春为界，按年柱规则）。

    以公历 6月15日 为参考点（立春后），避免年初立春前日期偏差。
    需要年初日期时请传入具体月日。
    """
    dt = datetime(year, month, day)
    return get_year_ganzhi(dt)


# =============================================================================
# 神煞（简化列表 — 常用神煞）
# =============================================================================

# 天乙贵人: 甲戊庚=丑未, 乙己=子申, 丙丁=酉亥, 壬癸=卯巳, 辛=午寅
TIANYI_GUIREN = {
    "甲": ["丑", "未"], "戊": ["丑", "未"], "庚": ["丑", "未"],
    "乙": ["子", "申"], "己": ["子", "申"],
    "丙": ["酉", "亥"], "丁": ["酉", "亥"],
    "壬": ["卯", "巳"], "癸": ["卯", "巳"],
    "辛": ["午", "寅"],
}

# 文昌: 甲=巳, 乙=午, 丙=申, 丁=酉, 戊=申, 己=酉, 庚=亥, 辛=子, 壬=寅, 癸=卯
WENCHANG = {
    "甲": "巳", "乙": "午", "丙": "申", "丁": "酉", "戊": "申",
    "己": "酉", "庚": "亥", "辛": "子", "壬": "寅", "癸": "卯",
}

# 桃花（咸池）: 申子辰在酉, 亥卯未在子, 寅午戌在卯, 巳酉丑在午
TAOHUA = {
    frozenset(["申","子","辰"]): "酉",
    frozenset(["亥","卯","未"]): "子",
    frozenset(["寅","午","戌"]): "卯",
    frozenset(["巳","酉","丑"]): "午",
}

# 驿马: 申子辰在寅, 亥卯未在巳, 寅午戌在申, 巳酉丑在亥（三合局长生位之冲）
YIMA = {
    frozenset(["申","子","辰"]): "寅",
    frozenset(["亥","卯","未"]): "巳",
    frozenset(["寅","午","戌"]): "申",
    frozenset(["巳","酉","丑"]): "亥",
}

# 月德贵人: 寅午戌月见丙, 申子辰月见壬, 亥卯未月见庚, 巳酉丑月见甲
YUEDE = {
    frozenset(["申","子","辰"]): "壬",
    frozenset(["亥","卯","未"]): "庚",
    frozenset(["寅","午","戌"]): "丙",
    frozenset(["巳","酉","丑"]): "甲",
}

# 天德贵人: 正月丁、二月坤(申)、三月壬、四月辛、五月乾(亥)、六月甲、
#            七月癸、八月艮(寅)、九月丙、十月乙、十一月巽(巳)、十二月庚
TIANDE = {
    1: "丁", 2: "申", 3: "壬", 4: "辛", 5: "亥", 6: "甲",
    7: "癸", 8: "寅", 9: "丙", 10: "乙", 11: "巳", 12: "庚",
}

# 将星: 三合局帝旺位 — 申子辰在子, 亥卯未在卯, 寅午戌在午, 巳酉丑在酉
JIANGXING = {
    frozenset(["申","子","辰"]): "子",
    frozenset(["亥","卯","未"]): "卯",
    frozenset(["寅","午","戌"]): "午",
    frozenset(["巳","酉","丑"]): "酉",
}

# 华盖: 三合局墓库位 — 申子辰在辰, 亥卯未在未, 寅午戌在戌, 巳酉丑在丑
HUAGAI = {
    frozenset(["申","子","辰"]): "辰",
    frozenset(["亥","卯","未"]): "未",
    frozenset(["寅","午","戌"]): "戌",
    frozenset(["巳","酉","丑"]): "丑",
}

# 亡神: 申子辰在亥, 亥卯未在寅, 寅午戌在巳, 巳酉丑在申
WANGSHEN = {
    frozenset(["申","子","辰"]): "亥",
    frozenset(["亥","卯","未"]): "寅",
    frozenset(["寅","午","戌"]): "巳",
    frozenset(["巳","酉","丑"]): "申",
}

# 劫煞: 申子辰在巳, 亥卯未在申, 寅午戌在亥, 巳酉丑在寅
JIESHA = {
    frozenset(["申","子","辰"]): "巳",
    frozenset(["亥","卯","未"]): "申",
    frozenset(["寅","午","戌"]): "亥",
    frozenset(["巳","酉","丑"]): "寅",
}

# 学堂: 甲巳, 乙午, 丙申, 丁酉, 戊巳, 己午, 庚亥, 辛子, 壬寅, 癸卯
XUETANG = {
    "甲": "巳", "乙": "午", "丙": "申", "丁": "酉", "戊": "巳",
    "己": "午", "庚": "亥", "辛": "子", "壬": "寅", "癸": "卯",
}

# 金舆: 甲辰, 乙巳, 丙戊申, 丁己子, 庚寅, 辛丑, 壬亥, 癸卯
JINYU = {
    "甲": "辰", "乙": "巳", "丙": "申", "丁": "子", "戊": "申",
    "己": "子", "庚": "寅", "辛": "丑", "壬": "亥", "癸": "卯",
}

# 羊刃: 甲=卯, 乙=寅, 丙=午, 丁=巳, 戊=午, 己=巳, 庚=酉, 辛=申, 壬=子, 癸=亥
YANGREN = {
    "甲": "卯", "乙": "寅", "丙": "午", "丁": "巳", "戊": "午",
    "己": "巳", "庚": "酉", "辛": "申", "壬": "子", "癸": "亥",
}


def find_shensha(sizhu: dict, gender: str = "未知") -> dict:
    """查找四柱中的神煞."""
    nian_gan = sizhu["年干"]
    nian_zhi = sizhu["年支"]
    ri_gan = sizhu["日干"]
    ri_zhi = sizhu["日支"]

    result = []
    seen = set()  # 去重: (神煞名, 位置)

    def _add(name: str, position: str, meaning: str):
        key = (name, position)
        if key not in seen:
            seen.add(key)
            result.append({"神煞": name, "位置": position, "含义": meaning})

    # 天乙贵人（日干查+年干查）
    for g, label in [(ri_gan, "日干"), (nian_gan, "年干")]:
        if g in TIANYI_GUIREN:
            guiren = TIANYI_GUIREN[g]
            for p in ["年", "月", "日", "时"]:
                if sizhu[f"{p}支"] in guiren:
                    _add("天乙贵人", f"{p}支({label})", "逢凶化吉，贵人相助")

    # 文昌（日干查）
    if ri_gan in WENCHANG:
        wc = WENCHANG[ri_gan]
        for p in ["年", "月", "日", "时"]:
            if sizhu[f"{p}支"] == wc:
                _add("文昌星", f"{p}支", "文采出众，学业有成")

    for sanhe_set, taohua_zhi in TAOHUA.items():
        if nian_zhi in sanhe_set or ri_zhi in sanhe_set:
            for p in ["年", "月", "日", "时"]:
                if sizhu[f"{p}支"] == taohua_zhi:
                    _add("桃花（咸池）", f"{p}支", "异性缘佳，人缘好，也需防情色之困")

    for sanhe_set, yima_zhi in YIMA.items():
        if nian_zhi in sanhe_set or ri_zhi in sanhe_set:
            for p in ["年", "月", "日", "时"]:
                if sizhu[f"{p}支"] == yima_zhi:
                    _add("驿马", f"{p}支", "奔波劳碌，多走动变动")

    # 羊刃（日干查）
    if ri_gan in YANGREN:
        yr = YANGREN[ri_gan]
        for p in ["年", "月", "日", "时"]:
            if sizhu[f"{p}支"] == yr:
                _add("羊刃", f"{p}支", "刚强果断，但须防冲动伤人")

    # === 新增神煞 ===

    # 月德贵人（月支三合局查天干）
    yue_zhi = sizhu["月支"]
    for sanhe_set, de_gan in YUEDE.items():
        if yue_zhi in sanhe_set:
            for p in ["年", "月", "日", "时"]:
                if sizhu[f"{p}干"] == de_gan:
                    _add("月德贵人", f"{p}干{p}支", "逢凶化吉，福泽深厚，女性尤吉")

    # 天德贵人（农历月查）
    # 月支→农历月转换: 寅=1,卯=2,...,丑=12
    nongli_month = DIZHI.index(yue_zhi) + 1
    if nongli_month in TIANDE:
        tian_de = TIANDE[nongli_month]
        if tian_de in DIZHI:
            for p in ["年", "月", "日", "时"]:
                if sizhu[f"{p}支"] == tian_de:
                    _add("天德贵人", f"{p}支", "最大的吉神之一，能解诸凶，福报深厚")
        else:
            for p in ["年", "月", "日", "时"]:
                if sizhu[f"{p}干"] == tian_de:
                    _add("天德贵人", f"{p}干", "最大的吉神之一，能解诸凶，福报深厚")

    # 将星（年支或日支三合局帝旺位）
    for sanhe_set, jiang_zhi in JIANGXING.items():
        if nian_zhi in sanhe_set or ri_zhi in sanhe_set:
            for p in ["年", "月", "日", "时"]:
                if sizhu[f"{p}支"] == jiang_zhi:
                    _add("将星", f"{p}支", "领导才能，权威决断，适合管理岗位")

    # 华盖（年支或日支三合局墓库位）
    for sanhe_set, hg_zhi in HUAGAI.items():
        if nian_zhi in sanhe_set or ri_zhi in sanhe_set:
            for p in ["年", "月", "日", "时"]:
                if sizhu[f"{p}支"] == hg_zhi:
                    _add("华盖", f"{p}支", "孤独聪慧，有艺术/宗教/学术天赋，宜独处思考")

    # 亡神（年支三合局查）
    for sanhe_set, ws_zhi in WANGSHEN.items():
        if nian_zhi in sanhe_set:
            for p in ["年", "月", "日", "时"]:
                if sizhu[f"{p}支"] == ws_zhi:
                    _add("亡神", f"{p}支", "心神不定，多思多虑，但利于策划谋略")

    # 劫煞（年支三合局查）
    for sanhe_set, js_zhi in JIESHA.items():
        if nian_zhi in sanhe_set:
            for p in ["年", "月", "日", "时"]:
                if sizhu[f"{p}支"] == js_zhi:
                    _add("劫煞", f"{p}支", "意外波折，但劫煞带贵人反主机遇从危机中来")

    # 学堂（日干查）
    if ri_gan in XUETANG:
        xt = XUETANG[ri_gan]
        for p in ["年", "月", "日", "时"]:
            if sizhu[f"{p}支"] == xt:
                _add("学堂", f"{p}支", "学业有成，聪明好学，利于考试升学")

    # 金舆（日干查）
    if ri_gan in JINYU:
        jy = JINYU[ri_gan]
        for p in ["年", "月", "日", "时"]:
            if sizhu[f"{p}支"] == jy:
                _add("金舆", f"{p}支", "富格标志，得物质享受，宜从商")

    return result


# =============================================================================
# 五行统计
# =============================================================================

def count_wuxing(sizhu: dict) -> dict:
    """
    统计四柱中五行的分布。
    规则: 天干权重2, 地支本气权重2, 地支藏干(含本气之外的藏干)权重1。
    返回: {"分布": {五行: 权重}, "最强": str, "最弱": str, "分析": str}
    """
    counts = {"木": 0, "火": 0, "土": 0, "金": 0, "水": 0}

    # 天干 (权重2)
    for pillar in ["年", "月", "日", "时"]:
        gan = sizhu[f"{pillar}干"]
        wx = TIANGAN_WUXING[gan]
        counts[wx] += 2

    # 地支本气 (权重2)
    for pillar in ["年", "月", "日", "时"]:
        zhi = sizhu[f"{pillar}支"]
        wx = DIZHI_WUXING[zhi]
        counts[wx] += 2

    # 地支藏干 (权重1: 本气已在地支部分计入权重2, 此处中气/余气各权重1;
    # 为简化，全部藏干(含本气)权重1，本气重复计算是合理的因为地支本气单独计了2)
    for pillar in ["年", "月", "日", "时"]:
        for cg in sizhu["藏干"][pillar]:
            wx = TIANGAN_WUXING[cg]
            counts[wx] += 1

    total = sum(counts.values())
    distribution = {k: v for k, v in counts.items()}

    # 排序
    sorted_wx = sorted(distribution.items(), key=lambda x: -x[1])
    strongest = sorted_wx[0][0]
    weakest = sorted_wx[-1][0]

    # 分析文本
    pct_list = []
    for wx, w in sorted_wx:
        pct = round(w / total * 100, 1) if total > 0 else 0
        pct_list.append(f"{wx}{w}({pct}%)")
    dist_str = " > ".join(f"{wx}({w})" for wx, w in sorted_wx)

    day_gan = sizhu["日干"]
    ri_wx = TIANGAN_WUXING[day_gan]
    ri_rank = sorted_wx.index(next(x for x in sorted_wx if x[0] == ri_wx)) + 1

    analysis = f"日主{day_gan}属{ri_wx}(排名第{ri_rank}/5), "
    if ri_rank <= 2:
        analysis += f"五行较为均衡有力。最强{strongest}, 最弱{weakest}。"
    else:
        analysis += f"日主五行偏弱, 宜大运流年补{ri_wx}。最强{strongest}, 最弱{weakest}。"

    return {
        "分布": distribution,
        "排序": dist_str,
        "最强": strongest,
        "最弱": weakest,
        "分析": analysis,
    }


# =============================================================================
# 补充神煞
# =============================================================================

def _get_extra_shensha(sizhu: dict) -> dict:
    """
    计算补充神煞: 红鸾, 天喜, 禄神, 灾煞, 孤辰, 寡宿, 阴阳差错, 魁罡, 金舆。
    返回: {神煞名: [{"位置": str, "含义": str}, ...]}
    """
    nian_zhi = sizhu["年支"]
    ri_gan = sizhu["日干"]
    ri_zhi = sizhu["日支"]
    ri_zhu = sizhu["日柱"]

    result = {}

    # 红鸾: 按年支查 — 子上起丑, 丑上起寅, 寅上起卯, ..., 亥上起子
    # 公式: 红鸾 = (index_of_year_zhi + 1) % 12 → 地支
    DIZHI_LIST = ["子","丑","寅","卯","辰","巳","午","未","申","酉","戌","亥"]
    nian_zhi_idx = DIZHI_LIST.index(nian_zhi)
    hongluan_idx = (nian_zhi_idx + 1) % 12
    hongluan_zhi = DIZHI_LIST[hongluan_idx]
    hongluan_positions = []
    for p in ["年","月","日","时"]:
        if sizhu[f"{p}支"] == hongluan_zhi:
            hongluan_positions.append(p)
    if hongluan_positions:
        pos_str = "、".join(hongluan_positions)
        result["红鸾"] = [{"位置": f"{pos_str}支", "地支": hongluan_zhi,
                          "含义": "桃花喜气，主婚恋、添丁、喜庆之事"}]
    else:
        result["红鸾"] = [{"位置": "无", "地支": hongluan_zhi,
                          "含义": f"红鸾在{hongluan_zhi}方，逢{hongluan_zhi}年/大运出现"}]

    # 天喜: 红鸾的对冲位 (红鸾+6)%12
    tianxi_idx = (hongluan_idx + 6) % 12
    tianxi_zhi = DIZHI_LIST[tianxi_idx]
    tianxi_positions = []
    for p in ["年","月","日","时"]:
        if sizhu[f"{p}支"] == tianxi_zhi:
            tianxi_positions.append(p)
    if tianxi_positions:
        pos_str = "、".join(tianxi_positions)
        result["天喜"] = [{"位置": f"{pos_str}支", "地支": tianxi_zhi,
                          "含义": "大喜之事，婚嫁、升迁、得子之喜"}]
    else:
        result["天喜"] = [{"位置": "无", "地支": tianxi_zhi,
                          "含义": f"天喜在{tianxi_zhi}方，逢{tianxi_zhi}年/大运出现"}]

    # 禄神: 按日干查 — 甲禄寅, 乙禄卯, 丙戊禄巳, 丁己禄午, 庚禄申, 辛禄酉, 壬禄亥, 癸禄子
    LUSHEN = {"甲":"寅","乙":"卯","丙":"巳","丁":"午","戊":"巳",
              "己":"午","庚":"申","辛":"酉","壬":"亥","癸":"子"}
    lushen_zhi = LUSHEN.get(ri_gan, "")
    lushen_found = []
    for p in ["年","月","日","时"]:
        if sizhu[f"{p}支"] == lushen_zhi:
            lushen_found.append(p)
    if lushen_found:
        result["禄神"] = [{"位置": "、".join(f"{p}支" for p in lushen_found),
                          "地支": lushen_zhi,
                          "含义": "福禄寿喜，衣食无忧，身体健康，利事业财运"}]
    else:
        result["禄神"] = [{"位置": "无", "地支": lushen_zhi,
                          "含义": f"禄在{lushen_zhi}方，逢{lushen_zhi}年/运禄神到位"}]

    # 灾煞: 按年支三合局查 — 申子辰=午, 亥卯未=酉, 寅午戌=子, 巳酉丑=卯
    ZAISHA = {frozenset(["申","子","辰"]):"午", frozenset(["亥","卯","未"]):"酉",
              frozenset(["寅","午","戌"]):"子", frozenset(["巳","酉","丑"]):"卯"}
    zaisha_zhi = None
    for k, v in ZAISHA.items():
        if nian_zhi in k:
            zaisha_zhi = v
            break
    if zaisha_zhi:
        zaisha_found = []
        for p in ["年","月","日","时"]:
            if sizhu[f"{p}支"] == zaisha_zhi:
                zaisha_found.append(p)
        if zaisha_found:
            result["灾煞"] = [{"位置": "、".join(f"{p}支" for p in zaisha_found),
                              "地支": zaisha_zhi,
                              "含义": "意外灾祸、血光之兆，但灾煞带贵人可化险为夷"}]
        else:
            result["灾煞"] = [{"位置": "无", "地支": zaisha_zhi,
                              "含义": f"灾煞在{zaisha_zhi}方，逢{zaisha_zhi}年运需谨慎"}]

    # 孤辰/寡宿: 按年支三合局查
    # 亥子丑=寅(孤辰)戌(寡宿), 寅卯辰=巳丑, 巳午未=申辰, 申酉戌=亥未
    GUCHEN = {frozenset(["亥","子","丑"]):"寅", frozenset(["寅","卯","辰"]):"巳",
              frozenset(["巳","午","未"]):"申", frozenset(["申","酉","戌"]):"亥"}
    GUASU = {frozenset(["亥","子","丑"]):"戌", frozenset(["寅","卯","辰"]):"丑",
             frozenset(["巳","午","未"]):"辰", frozenset(["申","酉","戌"]):"未"}
    for name, gmap, meaning in [
        ("孤辰", GUCHEN, "性格孤僻，不喜社交，六亲缘薄，宜晚婚"),
        ("寡宿", GUASU, "孤独寡居之象，感情多波折，宜修身养性"),
    ]:
        target_zhi = None
        for k, v in gmap.items():
            if nian_zhi in k:
                target_zhi = v
                break
        if target_zhi:
            found = []
            for p in ["年","月","日","时"]:
                if sizhu[f"{p}支"] == target_zhi:
                    found.append(p)
            if found:
                result[name] = [{"位置": "、".join(f"{p}支" for p in found),
                                 "地支": target_zhi, "含义": meaning}]
            else:
                result[name] = [{"位置": "无", "地支": target_zhi,
                                 "含义": f"{name}在{target_zhi}方，逢{target_zhi}年运显现"}]

    # 阴阳差错: 特定日柱 — 丙子、丁丑、戊寅、辛卯、壬辰、癸巳、丙午、丁未、戊申、辛酉、壬戌、癸亥
    YYC_RIZHU = {"丙子","丁丑","戊寅","辛卯","壬辰","癸巳","丙午","丁未","戊申","辛酉","壬戌","癸亥"}
    if ri_zhu in YYC_RIZHU:
        result["阴阳差错"] = [{"位置": f"日柱{ri_zhu}",
                              "含义": "婚姻多波折，男女易生误会，宜晚婚或双方多沟通包容"}]

    # 魁罡: 特定日柱 — 庚辰、庚戌、壬辰、戊戌
    KUIGANG_RIZHU = {"庚辰","庚戌","壬辰","戊戌"}
    if ri_zhu in KUIGANG_RIZHU:
        result["魁罡"] = [{"位置": f"日柱{ri_zhu}",
                          "含义": "刚强果断，聪明但性格刚烈，宜自律不宜放纵，带魁罡者多掌权"}]

    # 金舆: 按日干查 — 甲辰, 乙巳, 丙戊申, 丁己子, 庚寅, 辛丑, 壬亥, 癸卯
    JINYU_MAP = {"甲":"辰","乙":"巳","丙":"申","丁":"子","戊":"申",
                 "己":"子","庚":"寅","辛":"丑","壬":"亥","癸":"卯"}
    jinyu_zhi = JINYU_MAP.get(ri_gan, "")
    jinyu_found = []
    for p in ["年","月","日","时"]:
        if sizhu[f"{p}支"] == jinyu_zhi:
            jinyu_found.append(p)
    if jinyu_found:
        result["金舆"] = [{"位置": "、".join(f"{p}支" for p in jinyu_found),
                          "地支": jinyu_zhi,
                          "含义": "富格标志，得物质享受，宜从商，有车马之福"}]
    else:
        result["金舆"] = [{"位置": "无", "地支": jinyu_zhi,
                          "含义": f"金舆在{jinyu_zhi}方，逢{jinyu_zhi}年运财禄丰厚"}]

    return result


# =============================================================================
# 综合排盘
# =============================================================================

def bazi_full(year: int, month: int, day: int, hour: int, gender: str = "未知") -> dict:
    """八字全盘排盘."""
    dt = datetime(year, month, day, hour)
    sizhu = pai_sizhu(year, month, day, hour)
    shishen = pai_shishen(sizhu)
    dayun = pai_dayun(sizhu["年干"], sizhu["年支"], sizhu["月支"], gender, dt, sizhu["日干"])
    shensha = find_shensha(sizhu, gender)

    current_year = datetime.now().year
    liunian = get_liunian(current_year)

    # 旬空(空亡): 日柱所在旬空哪两个地支
    ri_gz_idx = ganzhi_to_index(sizhu["日柱"])
    xunshou_idx = (ri_gz_idx // 10) * 10
    _xk_map = {0:["戌","亥"],10:["申","酉"],20:["午","未"],30:["辰","巳"],40:["寅","卯"],50:["子","丑"]}
    xunkong = _xk_map.get(xunshou_idx, [])

    # 四柱合冲刑害分析
    from utils import (get_tiangan_he, get_dizhi_liuhe, get_dizhi_liuchong,
                       get_dizhi_sanhe, get_dizhi_liuhai, DIZHI_SANXING, DIZHI_ZIXING)
    relations = {"天干五合": [], "地支六合": [], "地支六冲": [], "地支三合": [], "地支半合": [], "地支三会": [], "地支三刑": [], "地支六害": [], "自刑": []}
    zhi_list = [sizhu["年支"], sizhu["月支"], sizhu["日支"], sizhu["时支"]]
    zhi_names = ["年支", "月支", "日支", "时支"]
    gan_list = [sizhu["年干"], sizhu["月干"], sizhu["日干"], sizhu["时干"]]
    gan_names = ["年干", "月干", "日干", "时干"]

    # 天干五合（仅相邻天干: 年月/月日/日时）
    for i in range(3):
        he = get_tiangan_he(gan_list[i], gan_list[i+1])
        if he:
            relations["天干五合"].append(f"{gan_names[i]}{gan_list[i]}+{gan_names[i+1]}{gan_list[i+1]}→化{he}")

    # 地支六合/六冲
    for i in range(4):
        for j in range(i+1, 4):
            he = get_dizhi_liuhe(zhi_list[i], zhi_list[j])
            if he:
                relations["地支六合"].append(f"{zhi_names[i]}{zhi_list[i]}+{zhi_names[j]}{zhi_list[j]}→化{he}")
            chong = get_dizhi_liuchong(zhi_list[i], zhi_list[j])
            if chong:
                relations["地支六冲"].append(f"{zhi_names[i]}{zhi_list[i]}↔{zhi_names[j]}{zhi_list[j]}")
            # 六害
            hai = get_dizhi_liuhai(zhi_list[i], zhi_list[j])
            if hai:
                relations["地支六害"].append(f"{zhi_names[i]}{zhi_list[i]}↔{zhi_names[j]}{zhi_list[j]}")

    # 地支三合/半合/三刑
    for i in range(4):
        for j in range(i+1, 4):
            for k in range(j+1, 4):
                tri = get_dizhi_sanhe(zhi_list[i], zhi_list[j], zhi_list[k])
                if tri:
                    relations["地支三合"].append(f"{zhi_names[i]}{zhi_list[i]}+{zhi_names[j]}{zhi_list[j]}+{zhi_names[k]}{zhi_list[k]}→合{tri}局")
                z3 = {zhi_list[i], zhi_list[j], zhi_list[k]}
                for key, name in DIZHI_SANXING.items():
                    if len(key) == 3 and z3 == set(key):
                        relations["地支三刑"].append(f"{zhi_names[i]}{zhi_list[i]}+{zhi_names[j]}{zhi_list[j]}+{zhi_names[k]}{zhi_list[k]}→{name}")
    # 半合(只两两都不构成三合时就检查半合)
    from utils import DIZHI_SANHE as DS
    for i in range(4):
        for j in range(i+1, 4):
            for fs, wx in DS.items():
                zs = list(fs)
                if {zhi_list[i], zhi_list[j]}.issubset(set(zs)):
                    relations["地支半合"].append(f"{zhi_names[i]}{zhi_list[i]}+{zhi_names[j]}{zhi_list[j]}→半合{wx}局({zs[0]}{zs[1]}{zs[2]})")

    # 三会(寅卯辰=木, 巳午未=火, 申酉戌=金, 亥子丑=水)
    SANHUI = {
        frozenset(["寅","卯","辰"]): "木",
        frozenset(["巳","午","未"]): "火",
        frozenset(["申","酉","戌"]): "金",
        frozenset(["亥","子","丑"]): "水",
    }
    for i in range(4):
        for j in range(i+1, 4):
            for k in range(j+1, 4):
                z3 = frozenset([zhi_list[i], zhi_list[j], zhi_list[k]])
                if z3 in SANHUI:
                    relations["地支三会"].append(f"{zhi_names[i]}{zhi_list[i]}+{zhi_names[j]}{zhi_list[j]}+{zhi_names[k]}{zhi_list[k]}→会{SANHUI[z3]}方局")
    # 两支三刑: 子卯相刑
    for i in range(4):
        for j in range(i+1, 4):
            s2 = {zhi_list[i], zhi_list[j]}
            for key, name in DIZHI_SANXING.items():
                if len(key) == 2 and s2 == set(key):
                    relations["地支三刑"].append(f"{zhi_names[i]}{zhi_list[i]}+{zhi_names[j]}{zhi_list[j]}→{name}")
    # 自刑
    for i in range(4):
        if zhi_list[i] in DIZHI_ZIXING:
            dup = sum(1 for z in zhi_list if z == zhi_list[i])
            if dup >= 2:
                relations["自刑"].append(f"{zhi_names[i]}{zhi_list[i]}自刑")

    # 清洗空列表
    relations = {k: v for k, v in relations.items() if v}

    # 大运/流年与四柱的合冲刑害
    # 找出当前所处的实际大运（基于当前年龄）
    current_age = current_year - year
    current_dayun_idx = 0
    for idx, dy in enumerate(dayun["大运列表"]):
        if current_age >= dy["起运"]:
            current_dayun_idx = idx
    current_dayun = dayun["大运列表"][current_dayun_idx]
    dayun_gz = current_dayun["干支"]
    dayun_gan, dayun_zhi = split_ganzhi(dayun_gz)
    liunian_gan, liunian_zhi = split_ganzhi(liunian)

    dyn_relations = {"天干五合": [], "地支六合": [], "地支六冲": [], "地支三合": [], "地支半合": [], "地支三刑": [], "地支六害": [], "自刑": []}

    def _check_dyn(source_name, source_gan, source_zhi, label):
        """检查一个干支与四柱的合冲刑害。"""
        # 天干五合（仅相邻天干检查：年月/月日/日时）
        for i in range(4):
            he = get_tiangan_he(source_gan, gan_list[i])
            if he:
                dyn_relations["天干五合"].append(f"{label}{source_gan}+{gan_names[i]}{gan_list[i]}→化{he}")
        # 地支六合/六冲/六害
        for i in range(4):
            he = get_dizhi_liuhe(source_zhi, zhi_list[i])
            if he:
                dyn_relations["地支六合"].append(f"{label}{source_zhi}+{zhi_names[i]}{zhi_list[i]}→化{he}")
            chong = get_dizhi_liuchong(source_zhi, zhi_list[i])
            if chong:
                dyn_relations["地支六冲"].append(f"{label}{source_zhi}↔{zhi_names[i]}{zhi_list[i]}")
            hai = get_dizhi_liuhai(source_zhi, zhi_list[i])
            if hai:
                dyn_relations["地支六害"].append(f"{label}{source_zhi}↔{zhi_names[i]}{zhi_list[i]}")
        # 地支三合/半合
        for i in range(4):
            for j in range(i+1, 4):
                tri = get_dizhi_sanhe(source_zhi, zhi_list[i], zhi_list[j])
                if tri:
                    dyn_relations["地支三合"].append(f"{label}{source_zhi}+{zhi_names[i]}{zhi_list[i]}+{zhi_names[j]}{zhi_list[j]}→合{tri}局")
                # 半合
                from utils import DIZHI_SANHE as DS2
                for fs, wx in DS2.items():
                    zs = list(fs)
                    if {source_zhi, zhi_list[i]}.issubset(set(zs)):
                        dyn_relations["地支半合"].append(f"{label}{source_zhi}+{zhi_names[i]}{zhi_list[i]}→半合{wx}局")
        # 地支三刑/自刑
        for i in range(4):
            s2 = {source_zhi, zhi_list[i]}
            for key, name in DIZHI_SANXING.items():
                if len(key) == 2 and s2 == set(key):
                    dyn_relations["地支三刑"].append(f"{label}{source_zhi}+{zhi_names[i]}{zhi_list[i]}→{name}")
        if source_zhi in DIZHI_ZIXING:
            for i in range(4):
                if zhi_list[i] == source_zhi:
                    dyn_relations["自刑"].append(f"{label}{source_zhi}与{gan_names[i]}{zhi_list[i]}同自刑")

    _check_dyn("大运", dayun_gan, dayun_zhi, f"大运{dayun_gz}")
    _check_dyn("流年", liunian_gan, liunian_zhi, f"流年{liunian}")

    dyn_relations = {k: v for k, v in dyn_relations.items() if v}

    # 用神自动判断
    yongshen = _determine_yongshen(sizhu)

    # 流年十神
    liunian_gan, liunian_zhi = split_ganzhi(liunian)
    liunian_shishen_gan = get_shishen(sizhu["日干"], liunian_gan)

    # 空亡(旬空)应用到各柱
    kongwang_pillars = []
    for pillar in ["年","月","日","时"]:
        if sizhu[f"{pillar}支"] in xunkong:
            kongwang_pillars.append(f"{pillar}柱{sizhu[f'{pillar}支']}")
    kongwang_desc = []
    if kongwang_pillars:
        kw = "、".join(kongwang_pillars)
        kongwang_desc.append(f"{kw}旬空 — 这些柱的力量暂时减弱")
    if sizhu["日支"] in xunkong:
        kongwang_desc.append("日支旬空 → 配偶宫空亡，婚恋需待填实之年")
    if sizhu["时支"] in xunkong:
        kongwang_desc.append("时支旬空 → 子女宫空亡，晚年运或子女运偏弱")

    # 空亡详情: 每柱若逢空亡，分析影响及填实/冲空时机
    kongwang_details = []
    zhi_to_wuxing = {"子":"水","丑":"土","寅":"木","卯":"木","辰":"土","巳":"火",
                     "午":"火","未":"土","申":"金","酉":"金","戌":"土","亥":"水"}
    liuchong_map = {"子":"午","午":"子","丑":"未","未":"丑","寅":"申","申":"寅",
                    "卯":"酉","酉":"卯","辰":"戌","戌":"辰","巳":"亥","亥":"巳"}
    pillar_labels = {"年": "祖上/童年", "月": "父母/青年", "日": "配偶/中年", "时": "子女/晚年"}
    for pillar in ["年","月","日","时"]:
        zhi = sizhu[f"{pillar}支"]
        if zhi in xunkong:
            label = pillar_labels[pillar]
            wx = zhi_to_wuxing[zhi]
            chong_zhi = liuchong_map.get(zhi, "")
            tianshi = f"遇{chong_zhi}年/大运(冲空)" if chong_zhi else ""
            items = [zhi]
            items.append(chong_zhi) if chong_zhi else None
            detail = {
                "柱": f"{pillar}柱({label})",
                "空亡地支": zhi,
                "五行": wx,
                "影响": f"{label}方面力量减弱，{pillar}宫虚浮不定，对应六亲缘薄或该阶段运势起伏",
                "填实": f"逢{zhi}年或{zhi}大运({wx}旺年)可填实",
                "冲空": tianshi if tianshi else "无冲空之支",
                "化解": f"宜补{wx}五行，多在{wx}旺之方位/年份行事",
            }
            kongwang_details.append(detail)

    # 五行统计
    wuxing_stats = count_wuxing(sizhu)

    # 补充神煞
    extra_shensha = _get_extra_shensha(sizhu)

    return {
        "四柱": sizhu,
        "十神": shishen,
        "大运": dayun,
        "神煞": shensha,
        "补充神煞": extra_shensha,
        "流年": liunian,
        "流年十神": liunian_shishen_gan,
        "当前流年": f"{current_year}年 {liunian}({liunian_shishen_gan})",
        "旬空": xunkong,
        "旬空分析": kongwang_desc,
        "空亡详情": kongwang_details,
        "合冲刑害": relations,
        "大运流年合冲刑害": dyn_relations,
        "用神分析": yongshen,
        "五行统计": wuxing_stats,
        "五行": {
            "年": sizhu["纳音"]["年"],
            "月": sizhu["纳音"]["月"],
            "日": sizhu["纳音"]["日"],
            "时": sizhu["纳音"]["时"],
        },
    }


# =============================================================================
# 用神自动判断
# =============================================================================

# 日干五行 → 帮扶五行（同五行+生我五行）
_HU_WUXING = {
    "木": {"木", "水"},
    "火": {"火", "木"},
    "土": {"土", "火"},
    "金": {"金", "土"},
    "水": {"水", "金"},
}


def _score_rizhu_wangshuai(sizhu: dict) -> dict:
    """
    日主旺衰评分。
    月令权重最大，其余天干次之，地支藏干再次之。
    返回: {"旺衰": "身旺/身弱/中和", "得分": int, "详情": [...]}
    """
    ri_gan = sizhu["日干"]
    ri_wx = TIANGAN_WUXING[ri_gan]
    yue_zhi = sizhu["月支"]
    yue_wx = DIZHI_WUXING[yue_zhi]
    ri_yy = TIANGAN_YINYANG[ri_gan]

    score = 0
    details = []

    # 月令评分: 同五行+40, 生我+30, 我生-20, 克我-30, 我克-10
    if yue_wx == ri_wx:
        score += 40
        details.append(f"月令{yue_zhi}({yue_wx})与日主同五行 +40")
    elif wuxing_sheng(yue_wx) == ri_wx:
        score += 30
        details.append(f"月令{yue_zhi}({yue_wx})生日主 +30")
    elif wuxing_sheng(ri_wx) == yue_wx:
        score -= 20
        details.append(f"日主生月令{yue_zhi}({yue_wx}) -20")
    elif wuxing_ke(yue_wx) == ri_wx:
        score -= 30
        details.append(f"月令{yue_zhi}({yue_wx})克日主 -30")
    elif wuxing_ke(ri_wx) == yue_wx:
        score -= 10
        details.append(f"日主克月令{yue_zhi}({yue_wx}) -10")

    # 四柱天干评分(除日干): 同五行+10, 生我+8, 我生-5, 克我-8, 我克-3
    for pillar in ["年", "月", "时"]:
        g = sizhu[f"{pillar}干"]
        g_wx = TIANGAN_WUXING[g]
        if g_wx == ri_wx:
            score += 10
            details.append(f"{pillar}干{g}({g_wx})与日主同五行 +10")
        elif wuxing_sheng(g_wx) == ri_wx:
            score += 8
            details.append(f"{pillar}干{g}({g_wx})生日主 +8")
        elif wuxing_sheng(ri_wx) == g_wx:
            score -= 5
            details.append(f"日主生{pillar}干{g}({g_wx}) -5")
        elif wuxing_ke(g_wx) == ri_wx:
            score -= 8
            details.append(f"{pillar}干{g}({g_wx})克日主 -8")
        elif wuxing_ke(ri_wx) == g_wx:
            score -= 3
            details.append(f"日主克{pillar}干{g}({g_wx}) -3")

    # 地支藏干评分(本气权重3, 中气2, 余气1)
    for pillar in ["年", "月", "日", "时"]:
        cang = sizhu["藏干"][pillar]
        for idx, cg in enumerate(cang):
            w = 3 if idx == 0 else (2 if idx == 1 else 1)
            cg_wx = TIANGAN_WUXING[cg]
            if cg_wx == ri_wx:
                score += 5 * w
                details.append(f"{pillar}支藏{cg}({cg_wx})同五行 +{5*w}")
            elif wuxing_sheng(cg_wx) == ri_wx:
                score += 3 * w
                details.append(f"{pillar}支藏{cg}({cg_wx})生日主 +{3*w}")
            elif wuxing_ke(cg_wx) == ri_wx:
                score -= 4 * w
                details.append(f"{pillar}支藏{cg}({cg_wx})克日主 -{4*w}")
            elif wuxing_sheng(ri_wx) == cg_wx:
                score -= 2 * w
                details.append(f"日主生{pillar}支藏{cg}({cg_wx})泄身 -{2*w}")
            elif wuxing_ke(ri_wx) == cg_wx:
                score -= 3 * w
                details.append(f"日主克{pillar}支藏{cg}({cg_wx})耗身 -{3*w}")

    # 日支特殊加权(坐支=日主根基)
    ri_zhi_wx = DIZHI_WUXING[sizhu["日支"]]
    if ri_zhi_wx == ri_wx:
        score += 10
        details.append(f"日坐{sizhu['日支']}({ri_zhi_wx})日主通根 +10")

    # 判等
    if score >= 20:
        ws = "身旺"
    elif score <= -20:
        ws = "身弱"
    else:
        ws = "中和"

    return {"旺衰": ws, "得分": score, "详情": details}


def _determine_yongshen(sizhu: dict) -> dict:
    """
    根据日主旺衰定用神。
    返回: {"用神": [...], "忌神": [...], "喜神": [...], "说明": str}
    """
    ri_gan = sizhu["日干"]
    ri_wx = TIANGAN_WUXING[ri_gan]
    ri_yy = TIANGAN_YINYANG[ri_gan]
    ri_yy_str = "阳" if ri_yy == "阳" else "阴"

    ws_result = _score_rizhu_wangshuai(sizhu)
    ws = ws_result["旺衰"]
    score = ws_result["得分"]

    helper = _HU_WUXING[ri_wx]  # {同五行, 生我五行}

    # 从格/专旺格/化格检测
    cong_type = None
    ga_type = None

    # 从强/专旺检测: 得分极高(>=100)且月令为同五行或生我 → 可能是专旺格或从强格
    # 从弱检测: 得分极低(<=-80)且日主无根无生 → 可能是从弱格
    zhi_helper_count = sum(
        1 for pillar in ["年","月","日","时"]
        if DIZHI_WUXING[sizhu[f"{pillar}支"]] in helper
    )
    gan_helper_count = sum(
        1 for pillar in ["年","月","时"]
        if TIANGAN_WUXING[sizhu[f"{pillar}干"]] in helper
    )

    if score >= 100:
        # 从强格/专旺格
        cong_type = f"从强(日主极旺，独强)"
        yong_liuqin = list(helper)
        ji_liuqin = [wx for wx in "木火土金水" if wx not in helper]
        yong_desc = f"从强格/专旺格 — 日主极旺不可逆，以帮扶为用"
        ji_desc = "最忌官杀克身逆势"
    elif score <= -80 and zhi_helper_count <= 1 and gan_helper_count <= 0:
        # 从弱格
        cong_type = f"从弱(日主极弱无根)"
        yong_liuqin = [wx for wx in "木火土金水" if wx not in helper]
        ji_liuqin = list(helper)
        yong_desc = "从弱格 — 日主极弱无根，顺势从势，以克泄耗为用"
        ji_desc = "最忌印比帮扶逆势"
    elif ws == "身旺":
        yong_liuqin = [wx for wx in "木火土金水" if wx not in helper]
        ji_liuqin = list(helper)
        yong_desc = "身旺宜克泄耗，用官杀制身、食伤泄秀、财星耗身"
        ji_desc = "忌印比帮扶"
    elif ws == "身弱":
        yong_liuqin = list(helper)
        ji_liuqin = [wx for wx in "木火土金水" if wx not in helper]
        yong_desc = "身弱宜生扶，用印星生身、比劫帮身"
        ji_desc = "忌官杀克身、食伤泄身、财星耗身"
    else:
        yong_liuqin = []
        ji_liuqin = []
        yong_desc = "中和命局，用神以大运流年为导向，顺其自然"
        ji_desc = "无特定忌神"

    # 调候用神: 根据月令补充专属用神
    tiaohou = {"提示": []}
    yue_zhi = sizhu["月支"]
    ri_wx = TIANGAN_WUXING[ri_gan]
    # 冬月(亥子丑): 需火调候
    if yue_zhi in ("亥","子","丑") and ri_wx in ("金","水","土"):
        tiaohou["提示"].append(f"冬月{yue_zhi}寒凝，需火调候暖局")
    # 夏月(巳午未): 需水调候
    if yue_zhi in ("巳","午","未") and ri_wx in ("火","土","木"):
        tiaohou["提示"].append(f"夏月{yue_zhi}炎燥，需水调候润局")

    # 格局判定: 月令本气/透干的十神格局
    geju_info = _detect_geju(sizhu)

    return {
        "日主": f"{ri_gan}({ri_wx},{ri_yy_str})",
        "旺衰": ws,
        "旺衰得分": score,
        "旺衰详情": ws_result["详情"],
        "用神五行": yong_liuqin,
        "忌神五行": ji_liuqin,
        "用神说明": yong_desc,
        "忌神说明": ji_desc,
        "调候": tiaohou,
        "格局": geju_info,
        "从格": cong_type,
    }


def _detect_geju(sizhu: dict) -> dict:
    """以月令本气十神定格局。"""
    ri_gan = sizhu["日干"]
    yue_zhi = sizhu["月支"]
    yue_zhi_main_cg = DIZHI_CANGGAN[yue_zhi][0]  # 本气
    yue_ling_shishen = get_shishen(ri_gan, yue_zhi_main_cg)

    geju_name = f"{yue_ling_shishen}格(月令{yue_zhi}本气{yue_zhi_main_cg})"

    # 检查透干: 月令藏干是否在天干上透出
    tougan = []
    for cg in DIZHI_CANGGAN[yue_zhi]:
        for p in ["年","月","日","时"]:
            if sizhu[f"{p}干"] == cg:
                tougan.append(f"{p}干{cg}")
    tougan_str = "、".join(tougan) if tougan else "未透出"

    return {
        "名称": geju_name,
        "月令十神": yue_ling_shishen,
        "透干": tougan_str,
        "说明": f"月令{yue_zhi}本气为{yue_zhi_main_cg}，对日主形成{yue_ling_shishen}格局",
    }

if __name__ == "__main__":
    import json
    # Test: 1990-06-15 08:00 男
    result = bazi_full(1990, 6, 15, 8, "男")
    print(json.dumps(result, ensure_ascii=False, indent=2))
