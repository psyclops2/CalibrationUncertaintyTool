from PySide6.QtCore import Qt
import traceback
from decimal import Decimal, getcontext
from .config_loader import ConfigLoader
from .translation_keys import (
    NORMAL_DISTRIBUTION,
    RECTANGULAR_DISTRIBUTION,
    TRIANGULAR_DISTRIBUTION,
    U_DISTRIBUTION,
)


def calculate_type_a_uncertainty(measurements_str):
    """TypeA荳咲｢ｺ縺九＆縺ｮ險育ｮ励ｒ陦後≧"""
    try:
        if not measurements_str:
            return None, None, None, None

        # 繧ｫ繝ｳ繝槫玄蛻・ｊ縺ｮ貂ｬ螳壼､繧呈焚蛟､縺ｮ繝ｪ繧ｹ繝医↓螟画鋤
        measurements = [Decimal(x.strip()) for x in measurements_str.split(",")]

        if not measurements:
            return None, None, None, None

        # 閾ｪ逕ｱ蠎ｦ・医ョ繝ｼ繧ｿ謨ｰ - 1・・
        degrees_of_freedom = len(measurements) - 1

        # 蟷ｳ蝮・､・井ｸｭ螟ｮ蛟､・・
        central_value = sum(measurements) / Decimal(len(measurements))

        # 讓呎ｺ紋ｸ咲｢ｺ縺九＆・域ｨ呎ｺ門￥蟾ｮ / 竏嗜・・
        if len(measurements) > 1:
            variance = sum((x - central_value) ** 2 for x in measurements) / Decimal(
                len(measurements) - 1
            )
            standard_uncertainty = variance.sqrt() / Decimal(len(measurements)).sqrt()
        else:
            standard_uncertainty = 0

        return degrees_of_freedom, central_value, standard_uncertainty, measurements_str

    except Exception as e:
        print(f"縲舌お繝ｩ繝ｼ縲禅ypeA荳咲｢ｺ縺九＆險育ｮ励お繝ｩ繝ｼ: {str(e)}")
        print(traceback.format_exc())
        return None, None, None, None


def calculate_type_b_uncertainty(half_width_str, divisor_str):
    """TypeB荳咲｢ｺ縺九＆縺ｮ險育ｮ励ｒ陦後≧"""
    try:
        if not half_width_str or not divisor_str:
            return None, None

        # 邊ｾ蠎ｦ繧定ｨｭ螳・
        config = ConfigLoader()
        getcontext().prec = config.get_precision()

        # 譁・ｭ怜・繧奪ecimal縺ｫ螟画鋤
        half_width = Decimal(half_width_str)
        divisor = Decimal(divisor_str)

        # 讓呎ｺ紋ｸ咲｢ｺ縺九＆繧定ｨ育ｮ暦ｼ亥濠蛟､蟷・髯､謨ｰ・・
        standard_uncertainty = half_width / divisor

        return half_width, standard_uncertainty

    except ValueError:
        print("縲舌お繝ｩ繝ｼ縲第焚蛟､螟画鋤繧ｨ繝ｩ繝ｼ")
        return None, None
    except Exception as e:
        print(f"縲舌お繝ｩ繝ｼ縲禅ypeB荳咲｢ｺ縺九＆險育ｮ励お繝ｩ繝ｼ: {str(e)}")
        print(traceback.format_exc())
        return None, None


def get_distribution_divisor(distribution):
    """蛻・ｸ・・遞ｮ鬘槭↓蠢懊§縺滄勁謨ｰ繧貞叙蠕・"""
    config = ConfigLoader()
    divisors = config.get_distribution_divisors()
    distribution_key = get_distribution_translation_key(distribution)
    if not distribution_key:
        distribution_key = distribution
    return {
        NORMAL_DISTRIBUTION: "",  # 繝ｦ繝ｼ繧ｶ繝ｼ蜈･蜉・
        RECTANGULAR_DISTRIBUTION: divisors["rectangular"],  # 竏・
        TRIANGULAR_DISTRIBUTION: divisors["triangular"],  # 竏・
        U_DISTRIBUTION: divisors["u"],  # 竏・
        "Normal Distribution": "",
        "Rectangular Distribution": divisors["rectangular"],
        "Triangular Distribution": divisors["triangular"],
        "U-shaped Distribution": divisors["u"],
    }.get(distribution_key, "")


def get_distribution_translation_key(distribution):
    """蛻・ｸ・Λ繝吶Ν/繧ｳ繝ｼ繝峨°繧臥ｿｻ險ｳ繧ｭ繝ｼ繧貞叙蠕・"""
    distribution_map = {
        "Normal Distribution": NORMAL_DISTRIBUTION,
        "Rectangular Distribution": RECTANGULAR_DISTRIBUTION,
        "Triangular Distribution": TRIANGULAR_DISTRIBUTION,
        "U-shaped Distribution": U_DISTRIBUTION,
    }
    if distribution in distribution_map:
        return distribution_map[distribution]
    if distribution in distribution_map.values():
        return distribution
    return ""


def create_empty_value_dict():
    """空の値辞書を作成"""
    return {
        "measurements": "",
        "degrees_of_freedom": 0,
        "central_value": "",
        "standard_uncertainty": "",
        "half_width": "",
        "fixed_value": "",
        "description": "",
        "calculation_formula": "",
        "divisor": "",
    }


def find_variable_item(variable_list, variable_name):
    """螟画焚繝ｪ繧ｹ繝医°繧画欠螳壹＆繧後◆螟画焚縺ｮ繧｢繧､繝・Β繧呈､懃ｴ｢"""
    for i in range(variable_list.count()):
        item = variable_list.item(i)
        if item.data(Qt.UserRole) == variable_name:
            return item
    return None
