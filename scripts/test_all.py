#!/usr/bin/env python3
"""推算 Skill — 综合测试"""

import sys; sys.stdout.reconfigure(encoding='utf-8')  # Windows GBK 修复

import os, json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from utils import (
    xiaoliuren, XIAOLIUREN_STATIONS,
    number_to_bagua, number_to_yao,
    day_ganzhi, SEXAGENARY, TIANGAN, DIZHI,
    ganzhi_to_index, index_to_ganzhi,
)
from bagua import (
    meihua_from_numbers, meihua_from_datetime,
    liuyao_construct, liuyao_zhuanggua, liuyao_auto_qigua,
    verify_liuyao, HEXAGRAMS,
    get_hexagram_by_trigrams, get_nazhi, get_liuqin,
    get_liushou, get_shiying, PALACE_WUXING,
    NAZHI_YANG, NAZHI_YIN,
)
from ganzhi import (
    pai_sizhu, get_year_ganzhi, get_month_ganzhi,
    get_hour_ganzhi, determine_nongli_month,
    day_ganzhi as gz_day_ganzhi, bazi_full,
)
from datetime import datetime, date

PASS = 0
FAIL = 0

def check(desc, condition):
    global PASS, FAIL
    if condition:
        PASS += 1
        print(f"  [PASS] {desc}")
    else:
        FAIL += 1
        print(f"  [FAIL] {desc}")

print("=" * 60)
print("推算 Skill — 综合测试")
print("=" * 60)

# =============================================================================
# 1. 干支基础测试
# =============================================================================
print("\n## 1. 干支基础")

# 六十甲子循环
check("六十甲子表有60项", len(SEXAGENARY) == 60)
check("甲子在索引0", SEXAGENARY[0] == "甲子")
check("癸亥在索引59", SEXAGENARY[59] == "癸亥")

# 日柱计算
check("1900-01-01 = 甲戌", day_ganzhi(date(1900, 1, 1)) == "甲戌")
check("2026-06-23 日柱存在且合法", day_ganzhi(date(2026, 6, 23)) in SEXAGENARY)

# 年柱（以立春为界）
check("2024-02-03 年柱为癸卯(立春前)", get_year_ganzhi(datetime(2024, 2, 3, 12, 0)) == "癸卯")
check("2024-02-05 年柱为甲辰(立春后)", get_year_ganzhi(datetime(2024, 2, 5, 12, 0)) == "甲辰")

# =============================================================================
# 2. 小六壬测试
# =============================================================================
print("\n## 2. 小六壬")

result = xiaoliuren(1, 1)  # 正月, 初一
check("正月+初一 落位在六掌诀中", result["final_station"] in XIAOLIUREN_STATIONS)
check("月上起日中间步骤存在", "month_station" in result)
check("日落位属性存在", "attrs" in result)

result2 = xiaoliuren(6, 15, "午")
check("六月十五午时 落位有效", result2["final_station"] in XIAOLIUREN_STATIONS)

# 边界测试
result3 = xiaoliuren(12, 30, "子")
check("腊月三十子时 不报错", result3["final_station"] in XIAOLIUREN_STATIONS)

# =============================================================================
# 3. 梅花易数测试
# =============================================================================
print("\n## 3. 梅花易数")

meihua = meihua_from_numbers(123, 456, 789)
check("本卦存在", meihua["本卦"] is not None)
check("互卦存在", meihua["互卦"] is not None)
check("变卦存在", meihua["变卦"] is not None)
check("体卦在八卦中", meihua["体卦"] in ["乾","兑","离","震","巽","坎","艮","坤"])
check("用卦在八卦中", meihua["用卦"] in ["乾","兑","离","震","巽","坎","艮","坤"])
check("体卦五行有效", meihua["体卦五行"] in "木火土金水")
check("体用关系有效", meihua["体用关系"] in ["同","a生b","a克b","a被b生","a被b克"])
check("动爻在1-6", 1 <= meihua["动爻"] <= 6)

# 时间起卦
now_meihua = meihua_from_datetime()
check("时间起卦 本卦非空", now_meihua["本卦"] is not None)

