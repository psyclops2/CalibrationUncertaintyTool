from PySide6.QtCore import Qt
import traceback
from decimal import Decimal, getcontext
from .config_loader import ConfigLoader

def calculate_type_a_uncertainty(measurements_str):
    """TypeA不確かさの計算を行う"""
    try:
        if not measurements_str:
            return None, None, None, None
            
        # カンマ区切りの測定値を数値のリストに変換
        measurements = [Decimal(x.strip()) for x in measurements_str.split(',')]
        
        if not measurements:
            return None, None, None, None
            
        # 自由度（データ数 - 1）
        degrees_of_freedom = len(measurements) - 1
        
        # 平均値（中央値）
        central_value = sum(measurements) / Decimal(len(measurements))
        
        # 標準不確かさ（標準偏差 / √n）
        if len(measurements) > 1:
            variance = sum((x - central_value) ** 2 for x in measurements) / Decimal(len(measurements) - 1)
            standard_uncertainty = variance.sqrt() / Decimal(len(measurements)).sqrt()
        else:
            standard_uncertainty = 0
            
        return degrees_of_freedom, central_value, standard_uncertainty, measurements_str
        
    except Exception as e:
        print(f"【エラー】TypeA不確かさ計算エラー: {str(e)}")
        print(traceback.format_exc())
        return None, None, None, None

def calculate_type_b_uncertainty(half_width_str, divisor_str):
    """TypeB不確かさの計算を行う"""
    try:
        if not half_width_str or not divisor_str:
            return None, None
            
        # 精度を設定
        config = ConfigLoader()
        getcontext().prec = config.get_precision()
            
        # 文字列をDecimalに変換
        half_width = Decimal(half_width_str)
        divisor = Decimal(divisor_str)
        
        # 標準不確かさを計算（半値幅/除数）
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
    """分布の種類に応じた除数を取得"""
    config = ConfigLoader()
    divisors = config.get_distribution_divisors()
    return {
        '正規分布': '',  # ユーザー入力
        '矩形分布': divisors['rectangular'],  # √3
        '三角分布': divisors['triangular'],  # √6
        'U分布': divisors['u']   # √2
    }.get(distribution, '')

def create_empty_value_dict():
    """空の値辞書を作成"""
    return {
        'measurements': '',
        'degrees_of_freedom': 0,
        'central_value': '',
        'standard_uncertainty': '',
        'half_width': '',
        'fixed_value': '',
        'description': ''
    }

def find_variable_item(variable_list, variable_name):
    """変数リストから指定された変数のアイテムを検索"""
    for i in range(variable_list.count()):
        item = variable_list.item(i)
        if item.data(Qt.UserRole) == variable_name:
            return item
    return None 