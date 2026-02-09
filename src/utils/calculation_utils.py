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
        float: 計算結果
    """
    try:
        if not formula:
            return None
            
        # 変数が指定されていない場合は空の辞書を使用
        if variables is None:
            variables = {}
            
        # 精度を設定
        config = ConfigLoader()
        precision = config.get_precision()
        getcontext().prec = precision
        
        # 変数を式に代入（Decimalに変換）
        for var_name, var_value in variables.items():
            # 変数名を値に置換（常にDecimal文字列で）
            # ギリシャ文字を含む変数名も正しく置換されるように、正規表現を使用
            import re
            formula = re.sub(r'\b' + re.escape(var_name) + r'\b', f'Decimal("{var_value}")', formula)
            
        # ^演算子を**演算子に置き換え
        formula = formula.replace('^', '**')
            
        # 式を評価（Decimalを使用）
        # 数値をDecimalに変換
        formula = re.sub(r'(\d+\.?\d*)', r'Decimal("\1")', formula)
        
        # 式を評価
        result = eval(formula, {"Decimal": Decimal})
        
        # Decimalのまま返す
        return result
        
    except Exception as e:
        log_error(f"計算式の評価エラー: {str(e)}", details=traceback.format_exc())
        return None 
