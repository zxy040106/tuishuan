# 推算 — Chinese Fortune-Telling

基于 Python 的中国传统命理推算工具集，支持**小六壬、梅花易数、六爻、八字、紫微斗数、奇门遁甲**六种方法。

## 📚 支持的推算方法

| 方法 | 说明 | 适用场景 |
|------|------|----------|
| **小六壬** | 掌诀推算，简单快速 | 日常小事、方位吉凶、速断 |
| **梅花易数** | 以数起卦，灵活多变 | 具体问题占卜、事件预测 |
| **六爻** | 纳甲筮法，信息量大 | 精细占卜、应期推断 |
| **八字** | 四柱命理，人生全局 | 命运走势、性格分析、大运流年 |
| **紫微斗数** | 星曜排盘，十二宫 | 人生全局、各领域详析 |
| **奇门遁甲** | 时空盘式，方位择吉 | 决策指导、方位选择、时机把握 |

## 🗂️ 项目结构

```
推算/
├── SKILL.md                    # 核心 Skill 定义与推算规则
├── scripts/                    # Python 推算引擎
│   ├── bagua.py                # 梅花易数与六爻卦象逻辑
│   ├── ganzhi.py               # 干支计算、八字排盘
│   ├── qimen.py                # 奇门遁甲排盘
│   ├── ziwei.py                # 紫微斗数排盘
│   ├── utils.py                # 小六壬、干支工具、通用函数
│   └── test_all.py             # 综合测试
├── references/                 # 参考文档
│   ├── methods/                # 各方法详细说明
│   │   ├── xiaoliuren.md
│   │   ├── meihua.md
│   │   ├── liuyao.md
│   │   ├── bazi.md
│   │   ├── ziwei.md
│   │   └── qimen.md
│   └── shared/                 # 共享知识库
│       ├── bagua.md            # 八卦基础
│       ├── ganzhi.md           # 干支体系
│       ├── wuxing.md           # 五行生克
│       ├── calendar.md         # 农历与节气
│       └── glossary.md         # 算命术语词典（含白话解释）
└── assets/templates/           # 输出模板
    ├── liuyao_form.md          # 六爻断卦表单
    └── reading_report.md       # 推算报告模板
```

## 🚀 快速开始

### 运行测试

```bash
cd scripts
python test_all.py
```

### 核心功能示例

```python
from utils import xiaoliuren, day_ganzhi
from bagua import meihua_from_numbers, liuyao_auto_qigua
from ganzhi import pai_sizhu, bazi_full

# 小六壬：农历月日时起卦
result = xiaoliuren(month=3, day=15, hour=9)

# 梅花易数：报数起卦
gua = meihua_from_numbers(upper=5, lower=8, changing=3)

# 八字：排四柱
bazi = bazi_full(2000, 1, 1, 12)

# 六爻：自动起卦
liuyao = liuyao_auto_qigua()
```

## 🔧 依赖

- Python ≥ 3.10
- 无第三方依赖（纯标准库实现）

## ⚠️ 免责声明

本项目仅供文化研究和学习参考。推算结果不应被视为科学预测或决策依据。人生重大决策请理性判断。

## 📄 许可

MIT License
