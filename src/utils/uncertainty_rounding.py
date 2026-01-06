from decimal import Decimal, ROUND_HALF_UP, ROUND_DOWN
from .config_loader import ConfigLoader
import traceback

def get_uncertainty_rounding_settings():
    """不確かさの丸め設定を取得"""
    config = ConfigLoader()
    return {
        'significant_digits': int(config.config.get('UncertaintyRounding', 'significant_digits', fallback='2')),
        'rounding_mode': config.config.get('UncertaintyRounding', 'rounding_mode', fallback='5_percent')
    }

def round_uncertainty(value: Decimal, mode: str = None) -> Decimal:
    """
    不確かさの値を有効数字で丸める
    
    Args:
        value (Decimal): 丸め対象の不確かさ値
        mode (str): 丸めモード（'round_up' or '5_percent'）
            - 'round_up': 常に切上げ
            - '5_percent': 5%ルールによる自動切上げ/切り下げ
            - None: 設定ファイルの値を使用
            
    Returns:
        Decimal: 丸められた不確かさ値
    """
    try:
        if value == 0:
            return Decimal('0')
            
        # 設定値の取得
        settings = get_uncertainty_rounding_settings()
        significant_digits = settings['significant_digits']
        
        # 丸めモードの決定
        if mode is None:
            mode = settings['rounding_mode']
        
        # 有効数字の位置を計算
        abs_value = abs(value)
        exponent = 0
        while abs_value >= 10:
            abs_value /= 10
            exponent += 1
        while abs_value < 1:
            abs_value *= 10
            exponent -= 1
        
        # 有効数字の位置に合わせて丸める
        rounding_position = -exponent + (significant_digits - 1)
        
        if mode == 'round_up':
            # 常に切上げ
            rounded_value = abs_value.quantize(Decimal('1.' + '0' * (significant_digits - 1)), rounding=ROUND_HALF_UP)
        else:  # 5_percent
            # 5%ルールによる自動切上げ/切り下げ
            # 切り捨てる値を計算
            rounded_down = abs_value.quantize(Decimal('1.' + '0' * (significant_digits - 1)), rounding=ROUND_DOWN)
            difference = abs_value - rounded_down
            
            # 差が5%以下かチェック
            if difference / abs_value <= Decimal('0.05'):
                # 5%以下なら切り捨て
                rounded_value = rounded_down
            else:
                # 5%以上なら切上げ
                rounded_value = rounded_down + Decimal('1.' + '0' * (significant_digits - 1))
        
        # 指数を戻す
        final_value = rounded_value * (Decimal('10') ** exponent)
        
        # 負の数の場合、符号を戻す
        if value < 0:
            final_value = -final_value
            
        return final_value
        
    except Exception as e:
        print(f"【エラー】不確かさの丸めエラー: {str(e)}")
        print(traceback.format_exc())
        return Decimal('0')

def format_uncertainty(value: Decimal, mode: str = None) -> str:
    """
    不確かさの値を有効数字で丸め、指数表記の文字列に変換
    
    Args:
        value (Decimal): 丸め対象の不確かさ値
        mode (str): 丸めモード（'round_up' or '5_percent'）
            
    Returns:
        str: 丸められた不確かさ値の文字列表記
    """
    try:
        # 丸め
        rounded_value = round_uncertainty(value, mode)
        
        # 指数表記に変換
        abs_value = abs(rounded_value)
        exponent = 0
        
        # 指数を計算（3の倍数に調整）
        while abs_value >= 1000:
            abs_value /= 1000
            exponent += 3
        while abs_value < 1 and abs_value != 0:
            abs_value *= 1000
            exponent -= 3
            
        # 設定された有効数字に合わせて表示桁数を決定
        settings = get_uncertainty_rounding_settings()
        significant_digits = max(settings['significant_digits'], 1)
        decimal_places = max(significant_digits - 1, 0)
        format_str = f"{{:.{decimal_places}f}}"
        
        # 負の数の場合、符号を戻す
        if rounded_value < 0:
            abs_value = -abs_value
            
        # 指数表記を正しく表示するための処理
        if abs_value >= 1000:
            abs_value /= 1000
            exponent += 3
        elif abs_value < 1 and abs_value != 0:
            abs_value *= 1000
            exponent -= 3
            
        return f"{format_str.format(abs_value)} E{exponent}"
        
    except Exception as e:
        print(f"【エラー】不確かさの文字列変換エラー: {str(e)}")
        return "0"
