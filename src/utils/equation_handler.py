import sympy as sp
import traceback

class EquationHandler:
    def __init__(self, main_window):
        self.main_window = main_window

    def get_target_equation(self, result_var):
        """選択された計算結果変数の式を取得"""
        try:
            print(f"【デバッグ】式取得開始: {result_var}")
            # モデル式から連立方程式を取得
            equations = [eq.strip() for eq in self.main_window.last_equation.split(',')]
            
            # 連立方程式を整理
            resolved_equation = self.resolve_equation(result_var, equations)
            if resolved_equation:
                return resolved_equation
            
            # 整理できない場合は元の式を返す
            for eq in equations:
                if '=' not in eq:
                    continue
                left_side = eq.split('=', 1)[0].strip()
                if left_side == result_var:
                    return eq
            return None
            
        except Exception as e:
            print(f"【エラー】式取得エラー: {str(e)}")
            print(traceback.format_exc())
            return None

    def resolve_equation(self, target_var, equations):
        """連立方程式を整理して、目標変数の式を入力変数だけの式に変換"""
        try:
            # 式を辞書に変換（左辺をキー、右辺を値とする）
            eq_dict = {}
            for eq in equations:
                if '=' not in eq:
                    continue
                left, right = eq.split('=', 1)
                eq_dict[left.strip()] = right.strip()
            
            # 目標変数の式を取得
            if target_var not in eq_dict:
                return None
            
            # 式を再帰的に展開
            def expand_expression(expr):
                # 式を分割
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
                
                # 各項を展開
                expanded_terms = []
                for term in terms:
                    if term in '+-*/^()':
                        expanded_terms.append(term)
                    else:
                        # 変数が定義式に含まれている場合は展開
                        if term in eq_dict:
                            expanded_terms.append(f"({expand_expression(eq_dict[term])})")
                        else:
                            expanded_terms.append(term)
                
                return ''.join(expanded_terms)
            
            # 式を展開
            expanded_right = expand_expression(eq_dict[target_var])
            return f"{target_var} = {expanded_right}"
            
        except Exception as e:
            print(f"【エラー】式の整理エラー: {str(e)}")
            print(traceback.format_exc())
            return None

    def get_variables_from_equation(self, equation):
        """式から変数を抽出"""
        try:
            # 演算子で式を分割
            for op in ['+', '-', '*', '/', '^', '(', ')', ',']:
                equation = equation.replace(op, f' {op} ')
            terms = equation.split()
            
            # 変数を抽出
            variables = []
            for term in terms:
                if term not in ['+', '-', '*', '/', '^', '(', ')', ',']:
                    try:
                        float(term)  # 数値かどうかをチェック
                    except ValueError:
                        if term not in variables:
                            variables.append(term)
            
            return variables
            
        except Exception as e:
            print(f"【エラー】変数抽出エラー: {str(e)}")
            print(traceback.format_exc())
            return []

    def calculate_sensitivity(self, equation, target_var, variables, value_handler):
        """感度係数を計算"""
        try:
            # 変数をSymbolとして定義
            symbols = {}
            for var in variables:
                symbols[var] = sp.Symbol(var)
            
            # 式を解析（^を**に変換）
            expr_str = equation.replace('^', '**')
            expr = sp.sympify(expr_str, locals=symbols)
            
            # 偏微分を計算
            derivative = sp.diff(expr, symbols[target_var])
            
            # 各変数に中央値を代入
            for var in variables:
                central_value = value_handler.get_central_value(var)
                if central_value:
                    try:
                        derivative = derivative.subs(symbols[var], float(central_value))
                    except (ValueError, TypeError):
                        return ''
            
            return derivative
            
        except Exception as e:
            print(f"【エラー】感度係数計算エラー: {str(e)}")
            print(traceback.format_exc())
            return ''

    def calculate_result_central_value(self, equation, variables, value_handler):
        """計算結果の中央値を計算"""
        try:
            # 変数をSymbolとして定義
            symbols = {}
            for var in variables:
                symbols[var] = sp.Symbol(var)
            
            # 式を解析（^を**に変換）
            expr_str = equation.replace('^', '**')
            expr = sp.sympify(expr_str, locals=symbols)
            
            # 各変数に中央値を代入
            for var in variables:
                central_value = value_handler.get_central_value(var)
                if central_value:
                    try:
                        expr = expr.subs(symbols[var], float(central_value))
                    except (ValueError, TypeError):
                        return ''
            
            return float(expr)
            
        except Exception as e:
            print(f"【エラー】中央値計算エラー: {str(e)}")
            print(traceback.format_exc())
            return '' 