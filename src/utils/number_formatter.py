import math
from decimal import Decimal
from .config_loader import ConfigLoader
import traceback

def format_number(value) -> tuple[Decimal, int]:
    """
    数値（floatまたはDecimal）を適切な桁数で丸めて返す
    Args:
        value (float or Decimal): 丸め対象の数値
    Returns:
        tuple[Decimal, int]: 丸められた数値と指数
    """
    """
    数値を適切な桁数で丸めて返す
    
    Args:
        value (float): 丸め対象の数値
        
    Returns:
        tuple[float, int]: 丸められた数値と指数
    """
    try:
        # float型ならDecimalに変換
        if not isinstance(value, Decimal):
            value = Decimal(str(value))
        if value == 0:
            return Decimal('0'), 0
        abs_value = abs(value)
        exponent = 0
        
        # 指数を計算（3の倍数に調整）
        while abs_value >= 1000:
            abs_value /= 1000
            exponent += 3
        while abs_value < 1 and abs_value != 0:
            abs_value *= 1000
            exponent -= 3
            
        # 設定された桁数で丸める
        config = ConfigLoader()
        decimal_places = config.get_rounding_settings()['decimal_places']
        rounded_value = round(abs_value, decimal_places)
        
        # 負の数の場合、符号を戻す
        if value < 0:
            rounded_value = -rounded_value
            
        # 指数表記に変換
        if exponent == 0:
            return rounded_value, exponent
        else:
            return rounded_value * (Decimal('10') ** exponent), exponent
            
    except Exception as e:
        print(f"【エラー】数値の丸めエラー: {str(e)}")
        print(traceback.format_exc())
        return "0", 0

def format_number_str(value):
    """
    数値（floatまたはDecimal）を3の倍数の指数表記の文字列に変換
    Args:
        value (float or Decimal): 変換する数値
    Returns:
        str: 指数表記の文字列（例: 1.234567 E3）
    """
    """
    数値を3の倍数の指数表記の文字列に変換
    
    Args:
        value (float): 変換する数値
        
    Returns:
        str: 指数表記の文字列
        例: 1.234567E3
    """
    try:
        real_part, exponent = format_number(value)
        
        if exponent == 0:
            return f"{real_part}"
        else:
            # 指数表記を正しく表示するための処理
            abs_value = abs(real_part)
            if abs_value >= 1000:
                abs_value /= 1000
                exponent += 3
            elif abs_value < 1 and abs_value != 0:
                abs_value *= 1000
                exponent -= 3
            
            if real_part < 0:
                abs_value = -abs_value
            # 桁数の設定を取得
            config = ConfigLoader()
            decimal_places = config.get_rounding_settings()['decimal_places']
            format_str = f"{{:.{decimal_places}f}}"
            return f"{format_str.format(abs_value)} E{exponent}"
            
    except Exception as e:
        print(f"【エラー】文字列変換エラー: {str(e)}")
        return "0" 