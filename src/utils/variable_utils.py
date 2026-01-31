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
    """TypeA不確かさ（測定値の平均と標準不確かさ）を計算する。"""
    try:
        if not measurements_str:
            return None, None, None, None

        # カンマ区切りの測定値文字列を Decimal に変換
        measurements = [Decimal(x.strip()) for x in measurements_str.split(",")]

        if not measurements:
            return None, None, None, None

        # 自由度 = n - 1
        degrees_of_freedom = len(measurements) - 1

        # 中央値（ここでは算術平均）
        central_value = sum(measurements) / Decimal(len(measurements))

        # 標準不確かさ = 標本標準偏差 / sqrt(n)
        if len(measurements) > 1:
            variance = sum((x - central_value) ** 2 for x in measurements) / Decimal(
                len(measurements) - 1
            )
            standard_uncertainty = variance.sqrt() / Decimal(len(measurements)).sqrt()
        else:
            standard_uncertainty = 0

        return degrees_of_freedom, central_value, standard_uncertainty, measurements_str

    except Exception as e:
        print(f"【エラー】TypeA不確かさ計算エラー: {str(e)}")
        print(traceback.format_exc())
        return None, None, None, None


def calculate_type_b_uncertainty(half_width_str, divisor_str):
    """TypeB不確かさ（半値幅と除数から標準不確かさ）を計算する。"""
    try:
        if not half_width_str or not divisor_str:
            return None, None

        # 精度設定を反映
        config = ConfigLoader()
        getcontext().prec = config.get_precision()

        # 文字列を Decimal に変換
        half_width = Decimal(half_width_str)
        divisor = Decimal(divisor_str)

        # 標準不確かさ = 半値幅 / 除数
        standard_uncertainty = half_width / divisor

        return half_width, standard_uncertainty

    except ValueError:
        print("【エラー】数値変換エラー")
        return None, None
    except Exception as e:
        print(f"【エラー】TypeB不確かさ計算エラー: {str(e)}")
        print(traceback.format_exc())
        return None, None


def get_distribution_divisor(distribution):
    """分布に対応する除数を返す。"""
    config = ConfigLoader()
    divisors = config.get_distribution_divisors()
    distribution_key = get_distribution_translation_key(distribution)
    if not distribution_key:
        distribution_key = distribution
    return {
        NORMAL_DISTRIBUTION: "",  # 正規分布
        RECTANGULAR_DISTRIBUTION: divisors["rectangular"],  # 一様（矩形）分布
        TRIANGULAR_DISTRIBUTION: divisors["triangular"],  # 三角分布
        U_DISTRIBUTION: divisors["u"],  # U字分布
        "Normal Distribution": "",
        "Rectangular Distribution": divisors["rectangular"],
        "Triangular Distribution": divisors["triangular"],
        "U-shaped Distribution": divisors["u"],
    }.get(distribution_key, "")


def get_distribution_translation_key(distribution):
    """分布名（表示名/翻訳キー）を翻訳キーに正規化して返す。"""
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
    """空の値辞書を作成する。"""
    return {
        "measurements": "",
        "degrees_of_freedom": 0,
        "central_value": "",
        "standard_uncertainty": "",
        "half_width": "",
        "description": "",
        "calculation_formula": "",
        "divisor": "",
    }


def find_variable_item(variable_list, variable_name):
    """変数リストから variable_name に一致する項目を探す。"""
    for i in range(variable_list.count()):
        item = variable_list.item(i)
        if item.data(Qt.UserRole) == variable_name:
            return item
    return None
