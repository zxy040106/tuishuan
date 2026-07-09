#!/usr/bin/env python3
"""推算 Skill — 紫微斗数模块"""

import sys; sys.stdout.reconfigure(encoding='utf-8')  # Windows GBK 修复

import os
from datetime import datetime, date
from typing import Dict, List, Optional, Tuple

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from utils import (
    TIANGAN, DIZHI, SEXAGENARY, TIANGAN_YINYANG, DIZHI_WUXING,
    DIZHI_CANGGAN, SHICHEN_ORDER, HOUR_TO_SHICHEN,
    dizhi_step, month_ganzhi, ganzhi_to_index, index_to_ganzhi,
    split_ganzhi, join_ganzhi,
)
from ganzhi import get_year_ganzhi, determine_nongli_month, determine_nongli_day, determine_calendar_lunar_month

# =============================================================================
# 十二宫名称
# =============================================================================
PALACES = ["命宫","兄弟","夫妻","子女","财帛","疾厄","迁移","交友","官禄","田宅","福德","父母"]

# 十二宫地支顺序（从寅宫开始，逆时针/顺数）
# 寅卯辰巳午未申酉戌亥子丑 为固定宫位
GONG_DIZHI = ["寅","卯","辰","巳","午","未","申","酉","戌","亥","子","丑"]

# =============================================================================
# 安命宫和十二宫
# =============================================================================

def an_minggong(lunar_month: int, birth_hour_zhi: str) -> str:
    """
    安命宫:
    从寅宫起正月, 顺数至出生月 → 从该位起子时, 逆数至出生时
    返回命宫地支。
    """
    # 月: 从寅起正月顺数
    # 正月=寅, 二月=卯, ..., 腊月=丑
    month_dizhi = DIZHI[(2 + (lunar_month - 1)) % 12]  # 寅=2

    # 时: 从月位置起子时逆数至出生时
    hour_idx = SHICHEN_ORDER.index(birth_hour_zhi)  # 子=0, 丑=1, ...
    month_pos = DIZHI.index(month_dizhi)

    # 逆数: 月位置=子时, 每过一个时辰逆退一位
    minggong_pos = (month_pos - hour_idx) % 12
    return DIZHI[minggong_pos]


def an_shiergong(minggong_zhi: str) -> dict:
    """
    安十二宫:
    从命宫逆时针排: 命宫→兄弟→夫妻→子女→财帛→疾厄→迁移→交友→官禄→田宅→福德→父母
    返回 {宫名: 地支}
    """
    minggong_idx = DIZHI.index(minggong_zhi)
    result = {}
    for i, name in enumerate(PALACES):
        zhi_idx = (minggong_idx - i) % 12  # 逆排
        result[name] = DIZHI[zhi_idx]
    return result


def an_gonggan(shiergong: dict, year_gan: str) -> dict:
    """
    安十二宫天干:
    用五虎遁法（年上起月）确定每个宫的天干。
    寅宫天干由年干决定，其余顺推。
    """
    # 年干 → 寅宫天干
    yin_gan_map = {
        "甲":"丙","己":"丙",
        "乙":"戊","庚":"戊",
        "丙":"庚","辛":"庚",
        "丁":"壬","壬":"壬",
        "戊":"甲","癸":"甲",
    }
    yin_gan = yin_gan_map[year_gan]

    result = {}
    for name in PALACES:
        zhi = shiergong[name]
        zhi_idx = DIZHI.index(zhi)
        yin_idx = DIZHI.index("寅")
        offset = (zhi_idx - yin_idx) % 12
        gan_idx = (TIANGAN.index(yin_gan) + offset) % 10
        result[name] = TIANGAN[gan_idx] + zhi
    return result


# =============================================================================
# 五行局
# =============================================================================

# 五行局由命宫干支的纳音决定（纳音五行）
# 水二局、木三局、金四局、土五局、火六局

def wuxing_ju(ming_gong_ganzhi: str) -> Tuple[str, int]:
    """
    返回 (五行, 局数)
    水二局、木三局、金四局、土五局、火六局
    """
    from utils import NAYIN
    nayin = NAYIN[ming_gong_ganzhi]
    # 纳音最后一个字是五行: 海中金 → 金
    wx = nayin[-1]

    ju_map = {"水": 2, "木": 3, "金": 4, "土": 5, "火": 6}
    return wx, ju_map[wx]


# =============================================================================
# 星曜亮度（庙旺利陷）—— 14主星 × 12地支
# =============================================================================

# 亮度等级: 庙 > 旺 > 得 > 利 > 平 > 不 > 陷
# 数据以《紫微斗数全书》为基准，三合派庙旺标准。
STAR_BRIGHTNESS = {
    "紫微": {
        "子":"平", "丑":"庙", "寅":"旺", "卯":"旺", "辰":"得", "巳":"旺",
        "午":"庙", "未":"庙", "申":"旺", "酉":"旺", "戌":"得", "亥":"旺",
    },
    "天机": {
        "子":"庙", "丑":"陷", "寅":"得", "卯":"旺", "辰":"利", "巳":"陷",
        "午":"庙", "未":"陷", "申":"得", "酉":"旺", "戌":"利", "亥":"陷",
    },
    "太阳": {
        "子":"陷", "丑":"陷", "寅":"旺", "卯":"庙", "辰":"旺", "巳":"旺",
        "午":"庙", "未":"得", "申":"得", "酉":"平", "戌":"陷", "亥":"陷",
    },
    "武曲": {
        "子":"旺", "丑":"庙", "寅":"得", "卯":"利", "辰":"庙", "巳":"平",
        "午":"旺", "未":"庙", "申":"得", "酉":"庙", "戌":"陷", "亥":"陷",
    },
    "天同": {
        "子":"旺", "丑":"陷", "寅":"利", "卯":"平", "辰":"平", "巳":"庙",
        "午":"陷", "未":"陷", "申":"旺", "酉":"平", "戌":"平", "亥":"庙",
    },
    "廉贞": {
        "子":"平", "丑":"陷", "寅":"庙", "卯":"平", "辰":"陷", "巳":"陷",
        "午":"平", "未":"旺", "申":"利", "酉":"平", "戌":"陷", "亥":"陷",
    },
    "天府": {
        "子":"庙", "丑":"庙", "寅":"庙", "卯":"陷", "辰":"庙", "巳":"得",
        "午":"旺", "未":"陷", "申":"得", "酉":"旺", "戌":"庙", "亥":"得",
    },
    "太阴": {
        "子":"得", "丑":"旺", "寅":"陷", "卯":"陷", "辰":"陷", "巳":"陷",
        "午":"陷", "未":"庙", "申":"旺", "酉":"庙", "戌":"庙", "亥":"庙",
    },
    "贪狼": {
        "子":"旺", "丑":"平", "寅":"庙", "卯":"平", "辰":"平", "巳":"陷",
        "午":"旺", "未":"平", "申":"平", "酉":"旺", "戌":"平", "亥":"陷",
    },
    "巨门": {
        "子":"旺", "丑":"陷", "寅":"得", "卯":"得", "辰":"陷", "巳":"旺",
        "午":"旺", "未":"陷", "申":"得", "酉":"得", "戌":"陷", "亥":"旺",
    },
    "天相": {
        "子":"庙", "丑":"庙", "寅":"得", "卯":"陷", "辰":"得", "巳":"平",
        "午":"庙", "未":"庙", "申":"得", "酉":"陷", "戌":"得", "亥":"得",
    },
    "天梁": {
        "子":"旺", "丑":"旺", "寅":"庙", "卯":"庙", "辰":"庙", "巳":"得",
        "午":"庙", "未":"庙", "申":"得", "酉":"得", "戌":"得", "亥":"陷",
    },
    "七杀": {
        "子":"旺", "丑":"旺", "寅":"庙", "卯":"旺", "辰":"庙", "巳":"平",
        "午":"旺", "未":"庙", "申":"旺", "酉":"旺", "戌":"庙", "亥":"平",
    },
    "破军": {
        "子":"庙", "丑":"旺", "寅":"得", "卯":"平", "辰":"旺", "巳":"平",
        "午":"庙", "未":"旺", "申":"得", "酉":"陷", "戌":"得", "亥":"庙",
    },
}

BRIGHTNESS_LEVEL = {"庙":7, "旺":6, "得":5, "利":4, "平":3, "不":2, "陷":1}

