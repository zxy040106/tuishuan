#!/usr/bin/env python3
"""推算 Skill — 奇门遁甲模块"""

import sys; sys.stdout.reconfigure(encoding='utf-8')  # Windows GBK 修复

import os
from datetime import datetime, date
from typing import Dict, List, Optional, Tuple

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from utils import (
    TIANGAN, DIZHI, SEXAGENARY,
    split_ganzhi, ganzhi_to_index, HOUR_TO_SHICHEN, SHICHEN_ORDER,
    day_ganzhi_index, day_ganzhi, dizhi_step,
    get_solar_term_date,
)
from ganzhi import determine_nongli_month

# =============================================================================
# 奇门基础数据
# =============================================================================

# 九宫（后天八卦）
# 4 9 2
# 3 5 7
# 8 1 6

GONG_POS = {
    1: {"name": "坎一宫", "bagua": "坎", "direction": "北", "wuxing": "水", "number": 1},
    2: {"name": "坤二宫", "bagua": "坤", "direction": "西南", "wuxing": "土", "number": 2},
    3: {"name": "震三宫", "bagua": "震", "direction": "东", "wuxing": "木", "number": 3},
    4: {"name": "巽四宫", "bagua": "巽", "direction": "东南", "wuxing": "木", "number": 4},
    5: {"name": "中五宫", "bagua": "中", "direction": "中", "wuxing": "土", "number": 5},
    6: {"name": "乾六宫", "bagua": "乾", "direction": "西北", "wuxing": "金", "number": 6},
    7: {"name": "兑七宫", "bagua": "兑", "direction": "西", "wuxing": "金", "number": 7},
    8: {"name": "艮八宫", "bagua": "艮", "direction": "东北", "wuxing": "土", "number": 8},
    9: {"name": "离九宫", "bagua": "离", "direction": "南", "wuxing": "火", "number": 9},
}

# 九星
JIU_XING = ["天蓬","天芮","天冲","天辅","天禽","天心","天柱","天任","天英"]

JIU_XING_WUXING = {
    "天蓬":"水","天芮":"土","天冲":"木","天辅":"木","天禽":"土",
    "天心":"金","天柱":"金","天任":"土","天英":"火",
}

# 八门
BA_MEN = ["休","生","伤","杜","景","死","惊","开"]

BA_MEN_WUXING = {
    "休":"水","生":"土","伤":"木","杜":"木",
    "景":"火","死":"土","惊":"金","开":"金",
}

# 八神（阳遁顺序）
BA_SHEN_YANG = ["值符","螣蛇","太阴","六合","白虎","玄武","九地","九天"]
# 八神（阴遁顺序 = 反序）
BA_SHEN_YIN = ["值符","九天","九地","玄武","白虎","六合","太阴","螣蛇"]

# 三奇六仪
SAN_QI = ["乙","丙","丁"]
LIU_YI = ["戊","己","庚","辛","壬","癸"]


# =============================================================================
# 阴阳遁判断
# =============================================================================

def is_yangdun(dt: datetime) -> bool:
    """冬至后到夏至前 = 阳遁, 夏至后到冬至前 = 阴遁（天文算法动态计算）."""
    y = dt.year
    dz = get_solar_term_date(y, "冬至")
    xz = get_solar_term_date(y, "夏至")
    target = dt.date() if isinstance(dt, datetime) else dt
    if isinstance(target, datetime):
        target = target.date()
    # 冬至(含) → 夏至(不含) = 阳遁
    if dz <= target < xz:
        return True
    # 夏至(含) → 冬至(不含) = 阴遁
    if xz <= target < dz:
        return False
    # 跨年：元旦可能在冬至之前（12月）
    if target >= dz or target < xz:
        return True  # 冬至后到下一年夏至前
    return False


# =============================================================================
# 局数计算（置闰法简化版）
# =============================================================================

# 二十四节气对应的局数基础（每个节气分上中下三元）
# 阳遁节气: 冬至 小寒 大寒 立春 雨水 惊蛰 春分 清明 谷雨 立夏 小满 芒种
# 阴遁节气: 夏至 小暑 大暑 立秋 处暑 白露 秋分 寒露 霜降 立冬 小雪 大雪