# 换几组数字再测
for a, b, c in [(1, 2, 3), (8, 8, 8), (7, 7, 7)]:
    m = meihua_from_numbers(a, b, c)
    check(f"三数({a},{b},{c}) 起卦成功", m["本卦"] is not None)

# =============================================================================
# 4. 六爻测试
# =============================================================================
print("\n## 4. 六爻")

# 4.1 手动构建
lines = [7, 8, 6, 7, 7, 9]  # 2个动爻
result = liuyao_construct(lines)
check("本卦非空", result["本卦"] is not None)
check("动爻正确", result["动爻"] == [3, 6])
check("摇卦记录保存", result["摇卦记录"] == lines)

# 装卦
today_gz = day_ganzhi(date.today())
zhuanggua = liuyao_zhuanggua(result, today_gz)
check("装卦无错误", "error" not in zhuanggua)
check("卦宫有效", zhuanggua["卦宫"] in ["乾","坎","艮","震","巽","离","坤","兑"])
check("世爻在1-6", 1 <= zhuanggua["世爻位置"] <= 6)
check("应爻在1-6", 1 <= zhuanggua["应爻位置"] <= 6)
check("六爻辞6条", len(zhuanggua["爻辞"]) == 6)
check("六兽6个", len(zhuanggua["六兽"]) == 6)

# 检查每条爻
for y in zhuanggua["爻辞"]:
    check(f"{y['爻位']} 纳支非空", y["纳支"] != "")
    check(f"{y['爻位']} 六亲非空", y["六亲"] != "")
    check(f"{y['爻位']} 六兽非空", y["六兽"] != "")

# 检查世应唯一性
shi_count = sum(1 for y in zhuanggua["爻辞"] if y["世应"] == "世")
ying_count = sum(1 for y in zhuanggua["爻辞"] if y["世应"] == "应")
check("恰好一个世爻", shi_count == 1)
check("恰好一个应爻", ying_count == 1)

# 4.2 自动起卦
auto_result = liuyao_auto_qigua()
check("自动起卦 本卦非空", auto_result["本卦"] is not None)
auto_issues = verify_liuyao(auto_result)
check("自动起卦 自检通过", len(auto_issues) == 0)

# 4.3 不动爻的卦（全静爻）
jing_lines = [7, 8, 7, 8, 7, 8]
jing_result = liuyao_construct(jing_lines)
check("静卦 动爻为空", len(jing_result["动爻"]) == 0)
jing_zg = liuyao_zhuanggua(jing_result, today_gz)
check("静卦 装卦成功", "error" not in jing_zg)

# 4.4 全动爻的卦
dong_lines = [6, 9, 6, 9, 6, 9]
dong_result = liuyao_construct(dong_lines)
check("全动卦 动爻有6个", len(dong_result["动爻"]) == 6)

# =============================================================================
# 5. 六十四卦完整性测试
# =============================================================================
print("\n## 5. 六十四卦完整性")

check("六十四卦完整", len(HEXAGRAMS) == 64)

# 每宫8卦
from collections import Counter
palace_count = Counter(h["palace"] for h in HEXAGRAMS)
for p in ["乾","坎","艮","震","巽","离","坤","兑"]:
    check(f"{p}宫有8卦", palace_count[p] == 8)

# 每卦能查到纳支
for h in HEXAGRAMS:
    nazhi = get_nazhi(h)
    check(f"{h['full_name']} 纳支有6条", len(nazhi) == 6)

# =============================================================================
# 6. 八字排盘测试（基础验证，第二阶段才用）
# =============================================================================
print("\n## 6. 八字排盘（基础验证）")

sizhu = pai_sizhu(1990, 6, 15, 8)
check("四柱完整", all(k in sizhu for k in ["年柱","月柱","日柱","时柱"]))
check("纳音完整", all(k in sizhu["纳音"] for k in ["年","月","日","时"]))
check("日干五行有效", sizhu["日主五行"] in "木火土金水")

