from PySide6.QtWidgets import (QWidget, QVBoxLayout, QGroupBox,
                             QTableWidget, QTableWidgetItem, QHeaderView,
                             QTextEdit)
from PySide6.QtCore import Qt, Signal, Slot
import sympy as sp
import traceback
import re

class PartialDerivativeTab(QWidget):
    """偏微分タブ"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        print("【デバッグ】PartialDerivativeTab初期化")
        self.setup_ui()
        
    def setup_ui(self):
        """UIの設定"""
        print("【デバッグ】setup_ui開始")
        layout = QVBoxLayout()
        
        # 現在のモデル式表示エリア
        equation_group = QGroupBox("現在のモデル式")
        equation_layout = QVBoxLayout()
        
        self.equation_display = QTextEdit()
        self.equation_display.setReadOnly(True)
        equation_layout.addWidget(self.equation_display)
        
        equation_group.setLayout(equation_layout)
        layout.addWidget(equation_group)
        
        # 偏微分表示エリア
        derivative_group = QGroupBox("偏微分")
        derivative_layout = QVBoxLayout()
        
        self.partial_diff_area = QTextEdit()
        self.partial_diff_area.setReadOnly(True)
        derivative_layout.addWidget(self.partial_diff_area)
        
        derivative_group.setLayout(derivative_layout)
        layout.addWidget(derivative_group)
        
        self.setLayout(layout)
        print("【デバッグ】setup_ui完了")
        
    def update_equation_display(self):
        """現在のモデル式を表示エリアに更新"""
        try:
            if hasattr(self.parent, 'last_equation'):
                self.equation_display.setText(self.parent.last_equation)
                self.calculate_partial_derivatives()
        except Exception as e:
            print(f"【エラー】モデル式表示更新エラー: {str(e)}")
            print(traceback.format_exc())
            
    def calculate_partial_derivatives(self):
        """偏微分の計算と表示"""
        try:
            equation = self.parent.last_equation
            if not equation:
                self.partial_diff_area.clear()
                return
                
            # 方程式を分割
            equations = [eq.strip() for eq in equation.split(',')]
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
                right_side = right_side.strip()
                
                # 変数をSymbolとして定義
                symbols = {}
                for eq in equations:
                    if '=' not in eq:
                        continue
                    left, right = eq.split('=', 1)
                    left = left.strip()
                    right = right.strip()
                    symbols[left] = sp.Symbol(left)
                    
                    # 右辺の変数も追加
                    for op in ['+', '-', '*', '/', '^', '(', ')', ',']:
                        right = right.replace(op, f' {op} ')
                    terms = right.split()
                    for term in terms:
                        if term not in ['+', '-', '*', '/', '^', '(', ')', ',']:
                            try:
                                float(term)
                            except ValueError:
                                symbols[term] = sp.Symbol(term)
                
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
                        derivative_str = re.sub(r'([a-zA-Z])_([a-zA-Z0-9]+)', r'\1<sub>\2</sub>', derivative_str)
                        derivative_str = re.sub(r'\^([0-9]+)', r'<sup>\1</sup>', derivative_str)
                        
                        formatted_left = re.sub(r'([a-zA-Z])_([a-zA-Z0-9]+)', r'\1<sub>\2</sub>', left_side)
                        
                        derivative_parts.append(f"∂{formatted_left}/∂{var} = {derivative_str}")
                    except Exception as e:
                        print(f"【デバッグ】変数 {var} の偏微分計算エラー: {str(e)}")
                        self.parent.log_error(f"変数 {var} の偏微分計算エラー: {str(e)}", "偏微分エラー")
                        derivative_parts.append(f"∂{left_side}/∂{var} = エラー: {str(e)}")
            
            # 結果を表示
            if derivative_parts:
                html_content = '<div style="font-family: Times New Roman; font-size: 14px;">'
                for part in derivative_parts:
                    html_content += f'<div>{part}</div><br>'
                html_content += '</div>'
                print(f"【デバッグ】偏微分HTML: {html_content}")
                self.partial_diff_area.setHtml(html_content)
            else:
                self.partial_diff_area.clear()
                
        except Exception as e:
            print(f"【デバッグ】偏微分の計算でエラー: {str(e)}")
            self.parent.log_error(f"偏微分計算エラー: {str(e)}", "偏微分エラー")
            self.partial_diff_area.setText(f"偏微分の計算中にエラーが発生しました：{str(e)}") 