# 各节气上元局数 (阳遁1-9, 阴遁也用1-9, 但是盘式相反)
JIEQI_JU = {
    # 阳遁
    "冬至": (1, 7, 4),   # 上元1, 中元7, 下元4
    "小寒": (2, 8, 5),
    "大寒": (3, 9, 6),
    "立春": (8, 5, 2),
    "雨水": (9, 6, 3),
    "惊蛰": (1, 7, 4),
    "春分": (3, 9, 6),
    "清明": (4, 1, 7),
    "谷雨": (5, 2, 8),
    "立夏": (4, 1, 7),
    "小满": (5, 2, 8),
    "芒种": (6, 3, 9),
    # 阴遁
    "夏至": (9, 3, 6),
    "小暑": (8, 2, 5),
    "大暑": (7, 1, 4),
    "立秋": (2, 5, 8),
    "处暑": (1, 4, 7),
    "白露": (9, 3, 6),
    "秋分": (7, 1, 4),
    "寒露": (6, 9, 3),
    "霜降": (5, 8, 2),
    "立冬": (6, 9, 3),
    "小雪": (5, 8, 2),
    "大雪": (4, 7, 1),
}

# 二十四节气名（按公历顺序，从小寒开始）
_JIEQI_ALL = [
    "小寒","大寒","立春","雨水","惊蛰","春分","清明","谷雨",
    "立夏","小满","芒种","夏至","小暑","大暑","立秋","处暑",
    "白露","秋分","寒露","霜降","立冬","小雪","大雪","冬至",
]


def get_current_jieqi(dt: datetime) -> str:
    """获取当前日期所属的节气（动态天文计算，无年份限制）."""
    y = dt.year
    target = dt.date() if isinstance(dt, datetime) else dt
    if isinstance(target, datetime):
        target = target.date()

    # 收集本年 + 上下年的全部节气日期
    all_terms = []
    for name in _JIEQI_ALL:
        all_terms.append((get_solar_term_date(y - 1, name), name))
        all_terms.append((get_solar_term_date(y, name), name))
        all_terms.append((get_solar_term_date(y + 1, name), name))
    all_terms = sorted(set(all_terms))

    # 找最近的上一个节气
    prev = "冬至"
    for d, name in all_terms:
        if d > target:
            break
        prev = name
    return prev


def determine_yuan(day_gz_index: int) -> int:
    """
    根据日干支确定三元: 上元=0, 中元=1, 下元=2.
    符头: 甲子/甲戌/甲申/甲午/甲辰/甲寅 为上元符头
    规律: 从符头日起0-4天为上元, 5-9天为中元, 10-14天为下元
    """
    futou_indices = [0, 10, 20, 30, 40, 50]

    if day_gz_index in futou_indices:
        return 0

    # 找到最近的上一个符头：取所有符头中 diff 最小且 <15 的那个
    best_diff = 999
    for ft in futou_indices:
        diff = (day_gz_index - ft) % 60
        if diff < 15 and diff < best_diff:
            best_diff = diff

    if best_diff < 5:
        return 0  # 上元
    elif best_diff < 10:
        return 1  # 中元
    else:
        return 2  # 下元


def get_ju_number(dt: datetime) -> int:
    """获取局数(1-9)."""
    jieqi = get_current_jieqi(dt)
    day_gz_idx = day_ganzhi_index(date(dt.year, dt.month, dt.day))
    yuan = determine_yuan(day_gz_idx)

    if jieqi in JIEQI_JU:
        ju = JIEQI_JU[jieqi][yuan]
        return ju
    return 1  # fallback


# =============================================================================
# 排地盘（三奇六仪）
# =============================================================================

