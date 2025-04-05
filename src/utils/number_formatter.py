def format_number(value):
    """
    数値を3の倍数の指数表記に変換し、実数部を小数点以下6桁で丸める
    
    Args:
        value (float): 変換する数値
        
    Returns:
        tuple: (実数部, 指数部)
        例: (1.234567, 3) -> 1.234567E3
    """
    try:
        # 数値が0の場合の特別処理
        if value == 0:
            return (0.0, 0)
            
        # 絶対値を取得
        abs_value = abs(value)
        
        # 指数を計算（3の倍数に調整）
        exponent = 0
        while abs_value >= 1000:
            abs_value /= 1000
            exponent += 3
        while abs_value < 1 and abs_value != 0:
            abs_value *= 1000
            exponent -= 3
            
        # 実数部を小数点以下6桁で丸める
        rounded_value = round(abs_value, 6)
        
        # 元の数値が負の場合、実数部も負にする
        if value < 0:
            rounded_value = -rounded_value
            
        return (rounded_value, exponent)
        
    except (TypeError, ValueError) as e:
        print(f"【エラー】数値変換エラー: {str(e)}")
        return (0.0, 0)

def format_number_str(value):
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
            return f"{real_part}E{exponent}"
            
    except Exception as e:
        print(f"【エラー】文字列変換エラー: {str(e)}")
        return "0" 