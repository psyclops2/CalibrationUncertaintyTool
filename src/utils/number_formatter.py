from decimal import Decimal, ROUND_HALF_UP, ROUND_UP, ROUND_DOWN
from .config_loader import ConfigLoader
import traceback
from .app_logger import log_error

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


def _round_to_significant_digits(value: Decimal, significant_digits: int, rounding_mode=ROUND_HALF_UP) -> Decimal:
    """指定した有効数字で丸める"""
    if value == 0:
        return Decimal('0')

    exponent = value.adjusted()  # 10進指数
    quantize_exp = Decimal(f"1e{exponent - significant_digits + 1}")
    return value.quantize(quantize_exp, rounding=rounding_mode)


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


def format_central_value(value) -> str:
    """校正値（中央値）を有効数字設定で丸めて指数表記に変換"""
    try:
        digits, _ = _get_uncertainty_settings()
        rounded = _round_to_significant_digits(_to_decimal(value), digits, ROUND_HALF_UP)
        return _format_with_exponent(rounded, digits)
    except Exception as e:
        log_error(f"校正値の文字列変換エラー: {str(e)}", details=traceback.format_exc())
        return "0"


def format_standard_uncertainty(value) -> str:
    """標準不確かさを(有効数字+2)で丸めて指数表記に変換"""
    try:
        base_digits, _ = _get_uncertainty_settings()
        digits = base_digits + 2
        rounded = _round_to_significant_digits(_to_decimal(value), digits, ROUND_HALF_UP)
        return _format_with_exponent(rounded, digits)
    except Exception as e:
        log_error(f"標準不確かさの文字列変換エラー: {str(e)}", details=traceback.format_exc())
        return "0"


def _round_with_five_percent_rule(value: Decimal, significant_digits: int) -> Decimal:
    """5%ルールで有効数字丸め"""
    if value == 0:
        return Decimal('0')

    exponent = value.adjusted()
    quantize_exp = Decimal(f"1e{exponent - significant_digits + 1}")

    rounded_down = value.copy_abs().quantize(quantize_exp, rounding=ROUND_DOWN)
    difference = value.copy_abs() - rounded_down

    if difference == 0 or (difference / value.copy_abs()) <= Decimal('0.05'):
        candidate = rounded_down
    else:
        candidate = rounded_down + quantize_exp

    return candidate if value >= 0 else -candidate


def _round_expanded_uncertainty(value: Decimal, digits: int, mode: str) -> Decimal:
    """拡張不確かさを設定に従って丸める"""
    if mode == 'round_up':
        return _round_to_significant_digits(value, digits, ROUND_UP)
    return _round_with_five_percent_rule(value, digits)


def format_expanded_uncertainty(value) -> str:
    """拡張不確かさを有効数字設定と丸めモードで丸めて指数表記に変換"""
    try:
        digits, mode = _get_uncertainty_settings()

        dec_value = _to_decimal(value)
        rounded = _round_expanded_uncertainty(dec_value, digits, mode)

        return _format_with_exponent(rounded, digits)
    except Exception as e:
        log_error(f"拡張不確かさの文字列変換エラー: {str(e)}", details=traceback.format_exc())
        return "0"


def format_contribution_rate(rate: float) -> str:
    """寄与率を小数点以下2桁でパーセント表記に"""
    return f"{rate:.2f} %"


def format_coverage_factor(value) -> str:
    """包含係数を小数点以下2桁で表記"""
    try:
        return f"{_to_decimal(value).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)}"
    except Exception as e:
        log_error(f"包含係数の文字列変換エラー: {str(e)}", details=traceback.format_exc())
        return "0"


def format_central_value_with_uncertainty(value, expanded_uncertainty) -> str:
    """拡張不確かさの桁に合わせて中央値を表示"""
    try:
        digits, mode = _get_uncertainty_settings()
        rounded_uncertainty = _round_expanded_uncertainty(_to_decimal(expanded_uncertainty), digits, mode)

        if rounded_uncertainty == 0:
            return format_central_value(value)

        quantize_exp = Decimal(f"1e{rounded_uncertainty.adjusted() - digits + 1}")
        decimals = max(-quantize_exp.as_tuple().exponent, 0)
        rounded_value = _to_decimal(value).quantize(quantize_exp, rounding=ROUND_HALF_UP)
        return f"{rounded_value:.{decimals}f}"
    except Exception as e:
        log_error(f"不確かさに合わせた中央値の文字列変換エラー: {str(e)}", details=traceback.format_exc())
        return format_central_value(value)


def format_number_str(value):
    """汎用的な指数表記（既存互換用、UncertaintyRoundingの設定を使用）"""
    try:
        digits, _ = _get_uncertainty_settings()
        dec_value = _to_decimal(value)
        digits = max(digits, 1)
        rounded = _round_to_significant_digits(dec_value, digits, ROUND_HALF_UP)
        return _format_with_exponent(rounded, digits)
    except Exception as e:
        log_error(f"汎用数値の文字列変換エラー: {str(e)}", details=traceback.format_exc())
        return "0"