def bu_dipan(ju_num: int, is_yang: bool) -> dict:
    """
    布地盘。
    阳遁X局: 戊从X宫起, 顺排戊己庚辛壬癸丁丙乙
    阴遁X局: 戊从X宫起, 逆排戊己庚辛壬癸丁丙乙
    中五宫寄坤二宫。
    """
    order = ["戊","己","庚","辛","壬","癸","丁","丙","乙"]

    dipan = {}  # {gong: str}
    for i, gan in enumerate(order):
        if is_yang:
            gong = ((ju_num - 1) + i) % 9 + 1
        else:
            gong = ((ju_num - 1) - i) % 9 + 1

        # 中五宫寄坤二宫
        if gong == 5:
            gong = 2

        if gong in dipan:
            dipan[gong] = dipan[gong] + "/" + gan
        else:
            dipan[gong] = gan

    return dipan


# =============================================================================
# 定值符星和值使门
# =============================================================================

def get_zhifu_zhishi(hour_ganzhi: str, dipan: dict, is_yang: bool) -> Tuple[str, str, int, int]:
    """
    根据时辰确定值符星和值使门。

    返回: (值符星名, 值使门名, 值符星所在宫, 值使门落宫)

    值符星: 时干落宫对应的九星（时干在哪一宫，该宫原生星即为值符）
    值使门: 旬首宫对应的八门（旬首六仪落宫的原生门即为值使）
    值使门落宫: 从旬首宫按 advancement 顺/逆数八宫
    """
    hour_gan = hour_ganzhi[0]
    hour_zhi = hour_ganzhi[1]

    # 甲时需映射为旬首对应的六仪（甲子→戊, 甲戌→己, ...）
    XUNSHOU_MAP = {"子":"戊", "戌":"己", "申":"庚", "午":"辛", "辰":"壬", "寅":"癸"}
    xunshou_liuyi = XUNSHOU_MAP.get(hour_zhi, "") if hour_gan == "甲" else ""

    # 时干在地盘哪一宫（用于值符星落宫 & 天盘旋转）
    search_gan = xunshou_liuyi if hour_gan == "甲" else hour_gan
    hour_gan_gong = None
    for gong, gan in dipan.items():
        if gan == search_gan or (isinstance(gan, str) and search_gan in gan):
            hour_gan_gong = gong
            break

    if hour_gan_gong is None:
        hour_gan_gong = 1

    # 值符星: 时干落宫对应的九星
    xing_gong_map = {
        1:"天蓬", 2:"天芮", 3:"天冲", 4:"天辅",
        5:"天禽", 6:"天心", 7:"天柱", 8:"天任", 9:"天英",
    }
    zhifu_xing = xing_gong_map.get(hour_gan_gong, "天禽")

    # === 值使门: 旬首宫原生门 ===
    from utils import ganzhi_to_index, SEXAGENARY
    hour_gz_idx = ganzhi_to_index(hour_ganzhi)
    xunshou_idx = (hour_gz_idx // 10) * 10
    xunshou_zhi = SEXAGENARY[xunshou_idx][1]  # 旬首地支
    advancement = (SHICHEN_ORDER.index(hour_zhi) - SHICHEN_ORDER.index(xunshou_zhi)) % 12

    # 旬首六仪（非甲时需计算）
    if hour_gan == "甲":
        xunshou_liuyi_for_search = xunshou_liuyi
    else:
        # 本旬甲…时 → 反查六仪
        _xunshou_gz = SEXAGENARY[xunshou_idx]
        _xunshou_gan, _xunshou_zhi2 = _xunshou_gz[0], _xunshou_gz[1]
        xunshou_liuyi_for_search = XUNSHOU_MAP.get(_xunshou_zhi2, "戊")

    # 旬首宫: 旬首六仪地盘落宫
    xunshou_gong = None
    for gong, gan in dipan.items():
        if gan == xunshou_liuyi_for_search or (isinstance(gan, str) and xunshou_liuyi_for_search in gan):
            xunshou_gong = gong
            break
    if xunshou_gong is None:
        xunshou_gong = 1

    # 八门固定宫对应
    men_gong_map = {
        1:"休", 2:"死", 3:"伤", 4:"杜",
        5:"死", 6:"开", 7:"惊", 8:"生", 9:"景",
    }
    # 值使门 = 旬首宫原生门
    zhishi_men = men_gong_map.get(xunshou_gong, "休")

    # 值使门落宫: 从旬首宫按 advancement 在洛书九宫上阳顺/阴逆数
    # 九宫数字序列（洛书序，跳5宫）: 1→2→3→4→6→7→8→9→1...
    LUOSHU_ORDER = [1, 2, 3, 4, 6, 7, 8, 9]
    start_idx = LUOSHU_ORDER.index(xunshou_gong) if xunshou_gong in LUOSHU_ORDER else 0
    if is_yang:
        zhishi_gong = LUOSHU_ORDER[(start_idx + advancement) % 8]
    else:
        zhishi_gong = LUOSHU_ORDER[(start_idx - advancement + 8) % 8]

    return zhifu_xing, zhishi_men, hour_gan_gong, zhishi_gong


# =============================================================================
# 排天盘和人盘
# =============================================================================

def bu_tianpan(dipan: dict, zhifu_xing: str, zhifu_gong: int,
               is_yang: bool) -> dict:
    """排天盘(九星): 值符星转到时干宫, 其他八星跟随旋转。中五宫寄坤二宫。"""
    target_gong = zhifu_gong  # 值符星去时干所在宫

    jx_order = ["天蓬","天芮","天冲","天辅","天禽","天心","天柱","天任","天英"]
    zhifu_idx = jx_order.index(zhifu_xing)

    tianpan = {}
    for i in range(9):
        xing = jx_order[(zhifu_idx + i) % 9]
        if is_yang:
            gong = ((target_gong - 1) + i) % 9 + 1
        else:
            gong = ((target_gong - 1) - i) % 9 + 1
        # 中五宫寄坤二宫 — 用 "+" 连接同宫之星
        gong_key = 2 if gong == 5 else gong
        if gong_key in tianpan:
            tianpan[gong_key] = tianpan[gong_key] + "+" + xing
        else:
            tianpan[gong_key] = xing

    return tianpan


def bu_tianpan_gan(dipan: dict, zhifu_xing: str, zhifu_gong: int,
                   is_yang: bool) -> dict:
    """
    排天盘干（天盘三奇六仪）。
    1. 找值符星在地盘的原生宫位 → 该宫地盘干为值符干
    2. 值符干随值符星转到时干宫(zhifu_gong)
    3. 其余九干按三奇六仪顺序阳顺阴逆旋转
    """
    # 值符星原生宫
    xing_gong_map = {1:"天蓬",2:"天芮",3:"天冲",4:"天辅",5:"天禽",6:"天心",7:"天柱",8:"天任",9:"天英"}
    zf_origin_gong = None
    for g, x in xing_gong_map.items():
        if x == zhifu_xing:
            zf_origin_gong = g
            break
    if zf_origin_gong is None:
        zf_origin_gong = 5

    # 值符干 = 值符星原生宫的地盘干（取第一个，忽略寄宫 "/"）
    zf_gan_raw = dipan.get(zf_origin_gong, "戊")
    zf_gan = zf_gan_raw.split("/")[0] if isinstance(zf_gan_raw, str) else zf_gan_raw

    order = ["戊","己","庚","辛","壬","癸","丁","丙","乙"]
    zf_idx = order.index(zf_gan) if zf_gan in order else 0

    result = {}
    for i in range(9):
        gan = order[(zf_idx + i) % 9]
        if is_yang:
            gong = ((zhifu_gong - 1) + i) % 9 + 1
        else:
            gong = ((zhifu_gong - 1) - i) % 9 + 1
        gong_key = 2 if gong == 5 else gong
        if gong_key in result:
            result[gong_key] = result[gong_key] + "/" + gan
        else:
            result[gong_key] = gan

    return result


def check_ge_patterns(dipan: dict, tianpan_gan: dict) -> list:
    """
    检测天盘干+地盘干形成的格局（克应）。
    返回检测到的格局列表 [{格局, 宫位, 组合, 含义, 吉凶}]。
    """
    GE_PATTERNS = {
        ("戊","丙"): ("青龙返首","事情可成、有大进展","吉"),
        ("丙","戊"): ("飞鸟跌穴","收益好、回报高","吉"),
        ("乙","辛"): ("青龙逃走","宜走不宜留","凶"),
        ("辛","乙"): ("白虎猖狂","凶险突生","凶"),
        ("丁","癸"): ("朱雀投江","文书口舌之祸","凶"),
        ("癸","丁"): ("螣蛇夭矫","事情曲折复杂","凶"),
        ("庚","丙"): ("太白入荧","贼寇必来（敌动）","凶"),
        ("丙","庚"): ("荧入太白","贼寇必退（敌退）","吉"),
        ("戊","戊"): ("伏吟","事情停滞不前","凶"),
        ("庚","庚"): ("战格","两强相争","凶"),
        # qimen.md 补充格局
        ("戊","乙"): ("青龙和合","贵人相助，事情顺利","吉"),
        ("戊","丁"): ("青龙耀明","光明正大，谒贵求名","吉"),
        ("乙","戊"): ("利阴害阳","利于暗中行事，不利公开","凶"),
        ("丁","丙"): ("星随月转","得贵人提携，渐入佳境","吉"),
        ("己","庚"): ("刑格返名","词讼纠纷，不宜主动出击","凶"),
        ("庚","癸"): ("大格","事情有重大阻碍","凶"),
        ("庚","壬"): ("小格","小有阻碍，需绕道而行","凶"),
        ("庚","己"): ("刑格","刑伤官非","凶"),
        ("辛","丁"): ("狱神得奇","囚禁中获救，绝处逢生","吉"),
        ("辛","丙"): ("干合悖师","事情有变，需灵活应对","凶"),
        ("壬","戊"): ("小蛇化龙","从小变大，事情向好发展","吉"),
        ("癸","戊"): ("天乙会合","贵人暗助，事情可成","吉"),
    }
    result = []
    for gong in range(1, 10):
        if gong == 5: continue
        tg_raw = tianpan_gan.get(gong, "")
        dg_raw = dipan.get(gong, "")
        if not tg_raw or not dg_raw: continue
        tg = tg_raw.split("/")[0] if isinstance(tg_raw, str) else tg_raw
        dg = dg_raw.split("/")[0] if isinstance(dg_raw, str) else dg_raw
        key = (tg, dg)
        if key in GE_PATTERNS:
            name, meaning, ji_xiong = GE_PATTERNS[key]
            result.append({
                "格局": name, "宫位": f"第{gong}宫",
                "组合": f"{tg}+{dg}", "含义": meaning, "吉凶": ji_xiong,
            })
    return result


def bu_renpan(zhishi_men: str, zhishi_gong: int, is_yang: bool) -> dict:
    """排人盘（八门）: 值使门转到 zhishi_gong 所在宫."""
    # 八宫顺序按后天八卦方位: 坎1→艮8→震3→巽4→离9→坤2→兑7→乾6
    PALACE_ORDER_8 = [1, 8, 3, 4, 9, 2, 7, 6]
    target_idx = PALACE_ORDER_8.index(zhishi_gong) if zhishi_gong in PALACE_ORDER_8 else 0
    zhishi_idx = BA_MEN.index(zhishi_men)

    renpan = {}
    for i in range(8):
        men = BA_MEN[(zhishi_idx + i) % 8]
        if is_yang:
            gong = PALACE_ORDER_8[(target_idx + i) % 8]
        else:
            gong = PALACE_ORDER_8[(target_idx - i + 8) % 8]
        renpan[gong] = men

    return renpan


def bu_shenpan(zhifu_gong: int, is_yang: bool) -> dict:
    """排神盘（八神）. 阳遁顺排，阴遁逆排."""
    # 八宫顺序按后天八卦方位: 坎1→艮8→震3→巽4→离9→坤2→兑7→乾6
    PALACE_ORDER_8 = [1, 8, 3, 4, 9, 2, 7, 6]
    shen_list = BA_SHEN_YANG if is_yang else BA_SHEN_YIN
    target_idx = PALACE_ORDER_8.index(zhifu_gong) if zhifu_gong in PALACE_ORDER_8 else 0

    shenpan = {}
    for i in range(8):
        shen = shen_list[i]
        if is_yang:
            gong = PALACE_ORDER_8[(target_idx + i) % 8]
        else:
            gong = PALACE_ORDER_8[(target_idx - i + 8) % 8]
        shenpan[gong] = shen

    return shenpan


# =============================================================================
# 综合排盘
# =============================================================================

def qimen_pai_pan(dt: datetime) -> dict:
    """
    时家奇门置闰法 完整排盘。

    参数: dt - 具体日期时间
    """
    is_yang = is_yangdun(dt)
    ju_num = get_ju_number(dt)
    jieqi = get_current_jieqi(dt)

    # 时柱
    day_gz = day_ganzhi(date(dt.year, dt.month, dt.day))
    day_gan = day_gz[0]
    shichen = HOUR_TO_SHICHEN.get(dt.hour, "子")

    # 日上起时
    from utils import DAY_GAN_TO_ZISHI_GAN
    base_gan = DAY_GAN_TO_ZISHI_GAN[day_gan]
    hour_gan_idx = (TIANGAN.index(base_gan) + SHICHEN_ORDER.index(shichen)) % 10
    hour_gz = TIANGAN[hour_gan_idx] + shichen

    # 排地盘
    dipan = bu_dipan(ju_num, is_yang)

    # 定值符值使
    zhifu_xing, zhishi_men, zhifu_gong, zhishi_gong = get_zhifu_zhishi(hour_gz, dipan, is_yang)

    # 排天盘（九星）
    tianpan = bu_tianpan(dipan, zhifu_xing, zhifu_gong, is_yang)

    # 排天盘干（天盘三奇六仪）
    tianpan_gan = bu_tianpan_gan(dipan, zhifu_xing, zhifu_gong, is_yang)

    # 排人盘
    renpan = bu_renpan(zhishi_men, zhishi_gong, is_yang)

    # 排神盘
    shenpan = bu_shenpan(zhifu_gong, is_yang)

    # 日干落宫: 查天盘干（旋转层），甲遁于值符所在宫
    ri_gan_gong = None
    if day_gan == "甲":
        ri_gan_gong = zhifu_gong  # 遁甲：甲随值符
    else:
        for gong, gan in tianpan_gan.items():
            if day_gan == gan or (isinstance(gan, str) and day_gan in gan):
                ri_gan_gong = gong
                break
        if ri_gan_gong is None:
            ri_gan_gong = zhifu_gong  # 兜底

    # 时干落宫: 甲遁于值符宫，其余时干从天盘查找
    hour_gan = hour_gz[0]
    shi_gan_gong = zhifu_gong  # 甲遁
    if hour_gan != "甲":
        for gong, gan in tianpan_gan.items():
            tg = gan.split("/")[0] if isinstance(gan, str) else gan
            if hour_gan == tg:
                shi_gan_gong = gong
                break

    # 格局检测
    ge_patterns = check_ge_patterns(dipan, tianpan_gan)

    # 门宫生克: 八门五行 vs 九宫五行
    men_gong_shengke = []
    from utils import wuxing_relation as qm_wx_rel
    for gong_num in range(1, 10):
        if gong_num == 5: continue
        men = renpan.get(gong_num, "")
        gong_wx = GONG_POS[gong_num]["wuxing"]
        men_wx = BA_MEN_WUXING.get(men, "")
        if men and men_wx:
            rel = qm_wx_rel(men_wx, gong_wx)
            desc = {
                "同": f"{men}({men_wx})比和宫({gong_wx}) — 门宫相合",
                "a生b": f"{men}({men_wx})生宫({gong_wx}) — 门生宫为泄(吉门减力)",
                "a克b": f"{men}({men_wx})克宫({gong_wx}) — 门克宫为迫(凶门更凶)",
                "a被b生": f"宫({gong_wx})生{men}({men_wx}) — 宫生门为和(吉门得生)",
                "a被b克": f"宫({gong_wx})克{men}({men_wx}) — 宫克门为制(凶门被制)",
            }
            men_gong_shengke.append({
                "宫位": GONG_POS[gong_num]["name"],
                "门": men,
                "关系": desc.get(rel, ""),
            })

    # 旬空/空亡: 日柱所在旬空地支对应的宫位
    xun_kong_gong = []
    xk_map = {0:["戌","亥"],10:["申","酉"],20:["午","未"],30:["辰","巳"],40:["寅","卯"],50:["子","丑"]}
    day_gz_idx = ganzhi_to_index(day_gz)
    xunshou = (day_gz_idx // 10) * 10
    xk_zhi = xk_map.get(xunshou, [])
    for xz in xk_zhi:
        for gn, info in GONG_POS.items():
            if info["bagua"] == "乾" and xz in ["戌","亥"]: xun_kong_gong.append(gn)
            elif info["bagua"] == "坤" and xz in ["未","申"]: xun_kong_gong.append(gn)
            elif info["bagua"] == "震" and xz == "卯": xun_kong_gong.append(gn)
            elif info["bagua"] == "巽" and xz in ["辰","巳"]: xun_kong_gong.append(gn)
            elif info["bagua"] == "坎" and xz == "子": xun_kong_gong.append(gn)
            elif info["bagua"] == "离" and xz == "午": xun_kong_gong.append(gn)
            elif info["bagua"] == "艮" and xz in ["丑","寅"]: xun_kong_gong.append(gn)
            elif info["bagua"] == "兑" and xz == "酉": xun_kong_gong.append(gn)
    xun_kong_gong = list(set(xun_kong_gong))

    # 三奇入墓检测
    qimen_sanqi_rumu = []
    MU_GONG = {"乙":4, "丙":6, "丁":8}  # 乙入巽4, 丙入乾6, 丁入艮8
    for gong_num in range(1, 10):
        if gong_num == 5: continue
        tg_raw = tianpan_gan.get(gong_num, "")
        if tg_raw:
            for qi in ["乙","丙","丁"]:
                if qi in tg_raw and gong_num == MU_GONG.get(qi):
                    qimen_sanqi_rumu.append(f"{qi}在{GONG_POS[gong_num]['name']}入墓")

    # 伏吟/反吟检测
    qimen_fuyin = None
    all_same = all(
        (tianpan_gan.get(g, "") == dipan.get(g, "") or
         tianpan_gan.get(g, "").split("/")[0] == dipan.get(g, "").split("/")[0])
        for g in range(1, 10) if g != 5
    )
    if all_same:
        qimen_fuyin = "伏吟 — 全局天地盘相同，事情停滞不前"
    # 反吟: 天盘干与地盘干全部对冲(天盘各宫干与地盘对宫干相同)
    qimen_fanyin = None
    if not all_same:
        opposite_pairs = 0
        for g in range(1, 10):
            if g == 5: continue
            tg = (tianpan_gan.get(g, "") or "").split("/")[0]
            opposite_g = 10 - g if 10 - g != 5 else 2
            dg = (dipan.get(opposite_g, "") or "").split("/")[0]
            if tg and dg and tg == dg:
                opposite_pairs += 1
        if opposite_pairs >= 4:
            qimen_fanyin = "反吟 — 天地盘对冲，事情反复多变"

    # 构建九宫完整信息
    palaces = []
    for gong_num in range(1, 10):
        if gong_num == 5:
            info = GONG_POS[gong_num].copy()
            info["地盘干"] = dipan.get(2, "")
            info["天盘干"] = tianpan_gan.get(2, "")
            info["天盘星"] = tianpan.get(2, "")
            info["八门"] = renpan.get(2, "")
            info["八神"] = shenpan.get(2, "")
            info["寄宫"] = "寄坤二宫"
            palaces.append(info)
        else:
            info = GONG_POS[gong_num].copy()
            info["地盘干"] = dipan.get(gong_num, "")
            info["天盘干"] = tianpan_gan.get(gong_num, "")
            info["天盘星"] = tianpan.get(gong_num, "")
            info["八门"] = renpan.get(gong_num, "")
            info["八神"] = shenpan.get(gong_num, "")
            palaces.append(info)

    return {
        "时间": dt.strftime("%Y-%m-%d %H:00"),
        "节气": jieqi,
        "阴阳遁": "阳遁" if is_yang else "阴遁",
        "局数": f"{'阳遁' if is_yang else '阴遁'}{ju_num}局",
        "时辰": hour_gz,
        "值符星": zhifu_xing,
        "值使门": zhishi_men,
        "九宫": palaces,
        "日干落宫": ri_gan_gong,
        "时干落宫": shi_gan_gong,
        "格局": ge_patterns,
        "门宫生克": men_gong_shengke,
        "旬空宫": xun_kong_gong,
        "三奇入墓": qimen_sanqi_rumu,
        "伏吟": qimen_fuyin,
        "反吟": qimen_fanyin,
        "流派声明": "时家奇门·置闰法",
    }


# =============================================================================
# 自检
# =============================================================================

def verify_qimen(result: dict) -> list:
    """奇门排盘自检."""
    issues = []

    palaces = result.get("九宫", [])
    if len(palaces) != 9:
        issues.append(f"九宫数量异常: {len(palaces)}")

    # 检查地盘三奇六仪是否完整
    all_dipan = set()
    for p in palaces:
        dg = p.get("地盘干", "")
        if dg:
            for ch in dg:
                if ch != "/":  # 跳过寄宫分隔符
                    all_dipan.add(ch)
    expected = set(["戊","己","庚","辛","壬","癸","丁","丙","乙"])
    if all_dipan != expected:
        issues.append(f"地盘干不完整: 缺{expected - all_dipan}, 多{all_dipan - expected}")

    # 局数在合理范围
    ju = result.get("局数", "")
    if "局" not in ju:
        issues.append("局数格式异常")

    # 阴阳遁与节气匹配
    jieqi = result.get("节气", "")
    yinyang = result.get("阴阳遁", "")
    yang_jieqi = ["冬至","小寒","大寒","立春","雨水","惊蛰","春分","清明","谷雨","立夏","小满","芒种"]
    yin_jieqi = ["夏至","小暑","大暑","立秋","处暑","白露","秋分","寒露","霜降","立冬","小雪","大雪"]

    if jieqi in yang_jieqi and yinyang != "阳遁":
        issues.append(f"{jieqi}应为阳遁, 实际为{yinyang}")
    if jieqi in yin_jieqi and yinyang != "阴遁":
        issues.append(f"{jieqi}应为阴遁, 实际为{yinyang}")

    return issues


# =============================================================================
# Standalone testing
# =============================================================================

if __name__ == "__main__":
    import json

    print("=" * 60)
    print("奇门遁甲 排盘测试")
    print("=" * 60)

    # 测试: 2026-06-23 14:00 (当前日期夏至后, 应为阴遁)
    dt = datetime(2026, 6, 23, 14, 0)
    result = qimen_pai_pan(dt)

    print(f"时间: {result['时间']}")
    print(f"节气: {result['节气']}")
    print(f"局数: {result['局数']}")
    print(f"时辰: {result['时辰']}")
    print(f"值符星: {result['值符星']}")
    print(f"值使门: {result['值使门']}")
    print(f"日干落宫: {result['日干落宫']}")
    print(f"时干落宫: {result['时干落宫']}")

    print("\n九宫:")
    for p in result["九宫"]:
        ji = f" ({p.get('寄宫','')})" if p.get('寄宫') else ""
        print(f"  {p['name']}{ji}: 地盘[{p['地盘干']}] 天盘[{p['天盘星']}] 八门[{p['八门']}] 八神[{p['八神']}]")

    print("\n自检:")
    issues = verify_qimen(result)
    if issues:
        for i in issues:
            print(f"  [!] {i}")
    else:
        print("  [OK] 自检通过")
