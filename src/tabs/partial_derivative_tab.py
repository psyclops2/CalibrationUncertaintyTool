from PySide6.QtWidgets import (QWidget, QVBoxLayout, QGroupBox,
                             QTableWidget, QTableWidgetItem, QHeaderView,
                             QTextEdit)
from PySide6.QtCore import Qt, Signal, Slot
import sympy as sp
import traceback
import re
from src.tabs.base_tab import BaseTab
from src.utils.translation_keys import *
from src.utils.equation_normalizer import normalize_equation_text

class PartialDerivativeTab(BaseTab):
    """偏微分タブ"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent

        self.setup_ui()

    def retranslate_ui(self):
        """UIのテキストを現在の言語で更新"""
        self.equation_group.setTitle(self.tr(LABEL_EQUATION))
        self.derivative_group.setTitle(self.tr(PARTIAL_DERIVATIVE_TITLE))
        # 式の表示と偏微分を再計算して表示を更新
        self.update_equation_display()
        
    def setup_ui(self):
        """UIの設定"""

        layout = QVBoxLayout()
        
        # 現在のモデル式表示エリア
        self.equation_group = QGroupBox(self.tr(LABEL_EQUATION))
        equation_layout = QVBoxLayout()
        
        self.equation_display = QTextEdit()
        self.equation_display.setReadOnly(True)
        equation_layout.addWidget(self.equation_display)
        
        self.equation_group.setLayout(equation_layout)
        layout.addWidget(self.equation_group)
        
        # 偏微分表示エリア
        self.derivative_group = QGroupBox(self.tr(PARTIAL_DERIVATIVE_TITLE))
        derivative_layout = QVBoxLayout()
        
        self.partial_diff_area = QTextEdit()
        self.partial_diff_area.setReadOnly(True)
        derivative_layout.addWidget(self.partial_diff_area)
        
        self.derivative_group.setLayout(derivative_layout)
        layout.addWidget(self.derivative_group)
        
        self.setLayout(layout)

        
    def update_equation_display(self):
        """現在のモデル式を表示エリアに更新"""
        try:
            # まず親ウィンドウのlast_equationを確認
            equation = getattr(self.parent, 'last_equation', '')
            
            # last_equationが空の場合、モデル式タブから直接取得
            if not equation and hasattr(self.parent, 'model_equation_tab'):
                equation = self.parent.model_equation_tab.equation_input.toPlainText().strip()
                # 取得した式を親ウィンドウに設定
                if equation:
                    self.parent.last_equation = equation
            
            if equation:
                self.equation_display.setText(equation)
                self.calculate_partial_derivatives()
            else:
                self.equation_display.clear()
                self.partial_diff_area.clear()
        except Exception as e:
            print(f"【エラー】モデル式表示更新エラー: {str(e)}")
            print(traceback.format_exc())
            
    def calculate_partial_derivatives(self):
        """偏微分の計算と表示"""
        try:
            # まず親ウィンドウのlast_equationを確認
            equation = getattr(self.parent, 'last_equation', '')
            
            # last_equationが空の場合、モデル式タブから直接取得
            if not equation and hasattr(self.parent, 'model_equation_tab'):
                equation = self.parent.model_equation_tab.equation_input.toPlainText().strip()
                # 取得した式を親ウィンドウに設定
                if equation:
                    self.parent.last_equation = equation
            
            if not equation:
                self.partial_diff_area.clear()
                return

            equation_for_calc = normalize_equation_text(equation)
                
            # 方程式を分割
            equations = [eq.strip() for eq in equation_for_calc.split(',')]
            derivative_parts = []
            
            # 計算結果変数を取得
            result_vars = []
            for eq in equations:
                if '=' not in eq:
                    continue
                left_side = eq.split('=', 1)[0].strip()
                result_vars.append(left_side)
            
            # 各計算結果変数について処理
            for result_var in result_vars:
                # 結果変数の式を取得
                target_eq = None
                for eq in equations:
                    if '=' not in eq:
                        continue
                    left_side = eq.split('=', 1)[0].strip()
                    if left_side == result_var:
                        target_eq = eq
                        break
                
                if not target_eq:
                    continue
                
                # 結果変数の式を解析
                left_side, right_side = target_eq.split('=', 1)
                left_side = left_side.strip()
                right_side = normalize_equation_text(right_side.strip())
                
                # 変数をSymbolとして定義
                symbols = {}
                for eq in equations:
                    if '=' not in eq:
                        continue
                    left, right = eq.split('=', 1)
                    left = left.strip()
                    right = right.strip()
                    symbols[left] = sp.Symbol(left)
                    
                    # 右辺の変数も追加（ギリシャ文字対応）
                    import re
                    right_vars = re.findall(r'[a-zA-Zα-ωΑ-Ω][a-zA-Z0-9_α-ωΑ-Ω]*', right)
                    for var in right_vars:
                        if var not in symbols:
                            symbols[var] = sp.Symbol(var)
                
                # 結果変数の式を解析
                expr_str = right_side.replace('^', '**')
                expr = sp.sympify(expr_str, locals=symbols)
                
                # 各変数について偏微分を計算
                for var in symbols:
                    if var == result_var:
                        continue
                        
                    try:
                        # 連鎖律を使用して偏微分を計算
                        derivative = sp.diff(expr, symbols[var])
                        
                        # 表示用の文字列に変換
                        derivative_str = str(derivative)
                        derivative_str = derivative_str.replace('**', '^')
                        derivative_str = derivative_str.replace('*', '·')
                        
                        # 下付き文字と上付き文字の処理
                        derivative_str = re.sub(r'([a-zA-Zα-ωΑ-Ω])_([a-zA-Z0-9α-ωΑ-Ω]+)', r'\1<sub>\2</sub>', derivative_str)
                        derivative_str = re.sub(r'\^([0-9]+)', r'<sup>\1</sup>', derivative_str)
                        
                        formatted_left = re.sub(r'([a-zA-Zα-ωΑ-Ω])_([a-zA-Z0-9α-ωΑ-Ω]+)', r'\1<sub>\2</sub>', left_side)
                        
                        derivative_parts.append(f"∂{formatted_left}/∂{var} = {derivative_str}")
                    except Exception as e:

                        self.parent.log_error(f"変数 {var} の偏微分計算エラー: {str(e)}", self.tr(DERIVATIVE_CALCULATION_ERROR))
                        derivative_parts.append(f"∂{left_side}/∂{var} = {self.tr(ERROR_OCCURRED)}: {str(e)}")
            
            # 結果を表示
            if derivative_parts:
                html_content = '<div style="font-family: Times New Roman; font-size: 14px;">'
                for part in derivative_parts:
                    html_content += f'<div>{part}</div><br>'
                html_content += '</div>'

                self.partial_diff_area.setHtml(html_content)
            else:
                self.partial_diff_area.clear()
                
        except Exception as e:

            self.parent.log_error(f"偏微分計算エラー: {str(e)}", self.tr(DERIVATIVE_CALCULATION_ERROR))
            self.partial_diff_area.setText(f"{self.tr(DERIVATIVE_CALCULATION_ERROR)}: {str(e)}") 