# 辅星庙旺表（主要甲级辅星）
FU_BRIGHTNESS = {
    "文昌": {"子":"得","丑":"陷","寅":"得","卯":"庙","辰":"陷","巳":"得","午":"陷","未":"得","申":"平","酉":"旺","戌":"陷","亥":"平"},
    "文曲": {"子":"庙","丑":"得","寅":"平","卯":"旺","辰":"得","巳":"庙","午":"平","未":"陷","申":"得","酉":"得","戌":"平","亥":"陷"},
    "左辅": {"子":"旺","丑":"陷","寅":"得","卯":"得","辰":"平","巳":"陷","午":"旺","未":"陷","申":"得","酉":"得","戌":"平","亥":"得"},
    "右弼": {"子":"得","丑":"陷","寅":"平","卯":"得","辰":"陷","巳":"得","午":"得","未":"陷","申":"得","酉":"得","戌":"平","亥":"得"},
    "天魁": {"子":"旺","丑":"庙","寅":"得","卯":"平","辰":"平","巳":"得","午":"旺","未":"庙","申":"得","酉":"平","戌":"平","亥":"得"},
    "天钺": {"子":"得","丑":"庙","寅":"平","卯":"平","辰":"得","巳":"平","午":"得","未":"庙","申":"平","酉":"平","戌":"得","亥":"平"},
    "禄存": {"子":"平","丑":"得","寅":"庙","卯":"旺","辰":"平","巳":"得","午":"平","未":"得","申":"平","酉":"旺","戌":"得","亥":"平"},
    "擎羊": {"子":"陷","丑":"庙","寅":"得","卯":"陷","辰":"庙","巳":"得","午":"陷","未":"庙","申":"得","酉":"陷","戌":"庙","亥":"陷"},
    "陀罗": {"子":"陷","丑":"庙","寅":"得","卯":"陷","辰":"庙","巳":"得","午":"陷","未":"庙","申":"得","酉":"陷","戌":"庙","亥":"陷"},
    "火星": {"子":"陷","丑":"得","寅":"庙","卯":"陷","辰":"得","巳":"陷","午":"旺","未":"得","申":"庙","酉":"陷","戌":"得","亥":"陷"},
    "铃星": {"子":"陷","丑":"得","寅":"庙","卯":"陷","辰":"得","巳":"陷","午":"旺","未":"得","申":"庙","酉":"陷","戌":"得","亥":"陷"},
    "地空": {"子":"陷","丑":"陷","寅":"得","卯":"陷","辰":"得","巳":"庙","午":"陷","未":"得","申":"得","酉":"陷","戌":"得","亥":"陷"},
    "地劫": {"子":"陷","丑":"得","寅":"陷","卯":"陷","辰":"得","巳":"陷","午":"陷","未":"得","申":"陷","酉":"陷","戌":"得","亥":"陷"},
}


def get_star_brightness(star_name: str, zhi: str) -> str:
    """返回某星在某地支宫位的庙旺利陷等级。主星查主星表，辅星查辅星表，均无则默认'平'。"""
    bm = STAR_BRIGHTNESS.get(star_name, FU_BRIGHTNESS.get(star_name, {}))
    return bm.get(zhi, "平")


# =============================================================================
# 身宫
# =============================================================================

# 身主星 — 按出生年支确定（口诀：子午天相，丑未天梁，寅申天同，卯酉天机，辰戌文昌，巳亥火星）
SHENZHU_STAR = {
    "子":"天相", "午":"天相",
    "丑":"天梁", "未":"天梁",
    "寅":"天同", "申":"天同",
    "卯":"天机", "酉":"天机",
    "辰":"文昌", "戌":"文昌",
    "巳":"火星", "亥":"火星",
}

# 命主星 — 按出生年支确定（口诀：子贪狼，丑亥巨门，寅戌禄存，卯酉文曲，辰申廉贞，巳未武曲，午破军）
MINGZHU_STAR = {
    "子":"贪狼",
    "丑":"巨门", "亥":"巨门",
    "寅":"禄存", "戌":"禄存",
    "卯":"文曲", "酉":"文曲",
    "辰":"廉贞", "申":"廉贞",
    "巳":"武曲", "未":"武曲",
    "午":"破军",
}


def an_shengong(lunar_month: int, birth_hour_zhi: str) -> str:
    """
    安身宫:
    从寅宫起正月顺数至出生月 → 从月位起子时**顺数**至出生时。
    与命宫的区别: 命宫逆数时辰, 身宫顺数时辰。
    返回身宫地支。
    """
    # 月: 从寅起正月顺数 → 正月=寅, 二月=卯, ...
    month_dizhi = DIZHI[(2 + (lunar_month - 1)) % 12]

    hour_idx = SHICHEN_ORDER.index(birth_hour_zhi)
    month_pos = DIZHI.index(month_dizhi)

    # 顺数
    shengong_pos = (month_pos + hour_idx) % 12
    return DIZHI[shengong_pos]


# =============================================================================
# 来因宫
# =============================================================================

def an_laiyingong(shiergong_ganzhi: dict, year_gan: str) -> str:
    """
    找出来因宫: 十二宫天干中与生年年干相同的宫位。
    来因宫是四化解盘的原点——同一组四化在不同来因宫含义完全不同。
    """
    for pal_name, gz in shiergong_ganzhi.items():
        if gz[0] == year_gan:
            return pal_name
    return "命宫"  # 兜底: 年干必出现在某宫天干中


# =============================================================================
# 特殊格局检测
# =============================================================================

