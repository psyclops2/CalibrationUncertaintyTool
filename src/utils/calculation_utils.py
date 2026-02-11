import re
import math
import traceback
import decimal
from decimal import Decimal, getcontext
from .config_loader import ConfigLoader
from .app_logger import log_error


def evaluate_formula(formula, variables=None):
    """
    計算式を評価して結果を返す

    Args:
        formula (str): 評価する計算式
        variables (dict): 変数名と値の辞書

    Returns:
        Decimal | None: 計算結果
    """
    try:
        if not formula:
            return None

        if variables is None:
            variables = {}

        config = ConfigLoader()
        precision = config.get_precision()
        getcontext().prec = precision

        # ^ を Python のべき乗演算子へ変換
        formula = formula.replace('^', '**')

        # 数値リテラルを Decimal に変換（科学記法: 1e-6, 1E3 に対応）
        # 例: 50e-6, 2E3, 0.5e+2, .25E-1
        number_pattern = (
            r'(?<![A-Za-z_"])'
            r'((?:\d+\.\d*|\.\d+|\d+)(?:[eE][+-]?\d+)?)'
        )
        formula = re.sub(number_pattern, r'Decimal("\1")', formula)

        # 変数展開は数値変換の後に実行する。
        # 先に実行すると Decimal("...") 内の数字が再置換される。
        for var_name, var_value in variables.items():
            formula = re.sub(
                r'\b' + re.escape(str(var_name)) + r'\b',
                f'Decimal("{var_value}")',
                formula,
            )

        result = eval(formula, {"Decimal": Decimal, "math": math})
        return result

    except Exception as e:
        log_error(f"計算式の評価エラー: {str(e)}", details=traceback.format_exc())
        return None