bazi = bazi_full(2000, 1, 1, 12, "女")
check("八字全盘 大运有8步", len(bazi["大运"]["大运列表"]) == 8)
check("八字全盘 神煞存在", isinstance(bazi["神煞"], list))
check("八字全盘 流年有效", bazi["流年"] in SEXAGENARY)

# =============================================================================
# 7. 紫微斗数测试
# =============================================================================
print("\n## 7. 紫微斗数")

from ziwei import ziwei_pailiang, verify_ziwei

# 测试1: 1990-06-15 08:00 男 (腊月十五)
r1 = ziwei_pailiang(1990, 6, 15, 8, "男", None, 15)
check("紫微-命宫非空", r1["命宫"] in DIZHI)
check("紫微-命宫有干支", len(r1["命宫干支"]) == 2)
check("紫微-五行局含'局'", "局" in r1["五行局"])
check("紫微-紫微星落宫有效", r1["紫微星落宫"] in DIZHI)
check("紫微-天府星落宫有效", r1["天府星落宫"] in DIZHI)
check("紫微-四化有4项", len(r1["四化"]) == 4)
check("紫微-十二宫12个", len(r1["十二宫"]) == 12)
check("紫微-大限非空", len(r1["大限"]["大限"]) == 12)

# 每宫必须有地支和干支
for p in r1["十二宫"]:
    check(f"紫微-{p['宫名']}有地支", p["地支"] in DIZHI)
    check(f"紫微-{p['宫名']}有干支", len(p["干支"]) == 2)

# 自检
issues1 = verify_ziwei(r1)
check("紫微-自检通过(1990男)", len(issues1) == 0)

# 测试2: 2000-01-01 12:00 女
r2 = ziwei_pailiang(2000, 1, 1, 12, "女", None, 1)
check("紫微-命宫有效(2000女)", r2["命宫"] in DIZHI)
issues2 = verify_ziwei(r2)
check("紫微-自检通过(2000女)", len(issues2) == 0)

# 测试3: 2004-01-06 01:40 男 (你的盘)
r3 = ziwei_pailiang(2004, 1, 6, 1, "男")
check("紫微-命宫有效(2004男)", r3["命宫"] in DIZHI)
check("紫微-五行局=金4局", r3["五行局"] == "金4局")
check("紫微-天府在巳", r3["天府星落宫"] == "巳")
check("紫微-化忌=贪狼", r3["四化"]["忌"] == "贪狼")
issues3 = verify_ziwei(r3)
check("紫微-自检通过(2004男)", len(issues3) == 0)

# =============================================================================
# 8. 奇门遁甲测试
# =============================================================================
print("\n## 8. 奇门遁甲")

from qimen import qimen_pai_pan, verify_qimen
from datetime import datetime

# 测试1: 夏至后 — 阴遁
dt1 = datetime(2026, 6, 23, 14, 0)
r4 = qimen_pai_pan(dt1)
check("奇门-阴阳遁=阴遁(夏至后)", r4["阴阳遁"] == "阴遁")
check("奇门-局数含'局'", "局" in r4["局数"])
check("奇门-值符星非空", len(r4["值符星"]) > 0)
check("奇门-值使门非空", len(r4["值使门"]) > 0)
check("奇门-九宫9个", len(r4["九宫"]) == 9)
check("奇门-日干落宫有效", isinstance(r4["日干落宫"], int) or r4["日干落宫"] is None)
for p in r4["九宫"]:
    check(f"奇门-{p['name']}有八字", "bagua" in p)
issues4 = verify_qimen(r4)
check("奇门-自检通过(夏至后阴遁)", len(issues4) == 0)

# 测试2: 冬至后 — 阳遁
dt2 = datetime(2026, 1, 15, 10, 0)
r5 = qimen_pai_pan(dt2)
check("奇门-阴阳遁=阳遁(冬至后)", r5["阴阳遁"] == "阳遁")
issues5 = verify_qimen(r5)
check("奇门-自检通过(冬至后阳遁)", len(issues5) == 0)