def check_patterns(result: dict) -> list:
    """
    检测命盘中的特殊格局。返回检测到的格局列表。
    每个格局包含 {名称, 条件, 含义}。
    """
    palaces = {p["宫名"]: p for p in result.get("十二宫", [])}
    stars_by_zhi = {}
    for p in result.get("十二宫", []):
        zhi = p["地支"]
        stars_by_zhi[zhi] = {
            "主星": p["主星"],
            "辅星": p["辅星"],
            "宫名": p["宫名"],
        }

    # 空宫借对宫: 无主星的宫位借用对宫(相差6位)的主星
    empty_palaces = []
    for name, p in palaces.items():
        if not p.get("主星"):
            dui_name = PALACES[(PALACES.index(name) + 6) % 12] if name in PALACES else ""
            dui_p = palaces.get(dui_name, {})
            dui_main = dui_p.get("主星", [])
            empty_palaces.append({
                "宫名": name,
                "地支": p["地支"],
                "对宫": dui_name,
                "借星": dui_main,
            })
            # 将借来的星临时加入 stars_by_zhi 用于格局检测
            zhi = p["地支"]
            if zhi in stars_by_zhi and dui_main:
                stars_by_zhi[zhi]["主星"] = list(set(stars_by_zhi[zhi].get("主星", []) + dui_main))

    patterns = []

    def all_stars_in_palace(pal_name):
        """返回该宫所有星（主星+辅星）"""
        p = palaces.get(pal_name, {})
        return set(p.get("主星", []) + p.get("辅星", []))

    def all_stars_in_zhi(zhi):
        s = stars_by_zhi.get(zhi, {})
        return set(s.get("主星", []) + s.get("辅星", []))

    def has_star(pal_name, star):
        return star in all_stars_in_palace(pal_name)

    def has_star_zhi(zhi, star):
        return star in all_stars_in_zhi(zhi)

    def both_stars(pal_name, s1, s2):
        s = all_stars_in_palace(pal_name)
        return s1 in s and s2 in s

    # 1) 紫府同宫 — 紫微+天府同宫
    for name, p in palaces.items():
        if both_stars(name, "紫微", "天府"):
            patterns.append({"名称":"紫府同宫","条件":f"紫微+天府同宫于{name}","含义":"大格局，领导力+包容力兼备"})

    # 2) 日月同宫 — 太阳+太阴同宫（仅丑未）
    for name, p in palaces.items():
        zhi = p["地支"]
        if zhi in ("丑","未") and both_stars(name, "太阳", "太阴"):
            patterns.append({"名称":"日月同宫","条件":f"太阳+太阴同宫于{name}({zhi})","含义":"阴阳调和，性格平衡，处事圆融"})

    # 3) 杀破狼 — 七杀+破军+贪狼 三颗星须全部在命宫三方四正
    ming_gong = palaces.get("命宫", {})
    ming_zhi = ming_gong.get("地支", "")
    cai_zhi = palaces.get("财帛", {}).get("地支", "")
    guan_zhi = palaces.get("官禄", {}).get("地支", "")
    mq_zhi = palaces.get("迁移", {}).get("地支", "")
    sanfang_zhi = {ming_zhi, cai_zhi, guan_zhi, mq_zhi}
    spb_stars = {"七杀","破军","贪狼"}
    spb_count = 0
    found_spb = set()
    for z in sanfang_zhi:
        found = spb_stars & all_stars_in_zhi(z)
        spb_count += len(found)
        found_spb |= found
    if len(found_spb) >= 3:
        patterns.append({"名称":"杀破狼","条件":"七杀+破军+贪狼三颗均在命宫三方四正","含义":"人生变动大，起伏多，适合开创性事业"})

    # 4) 机月同梁 — 天机+太阴+天同+天梁在命宫三方
    jytl_stars = {"天机","太阴","天同","天梁"}
    jytl_count = 0
    for z in sanfang_zhi:
        jytl_count += len(jytl_stars & all_stars_in_zhi(z))
    if jytl_count >= 3:
        patterns.append({"名称":"机月同梁","条件":"天机+太阴+天同+天梁见于命宫三方","含义":"适合稳定行业（公职/教育/文化），做事稳妥"})

    # 5) 府相朝垣 — 天府+天相分别在命宫两夹或三方
    fu = any(has_star(n, "天府") for n in PALACES)
    xiang = any(has_star(n, "天相") for n in PALACES)
    ming_idx = PALACES.index("命宫") if "命宫" in PALACES else 0
    left = PALACES[(ming_idx + 1) % 12]
    right = PALACES[(ming_idx - 1) % 12]
    if fu and xiang:
        if has_star(left, "天府") or has_star(right, "天府") or has_star(left, "天相") or has_star(right, "天相"):
            patterns.append({"名称":"府相朝垣","条件":"天府/天相在命宫两夹","含义":"稳重有福德，受人尊敬"})
        else:
            patterns.append({"名称":"府相朝垣","条件":"天府+天相俱在命盘","含义":"稳重有福德，为人可靠"})

    # 6) 日月反背 — 太阳在酉戌亥子+太阴在卯辰巳午
    sun_zhi = None
    moon_zhi = None
    for name, p in palaces.items():
        if has_star(name, "太阳"): sun_zhi = p["地支"]
        if has_star(name, "太阴"): moon_zhi = p["地支"]
    if sun_zhi and moon_zhi:
        night_zhi = {"酉","戌","亥","子","丑"}
        day_zhi = {"卯","辰","巳","午","未"}
        if sun_zhi in night_zhi and moon_zhi in day_zhi:
            patterns.append({"名称":"日月反背","条件":f"太阳在{sun_zhi}(夜)+太阴在{moon_zhi}(昼)","含义":"作息与常人相反，性格独特，适合夜间/幕后工作"})

    # 7) 阳梁昌禄 — 太阳+天梁+文昌+禄存四星会合
    ylcl_stars = {"太阳","天梁","文昌","禄存"}
    ylcl_count = 0
    for z in sanfang_zhi:
        ylcl_count += len(ylcl_stars & all_stars_in_zhi(z))
    if ylcl_count >= 4:
        patterns.append({"名称":"阳梁昌禄","条件":"太阳+天梁+文昌+禄存会合于命宫三方","含义":"考试运极佳，功名显达，学术有成"})

    # 8) 火贪格 — 火星+贪狼同宫或三合
    for name, p in palaces.items():
        if has_star(name, "火星") and has_star(name, "贪狼"):
            patterns.append({"名称":"火贪格","条件":f"火星+贪狼同宫于{name}","含义":"暴发格局，横发横破，来得快去得也快"})

    # 9) 铃贪格 — 铃星+贪狼同宫或三合
    for name, p in palaces.items():
        if has_star(name, "铃星") and has_star(name, "贪狼"):
            patterns.append({"名称":"铃贪格","条件":f"铃星+贪狼同宫于{name}","含义":"暗中积累后爆发，厚积薄发型暴富"})

    # 10) 巨日同宫 — 巨门+太阳同宫
    for name, p in palaces.items():
        if both_stars(name, "巨门", "太阳"):
            patterns.append({"名称":"巨日同宫","条件":f"巨门+太阳同宫于{name}","含义":"口才极佳，适合外交/法律/教育，以言语立足"})

    # 11) 月朗天门 — 太阴在亥宫
    moon_zhi = None
    for name, p in palaces.items():
        if has_star(name, "太阴"):
            moon_zhi = p["地支"]
    if moon_zhi == "亥":
        patterns.append({"名称":"月朗天门","条件":"太阴在亥宫","含义":"才华外露，女命极佳，月照天门清贵格"})

    # 12) 日照雷门 — 太阳在卯宫
    sun_zhi = None
    for name, p in palaces.items():
        if has_star(name, "太阳"):
            sun_zhi = p["地支"]
    if sun_zhi == "卯":
        patterns.append({"名称":"日照雷门","条件":"太阳在卯宫","含义":"朝气蓬勃，早年得志，光明磊落"})

    # 13) 雄宿乾元 — 廉贞在寅
    for name, p in palaces.items():
        if has_star(name, "廉贞") and p["地支"] == "寅":
            patterns.append({"名称":"雄宿乾元","条件":"廉贞在寅宫","含义":"刚毅正直，逆境中崛起，百折不挠"})
            break

    # 14) 石中隐玉 — 巨门在子或午
    for name, p in palaces.items():
        if has_star(name, "巨门") and p["地支"] in ("子", "午"):
            patterns.append({"名称":"石中隐玉","条件":f"巨门在{p['地支']}宫","含义":"表面平实内里才华，需打磨方能发光"})
            break

    # 15) 明珠出海 — 太阳在卯+太阴在亥
    if sun_zhi == "卯" and moon_zhi == "亥":
        patterns.append({"名称":"明珠出海","条件":"太阳在卯+太阴在亥","含义":"阴阳并美，人生平衡，福泽深厚"})

    # === 新增格局 ===

    # 16) 禄马交驰 — 禄存+天马同宫或三合
    lu_ma = {z for z in sanfang_zhi if "禄存" in all_stars_in_zhi(z) and "天马" in all_stars_in_zhi(z)}
    if lu_ma:
        patterns.append({"名称":"禄马交驰","条件":"禄存+天马在命宫三方同宫","含义":"财官双美，奔波得财，动中获利"})

    # 17) 天乙拱命 — 天魁+天钺同在命宫三方四正
    kui_yue_count = 0
    for z in sanfang_zhi:
        stars = all_stars_in_zhi(z)
        if "天魁" in stars: kui_yue_count += 1
        if "天钺" in stars: kui_yue_count += 1
    if kui_yue_count >= 2:
        patterns.append({"名称":"天乙拱命","条件":"天魁+天钺在命宫三方四正","含义":"贵人运极强，逢凶化吉，处处有人相助"})

    # 18) 科权禄夹命 — 化科/化权/化禄在命宫两邻宫
    ming_p = palaces.get("命宫", {})
    ming_idx = PALACES.index("命宫")
    left_p = palaces.get(PALACES[(ming_idx + 1) % 12], {})
    right_p = palaces.get(PALACES[(ming_idx - 1) % 12], {})
    left_three = [t for t in left_p.get("四化", []) if any(x in t for x in ["化禄","化权","化科"])]
    right_three = [t for t in right_p.get("四化", []) if any(x in t for x in ["化禄","化权","化科"])]
    if len(left_three) + len(right_three) >= 2:
        patterns.append({"名称":"科权禄夹命","条件":"化禄/化权/化科在命宫两邻宫","含义":"三方吉化夹辅命宫，贵气逼人，易得权势地位"})

    # 19) 日月夹命 — 太阳+太阴分别在命宫左右邻宫
    sun_pal = moon_pal = None
    for name, p in palaces.items():
        if has_star(name, "太阳"): sun_pal = PALACES.index(name)
        if has_star(name, "太阴"): moon_pal = PALACES.index(name)
    if sun_pal is not None and moon_pal is not None:
        if {sun_pal, moon_pal} == {(ming_idx + 1) % 12, (ming_idx - 1) % 12}:
            patterns.append({"名称":"日月夹命","条件":"太阳+太阴在命宫左右邻宫","含义":"日月并明夹命，一生光明，富贵可期"})

    # 20) 巨机同宫 — 巨门+天机同宫
    for name, p in palaces.items():
        if both_stars(name, "巨门", "天机"):
            patterns.append({"名称":"巨机同宫","条件":f"巨门+天机同宫于{name}","含义":"口才与谋略兼备，适合策划/咨询/外交"})

    # 21) 辅弼拱主 — 左辅+右弼在三方四正
    fu_bi_count = 0
    for z in sanfang_zhi:
        stars = all_stars_in_zhi(z)
        if "左辅" in stars: fu_bi_count += 1
        if "右弼" in stars: fu_bi_count += 1
    if fu_bi_count >= 2:
        patterns.append({"名称":"辅弼拱主","条件":"左辅+右弼在命宫三方","含义":"得众人之力相助，人脉广、助力多"})

    # 22) 双禄交流 — 禄存+化禄同在命宫三方
    hua_lu_zhi = set()
    for pal_name, p in palaces.items():
        if "命宫" in PALACES:
            zhi = p["地支"]
            for tag in p.get("四化", []):
                if "化禄" in tag:
                    hua_lu_zhi.add(zhi)
    lucun_zhi = {z for z in sanfang_zhi if "禄存" in all_stars_in_zhi(z)}
    if lucun_zhi & hua_lu_zhi:
        patterns.append({"名称":"双禄交流","条件":"禄存+化禄同在命宫三方","含义":"财源滚滚，双禄交汇，富格之象"})

    # 23) 府相朝垣加强 — 天府或天相在命宫邻宫
    if has_star(left, "天府") or has_star(right, "天府"):
        patterns.append({"名称":"府相朝垣(天府夹命)","条件":"天府在命宫邻宫","含义":"稳重有靠，得贵人提携"})
    if has_star(left, "天相") or has_star(right, "天相"):
        patterns.append({"名称":"府相朝垣(天相夹命)","条件":"天相在命宫邻宫","含义":"公正有德，得人信任，适合辅佐之职"})

    # 24) 三奇嘉会 — 化禄+化权+化科同在命宫三方
    hua_types_in_sanfang = set()
    for z in sanfang_zhi:
        for pal_name, p in palaces.items():
            if p.get("地支") == z:
                for tag in p.get("四化", []):
                    if "化禄" in tag: hua_types_in_sanfang.add("禄")
                    if "化权" in tag: hua_types_in_sanfang.add("权")
                    if "化科" in tag: hua_types_in_sanfang.add("科")
    if len(hua_types_in_sanfang) >= 3:
        patterns.append({"名称":"三奇嘉会","条件":"化禄+化权+化科会合于命宫三方","含义":"科权禄三奇汇聚，富贵双全，才智出众"})

    # 25) 贪武同行 — 贪狼+武曲同宫(辰戌丑未)
    for name, p in palaces.items():
        if both_stars(name, "贪狼", "武曲") and p["地支"] in ("辰","戌","丑","未"):
            patterns.append({"名称":"贪武同行","条件":f"贪狼+武曲同宫于{name}({p['地支']})","含义":"暴发格局，适合冒险/金融/创业"})

    # 26) 紫微朝斗 — 紫微在午宫
    for name, p in palaces.items():
        if has_star(name, "紫微") and p["地支"] == "午":
            patterns.append({"名称":"紫微朝斗","条件":"紫微在午宫朝北斗","含义":"贵格，领导力极强，位高权重"})

    # 27) 日月并明 — 太阳在巳午+太阴在酉戌亥（日月都在庙旺之地）
    if sun_zhi and moon_zhi:
        sun_ming = sun_zhi in ("巳","午","未")
        moon_ming = moon_zhi in ("酉","戌","亥","丑","未")
        if sun_ming and moon_ming:
            patterns.append({"名称":"日月并明","条件":f"太阳在{sun_zhi}(旺地)+太阴在{moon_zhi}(庙地)","含义":"日月并耀，光明磊落，一生顺遂"})

    # 28) 马头带剑 — 天马在午宫+擎羊同宫
    for name, p in palaces.items():
        if p["地支"] == "午" and "擎羊" in all_stars_in_palace(name) and "天马" in all_stars_in_palace(name):
            patterns.append({"名称":"马头带剑","条件":"天马+擎羊在午宫","含义":"武职显达，马头带剑威震边疆，适合军警/体育/竞技"})

    # 29) 善荫朝纲 — 天机+天梁在辰或戌宫
    for name, p in palaces.items():
        if p["地支"] in ("辰","戌") and both_stars(name, "天机", "天梁"):
            patterns.append({"名称":"善荫朝纲","条件":f"天机+天梁在{p['地支']}宫","含义":"机谋善断，适合策划/咨询/幕僚"})

    # 空宫信息附在格局列表末尾(非格局，是盘面特征)
    if empty_palaces:
        kong_items = []
        for e in empty_palaces:
            stars = '、'.join(e['借星']) if e['借星'] else '无'
            kong_items.append(f"{e['宫名']}({e['地支']})借{e['对宫']}星{stars}")
        patterns.append({
            "名称": "空宫借对宫",
            "条件": "；".join(kong_items),
            "含义": "空宫需借对宫主星分析，力量较实宫为弱",
        })

    return patterns


