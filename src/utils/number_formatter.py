from decimal import Decimal, ROUND_HALF_UP, ROUND_UP, ROUND_DOWN
from .config_loader import ConfigLoader
import traceback

def _to_decimal(value: float | Decimal) -> Decimal:
    """float/Decimal を Decimal に正規化"""
    return value if isinstance(value, Decimal) else Decimal(str(value))


def _get_uncertainty_settings() -> tuple[int, str]:
    """有効数字設定と丸めモードを取得"""
    config = ConfigLoader()
    if config.config.has_section('UncertaintyRounding'):
        section = config.config['UncertaintyRounding']
        digits = int(section.get('significant_digits', 2))
        mode = section.get('rounding_mode', '5_percent')
    else:
        digits = 2
        mode = '5_percent'
    return digits, mode


def _calc_quantize_exp(value: Decimal, significant_digits: int) -> Decimal:
    """有効数字指定に対応する丸め単位を求める"""
    exponent = value.adjusted()  # 10進指数
    return Decimal(f"1e{exponent - significant_digits + 1}")


def _round_to_significant_digits(
    value: Decimal, significant_digits: int, rounding_mode=ROUND_HALF_UP
) -> tuple[Decimal, Decimal]:
    """指定した有効数字で丸め、丸め単位も返す"""
    if value == 0:
        return Decimal('0'), Decimal('1')

    quantize_exp = _calc_quantize_exp(value, significant_digits)
    return value.quantize(quantize_exp, rounding=rounding_mode), quantize_exp


def _format_with_exponent(value: Decimal, significant_digits: int) -> str:
    """丸め済みの値を3の倍数の指数表記で返す"""
    if value == 0:
        decimals = max(significant_digits - 1, 0)
        return f"{Decimal('0'):.{decimals}f}"

    abs_value = abs(value)
    exponent = 0

    while abs_value >= 1000:
        abs_value /= 1000
        exponent += 3
    while abs_value < 1:
        abs_value *= 1000
        exponent -= 3

    decimals = max(significant_digits - 1, 0)
    format_str = f"{{:.{decimals}f}}"
    if value < 0:
        abs_value = -abs_value

    if exponent == 0:
        return format_str.format(abs_value)
    return f"{format_str.format(abs_value)} E{exponent}"


def _format_with_exponent_fixed_decimals(value: Decimal, decimal_places: int) -> str:
    """指定の小数桁を保ったまま3の倍数の指数表記で返す"""
    if value == 0:
        return f"{Decimal('0'):.{decimal_places}f}"

    abs_value = abs(value)
    exponent = 0

    while abs_value >= 1000:
        abs_value /= 1000
        exponent += 3
    while abs_value < 1:
        abs_value *= 1000
        exponent -= 3

    format_str = f"{{:.{decimal_places}f}}"
    if value < 0:
        abs_value = -abs_value

    if exponent == 0:
        return format_str.format(abs_value)
    return f"{format_str.format(abs_value)} E{exponent}"


def format_central_value(value) -> str:
    """校正値（中央値）を有効数字設定で丸めて指数表記に変換"""
    try:
        digits, _ = _get_uncertainty_settings()
        rounded, _ = _round_to_significant_digits(_to_decimal(value), digits, ROUND_HALF_UP)
        return _format_with_exponent(rounded, digits)
    except Exception as e:
        print(f"【エラー】校正値の文字列変換エラー: {str(e)}")
        print(traceback.format_exc())
        return "0"


def format_standard_uncertainty(value) -> str:
    """標準不確かさを(有効数字+2)で丸めて指数表記に変換"""
    try:
        base_digits, _ = _get_uncertainty_settings()
        digits = base_digits + 2
        rounded, _ = _round_to_significant_digits(_to_decimal(value), digits, ROUND_HALF_UP)
        return _format_with_exponent(rounded, digits)
    except Exception as e:
        print(f"【エラー】標準不確かさの文字列変換エラー: {str(e)}")
        print(traceback.format_exc())
        return "0"


def _round_with_five_percent_rule(
    value: Decimal, significant_digits: int
) -> tuple[Decimal, Decimal]:
    """5%ルールで有効数字丸め（丸め単位も返す）"""
    if value == 0:
        return Decimal('0'), Decimal('1')

    quantize_exp = _calc_quantize_exp(value, significant_digits)

    rounded_down = value.copy_abs().quantize(quantize_exp, rounding=ROUND_DOWN)
    difference = value.copy_abs() - rounded_down

    if difference == 0 or (difference / value.copy_abs()) <= Decimal('0.05'):
        candidate = rounded_down
    else:
        candidate = rounded_down + quantize_exp

    rounded = candidate if value >= 0 else -candidate
    return rounded, quantize_exp


def _round_expanded_uncertainty(value: Decimal) -> tuple[Decimal, int, Decimal]:
    """拡張不確かさの丸め結果と桁情報を返す"""
    digits, mode = _get_uncertainty_settings()
    dec_value = _to_decimal(value)

    if mode == 'round_up':
        rounded, quantize_exp = _round_to_significant_digits(dec_value, digits, ROUND_UP)
    else:
        rounded, quantize_exp = _round_with_five_percent_rule(dec_value, digits)

    return rounded, digits, quantize_exp


def format_expanded_uncertainty(value) -> str:
    """拡張不確かさを有効数字設定と丸めモードで丸めて指数表記に変換"""
    try:
        rounded, digits, _ = _round_expanded_uncertainty(_to_decimal(value))
        return _format_with_exponent(rounded, digits)
    except Exception as e:
        print(f"【エラー】拡張不確かさの文字列変換エラー: {str(e)}")
        print(traceback.format_exc())
        return "0"


def format_expanded_uncertainty_with_quantum(value) -> tuple[str, Decimal]:
    """拡張不確かさの文字列表現と丸め単位を返す"""
    rounded, digits, quantize_exp = _round_expanded_uncertainty(_to_decimal(value))
    return _format_with_exponent(rounded, digits), quantize_exp


def format_central_value_with_quantum(value, quantize_exp: Decimal) -> str:
    """指定された丸め単位に従い中央値を丸めて指数表記に変換"""
    try:
        dec_value = _to_decimal(value)
        rounded = dec_value.quantize(quantize_exp, rounding=ROUND_HALF_UP)
        decimal_places = max(-quantize_exp.as_tuple().exponent, 0)
        return _format_with_exponent_fixed_decimals(rounded, decimal_places)
    except Exception as e:
        print(f"【エラー】中央値の丸め単位適用時の変換エラー: {str(e)}")
        print(traceback.format_exc())
        return "0"


def format_contribution_rate(rate: float) -> str:
    """寄与率を小数点以下2桁でパーセント表記に"""
    return f"{rate:.2f} %"


def format_coverage_factor(value) -> str:
    """包含係数を小数点以下2桁で表記"""
    try:
        return f"{_to_decimal(value).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)}"
    except Exception as e:
        print(f"【エラー】包含係数の文字列変換エラー: {str(e)}")
        print(traceback.format_exc())
        return "0"


def format_number_str(value):
    """汎用的な指数表記（既存互換用、UncertaintyRoundingの設定を使用）"""
    try:
        digits, _ = _get_uncertainty_settings()
        dec_value = _to_decimal(value)
        digits = max(digits, 1)
        rounded, _ = _round_to_significant_digits(dec_value, digits, ROUND_HALF_UP)
        return _format_with_exponent(rounded, digits)
    except Exception as e:
        print(f"【エラー】汎用数値の文字列変換エラー: {str(e)}")
        print(traceback.format_exc())
        return "0"
