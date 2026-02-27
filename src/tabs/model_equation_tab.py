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
from src.tabs.base_tab import BaseTab
from src.utils.translation_keys import *
from src.utils.equation_handler import EquationHandler
from src.utils.equation_normalizer import normalize_equation_text, normalize_variable_name
from src.utils.app_logger import log_debug, log_error

class DraggableListWidget(QListWidget):
    order_changed = Signal(list)  # 並び順変更時に新しい順序を通知するシグナル
    
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
        # 新しい並び順を取得してシグナルを発行
        new_order = [self.item(i).text() for i in range(self.count())]
        self.order_changed.emit(new_order)

class ModelEquationTab(BaseTab):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.variable_order_file = os.path.join("data", "variable_order.json")

        self.setup_ui()

    def retranslate_ui(self):
        """UIテキストを現在の言語設定で更新する"""
        log_debug(f"[DEBUG] Retranslating UI for context: {self.metaObject().className()}")
        self.equation_group.setTitle(self.tr(MODEL_EQUATION_INPUT))
        self.equation_input.setPlaceholderText(self.tr(EQUATION_PLACEHOLDER))
        self.variable_group.setTitle(self.tr(VARIABLE_LIST_DRAG_DROP))
        self.display_group.setTitle(self.tr(HTML_DISPLAY))
        
    def setup_ui(self):
        """メインウィンドウのUIを構築する"""

        layout = QVBoxLayout()
        
        # モデル方程式入力エリア
        self.equation_group = QGroupBox(self.tr(MODEL_EQUATION_INPUT))
        equation_layout = QVBoxLayout()
        
        self.equation_input = QTextEdit()
        self.equation_input.setAcceptRichText(False)
        self.equation_input.setPlaceholderText(self.tr(EQUATION_PLACEHOLDER))
        self.equation_input.setMaximumHeight(300)
        self.equation_input.focusOutEvent = self._on_equation_focus_lost
        equation_layout.addWidget(self.equation_input)
        
        self.equation_status = QLabel("")
        equation_layout.addWidget(self.equation_status)
        
        self.equation_group.setLayout(equation_layout)
        layout.addWidget(self.equation_group)
        
        # 変数リスト表示エリア
        self.variable_group = QGroupBox(self.tr(VARIABLE_LIST_DRAG_DROP))
        variable_layout = QVBoxLayout()
        
        self.variable_list = DraggableListWidget(self)
        self.variable_list.order_changed.connect(self.on_variable_order_changed)
        variable_layout.addWidget(self.variable_list)
        
        self.variable_group.setLayout(variable_layout)
        layout.addWidget(self.variable_group)
        
        # HTML表示エリア
        self.display_group = QGroupBox(self.tr(HTML_DISPLAY))
        display_layout = QVBoxLayout()
        
        self.html_display = QTextEdit()
        self.html_display.setReadOnly(True)
        self.html_display.setMaximumHeight(200)
        display_layout.addWidget(self.html_display)
        
        self.display_group.setLayout(display_layout)
        layout.addWidget(self.display_group)
        
        self.setLayout(layout)


    def on_variable_order_changed(self, new_order):
        """Handle variable order changes."""
        try:
            if not hasattr(self.parent, 'variables'):
                return

            input_vars = []
            result_vars = []
            for var in new_order:
                if var in self.parent.result_variables:
                    result_vars.append(var)
                else:
                    input_vars.append(var)

            self.parent.variables = result_vars + input_vars
            if hasattr(self.parent, 'variables_tab'):
                self.parent.variables_tab.update_variable_list(
                    self.parent.variables,
                    self.parent.result_variables
                )
        except Exception as e:
            log_error(f"変数の並び順更新エラー: {str(e)}", details=traceback.format_exc())
            QMessageBox.warning(self, self.tr(MESSAGE_ERROR), f"{self.tr('VARIABLE_ORDER_UPDATE_FAILED')}: {str(e)}")

    def save_variable_order(self):
        """Save variable order to JSON."""
        try:
            if not hasattr(self.parent, 'variables'):
                return

            os.makedirs(os.path.dirname(self.variable_order_file), exist_ok=True)
            with open(self.variable_order_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'variables': self.parent.variables,
                    'result_variables': self.parent.result_variables
                }, f, ensure_ascii=False, indent=2)
        except Exception as e:
            log_error(f"変数の並び順保存エラー: {str(e)}", details=traceback.format_exc())
            QMessageBox.critical(self, self.tr(MESSAGE_ERROR), f"{self.tr('VARIABLE_ORDER_SAVE_FAILED')}: {str(e)}")
            
    def load_variable_order(self):
        """変数の並び順をJSONファイルから読み込む"""
        try:
            if not os.path.exists(self.variable_order_file):
                return
                
            with open(self.variable_order_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            if not hasattr(self.parent, 'variables'):
                return
                
            # 保存済みの並び順を適用
            self.parent.variables = data.get('variables', self.parent.variables)
            self.parent.result_variables = data.get('result_variables', self.parent.result_variables)
            
            # Variables タブを更新
            if hasattr(self.parent, 'variables_tab'):
                self.parent.variables_tab.update_variable_list(
                    self.parent.variables,
                    self.parent.result_variables
                )
            
            # このタブの変数一覧を更新
            self.update_variable_list()
            

            
        except Exception as e:
            log_error(f"変数の並び順読込エラー: {str(e)}", details=traceback.format_exc())
            QMessageBox.critical(self, self.tr(MESSAGE_ERROR), f"{self.tr('VARIABLE_ORDER_LOAD_FAILED')}: {str(e)}")
            
    def update_variable_list(self):
        """変数リストを更新する"""
        try:
            self.variable_list.clear()
            
            if hasattr(self.parent, 'variables'):
                for var in self.parent.variables:
                    item = QListWidgetItem(var)
                    self.variable_list.addItem(item)
                    

        except Exception as e:
            log_error(f"変数リスト更新エラー: {str(e)}", details=traceback.format_exc())
            
    def _on_equation_focus_lost(self, event):
        """Handle focus out on equation input (internal)."""
        QTextEdit.focusOutEvent(self.equation_input, event)
        
        # 現在の方程式を取得
        current_equation = self.equation_input.toPlainText().strip() 
        
        # 変更がない場合は何もしない
        if current_equation == self.parent.last_equation:
            return

        try:
            applied = self.check_equation_changes(current_equation)
            if not applied:
                self.update_html_display(self.parent.last_equation)
                return

            # 偏微分タブを更新
            if hasattr(self.parent, 'partial_derivative_tab'):
                self.parent.partial_derivative_tab.update_equation_display()

            # レポートタブを更新
            if hasattr(self.parent, 'report_tab'):
                self.parent.report_tab.update_report()

            # 不確かさ計算タブを更新
            if hasattr(self.parent, 'uncertainty_calculation_tab'):
                self.parent.uncertainty_calculation_tab.update_result_combo()
                self.parent.uncertainty_calculation_tab.update_value_combo()
                
        except Exception as e:
            log_error(f"方程式処理エラー: {str(e)}", details=traceback.format_exc())
            self.equation_status.setText(f"エラー: {str(e)}")
        
        # HTML表示を必ず更新
        self.update_html_display(self.parent.last_equation)
        
    def on_equation_focus_lost(self, event):
        """Handle focus out on equation input."""
        self._on_equation_focus_lost(event)
        
    def check_equation_changes(self, equation):
        """方程式変更を確認し、変数の追加・削除を反映する"""
        try:
            log_debug(f"\n{'#'*80}")
            log_debug(f"#" + " " * 30 + "方程式変更チェック" + " " * 30 + "#")
            log_debug(f"{'#'*80}")
            log_debug(f"入力された方程式: '{equation}'")
            
            # 方程式を正規化
            normalized_equation = normalize_equation_text(equation)
            equations = [eq.strip() for eq in normalized_equation.split(',')]
            new_vars = set()  # 入力変数
            result_vars = set()  # 計算結果変数
            
            # まず左辺の変数を計算結果変数として収集

            for eq in equations:
                if '=' not in eq:
                    continue
                left_side = self._normalize_variable_name(eq.split('=', 1)[0])
                result_vars.add(left_side)
                log_debug(f"  - 左辺から検出: {left_side}")
            

            
            # 右辺から入力変数を抽出

            for eq in equations:
                if '=' not in eq:
                    continue
                    
                left_side, right_side = eq.split('=', 1)
                left_side = self._normalize_variable_name(left_side)
                right_side = right_side.strip()
                log_debug(f"  方程式解析: {left_side} = {right_side}")
                
                # 演算子を区切ってトークン化する
                for op in ['+', '-', '*', '/', '^', '(', ')', ',']:
                    right_side = right_side.replace(op, f' {op} ')
                terms = right_side.split()
                
                # 各項から変数候補を取り出す
                for term in terms:
                    # 演算子以外だけを対象にする
                    if term not in ['+', '-', '*', '/', '^', '(', ')', ',']:
                        # 数値でない場合だけ変数として扱う
                        try:
                            float(term)  # 数値ならスキップ
                        except ValueError:
                            normalized_term = self._normalize_variable_name(term)
                            if not normalized_term:
                                continue
                            if normalized_term not in result_vars:
                                new_vars.add(normalized_term)
                                log_debug(f"    入力変数として追加: {normalized_term}")
            



            
            # 変数の追加・削除を計算
            all_vars = new_vars | result_vars
            current_vars = {self._normalize_variable_name(var) for var in self.parent.variables}
            added_vars = all_vars - current_vars
            removed_vars = current_vars - all_vars
            


            
            # 削除がある場合は確認ダイアログを表示
            if removed_vars:

                msg = QMessageBox()
                msg.setIcon(QMessageBox.Question)
                msg.setWindowTitle("変数の変更確認")

                message = "モデル式の変更により、以下の変数の変更が必要です:\n\n"

                if added_vars:
                    added_inputs = added_vars & new_vars
                    added_results = added_vars & result_vars
                    if added_inputs:
                        message += f"追加される入力変数: {', '.join(sorted(added_inputs))}\n"
                    if added_results:
                        message += f"追加される計算結果: {', '.join(sorted(added_results))}\n"

                message += f"削除される変数: {', '.join(sorted(removed_vars))}\n"
                message += "\nこの変更を適用しますか？"

                msg.setText(message)
                msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
                msg.setDefaultButton(QMessageBox.No)
                
                log_debug("確認メッセージ:")
                log_debug(message)
                
                if msg.exec_() == QMessageBox.Yes:

                    
                    # 現在の変数順を取得
                    current_order = self.parent.variables.copy()
                    
                    # 削除対象を現在の順序から取り除く
                    current_order = [
                        var for var in current_order
                        if self._normalize_variable_name(var) not in removed_vars
                    ]
                    
                    # 追加変数は現在の順序の末尾に追加
                    existing_normalized = {self._normalize_variable_name(var) for var in current_order}
                    for var in added_vars:
                        if var not in existing_normalized:
                            current_order.append(var)
                    
                    # 変更内容を反映
                    input_vars = [var for var in current_order if var in new_vars]
                    result_var_list = [var for var in current_order if var in result_vars]
                    
                    # 計算結果変数を先頭、入力変数を後方に配置
                    self.parent.variables = result_var_list + input_vars
                    self.parent.result_variables = result_var_list
                    
        

                    
                    # 新しい変数の保存領域を初期化
                    for var in added_vars:
                        self.parent.ensure_variable_initialized(var, is_result=var in result_vars)

                    
                    # 削除された変数のデータを破棄
                    for var in list(self.parent.variable_values):
                        if self._normalize_variable_name(var) in removed_vars:
                            del self.parent.variable_values[var]

                    
                    # 必要なら親側の変数検出処理も再実行
                    if hasattr(self.parent, 'detect_variables'):

                        self.parent.detect_variables()
                    
                    # Variables タブの一覧を更新
                    if hasattr(self.parent, 'variables_tab'):

                        self.parent.variables_tab.update_variable_list(
                            self.parent.variables, 
                            self.parent.result_variables
                        )
                    
                    # このタブの変数一覧を更新
                    self.update_variable_list()
                    
                    # 最終的に適用した方程式を保存
                    self.parent.last_equation = equation

                    
                else:
                    # キャンセル時は元の方程式に戻す
                    self.equation_input.setText(self.parent.last_equation)
                    return False
            else:
                if added_vars:
                    # 現在の変数順を取得
                    current_order = self.parent.variables.copy()
                    
                    # 追加変数は現在の順序の末尾に追加
                    existing_normalized = {self._normalize_variable_name(var) for var in current_order}
                    for var in added_vars:
                        if var not in existing_normalized:
                            current_order.append(var)
                    
                    # 変更内容を反映
                    input_vars = [var for var in current_order if var in new_vars]
                    result_var_list = [var for var in current_order if var in result_vars]
                    
                    # 計算結果変数を先頭、入力変数を後方に配置
                    self.parent.variables = result_var_list + input_vars
                    self.parent.result_variables = result_var_list
                    
                    # 新しい変数の保存領域を初期化
                    for var in added_vars:
                        self.parent.ensure_variable_initialized(var, is_result=var in result_vars)
                    
                    # 必要なら親側の変数検出処理も再実行
                    if hasattr(self.parent, 'detect_variables'):
                        self.parent.detect_variables()
                    
                    # Variables タブの一覧を更新
                    if hasattr(self.parent, 'variables_tab'):
                        self.parent.variables_tab.update_variable_list(
                            self.parent.variables, 
                            self.parent.result_variables
                        )
                    
                    # このタブの変数一覧を更新
                    self.update_variable_list()
                
                # 変数追加だけなら方程式だけ保存
                self.parent.last_equation = equation

            
            log_debug(f"\n{'#'*80}")
            log_debug(f"#" + " " * 30 + "方程式変更チェック完了" + " " * 30 + "#")
            log_debug(f"{'#'*80}\n")
            return True
            
        except Exception as e:
            self.parent.log_error(
                f"方程式変更チェックエラー: {str(e)}",
                "方程式チェックエラー",
                details=traceback.format_exc(),
            )
            return False
            
    def resolve_equation(self, target_var, equations):
        """
        連立した方程式を展開して、指定した結果変数の式を解決する。
        
        Args:
            target_var (str): 対象の結果変数。例: 'W'
            equations (list): 方程式文字列のリスト。例: ['W = V * I', 'V = V_MEAS + V_CAL']
            
        Returns:
            str: 展開済みの式。例: 'W = (V_MEAS + V_CAL) * (I_MEAS + I_CAL)'
        """
        try:
            # 左辺をキー、右辺を値とする辞書へ変換
            eq_dict = {}
            for eq in equations:
                if '=' not in eq:
                    continue
                left, right = eq.split('=', 1)
                eq_dict[left.strip()] = right.strip()
            
            # 対象変数の式を取得
            if target_var not in eq_dict:
                return None
            
            # 右辺を再帰的に展開
            def expand_expression(expr):
                # 文字列を演算子単位で分解
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
                
                # 各項を再帰的に展開
                expanded_terms = []
                for term in terms:
                    if term in '+-*/^()':
                        expanded_terms.append(term)
                    else:
                        # 他の式で定義されていればさらに展開
                        if term in eq_dict:
                            expanded_terms.append(f"({expand_expression(eq_dict[term])})")
                        else:
                            expanded_terms.append(term)
                
                return ''.join(expanded_terms)
            
            # 対象変数の右辺を展開
            expanded_right = expand_expression(eq_dict[target_var])
            return f"{target_var} = {expanded_right}"
            
        except Exception as e:
            log_error(f"式展開エラー: {str(e)}", details=traceback.format_exc())
            return None

    def update_html_display(self, equation):
        """方程式をHTML形式で表示する"""
        try:
            if not equation:
                self.html_display.clear()
                return

            # 方程式を正規化
            normalized_equation = normalize_equation_text(equation)
            equations = [eq.strip() for eq in normalized_equation.split(',')]
            html_parts = []

            for eq in equations:
                if '=' not in eq:
                    continue

                # 乗算記号を中点で表示
                processed_eq = eq.replace('*', '・･')

                # 下付き表記に変換
                processed_eq = re.sub(r'([a-zA-Zﾎｱ-ﾏ火・ﾎｩ])_([a-zA-Z0-9ﾎｱ-ﾏ火・ﾎｩ]+)', r'\1<sub>\2</sub>', processed_eq)
                
                # べき乗を上付き表記に変換
                processed_eq = re.sub(r'\^(\d+|\([^)]+\))', r'<sup>\1</sup>', processed_eq)
                # 括弧内のべき乗も処理
                processed_eq = re.sub(r'\(([^)]+)\^(\d+|\([^)]+\))\)', r'(\1<sup>\2</sup>)', processed_eq)

                html_parts.append(processed_eq)

            # 表示サイズを整えてHTML化
            html = f'<div style="font-size: 16px;">{"<br>".join(html_parts)}</div>'
            
            self.html_display.setHtml(html)

        except Exception as e:
            log_error(f"HTML表示更新エラー: {str(e)}", details=traceback.format_exc())

    def detect_variables(self, equation):
        """モデル式から変数を抽出する"""
        try:
            # 現在の変数リストをクリア
            self.variables.clear()
            
            # 方程式を正規化
            normalized_equation = normalize_equation_text(equation)
            equations = [eq.strip() for eq in normalized_equation.split(',')]
            
            # 左辺の変数を計算結果変数として集める
            result_variables = set()
            
            # 左辺の変数を収集
            for eq in equations:
                if '=' not in eq:
                    continue
                left_side = self._normalize_variable_name(eq.split('=', 1)[0])
                result_variables.add(left_side)
            

            
            # 右辺から入力変数を抽出
            for eq in equations:
                if '=' not in eq:
                    continue
                    
                left_side, right_side = eq.split('=', 1)
                left_side = self._normalize_variable_name(left_side)
                right_side = right_side.strip()

                
                # 正規表現で変数名候補を検出
                detected_vars = re.findall(
                    r"[A-Za-z\u03B1-\u03C9\u0391-\u03A9][A-Za-z0-9_\u03B1-\u03C9\u0391-\u03A9]*",
                    right_side,
                )

                
                # 結果変数以外だけを入力変数として追加
                for var in detected_vars:
                    normalized_var = self._normalize_variable_name(var)
                    if normalized_var and normalized_var not in result_variables:
                        self.variables.append(normalized_var)
            
            # 重複を除去
            self.variables = list(dict.fromkeys(self.variables))

            
        except Exception as e:

            raise 

    def _normalize_variable_name(self, name):
        """前後の空白を除去し、変数名を正規化する"""
        return normalize_variable_name(name)

    def set_equation(self, equation):
        """Set equation text."""
        try:
            normalized_equation = equation or ""
            self.equation_input.setText(normalized_equation)
            self.update_html_display(normalized_equation)
            self.update_variable_list()
        except Exception as e:
            self.parent.log_error(
                f"方程式設定エラー: {str(e)}",
                "方程式設定エラー",
                details=traceback.format_exc(),
            )

    def on_equation_changed(self):
        """Handle equation text changes."""
        try:
            equation = self.equation_input.toPlainText().strip()
            self.update_html_display(equation)
            self.detect_variables(equation)

            if hasattr(self.parent, 'partial_derivative_tab'):
                self.parent.partial_derivative_tab.update_equation_display()
            if hasattr(self.parent, 'report_tab'):
                self.parent.report_tab.update_report()
            if hasattr(self.parent, 'uncertainty_calculation_tab'):
                self.parent.uncertainty_calculation_tab.update_result_combo()
                self.parent.uncertainty_calculation_tab.update_value_combo()
        except Exception as e:
            log_error(f"方程式変更処理エラー: {str(e)}", details=traceback.format_exc())

    def parse_equation(self, equation):
        import re
        normalized_equation = normalize_equation_text(equation)
        equations = [eq.strip() for eq in normalized_equation.split(',')]
        result_vars = []
        input_vars = set()
        for eq in equations:
            if '=' not in eq:
                continue
            left, right = eq.split('=', 1)
            left = self._normalize_variable_name(left)
            right = right.strip()
            result_vars.append(left)
            for var in re.findall(
                r"[A-Za-z_\u03B1-\u03C9\u0391-\u03A9][A-Za-z0-9_\u03B1-\u03C9\u0391-\u03A9]*",
                right,
            ):
                normalized_var = self._normalize_variable_name(var)
                if normalized_var and normalized_var != left:
                    input_vars.add(normalized_var)
        if hasattr(self.parent, 'result_variables'):
            self.parent.result_variables = result_vars
        if hasattr(self.parent, 'input_variables'):
            self.parent.input_variables = list(input_vars)
        variables = result_vars + [v for v in input_vars if v not in result_vars]
        if hasattr(self.parent, 'variables'):
            self.parent.variables = variables
        self._ensure_variable_values_initialized()
        return variables

    def _ensure_variable_values_initialized(self):
        """検出済みの変数に対応する variable_values を初期化する"""
        if not hasattr(self.parent, 'ensure_variable_initialized'):
            return

        for var in getattr(self.parent, 'result_variables', []):
            self.parent.ensure_variable_initialized(var, is_result=True)

        for var in getattr(self.parent, 'variables', []):
            if var not in getattr(self.parent, 'result_variables', []):
                self.parent.ensure_variable_initialized(var)