# =============================================================================
# 辅星扩充（乙级星）
# =============================================================================

def an_hongluan_tianxi(year_zhi: str) -> dict:
    """
    安红鸾天喜。
    红鸾: 卯起子年逆数。
    天喜: 红鸾的对宫（相差6位）。
    """
    start_idx = DIZHI.index("卯")
    year_idx = DIZHI.index(year_zhi)
    hongluan_zhi = DIZHI[(start_idx - year_idx) % 12]  # 子年=卯, 逆数
    tianxi_zhi = DIZHI[(DIZHI.index(hongluan_zhi) + 6) % 12]
    return {hongluan_zhi: ["红鸾"], tianxi_zhi: ["天喜"]}


def an_tianyao(year_zhi: str) -> dict:
    """安天姚: 丑起子年顺数。"""
    start_idx = DIZHI.index("丑")
    year_idx = DIZHI.index(year_zhi)
    tianyao_zhi = DIZHI[(start_idx + year_idx) % 12]
    return {tianyao_zhi: ["天姚"]}


def an_tianxing(birth_month: int) -> dict:
    """安天刑: 酉起正月顺数。"""
    tianxing_zhi = DIZHI[(DIZHI.index("酉") + (birth_month - 1)) % 12]
    return {tianxing_zhi: ["天刑"]}


def an_jieshen(birth_month: int) -> dict:
    """安解神: 戌起正月顺数。"""
    jieshen_zhi = DIZHI[(DIZHI.index("戌") + (birth_month - 1)) % 12]
    return {jieshen_zhi: ["解神"]}


def an_tianwu(birth_month: int) -> dict:
    """安天巫: 巳起正月顺数。"""
    tianwu_zhi = DIZHI[(DIZHI.index("巳") + (birth_month - 1)) % 12]
    return {tianwu_zhi: ["天巫"]}


def an_yinsha(birth_month: int) -> dict:
    """安阴煞: 寅起正月逆数。"""
    yinsha_zhi = DIZHI[(DIZHI.index("寅") - (birth_month - 1)) % 12]
    return {yinsha_zhi: ["阴煞"]}


def an_santai_bazuo(birth_day_zhi: str) -> dict:
    """安三台八座。三台: 辰起子日顺数; 八座: 戌起子日逆数。"""
    day_idx = SHICHEN_ORDER.index(birth_day_zhi)  # 复用时辰地支的顺序
    santai_zhi = DIZHI[(DIZHI.index("辰") + day_idx) % 12]
    bazuo_zhi = DIZHI[(DIZHI.index("戌") - day_idx) % 12]
    return {santai_zhi: ["三台"], bazuo_zhi: ["八座"]}


def an_enguang_tiangui(birth_hour_zhi: str) -> dict:
    """安恩光天贵。恩光: 戌起子时顺数; 天贵: 辰起子时逆数。"""
    hour_idx = SHICHEN_ORDER.index(birth_hour_zhi)
    enguang_zhi = DIZHI[(DIZHI.index("戌") + hour_idx) % 12]
    tiangui_zhi = DIZHI[(DIZHI.index("辰") - hour_idx) % 12]
    return {enguang_zhi: ["恩光"], tiangui_zhi: ["天贵"]}


