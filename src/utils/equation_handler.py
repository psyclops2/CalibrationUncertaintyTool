import sympy as sp
import traceback
import re
from decimal import Decimal, InvalidOperation
from .equation_normalizer import normalize_equation_text, normalize_variable_name
from .config_loader import ConfigLoader
from .app_logger import log_error

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
        except Exception as e:
            log_error(f"式取得エラー: {str(e)}", details=traceback.format_exc())
            return None

    def _split_equations(self, text):
        """Split equation text by comma/newline/semicolon."""
        if not text:
            return []
        return [part.strip() for part in re.split(r"[,\r\n;]+", text) if part.strip()]

    def _extract_rhs_expression(self, expression_text):
        """Extract a safe RHS expression for sympy parsing."""
        normalized = normalize_equation_text(expression_text or "").replace("^", "**").strip()
        if not normalized:
            return ""

        if "=" in normalized:
            if re.match(r"^\s*[A-Za-z\u03B1-\u03C9\u0391-\u03A9][A-Za-z0-9_\u03B1-\u03C9\u0391-\u03A9]*\s*=", normalized):
                normalized = normalized.split("=", 1)[1].strip()
            else:
                normalized = normalized.split("=", 1)[0].strip()
                normalized = re.sub(
                    r"\s+[A-Za-z\u03B1-\u03C9\u0391-\u03A9][A-Za-z0-9_\u03B1-\u03C9\u0391-\u03A9]*\s*$",
                    "",
                    normalized,
                ).strip()

        parts = self._split_equations(normalized)
        return parts[0] if parts else normalized


    def resolve_equation(self, target_var, equations):
        """騾｣遶区婿遞句ｼ上ｒ謨ｴ逅・＠縺ｦ縲∫岼讓吝､画焚縺ｮ蠑上ｒ蜈･蜉帛､画焚縺縺代・蠑上↓螟画鋤"""
        try:
            target_var = normalize_variable_name(target_var)
            # 蠑上ｒ霎樊嶌縺ｫ螟画鋤・亥ｷｦ霎ｺ繧偵く繝ｼ縲∝承霎ｺ繧貞､縺ｨ縺吶ｋ・・
            eq_dict = {}
            for eq in equations:
                if '=' not in eq:
                    continue
                left, right = eq.split('=', 1)
                eq_dict[normalize_variable_name(left)] = right.strip()
            
            # 逶ｮ讓吝､画焚縺ｮ蠑上ｒ蜿門ｾ・
            if target_var not in eq_dict:
                return None
            
            # 蠑上ｒ蜀榊ｸｰ逧・↓螻暮幕
            def expand_expression(expr):
                # 蠑上ｒ蛻・牡
                terms = []
                current_term = ''
                i = 0
                while i < len(expr):
                    char = expr[i]
                    if char in '+-*/^()':
                        if current_term:
                            terms.append(current_term.strip())
                            current_term = ''
                        terms.append(char)
                    else:
                        current_term += char
                    i += 1
                if current_term:
                    terms.append(current_term.strip())
                
                # 蜷・・ｒ螻暮幕
                expanded_terms = []
                for term in terms:
                    if term in '+-*/^()':
                        expanded_terms.append(term)
                    else:
                        # 螟画焚縺悟ｮ夂ｾｩ蠑上↓蜷ｫ縺ｾ繧後※縺・ｋ蝣ｴ蜷医・螻暮幕
                        if term in eq_dict:
                            expanded_terms.append(f"({expand_expression(eq_dict[term])})")
                        else:
                            expanded_terms.append(term)
                
                return ''.join(expanded_terms)
            
            # 蠑上ｒ螻暮幕
            expanded_right = expand_expression(eq_dict[target_var])
            return f"{target_var} = {expanded_right}"
            
        except Exception as e:
            log_error(f"蠑上・謨ｴ逅・お繝ｩ繝ｼ: {str(e)}", details=traceback.format_exc())
            return None

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
        """蠑上°繧牙､画焚繧呈歓蜃ｺ"""
        try:
            import re
            equation = normalize_equation_text(equation)
            # 豁｣隕剰｡ｨ迴ｾ縺ｧ螟画焚繧呈歓蜃ｺ・医ぐ繝ｪ繧ｷ繝｣譁・ｭ怜ｯｾ蠢懶ｼ・
            variables = re.findall(
                r"[A-Za-z\u03B1-\u03C9\u0391-\u03A9][A-Za-z0-9_\u03B1-\u03C9\u0391-\u03A9]*",
                equation,
            )
            # 驥崎､・ｒ髯､蜴ｻ
            normalized = [normalize_variable_name(var) for var in variables]
            return list(dict.fromkeys([var for var in normalized if var]))
            
        except Exception as e:
            log_error(f"螟画焚謚ｽ蜃ｺ繧ｨ繝ｩ繝ｼ: {str(e)}", details=traceback.format_exc())
            return []

    def calculate_sensitivity(self, equation, target_var, variables, value_handler):
        """感度係数を計算する。"""
        try:
            # 螟画焚繧担ymbol縺ｨ縺励※螳夂ｾｩ
            symbols = {}
            for var in variables:
                symbols[var] = sp.Symbol(var)
            
            # 蠑上ｒ隗｣譫撰ｼ・繧・*縺ｫ螟画鋤・・
            expr_str = self._extract_rhs_expression(equation)
            if not expr_str:
                return ''
            expr = sp.sympify(expr_str, locals=symbols)
            
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
            return ''

    def calculate_result_central_value(self, equation, variables, value_handler):
        """計算結果変数の中心値を計算する。"""
        try:
            # 螟画焚繧担ymbol縺ｨ縺励※螳夂ｾｩ
            symbols = {}
            for var in variables:
                symbols[var] = sp.Symbol(var)
            
            # 蠑上ｒ隗｣譫撰ｼ・繧・*縺ｫ螟画鋤・・
            expr_str = self._extract_rhs_expression(equation)
            if not expr_str:
                return ''
            expr = sp.sympify(expr_str, locals=symbols)
            
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
            return '' 