# 测试3: 春分附近
dt3 = datetime(2026, 3, 25, 8, 0)
r6 = qimen_pai_pan(dt3)
check("奇门-春分阳遁", r6["阴阳遁"] == "阳遁")
issues6 = verify_qimen(r6)
check("奇门-自检通过(春分)", len(issues6) == 0)

# =============================================================================
# 9. 纳支表测试
# =============================================================================
print("\n## 9. 纳支表验证")

for name, nazhi_list in NAZHI_YANG.items():
    check(f"阳卦{name}纳支6条", len(nazhi_list) == 6)
    for z in nazhi_list:
        check(f"阳卦{name}纳支{z}是阳支", z in ["子","寅","辰","午","申","戌"])

for name, nazhi_list in NAZHI_YIN.items():
    check(f"阴卦{name}纳支6条", len(nazhi_list) == 6)
    for z in nazhi_list:
        check(f"阴卦{name}纳支{z}是阴支", z in ["丑","亥","酉","未","巳","卯"])

# =============================================================================
# 10. 边界情况
# =============================================================================
print("\n## 10. 边界情况")

# 子时23:00
from utils import hour_to_shichen
check("23:00=子时", hour_to_shichen(23) == "子")
check("0:00=子时", hour_to_shichen(0) == "子")
check("12:00=午时", hour_to_shichen(12) == "午")

# 梅花取数边界
check("1÷8=乾", number_to_bagua(1) == "乾")
check("8÷8=坤", number_to_bagua(8) == "坤")
check("9÷8=乾", number_to_bagua(9) == "乾")

check("1÷6=第1爻", number_to_yao(1) == 1)
check("6÷6=第6爻", number_to_yao(6) == 6)
check("7÷6=第1爻", number_to_yao(7) == 1)

# =============================================================================
# 11. P0 修复专项测试: 天魁天钺、子时换日、年柱立春分界
# =============================================================================
print("\n## 11. P0修复专项验证")

from ziwei import an_tiankui_tianyue, ziwei_pailiang, PALACES as _PALACES
_check_palaces = list(_PALACES)
from ganzhi import get_year_ganzhi, get_year_ganzhi_by_chunjie
from datetime import datetime

# 天魁天钺口诀验证: "甲戊庚牛羊，乙己鼠猴乡，丙丁猪鸡位，壬癸兔蛇藏，辛逢虎马"
# 天魁(阳贵)+天钺(阴贵):
expected_kuiyue = {
    "甲": ("丑","未"), "戊": ("丑","未"), "庚": ("丑","未"),
    "乙": ("子","申"), "己": ("子","申"),
    "丙": ("亥","酉"), "丁": ("亥","酉"),
    "壬": ("卯","巳"), "癸": ("卯","巳"),
    "辛": ("午","寅"),
}
for gan, (kui_zhi, yue_zhi) in expected_kuiyue.items():
    r = an_tiankui_tianyue(gan)
    check(f"天魁-{gan}干天魁在{kui_zhi}", kui_zhi in r and "天魁" in r.get(kui_zhi, []))
    check(f"天钺-{gan}干天钺在{yue_zhi}", yue_zhi in r and "天钺" in r.get(yue_zhi, []))

# 丁年特殊测试（之前有bug）
r_ding = an_tiankui_tianyue("丁")
check("天魁-丁年天魁在亥(修复)", "亥" in r_ding and "天魁" in r_ding["亥"])
check("天钺-丁年天钺在酉(修复)", "酉" in r_ding and "天钺" in r_ding["酉"])
r_gui = an_tiankui_tianyue("癸")
check("天魁-癸年天魁在卯(修复)", "卯" in r_gui and "天魁" in r_gui["卯"])
check("天钺-癸年天钺在巳(修复)", "巳" in r_gui and "天钺" in r_gui["巳"])

# 年柱立春分界验证
dt_lichun = datetime(2024, 2, 5, 12, 0)  # 立春后、春节前
check("立春边界-2024-02-05立春后=甲辰", get_year_ganzhi(dt_lichun) == "甲辰")
check("立春边界-2024-02-05春节前(旧逻辑)≠甲辰", get_year_ganzhi_by_chunjie(dt_lichun) != "甲辰")