def an_xianchi(year_zhi: str) -> dict:
    """安咸池(桃花煞): 卯起子年逆数。"""
    start_idx = DIZHI.index("卯")
    year_idx = DIZHI.index(year_zhi)
    xianchi_zhi = DIZHI[(start_idx - year_idx) % 12]
    return {xianchi_zhi: ["咸池"]}


def an_guchen_guasu(year_zhi: str) -> dict:
    """
    安孤辰寡宿。年支三合局确定起点。
    孤辰: 寅(申子辰) 巳(亥卯未) 申(寅午戌) 亥(巳酉丑)
    寡宿: 戌(申子辰) 丑(亥卯未) 辰(寅午戌) 未(巳酉丑)
    """
    guchen_map = {
        ("申","子","辰"): "寅", ("亥","卯","未"): "巳",
        ("寅","午","戌"): "申", ("巳","酉","丑"): "亥",
    }
    guasu_map = {
        ("申","子","辰"): "戌", ("亥","卯","未"): "丑",
        ("寅","午","戌"): "辰", ("巳","酉","丑"): "未",
    }
    guchen_zhi = guasu_zhi = None
    for k, v in guchen_map.items():
        if year_zhi in k: guchen_zhi = v
    for k, v in guasu_map.items():
        if year_zhi in k: guasu_zhi = v
    result = {}
    if guchen_zhi: result[guchen_zhi] = ["孤辰"]
    if guasu_zhi: result[guasu_zhi] = ["寡宿"]
    return result


def an_tianku_tianxu(year_zhi: str) -> dict:
    """安天哭天虚。午起子年: 天哭逆数, 天虚顺数。"""
    year_idx = DIZHI.index(year_zhi)
    start = DIZHI.index("午")
    ku = DIZHI[(start - year_idx) % 12]
    xu = DIZHI[(start + year_idx) % 12]
    result = {ku: ["天哭"]}
    if xu != ku:
        result[xu] = ["天虚"]
    else:
        result[ku] = result[ku] + ["天虚"]
    return result


def an_longchi_fengge(year_zhi: str) -> dict:
    """安龙池凤阁。辰起子年顺数(龙池), 戌起子年逆数(凤阁)。"""
    year_idx = DIZHI.index(year_zhi)
    return {
        DIZHI[(DIZHI.index("辰") + year_idx) % 12]: ["龙池"],
        DIZHI[(DIZHI.index("戌") - year_idx) % 12]: ["凤阁"],
    }


def an_huagai(year_zhi: str) -> dict:
    """安华盖: 辰未戌丑(对应申子辰/亥卯未/寅午戌/巳酉丑)。"""
    m = {("申","子","辰"):"辰",("亥","卯","未"):"未",("寅","午","戌"):"戌",("巳","酉","丑"):"丑"}
    for k, v in m.items():
        if year_zhi in k: return {v: ["华盖"]}
    return {}


def an_feilian(birth_month: int) -> dict:
    """安蜚廉: 辰起正月顺数。"""
    return {DIZHI[(DIZHI.index("辰") + (birth_month - 1)) % 12]: ["蜚廉"]}


def an_posui(birth_month: int) -> dict:
    """安破碎: 巳起正月顺数。"""
    return {DIZHI[(DIZHI.index("巳") + (birth_month - 1)) % 12]: ["破碎"]}


# =============================================================================
# 博士十二神 — 从禄存宫起，阳男阴女顺行、阴男阳女逆行
# =============================================================================

BOSHI_STARS = ["博士","力士","青龙","小耗","将军","奏书","飞廉","喜神","病符","大耗","伏兵","官府"]

BOSHI_MEANINGS = {
    "博士": "聪明好学，利于科举考试",
    "力士": "有权势助力，得人扶持",
    "青龙": "喜事临门，财运亨通",
    "小耗": "小有损耗，注意节流",
    "将军": "有威势，能掌权",
    "奏书": "文书喜讯，消息通达",
    "飞廉": "口舌是非，慎言慎行",
    "喜神": "喜事连连，心情愉悦",
    "病符": "健康注意，小病缠身",
    "大耗": "破财损耗，投资谨慎",
    "伏兵": "暗中有阻，防小人",
    "官府": "官非诉讼，注意合规",
}


def an_boshi(lucun_zhi: str, gender: str, year_gan: str) -> dict:
    """
    安博士十二神。
    从禄存宫起博士，阳男/阴女顺行，阴男/阳女逆行。
    """
    nian_yy = TIANGAN_YINYANG[year_gan]
    is_shun = (nian_yy == "阳" and gender == "男") or (nian_yy == "阴" and gender == "女")
    start_idx = DIZHI.index(lucun_zhi)
    result = {}
    for i, name in enumerate(BOSHI_STARS):
        if is_shun:
            zhi = DIZHI[(start_idx + i) % 12]
        else:
            zhi = DIZHI[(start_idx - i) % 12]
        result[zhi] = result.get(zhi, []) + [name]
    return result


# =============================================================================
# 长生十二神 — 按五行局长生位顺排十二宫
# =============================================================================

CHANGSHENG_STARS = ["长生","沐浴","冠带","临官","帝旺","衰","病","死","墓","绝","胎","养"]

# 五行局 → 长生起始地支
WUXING_JU_CHANGSHENG = {
    "水": "申", "木": "亥", "火": "寅", "金": "巳", "土": "申",
}


def an_changsheng(wuxing_ju_name: str, gender: str, year_gan: str) -> dict:
    """
    安长生十二神。
    阳男/阴女顺行，阴男/阳女逆行。
    长生位: 水=申, 木=亥, 火=寅, 金=巳, 土=申。
    """
    nian_yy = TIANGAN_YINYANG[year_gan]
    is_shun = (nian_yy == "阳" and gender == "男") or (nian_yy == "阴" and gender == "女")
    changsheng_zhi = WUXING_JU_CHANGSHENG.get(wuxing_ju_name, "申")
    start_idx = DIZHI.index(changsheng_zhi)
    result = {}
    for i, name in enumerate(CHANGSHENG_STARS):
        if is_shun:
            zhi = DIZHI[(start_idx + i) % 12]
        else:
            zhi = DIZHI[(start_idx - i) % 12]
        result[zhi] = result.get(zhi, []) + [name]
    return result


# =============================================================================
# 流年十二神 — 从流年地支宫起太岁，顺排十二宫
# =============================================================================

LIUNIAN_STARS = ["太岁","晦气","丧门","贯索","官符","小耗","岁破","龙德","白虎","福德","吊客","病符"]


def an_liunian_shen(liunian_zhi: str) -> dict:
    """安流年十二神：从流年地支宫起太岁，顺排十二宫。"""
    start_idx = DIZHI.index(liunian_zhi)
    result = {}
    for i, name in enumerate(LIUNIAN_STARS):
        zhi = DIZHI[(start_idx + i) % 12]
        result[zhi] = result.get(zhi, []) + [name]
    return result


def an_ziwei(wuxing_ju_num: int, lunar_day: int) -> str:
    """
    安紫微星。
    根据五行局数和农历生日，确定紫微星所在宫位地支。

    算法: 生日 ÷ 局数 = 商(整数部分)

    如果整除:
      紫微位置 = 从寅宫数(商)位
    如果不整除:
      需要"补数"使生日能整除，补数方法为逐步增加
      紫微位置 = 从寅宫数(商 + 某种偏移)位

    简化算法表:
    """
    # 五行局对应的紫微星位置查找表
    # key = 局数, value = {生日: 紫微位置(从寅起算, 寅=0)}
    # 以下为完整的紫微星安星表

    ziwei_table = _build_ziwei_table()

    key = (wuxing_ju_num, lunar_day)
    if key in ziwei_table:
        offset = ziwei_table[key]
        # offset 是从寅宫数起的偏移
        return DIZHI[(2 + offset) % 12]  # 寅=索引2
    else:
        # 生日超出范围（>30），按算法推算
        # (生日 + X) 能被局数整除的最小 X 对应的偏移
        return _calc_ziwei_fallback(wuxing_ju_num, lunar_day)


