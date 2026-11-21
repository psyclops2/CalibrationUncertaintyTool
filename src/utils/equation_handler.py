import sympy as sp
import traceback
import re
from decimal import Decimal, InvalidOperation
from .equation_normalizer import normalize_equation_text, normalize_variable_name
from .quantity_notation import IDENTIFIER
from .config_loader import ConfigLoader
from .app_logger import log_error
from .model_expression import parse_expression, variable_names, split_equations

class EquationHandler:
    def __init__(self, main_window):
        self.main_window = main_window

    def get_target_equation(self, result_var):
        """選択された計算結果変数の式を返す。"""
        try:
            equation = getattr(self.main_window, "last_equation", "")
            if not equation and hasattr(self.main_window, "model_equation_tab"):
                equation = self.main_window.model_equation_tab.equation_input.toPlainText().strip()
                if equation:
                    self.main_window.last_equation = equation

            if not equation:
                return None

            normalized_equation = normalize_equation_text(equation)
            normalized_result_var = normalize_variable_name(result_var)
            equations = self._split_equations(normalized_equation)

            resolved_equation = self.resolve_equation(normalized_result_var, equations)
            if resolved_equation:
                return resolved_equation

            for eq in equations:
                if "=" not in eq:
                    continue
                left_side = normalize_variable_name(eq.split("=", 1)[0])
                if left_side == normalized_result_var:
                    return eq
            return None
        except ValueError:
            raise
        except Exception as e:
            log_error(f"式取得エラー: {str(e)}", details=traceback.format_exc())
            return None

    def _split_equations(self, text):
        """Split equation text by comma/newline/semicolon."""
        return split_equations(text)

    def _extract_rhs_expression(self, expression_text):
        """Extract a safe RHS expression for sympy parsing."""
        normalized = normalize_equation_text(expression_text or "").replace("^", "**").strip()
        if not normalized:
            return ""

        if "=" in normalized:
            if re.match(r"^\s*"+IDENTIFIER+r"\s*=", normalized):
                normalized = normalized.split("=", 1)[1].strip()
            else:
                normalized = normalized.split("=", 1)[0].strip()
                normalized = re.sub(
                    r"\s+"+IDENTIFIER+r"\s*$",
                    "",
                    normalized,
                ).strip()

        parts = self._split_equations(normalized)
        return parts[0] if parts else normalized


    def resolve_equation(self, target_var, equations):
        """Expand intermediate results into shared original input variables."""
        definitions = {}
        for equation in equations:
            if '=' not in equation:
                continue
            left, right = equation.split('=', 1)
            name = normalize_variable_name(left)
            if name in definitions:
                raise ValueError(f'結果の定義が重複しています: {name}')
            definitions[name] = right.strip()
        target_var = normalize_variable_name(target_var)
        if target_var not in definitions:
            return None
        cache = {}
        token = re.compile(IDENTIFIER)

        def expand(name, stack):
            if name in stack:
                raise ValueError('段階計算が循環しています: ' + ' → '.join(stack + [name]))
            if name in cache:
                return cache[name]
            def substitute(match):
                word = match.group(0)
                # Do not interpret the exponent of a numeric literal as a variable.
                if match.start() and definitions[name][match.start()-1] in '0123456789.':
                    return word
                if word in definitions:
                    return '(' + expand(word, stack + [name]) + ')'
                return word
            cache[name] = token.sub(substitute, definitions[name])
            return cache[name]

        return f'{target_var} = {expand(target_var, [])}'

    def _to_sympy_number(self, value):
        """蜈･蜉帛､繧奪ecimal邨檎罰縺ｧSymPy謨ｰ蛟､縺ｸ螟画鋤縺吶ｋ"""
        if value == '':
            return None
        try:
            decimal_value = Decimal(value)
        except (InvalidOperation, TypeError, ValueError):
            return None

        precision = ConfigLoader().get_precision()
        return sp.Float(str(decimal_value), precision)

    def get_variables_from_equation(self, equation):
        return variable_names(self._extract_rhs_expression(equation))

    def calculate_sensitivity(self, equation, target_var, variables, value_handler):
        """感度係数を計算する。"""
        try:
            # 螟画焚繧担ymbol縺ｨ縺励※螳夂ｾｩ
            symbols = {}
            for var in variables:
                symbols[var] = sp.Symbol(var, real=True)

            # 蠑上ｒ隗｣譫撰ｼ・繧・*縺ｫ螟画鋤・・
            expr_str = self._extract_rhs_expression(equation)
            if not expr_str:
                return ''
            expr = parse_expression(expr_str, symbols)

            # 蛛丞ｾｮ蛻・ｒ險育ｮ・
            derivative = sp.diff(expr, symbols[target_var])

            # 蜷・､画焚縺ｫ荳ｭ螟ｮ蛟､繧剃ｻ｣蜈･
            for var in variables:
                central_value = value_handler.get_central_value(var)
                if central_value == '':
                    continue
                sympy_value = self._to_sympy_number(central_value)
                if sympy_value is None:
                    return ''
                derivative = derivative.subs(symbols[var], sympy_value)

            return derivative

        except Exception as e:
            log_error(f"諢溷ｺｦ菫よ焚險育ｮ励お繝ｩ繝ｼ: {str(e)}", details=traceback.format_exc())
            raise ValueError(f'感度係数を計算できません: {e}') from e

    def calculate_result_central_value(self, equation, variables, value_handler):
        """計算結果変数の中心値を計算する。"""
        try:
            # 螟画焚繧担ymbol縺ｨ縺励※螳夂ｾｩ
            symbols = {}
            for var in variables:
                symbols[var] = sp.Symbol(var, real=True)

            # 蠑上ｒ隗｣譫撰ｼ・繧・*縺ｫ螟画鋤・・
            expr_str = self._extract_rhs_expression(equation)
            if not expr_str:
                return ''
            expr = parse_expression(expr_str, symbols)

            # 蜷・､画焚縺ｫ荳ｭ螟ｮ蛟､繧剃ｻ｣蜈･
            for var in variables:
                central_value = value_handler.get_central_value(var)
                if central_value == '':
                    continue
                sympy_value = self._to_sympy_number(central_value)
                if sympy_value is None:
                    return ''
                expr = expr.subs(symbols[var], sympy_value)
            try:
                return expr.evalf()
            except (TypeError, ValueError):
                return ''
        except Exception as e:
            log_error(f"荳ｭ螟ｮ蛟､險育ｮ励お繝ｩ繝ｼ: {str(e)}", details=traceback.format_exc())
            raise ValueError(f'中心値を計算できません: {e}') from e