# 紫微斗数年柱改用立春
r_lc = ziwei_pailiang(2024, 2, 5, 12, "男")
check("紫微-2024-02-05(立春后)年干=甲", r_lc["四化"] == ziwei_pailiang(2024, 2, 10, 12, "男")["四化"])
# 四化按甲干: 廉贞禄 破军权 武曲科 太阳忌
check("紫微-2024-02-05四化禄=廉贞(甲年)", r_lc["四化"]["禄"] == "廉贞")
check("紫微-2024-02-05四化忌=太阳(甲年)", r_lc["四化"]["忌"] == "太阳")

# 子时换日验证
r_zishi = ziwei_pailiang(2024, 6, 15, 23, "男")
r_nextday = ziwei_pailiang(2024, 6, 16, 0, "男")
check("子时换日-23:00农历日=次日0:00", r_zishi["农历日"] == r_nextday["农历日"])

# 新字段验证
r_v2 = ziwei_pailiang(1990, 6, 15, 8, "男", None, 15)
check("紫微v2-版本号=2.0", r_v2.get("ziwei_version") == "2.0")
check("紫微v2-身宫有效", r_v2.get("身宫") in DIZHI)
check("紫微v2-身主有效", len(r_v2.get("身主", "")) > 0)
check("紫微v2-来因宫有效", r_v2.get("来因宫") in _check_palaces)
check("紫微v2-有格局", isinstance(r_v2.get("格局"), list))
for p in r_v2["十二宫"]:
    check(f"紫微v2-{p['宫名']}有星曜亮度", p.get("星曜亮度") is not None)
    check(f"紫微v2-{p['宫名']}有身宫标记", isinstance(p.get("身宫"), bool))

# =============================================================================
# 12. 八字 P0 修复专项测试: 三合局、子时换日、节气边界
# =============================================================================
print("\n## 12. 八字P0修复专项验证")

from utils import get_dizhi_sanhe, get_solar_term_datetime
from ganzhi import get_year_ganzhi, pai_sizhu
from datetime import datetime

# 三合局验证
sanhe_tests = [
    (("申","子","辰"), "水"), (("亥","卯","未"), "木"),
    (("寅","午","戌"), "火"), (("巳","酉","丑"), "金"),
]
for (a,b,c), wx in sanhe_tests:
    for perm in [(a,b,c),(b,c,a),(c,a,b)]:
        check(f"三合局-{perm}→{wx}", get_dizhi_sanhe(*perm) == wx)

# 子时换日
r_23 = pai_sizhu(2024, 6, 15, 23)
r_00 = pai_sizhu(2024, 6, 16, 0)
check("子时换日-23:00日柱=次日0:00", r_23["日柱"] == r_00["日柱"])

# 立春边界精确时刻
# 2024立春约在2月4日16:21
dt_lc_before = datetime(2024, 2, 4, 10, 0)
dt_lc_after = datetime(2024, 2, 4, 18, 0)
check("立春边界-上午仍属上年(癸卯)", get_year_ganzhi(dt_lc_before) == "癸卯")
check("立春边界-下午已属新年(甲辰)", get_year_ganzhi(dt_lc_after) == "甲辰")

# 年柱非边界不误判
dt_midyear = datetime(2024, 7, 1, 12, 0)
check("年柱-2024年中=甲辰", get_year_ganzhi(dt_midyear) == "甲辰")
dt_jan = datetime(2024, 1, 15, 12, 0)
# 2024年1月15日在立春前，还是癸卯年
check("年柱-2024年初(立春前)=癸卯", get_year_ganzhi(dt_jan) == "癸卯")

# =============================================================================
# 结果汇总
# =============================================================================
print("\n" + "=" * 60)
total = PASS + FAIL
print(f"测试结果: {PASS}/{total} 通过, {FAIL}/{total} 失败")
if FAIL == 0:
    print("全部测试通过！")
else:
    print(f"有 {FAIL} 个测试失败，需要检查！")
print("=" * 60)