def _calc_ziwei_fallback(ju_num: int, lunar_day: int) -> str:
    """
    兜底算法（lunar_day > 30 时使用）。

    退位法 (标准紫微斗数安星法):
    逐日往回退，直到日期能被局数整除（或退至1），
    商数即为从寅宫起算的偏移量。

    原理: 紫微星每 ju_num 天前进一宫，在两次前进之间"原地停留"。
    退位法通过将日期退到上一个"前进日"来确定当前紫微星位置。
    """
    if lunar_day <= 0:
        return DIZHI[2]  # fallback: 寅宫

    d = lunar_day
    while d > 1 and d % ju_num != 0:
        d -= 1

    offset = d // ju_num if d > 0 else 0
    return DIZHI[(2 + offset) % 12]


def _build_ziwei_table() -> dict:
    """
    构建紫微星安星表（退位法）。

    算法说明:
    - 水2局: 每2天前进一宫 (D1→寅, D2→卯, D3→卯, D4→辰, ...)
    - 木3局: 每3天前进一宫 (D1→寅, D2→寅, D3→卯, D4→卯, D5→卯, D6→辰, ...)
    - 金4局: 每4天前进一宫
    - 土5局: 每5天前进一宫
    - 火6局: 每6天前进一宫

    紫微星单调顺时针方向前进，不会逆跳。
    """
    table = {}

    for ju_num in [2, 3, 4, 5, 6]:
        for day in range(1, 31):
            d = day
            while d > 1 and d % ju_num != 0:
                d -= 1
            offset = d // ju_num if d > 0 else 0
            table[(ju_num, day)] = offset % 12

    return table


# =============================================================================
# 安十四主星
# =============================================================================

# 紫微系星序（逆行）: 紫微→天机→(空一格)→太阳→武曲→天同→(空二格)→廉贞
ZIWEI_XI = ["紫微","天机","","太阳","武曲","天同","","","廉贞"]
# 天府系星序（顺行）: 天府→太阴→贪狼→巨门→天相→天梁→七杀→(空三格)→破军
TIANFU_XI = ["天府","太阴","贪狼","巨门","天相","天梁","七杀","","","","破军"]


def an_ziwei_xi_stars(ziwei_zhi: str) -> dict:
    """安紫微系6星."""
    stars = {}
    ziwei_idx = DIZHI.index(ziwei_zhi)

    # 紫微系逆行放置
    ziwei_offsets = [0, -1, -2, -3, -4, -5]  # 紫微 天机 X 太阳 武曲 天同 X X 廉贞
    ziwei_names = ["紫微","天机","","太阳","武曲","天同","","","廉贞"]

    # 实际上紫微系6星的位置是固定的相对偏移
    # 紫微(0), 天机(-1), 太阳(-3), 武曲(-4), 天同(-5), 廉贞(-8)
    offsets_map = {
        "紫微": 0, "天机": -1, "太阳": -3, "武曲": -4, "天同": -5, "廉贞": -8
    }

    for name, offset in offsets_map.items():
        zhi = DIZHI[(ziwei_idx + offset) % 12]
        stars[zhi] = stars.get(zhi, []) + [name]

    return stars


def an_tianfu(ziwei_zhi: str) -> str:
    """
    安天府星: 紫微与天府在寅申线对称。
    寅(2) ↔ 申(8), 中点=辰(5), 对称公式: tianfu_idx = (10 - ziwei_idx) % 12
    例如: 紫微在寅(2) → 天府在申(8); 紫微在申(8) → 天府在寅(2).
    """
    ziwei_idx = DIZHI.index(ziwei_zhi)  # 0-11
    tianfu_idx = (10 - ziwei_idx) % 12
    return DIZHI[tianfu_idx]


def an_tianfu_xi_stars(tianfu_zhi: str) -> dict:
    """安天府系8星."""
    stars = {}
    tianfu_idx = DIZHI.index(tianfu_zhi)

    offsets_map = {
        "天府": 0, "太阴": 1, "贪狼": 2, "巨门": 3,
        "天相": 4, "天梁": 5, "七杀": 6, "破军": 10,
    }

    for name, offset in offsets_map.items():
        zhi = DIZHI[(tianfu_idx + offset) % 12]
        stars[zhi] = stars.get(zhi, []) + [name]

    return stars


# =============================================================================
# 安辅星和煞星
# =============================================================================

def an_wenchang_wenqu(birth_hour_zhi: str) -> dict:
    """安文昌、文曲。文昌按戌起子时逆数, 文曲按辰起子时顺数。"""
    hour_idx = SHICHEN_ORDER.index(birth_hour_zhi)  # 子=0

    wenchang_start = DIZHI.index("戌")
    wenqu_start = DIZHI.index("辰")

    wenchang_zhi = DIZHI[(wenchang_start - hour_idx) % 12]
    wenqu_zhi = DIZHI[(wenqu_start + hour_idx) % 12]

    result = {}
    result[wenchang_zhi] = result.get(wenchang_zhi, []) + ["文昌"]
    result[wenqu_zhi] = result.get(wenqu_zhi, []) + ["文曲"]
    return result


def an_zuofu_youbi(birth_month: int) -> dict:
    """安左辅右弼。左辅辰起正月顺数, 右弼戌起正月逆数。"""
    # 正月=辰, 顺数
    zuofu_zhi = DIZHI[(DIZHI.index("辰") + (birth_month - 1)) % 12]
    youbi_zhi = DIZHI[(DIZHI.index("戌") - (birth_month - 1)) % 12]

    return {
        zuofu_zhi: ["左辅"],
        youbi_zhi: ["右弼"],
    }


def an_tiankui_tianyue(year_gan: str) -> dict:
    """安天魁天钺。按年干。"""
    kui_map = {
        "甲":"丑","戊":"丑","庚":"丑",
        "乙":"子","己":"子",
        "丙":"亥","丁":"亥",
        "壬":"卯","癸":"卯",
        "辛":"午",
    }
    yue_map = {
        "甲":"未","戊":"未","庚":"未",
        "乙":"申","己":"申",
        "丙":"酉","丁":"酉",
        "壬":"巳","癸":"巳",
        "辛":"寅",
    }
    result = {}
    if year_gan in kui_map:
        result[kui_map[year_gan]] = ["天魁"]
    if year_gan in yue_map:
        result[yue_map[year_gan]] = result.get(yue_map[year_gan], []) + ["天钺"]
    return result


def an_lucun_tianma(year_gan: str, year_zhi: str) -> dict:
    """安禄存和天马。禄存按年干, 天马按年支三合局。"""
    lucun_map = {
        "甲":"寅","乙":"卯","丙":"巳","丁":"午","戊":"巳",
        "己":"午","庚":"申","辛":"酉","壬":"亥","癸":"子",
    }
    # 天马: 申子辰在寅, 亥卯未在巳, 寅午戌在申, 巳酉丑在亥（三合局长生位之冲）
    tianma_map = {
        ("申","子","辰"): "寅",
        ("亥","卯","未"): "巳",
        ("寅","午","戌"): "申",
        ("巳","酉","丑"): "亥",
    }

    result = {}
    if year_gan in lucun_map:
        result[lucun_map[year_gan]] = result.get(lucun_map[year_gan], []) + ["禄存"]

    for sanhe, ma_zhi in tianma_map.items():
        if year_zhi in sanhe:
            result[ma_zhi] = result.get(ma_zhi, []) + ["天马"]
            break

    return result


def an_qingyang_tuoluo(year_gan: str) -> dict:
    """安擎羊陀罗。擎羊在禄存前一宫, 陀罗在禄存后一宫。"""
    lucun_map = {
        "甲":"寅","乙":"卯","丙":"巳","丁":"午","戊":"巳",
        "己":"午","庚":"申","辛":"酉","壬":"亥","癸":"子",
    }
    if year_gan not in lucun_map:
        return {}

    lucun_zhi = lucun_map[year_gan]
    lucun_idx = DIZHI.index(lucun_zhi)
    qingyang_zhi = DIZHI[(lucun_idx + 1) % 12]
    tuoluo_zhi = DIZHI[(lucun_idx - 1) % 12]

    return {
        qingyang_zhi: ["擎羊"],
        tuoluo_zhi: ["陀罗"],
    }


