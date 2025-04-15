from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                           QTextEdit, QGroupBox, QMessageBox, QLineEdit,
                           QListWidget, QListWidgetItem)
from PySide6.QtCore import Qt, Signal, Slot
import sympy as sp
import re
import traceback
import json
import os

from src.utils.equation_formatter import EquationFormatter

class DraggableListWidget(QListWidget):
    order_changed = Signal(list)  # 並び順が変更されたときに発火するシグナル
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDragDropMode(QListWidget.InternalMove)
        self.setSelectionMode(QListWidget.ExtendedSelection)
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDropIndicatorShown(True)
        self.setDefaultDropAction(Qt.MoveAction)
        
    def dropEvent(self, event):
        super().dropEvent(event)
        # 新しい並び順を取得してシグナルを発火
        new_order = [self.item(i).text() for i in range(self.count())]
        self.order_changed.emit(new_order)

class ModelEquationTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.variable_order_file = os.path.join("data", "variable_order.json")
        self.setup_ui()
        
    def setup_ui(self):
        """UIの設定"""
        layout = QVBoxLayout()
        
        # モデル方程式入力エリア
        equation_group = QGroupBox("モデル方程式の入力")
        equation_layout = QVBoxLayout()
        
        self.equation_input = QTextEdit()
        self.equation_input.setPlaceholderText("例: y = a * x + b, z = x^2 + y")
        self.equation_input.setMaximumHeight(300)
        self.equation_input.focusOutEvent = self._on_equation_focus_lost
        equation_layout.addWidget(self.equation_input)
        
        self.equation_status = QLabel("")
        equation_layout.addWidget(self.equation_status)
        
        equation_group.setLayout(equation_layout)
        layout.addWidget(equation_group)
        
        # 変数リスト表示エリア
        variable_group = QGroupBox("変数リスト（ドラッグ＆ドロップで並び順を変更できます）")
        variable_layout = QVBoxLayout()
        
        self.variable_list = DraggableListWidget(self)
        self.variable_list.order_changed.connect(self.on_variable_order_changed)
        variable_layout.addWidget(self.variable_list)
        
        variable_group.setLayout(variable_layout)
        layout.addWidget(variable_group)
        
        # HTML表示エリア
        display_group = QGroupBox("HTML表示")
        display_layout = QVBoxLayout()
        
        self.html_display = QTextEdit()
        self.html_display.setReadOnly(True)
        self.html_display.setMaximumHeight(200)
        display_layout.addWidget(self.html_display)
        
        display_group.setLayout(display_layout)
        layout.addWidget(display_group)
        
        self.setLayout(layout)

    def on_variable_order_changed(self, new_order):
        """変数の並び順が変更されたときの処理"""
        try:
            if not hasattr(self.parent, 'variables'):
                return
                
            # 入力変数と計算結果変数を区別
            input_vars = []
            result_vars = []
            
            for var in new_order:
                if var in self.parent.result_variables:
                    result_vars.append(var)
                else:
                    input_vars.append(var)
            
            # 親ウィンドウの変数リストを更新
            self.parent.variables = result_vars + input_vars
            
            # 変数タブの更新
            if hasattr(self.parent, 'variables_tab'):
                self.parent.variables_tab.update_variable_list(
                    self.parent.variables,
                    self.parent.result_variables
                )
            
            # 並び順を保存
            self.save_variable_order()
            
            print(f"【デバッグ】変数の並び順を更新: {self.parent.variables}")
            
        except Exception as e:
            print(f"【エラー】変数の並び順更新エラー: {str(e)}")
            print(traceback.format_exc())
            QMessageBox.warning(self, "エラー", "変数の並び順の更新に失敗しました。")
            
    def save_variable_order(self):
        """変数の並び順をJSONファイルに保存"""
        try:
            if not hasattr(self.parent, 'variables'):
                return
                
            # dataディレクトリが存在しない場合は作成
            os.makedirs(os.path.dirname(self.variable_order_file), exist_ok=True)
            
            with open(self.variable_order_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'variables': self.parent.variables,
                    'result_variables': self.parent.result_variables
                }, f, ensure_ascii=False, indent=2)
                
            print(f"【デバッグ】変数の並び順を保存: {self.variable_order_file}")
            
        except Exception as e:
            print(f"【エラー】変数の並び順保存エラー: {str(e)}")
            print(traceback.format_exc())
            QMessageBox.warning(self, "エラー", "変数の並び順の保存に失敗しました。")
            
    def load_variable_order(self):
        """変数の並び順をJSONファイルから読み込む"""
        try:
            if not os.path.exists(self.variable_order_file):
                return
                
            with open(self.variable_order_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            if not hasattr(self.parent, 'variables'):
                return
                
            # 保存された並び順を適用
            self.parent.variables = data.get('variables', self.parent.variables)
            self.parent.result_variables = data.get('result_variables', self.parent.result_variables)
            
            # 変数タブの更新
            if hasattr(self.parent, 'variables_tab'):
                self.parent.variables_tab.update_variable_list(
                    self.parent.variables,
                    self.parent.result_variables
                )
            
            # 変数リストの更新
            self.update_variable_list()
            
            print(f"【デバッグ】変数の並び順を読み込み: {self.parent.variables}")
            
        except Exception as e:
            print(f"【エラー】変数の並び順読み込みエラー: {str(e)}")
            print(traceback.format_exc())
            QMessageBox.warning(self, "エラー", "変数の並び順の読み込みに失敗しました。")
            
    def update_variable_list(self):
        """変数リストを更新"""
        try:
            self.variable_list.clear()
            
            if hasattr(self.parent, 'variables'):
                for var in self.parent.variables:
                    item = QListWidgetItem(var)
                    self.variable_list.addItem(item)
                    
            print(f"【デバッグ】変数リストを更新: {self.parent.variables}")
        except Exception as e:
            print(f"【エラー】変数リスト更新エラー: {str(e)}")
            print(traceback.format_exc())
            
    def _on_equation_focus_lost(self, event):
        """方程式入力エリアからフォーカスが外れたときの処理（内部メソッド）"""
        # 親クラスのfocusOutEventを呼び出す
        QTextEdit.focusOutEvent(self.equation_input, event)
        
        # 現在の方程式を取得
        current_equation = self.equation_input.toPlainText().strip() 
        
        # 前回の方程式と同じ場合は何もしない
        if current_equation == self.parent.last_equation:
            return
            
        # 方程式を解析して変数を抽出
        try:
            # 方程式を解析
            variables = self.parse_equation(current_equation)
            
            # 変数リストを更新
            if hasattr(self.parent, 'variables'):
                self.parent.variables = variables
                
                # 変数タブの強制更新
                if hasattr(self.parent, 'variables_tab'):
                    self.parent.variables_tab.update_variable_list(
                        self.parent.variables, 
                        self.parent.result_variables
                    )
                    
                # 変数リストを更新
                self.update_variable_list()
                
                # 前回の方程式を更新
                self.parent.last_equation = current_equation
                
                # 変数の並び順を保存
                self.save_variable_order()
                
                print(f"【デバッグ】方程式を解析: {variables}")
                
        except Exception as e:
            print(f"【エラー】方程式解析エラー: {str(e)}")
            print(traceback.format_exc())
            self.equation_status.setText(f"エラー: {str(e)}")
            
    def on_equation_focus_lost(self, event):
        """方程式入力エリアからフォーカスが外れたときの処理（公開メソッド）"""
        # 内部メソッドを呼び出す
        self._on_equation_focus_lost(event)
        
    def check_equation_changes(self, equation):
        """方程式の変更を監視し、変数の追加・削除を検出"""
        try:
            print(f"\n{'#'*80}")
            print(f"#" + " " * 30 + "方程式変更チェック" + " " * 30 + "#")
            print(f"{'#'*80}")
            print(f"入力された方程式: '{equation}'")
            
            # 方程式を分割
            equations = [eq.strip() for eq in equation.split(',')]
            new_vars = set()  # 入力変数
            result_vars = set()  # 計算結果変数
            
            # まず左辺の変数を収集（計算結果変数）
            print("\n【デバッグ】計算結果変数の検出:")
            for eq in equations:
                if '=' not in eq:
                    continue
                left_side = eq.split('=', 1)[0].strip()
                result_vars.add(left_side)
                print(f"  - 左辺から検出: {left_side}")
            
            print(f"【デバッグ】計算結果変数セット: {result_vars}")
            
            # 右辺から入力変数を検出
            print("\n【デバッグ】入力変数の検出:")
            for eq in equations:
                if '=' not in eq:
                    continue
                    
                left_side, right_side = eq.split('=', 1)
                right_side = right_side.strip()
                print(f"  方程式解析: {left_side} = {right_side}")
                
                # 演算子で式を分割
                # まず演算子の前後にスペースを追加
                for op in ['+', '-', '*', '/', '^', '(', ')', ',']:
                    right_side = right_side.replace(op, f' {op} ')
                terms = right_side.split()
                
                # 各項から変数を抽出
                for term in terms:
                    # 演算子でない項のみを処理
                    if term not in ['+', '-', '*', '/', '^', '(', ')', ',']:
                        # 数値でない項を変数として扱う
                        try:
                            float(term)  # 数値かどうかをチェック
                        except ValueError:
                            if term not in result_vars:
                                new_vars.add(term)
                                print(f"    → 入力変数として追加: {term}")
            
            print(f"\n【デバッグ】新しい入力変数セット: {new_vars}")
            print(f"【デバッグ】計算結果変数セット: {result_vars}")
            print(f"【デバッグ】現在の変数セット: {set(self.parent.variables)}")
            
            # 変数の追加・削除を検出
            all_vars = new_vars | result_vars
            added_vars = all_vars - set(self.parent.variables)
            removed_vars = set(self.parent.variables) - all_vars
            
            print(f"\n【デバッグ】追加される変数: {added_vars}")
            print(f"【デバッグ】削除される変数: {removed_vars}")
            
            # 変数の変更がある場合は確認ダイアログを表示
            if added_vars or removed_vars:
                print("\n【デバッグ】変数変更の確認ダイアログを表示")
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Question)
                msg.setWindowTitle("変数の変更確認")
                
                message = "モデル式の変更により、以下の変数の変更が必要です：\n\n"
                
                # 追加される変数を入力変数と計算結果変数に分けて表示
                if added_vars:
                    added_inputs = added_vars & new_vars
                    added_results = added_vars & result_vars
                    if added_inputs:
                        message += f"追加される入力変数：{', '.join(sorted(added_inputs))}\n"
                    if added_results:
                        message += f"追加される計算結果：{', '.join(sorted(added_results))}\n"
                
                if removed_vars:
                    message += f"削除される変数：{', '.join(sorted(removed_vars))}\n"
                message += "\nこの変更を適用しますか？"
                
                msg.setText(message)
                msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
                msg.setDefaultButton(QMessageBox.No)
                
                print("確認メッセージ:")
                print(message)
                
                if msg.exec_() == QMessageBox.Yes:
                    print("\n【デバッグ】変数の変更を適用")
                    
                    # 現在の変数の並び順を取得
                    current_order = self.parent.variables.copy()
                    
                    # 削除される変数を現在の並び順から削除
                    for var in removed_vars:
                        if var in current_order:
                            current_order.remove(var)
                    
                    # 追加される変数を現在の並び順の最後に追加
                    for var in added_vars:
                        if var not in current_order:
                            current_order.append(var)
                    
                    # 変更を適用
                    input_vars = [var for var in current_order if var in new_vars]
                    result_var_list = [var for var in current_order if var in result_vars]
                    
                    # 計算結果変数を先に、入力変数を後に
                    self.parent.variables = result_var_list + input_vars
                    self.parent.result_variables = result_var_list
                    
                    print(f"【デバッグ】変数リストを更新: {self.parent.variables}")
                    print(f"【デバッグ】計算結果変数リストを更新: {self.parent.result_variables}")
                    
                    # 新しい変数のために変数値辞書を初期化
                    for var in added_vars:
                        if var not in self.parent.variable_values:
                            if var in result_vars:
                                # 計算結果変数の初期化
                                self.parent.variable_values[var] = {
                                    'value': '計算結果',
                                    'type': None,
                                    'unit': '',
                                    'definition': '',
                                    'mode': 'result'
                                }
                                print(f"【デバッグ】計算結果変数を初期化: {var}")
                            else:
                                # 入力変数の初期化
                                self.parent.variable_values[var] = {
                                    'value': '',
                                    'type': 'A',
                                    'unit': '',
                                    'definition': '',
                                    'mode': 'input'
                                }
                                print(f"【デバッグ】入力変数を初期化: {var}")
                    
                    # 削除される変数の値を削除
                    for var in removed_vars:
                        if var in self.parent.variable_values:
                            del self.parent.variable_values[var]
                            print(f"【デバッグ】変数の値を削除: {var}")
                    
                    # 親オブジェクトの変数検出メソッドを呼び出す
                    if hasattr(self.parent, 'detect_variables'):
                        print("\n【デバッグ】親オブジェクトのdetect_variablesメソッドを呼び出し")
                        self.parent.detect_variables()
                    
                    # 変数タブの強制更新
                    if hasattr(self.parent, 'variables_tab'):
                        print("\n【デバッグ】変数タブを強制的に更新")
                        self.parent.variables_tab.update_variable_list(
                            self.parent.variables, 
                            self.parent.result_variables
                        )
                    
                    # 変数リストを更新
                    self.update_variable_list()
                    
                    # 最後に入力した方程式を保存
                    self.parent.last_equation = equation
                    print(f"【デバッグ】最後に入力した方程式を保存: '{equation}'")
                    
                else:
                    print("\n【デバッグ】変数の変更をキャンセル - 元の方程式に戻します")
                    # キャンセルの場合は元の方程式に戻す
                    self.equation_input.setText(self.parent.last_equation)
            else:
                # 変数の変更がない場合も方程式を保存
                self.parent.last_equation = equation
                print(f"\n【デバッグ】変数変更なし - 方程式のみ保存: '{equation}'")
            
            print(f"\n{'#'*80}")
            print(f"#" + " " * 30 + "方程式変更チェック完了" + " " * 30 + "#")
            print(f"{'#'*80}\n")
            
        except Exception as e:
            print(f"【エラー】方程式変更チェックエラー: {str(e)}")
            print(traceback.format_exc())
            self.parent.log_error(f"方程式の変更チェックエラー: {str(e)}", "方程式チェックエラー")
            
    def resolve_equation(self, target_var, equations):
        """
        連立方程式を整理して、目標変数の式を入力変数だけの式に変換
        
        Args:
            target_var (str): 目標変数（例: 'W'）
            equations (list): 連立方程式のリスト（例: ['W = V * I', 'V = V_MEAS + V_CAL', 'I = I_MEAS + I_CAL']）
            
        Returns:
            str: 整理された式（例: 'W = (V_MEAS + V_CAL) * (I_MEAS + I_CAL)'）
        """
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

    def update_html_display(self, equation):
        """方程式をHTML形式で表示"""
        try:
            if not equation:
                self.html_display.clear()
                return

            # 方程式を分割
            equations = [eq.strip() for eq in equation.split(',')]
            html_parts = []

            for eq in equations:
                if '=' not in eq:
                    continue

                # 乗算記号を中黒に変換
                processed_eq = eq.replace('*', '･')

                # 下付き文字の処理（_の後の文字や数字を下付き文字に変換）
                processed_eq = re.sub(r'([a-zA-Z])_([a-zA-Z0-9]+)', r'\1<sub>\2</sub>', processed_eq)
                
                # 上付き文字の処理（^の後の数字や文字を上付き文字に変換）
                processed_eq = re.sub(r'\^(\d+|\([^)]+\))', r'<sup>\1</sup>', processed_eq)
                # 括弧の中の^も処理
                processed_eq = re.sub(r'\(([^)]+)\^(\d+|\([^)]+\))\)', r'(\1<sup>\2</sup>)', processed_eq)

                html_parts.append(processed_eq)

            # 文字サイズを変更し、方程式を改行で結合
            html = f'<div style="font-size: 16px;">{"<br>".join(html_parts)}</div>'
            
            self.html_display.setHtml(html)

        except Exception as e:
            print(f"【エラー】HTML表示の更新エラー: {str(e)}")
            print(traceback.format_exc())

    def detect_variables(self, equation):
        """モデル式から変数を検出"""
        try:
            print(f"【デバッグ】変数検出開始: '{equation}'")
            print(f"【デバッグ】現在の変数リスト: {self.variables}")
            
            # 現在の変数リストをクリア
            self.variables.clear()
            
            # 方程式を分割
            equations = [eq.strip() for eq in equation.split(',')]
            
            # 左辺の変数（計算結果）を保持するセット
            result_variables = set()
            
            # まず左辺の変数を収集
            for eq in equations:
                if '=' not in eq:
                    continue
                left_side = eq.split('=', 1)[0].strip()
                result_variables.add(left_side)
            
            print(f"【デバッグ】計算結果変数: {result_variables}")
            
            # 右辺から変数を検出
            for eq in equations:
                if '=' not in eq:
                    continue
                    
                left_side, right_side = eq.split('=', 1)
                left_side = left_side.strip()
                right_side = right_side.strip()
                print(f"【デバッグ】方程式解析: 左辺='{left_side}', 右辺='{right_side}'")
                
                # 右辺から変数を検出（正規表現で直接検出）
                detected_vars = re.findall(r'[a-zA-Z][a-zA-Z0-9_]*', right_side)
                print(f"【デバッグ】検出された変数: {detected_vars}")
                
                # 計算結果変数でない変数のみを追加
                for var in detected_vars:
                    if var not in result_variables:
                        self.variables.append(var)
            
            # 重複を除去
            self.variables = list(dict.fromkeys(self.variables))
            print(f"【デバッグ】最終変数リスト: {self.variables}")
            
        except Exception as e:
            print(f"【デバッグ】変数検出エラー: {str(e)}")
            raise 

    def set_equation(self, equation):
        """方程式を設定する"""
        try:
            if equation:
                self.equation_input.setText(equation)
                self.update_html_display(equation)
                # 変数リストを更新
                self.update_variable_list()
        except Exception as e:
            print(f"【エラー】方程式設定エラー: {str(e)}")
            print(traceback.format_exc())
            self.parent.log_error(f"方程式の設定エラー: {str(e)}", "方程式設定エラー")

    def on_equation_changed(self):
        """数式が変更されたときの処理"""
        try:
            equation = self.equation_input.toPlainText()
            self.parent.last_equation = equation
            
            # HTML表示の更新
            self.update_html_display()
            
            # 変数の検出と更新
            self.detect_variables()
            
            # 偏微分タブの更新（新規追加）
            if hasattr(self.parent, 'partial_derivative_tab'):
                self.parent.partial_derivative_tab.update_equation_display()
                
        except Exception as e:
            print(f"【エラー】数式変更処理エラー: {str(e)}")
            print(traceback.format_exc()) 