def an_huoxing_lingxing(year_zhi: str, birth_hour_zhi: str) -> dict:
    """安火星铃星。火星按年支起, 铃星按年支起。"""
    # 火星: 申子辰寅起, 亥卯未酉起, 寅午戌丑起, 巳酉丑卯起
    # 然后从起始位顺数至时辰
    huo_start_map = {
        ("申","子","辰"): "寅",
        ("亥","卯","未"): "酉",
        ("寅","午","戌"): "丑",
        ("巳","酉","丑"): "卯",
    }
    # 铃星: 申子辰戌起, 亥卯未巳起, 寅午戌丑起, 巳酉丑卯起
    ling_start_map = {
        ("申","子","辰"): "戌",
        ("亥","卯","未"): "巳",
        ("寅","午","戌"): "丑",
        ("巳","酉","丑"): "卯",
    }

    hour_idx = SHICHEN_ORDER.index(birth_hour_zhi)

    huo_zhi = None
    ling_zhi = None

    # 火铃星起始表按三合局分组。注意 "丑" 同时出现在寅午戌和巳酉丑
    # 字典遍历是无序的，为避免歧义，用明确的 if-elif 匹配
    if year_zhi in ("巳","酉","丑"):
        huo_start = "卯"
        ling_start = "卯"
    elif year_zhi in ("寅","午","戌"):
        huo_start = "丑"
        ling_start = "丑"
    elif year_zhi in ("亥","卯","未"):
        huo_start = "酉"
        ling_start = "巳"
    else:  # 申子辰
        huo_start = "寅"
        ling_start = "戌"

    huo_zhi = DIZHI[(DIZHI.index(huo_start) + hour_idx) % 12]
    ling_zhi = DIZHI[(DIZHI.index(ling_start) + hour_idx) % 12]

    result = {}
    if huo_zhi:
        result[huo_zhi] = result.get(huo_zhi, []) + ["火星"]
    if ling_zhi:
        result[ling_zhi] = result.get(ling_zhi, []) + ["铃星"]
    return result


def an_dikong_dijie(birth_hour_zhi: str) -> dict:
    """安地空地劫。地空亥起子时逆数, 地劫亥起子时顺数。"""
    hour_idx = SHICHEN_ORDER.index(birth_hour_zhi)
    dikong_zhi = DIZHI[(DIZHI.index("亥") - hour_idx) % 12]
    dijie_zhi = DIZHI[(DIZHI.index("亥") + hour_idx) % 12]

    result = {}
    result[dikong_zhi] = result.get(dikong_zhi, []) + ["地空"]
    result[dijie_zhi] = result.get(dijie_zhi, []) + ["地劫"]
    return result


# =============================================================================
# 四化
# =============================================================================

def an_sihua(year_gan: str) -> dict:
    """按年干定四化落在哪颗星上。"""
    sihua_map = {
        "甲": (("廉贞","禄"),("破军","权"),("武曲","科"),("太阳","忌")),
        "乙": (("天机","禄"),("天梁","权"),("紫微","科"),("太阴","忌")),
        "丙": (("天同","禄"),("天机","权"),("文昌","科"),("廉贞","忌")),
        "丁": (("太阴","禄"),("天同","权"),("天机","科"),("巨门","忌")),
        "戊": (("贪狼","禄"),("太阴","权"),("右弼","科"),("天机","忌")),
        "己": (("武曲","禄"),("贪狼","权"),("天梁","科"),("文曲","忌")),
        "庚": (("太阳","禄"),("武曲","权"),("太阴","科"),("天同","忌")),
        "辛": (("巨门","禄"),("太阳","权"),("文曲","科"),("文昌","忌")),
        "壬": (("天梁","禄"),("紫微","权"),("左辅","科"),("武曲","忌")),
        "癸": (("破军","禄"),("巨门","权"),("太阴","科"),("贪狼","忌")),
    }

    year_sihua = sihua_map.get(year_gan, ())
    result = {}
    for star, hua in year_sihua:
        result[hua] = star
    return result


# =============================================================================
# 大限
# =============================================================================

def an_daxian(minggong_zhi: str, wuxing_ju_num: int, gender: str,
              year_gan: str) -> dict:
    """
    排大限。
    阳男/阴女 → 顺行（命宫→父母→福德→田宅→...）
    阴男/阳女 → 逆行（命宫→兄弟→夫妻→子女→...）
    """
    nian_yinyang = TIANGAN_YINYANG[year_gan]

    # 顺行还是逆行
    is_shun = False
    if nian_yinyang == "阳" and gender == "男":
        is_shun = True
    elif nian_yinyang == "阴" and gender == "女":
        is_shun = True

    # 大限起运年龄 = 五行局数（水二局2岁起, 木三局3岁起...）
    # 每宫固定管10年，这是紫微斗数的标准规则
    # 例如：金四局命宫4-13岁，兄弟宫14-23岁，夫妻宫24-33岁...
    base_age = wuxing_ju_num  # 第一个大限的起运年龄 = 五行局数

    # 大限走的宫顺序
    # 顺行: 命宫→父母→福德→田宅→官禄→交友→迁移→疾厄→财帛→子女→夫妻→兄弟
    shun_order = [0, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1]  # PALACES索引
    # 逆行: 命宫→兄弟→夫妻→子女→财帛→疾厄→迁移→交友→官禄→田宅→福德→父母
    ni_order = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]

    order = shun_order if is_shun else ni_order

    daxian = {}
    for i, pal_idx in enumerate(order):
        age_start = base_age + i * 10  # 每宫固定管10年
        age_end = age_start + 9
        daxian[PALACES[pal_idx]] = {
            "年龄": f"{age_start}-{age_end}岁",
            "起运": age_start,
        }

    return {
        "顺逆": "顺行" if is_shun else "逆行",
        "大限": daxian,
    }


# =============================================================================
# 综合排盘
# =============================================================================

def ziwei_pailiang(year: int, month: int, day: int, hour: int,
                   gender: str = "未知",
                   lunar_month: int = None, lunar_day: int = None) -> dict:
    """
    紫微斗数完整排盘。

    参数:
    - year, month, day, hour: 公历出生时间
    - gender: '男' or '女'
    - lunar_month, lunar_day: 如果已知农历月日可直接传入, 否则用公历近似
    """
    # 子时(23:00-23:59)按传统规则属次日, 日期需+1天
    if hour == 23:
        from datetime import timedelta
        dt = datetime(year, month, day, hour) + timedelta(days=1)
    else:
        dt = datetime(year, month, day, hour)

    # 年柱、年干年支（紫微斗数以立春为年柱分界，与八字一致）
    year_gz = get_year_ganzhi(dt)
    year_gan, year_zhi = split_ganzhi(year_gz)

    # 时辰地支
    birth_hour_zhi = HOUR_TO_SHICHEN.get(hour, "子")

    # 农历月日（紫微斗数用日历农历月，非节气月）
    if lunar_month is None:
        lunar_month = determine_calendar_lunar_month(dt)
    if lunar_day is None:
        lunar_day = determine_nongli_day(dt)  # 公历→农历日转换，精度 ±1 天

    # === 排盘流程 ===

    # 1. 安命宫
    minggong_zhi = an_minggong(lunar_month, birth_hour_zhi)

    # 2. 安十二宫地支
    shiergong_zhi = an_shiergong(minggong_zhi)

    # 3. 安十二宫天干
    shiergong_ganzhi = an_gonggan(shiergong_zhi, year_gan)

    # 4. 定五行局
    minggong_gz = shiergong_ganzhi["命宫"]
    wx_ju_name, wx_ju_num = wuxing_ju(minggong_gz)

    # 5. 安紫微星
    ziwei_zhi = an_ziwei(wx_ju_num, lunar_day)

    # 6. 安紫微系星
    ziwei_stars = an_ziwei_xi_stars(ziwei_zhi)

    # 7. 安天府星
    tianfu_zhi = an_tianfu(ziwei_zhi)

    # 8. 安天府系星
    tianfu_stars = an_tianfu_xi_stars(tianfu_zhi)

    # 9. 安文昌文曲
    cc_stars = an_wenchang_wenqu(birth_hour_zhi)

    # 10. 安左辅右弼
    zy_stars = an_zuofu_youbi(lunar_month)

    # 11. 安天魁天钺
    ky_stars = an_tiankui_tianyue(year_gan)

    # 12. 安禄存天马
    lt_stars = an_lucun_tianma(year_gan, year_zhi)

    # 13. 安擎羊陀罗
    qt_stars = an_qingyang_tuoluo(year_gan)

    # 14. 安火星铃星
    hl_stars = an_huoxing_lingxing(year_zhi, birth_hour_zhi)

    # 15. 安地空地劫
    kj_stars = an_dikong_dijie(birth_hour_zhi)

    # 16. 四化
    sihua = an_sihua(year_gan)

    # 17. 安身宫、身主、命主
    shengong_zhi = an_shengong(lunar_month, birth_hour_zhi)
    shenzhu = SHENZHU_STAR.get(year_zhi, "")
    mingzhu = MINGZHU_STAR.get(year_zhi, "")

    # 18. 找来因宫
    laiyin_gong = an_laiyingong(shiergong_ganzhi, year_gan)

    # 19. 安辅星（乙级及杂曜）
    day_gz = index_to_ganzhi(ganzhi_to_index(year_gz) + (lunar_day - 1))
    day_zhi = split_ganzhi(day_gz)[1]
    # 年支起星
    hl_tx_stars = an_hongluan_tianxi(year_zhi)
    ty_stars = an_tianyao(year_zhi)
    gc_stars = an_guchen_guasu(year_zhi)
    kx_stars = an_tianku_tianxu(year_zhi)
    lf_stars = an_longchi_fengge(year_zhi)
    hg_stars = an_huagai(year_zhi)
    xc_stars = an_xianchi(year_zhi)
    # 月支起星
    tx_stars = an_tianxing(lunar_month)
    js_stars = an_jieshen(lunar_month)
    tw_stars = an_tianwu(lunar_month)
    ys_stars = an_yinsha(lunar_month)
    fl_stars = an_feilian(lunar_month)
    ps_stars = an_posui(lunar_month)
    # 日/时起星
    sb_stars = an_santai_bazuo(day_zhi)
    eg_stars = an_enguang_tiangui(birth_hour_zhi)

    # 博士十二神：从禄存宫起
    lucun_zhi = list(lt_stars.keys())[0] if lt_stars else "寅"
    boshi_stars = an_boshi(lucun_zhi, gender, year_gan)

    # 长生十二神：按五行局起
    changsheng_stars = an_changsheng(wx_ju_name, gender, year_gan)

    # 流年十二神：按当前流年地支起
    current_liunian = get_year_ganzhi(datetime.now())
    liunian_zhi = split_ganzhi(current_liunian)[1] if current_liunian else "子"
    liunian_stars = an_liunian_shen(liunian_zhi)

    # 20. 汇总每宫星曜
    all_stars = {}  # {zhi: {main: [...], aux: [...]}}
    for zhi in GONG_DIZHI:
        all_stars[zhi] = {"主星": [], "辅星": []}

    # 合并主星
    for star_dict in [ziwei_stars, tianfu_stars]:
        for zhi, names in star_dict.items():
            all_stars[zhi]["主星"].extend(names)

    # 合并辅星
    for star_dict in [cc_stars, zy_stars, ky_stars, lt_stars, qt_stars, hl_stars, kj_stars,
                      hl_tx_stars, ty_stars, tx_stars, js_stars, tw_stars, ys_stars, sb_stars, eg_stars,
                      gc_stars, kx_stars, lf_stars, hg_stars, xc_stars, fl_stars, ps_stars,
                      boshi_stars, changsheng_stars, liunian_stars]:
        for zhi, names in star_dict.items():
            all_stars[zhi]["辅星"].extend(names)

    # 21. 构建十二宫完整信息
    palaces_full = []
    for pal_name in PALACES:
        zhi = shiergong_zhi[pal_name]
        gz = shiergong_ganzhi[pal_name]
        main = all_stars[zhi]["主星"]
        aux = all_stars[zhi]["辅星"]

        # 标记四化
        hua_tags = []
        for star in main + aux:
            for hua_type in ["禄","权","科","忌"]:
                if hua_type in sihua and sihua[hua_type] == star:
                    hua_tags.append(f"{star}化{hua_type}")

        # 星曜亮度（主星+主要辅星）
        brightness = {}
        for s in main:
            brightness[s] = get_star_brightness(s, zhi)
        for s in aux:
            if s in FU_BRIGHTNESS:
                brightness[s] = get_star_brightness(s, zhi)

        # 是否身宫
        is_shengong = (zhi == shengong_zhi)

        palaces_full.append({
            "宫名": pal_name,
            "地支": zhi,
            "干支": gz,
            "主星": main,
            "辅星": aux,
            "四化": hua_tags,
            "星曜亮度": brightness,
            "身宫": is_shengong,
        })

    # 22. 大限
    daxian = an_daxian(minggong_zhi, wx_ju_num, gender, year_gan)

    # 23. 格局检测
    result = {
        "命宫": minggong_zhi,
        "命宫干支": minggong_gz,
        "五行局": f"{wx_ju_name}{wx_ju_num}局",
        "紫微星落宫": ziwei_zhi,
        "天府星落宫": tianfu_zhi,
        "十二宫": palaces_full,
        "四化": sihua,
        "大限": daxian,
        "身宫": shengong_zhi,
        "身主": shenzhu,
        "命主": mingzhu,
        "来因宫": laiyin_gong,
        "农历月": lunar_month,
        "农历日": lunar_day,
        "ziwei_version": "2.0",
    }

    result["格局"] = check_patterns(result)
    return result


# =============================================================================
# 自检
# =============================================================================

def verify_ziwei(result: dict) -> list:
    """紫微斗数排盘自检."""
    issues = []

    # 十二宫完整性
    palaces = result.get("十二宫", [])
    if len(palaces) != 12:
        issues.append(f"十二宫数量异常: {len(palaces)}")

    # 每宫必须有地支和干支
    for p in palaces:
        if not p.get("地支"):
            issues.append(f"{p['宫名']} 缺少地支")
        if not p.get("干支"):
            issues.append(f"{p['宫名']} 缺少干支")

    # 紫微星应在合理宫位
    ziwei = result.get("紫微星落宫", "")
    if ziwei not in DIZHI:
        issues.append(f"紫微星位置异常: {ziwei}")

    # 天府星与紫微星对称
    tianfu = result.get("天府星落宫", "")
    if tianfu not in DIZHI:
        issues.append(f"天府星位置异常: {tianfu}")

    # 命宫应有干支
    if not result.get("命宫干支"):
        issues.append("缺少命宫干支")

    # 身宫
    shengong = result.get("身宫", "")
    if shengong not in DIZHI:
        issues.append(f"身宫位置异常: {shengong}")

    # 身主
    if not result.get("身主"):
        issues.append("缺少身主")

    # 庙旺利陷覆盖
    for p in palaces:
        if p.get("星曜亮度") is None:
            issues.append(f"{p['宫名']} 缺少星曜亮度")

    # 五行局
    if not result.get("五行局"):
        issues.append("缺少五行局")

    # 四化
    sihua = result.get("四化", {})
    if len(sihua) != 4:
        issues.append(f"四化数量异常: {len(sihua)} (应为4)")

    # 大限
    daxian = result.get("大限", {})
    if not daxian.get("大限"):
        issues.append("缺少大限信息")

    return issues


# =============================================================================
# Standalone testing
# =============================================================================

if __name__ == "__main__":
    import json

    print("=" * 60)
    print("紫微斗数 排盘测试")
    print("=" * 60)

    # 测试: 1990-06-15 08:00 男
    result = ziwei_pailiang(1990, 6, 15, 8, "男", None, 15)

    print(f"命宫: {result['命宫']} ({result['命宫干支']})")
    print(f"五行局: {result['五行局']}")
    print(f"紫微星: {result['紫微星落宫']}")
    print(f"天府星: {result['天府星落宫']}")
    print(f"四化: {result['四化']}")
    print(f"大限: {result['大限']['顺逆']}")

    print("\n十二宫:")
    for p in result["十二宫"]:
        main = ",".join(p["主星"]) if p["主星"] else "无主星"
        aux = ",".join(p["辅星"]) if p["辅星"] else "无辅星"
        sihua = ",".join(p["四化"]) if p["四化"] else ""
        print(f"  {p['宫名']}({p['地支']} {p['干支']}): 主=[{main}] 辅=[{aux}] {sihua}")

    print("\n大限:")
    for pal, info in result["大限"]["大限"].items():
        print(f"  {pal}: {info['年龄']}")

    issues = verify_ziwei(result)
    if issues:
        print("\n[!] 自检问题:")
        for i in issues:
            print(f"  - {i}")
    else:
        print("\n[OK] 自检通过")
