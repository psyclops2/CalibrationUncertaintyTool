import os
import traceback
import sympy as sp
import numpy as np
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QComboBox, 
                             QPushButton, QFileDialog, QTextEdit, QLabel, QMessageBox)
from PySide6.QtCore import Qt, Signal, Slot
from src.utils.equation_handler import EquationHandler
from src.utils.value_handler import ValueHandler
from src.utils.uncertainty_calculator import UncertaintyCalculator
from src.utils.number_formatter import format_number_str
from src.tabs.base_tab import BaseTab
from src.utils.translation_keys import *
from src.utils.equation_formatter import EquationFormatter

class ReportTab(BaseTab):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent

        
        # ユーティリティクラスの初期化
        self.equation_handler = EquationHandler(parent)
        self.value_handler = ValueHandler(parent)
        self.uncertainty_calculator = UncertaintyCalculator(parent)
        self.equation_formatter = EquationFormatter(parent)
        
        self.setup_ui()

    def retranslate_ui(self):
        """UIのテキストを現在の言語で更新"""
        self.result_label.setText(self.tr(RESULT_VARIABLE) + ":")
        self.generate_button.setText(self.tr(GENERATE_REPORT))
        self.save_button.setText(self.tr(SAVE_REPORT))
        # レポートを再生成して表示を更新
        self.generate_report()
        
    def setup_ui(self):
        """UIの設定"""

        main_layout = QVBoxLayout()
        
        # 選択部分のレイアウト
        selection_layout = QHBoxLayout()
        
        # 計算結果選択
        self.result_combo = QComboBox()
        self.result_combo.currentTextChanged.connect(self.on_result_changed)
        self.result_label = QLabel(self.tr(RESULT_VARIABLE) + ":")
        selection_layout.addWidget(self.result_label)
        selection_layout.addWidget(self.result_combo)
        
        # レポート生成ボタン
        self.generate_button = QPushButton(self.tr(GENERATE_REPORT))
        self.generate_button.clicked.connect(self.generate_report)
        selection_layout.addWidget(self.generate_button)
        
        # レポート保存ボタン
        self.save_button = QPushButton(self.tr(SAVE_REPORT))
        self.save_button.clicked.connect(self.save_report)
        selection_layout.addWidget(self.save_button)
        
        selection_layout.addStretch()
        main_layout.addLayout(selection_layout)
        
        # レポート表示部分
        self.report_display = QTextEdit()
        self.report_display.setReadOnly(True)
        main_layout.addWidget(self.report_display)
        
        self.setLayout(main_layout)

        
    def update_variable_list(self, variables=None, result_variables=None):
        """変数リストの更新（メインウィンドウからの呼び出し用）"""
        try:

            self.result_combo.clear()
            
            # 引数で渡された場合はそれを使用
            if result_variables:

                self.result_combo.addItems(result_variables)
            # 親ウィンドウから計算結果変数を取得
            elif hasattr(self.parent, 'result_variables'):
                result_vars = self.parent.result_variables

                self.result_combo.addItems(result_vars)
            else:
                pass

                
            # レポートの更新
            self.update_report()
            
        except Exception as e:
            print(f"【エラー】変数リスト更新エラー: {str(e)}")
            print(traceback.format_exc())
            
    def on_result_changed(self, result_var):
        """計算結果が変更されたときの処理"""
        if not result_var:
            return
            
        try:
            self.update_report()
        except Exception as e:
            print(f"【エラー】計算結果変更エラー: {str(e)}")
            print(traceback.format_exc())
            
    def generate_report(self):
        """レポートを生成して表示"""
        try:

            
            # 選択された計算結果変数を取得
            result_var = self.result_combo.currentText()
            if not result_var:

                return
                
            # 選択された計算結果変数の式を取得
            equation = self.equation_handler.get_target_equation(result_var)
            if not equation:

                return
                
            # レポートのHTMLを生成
            html = self.generate_report_html(equation)
            
            # レポートを表示
            self.report_display.setHtml(html)

            
        except Exception as e:
            print(f"【エラー】レポート生成エラー: {str(e)}")
            print(traceback.format_exc())
            QMessageBox.warning(self, self.tr(SAVE_ERROR), self.tr(REPORT_SAVE_ERROR))
            
    def generate_report_html(self, equation):
        """レポートのHTMLを生成（変数名リスト＋詳細情報dictから情報を取得して表示、未設定は"-"で埋める）"""
        try:
            result_var = self.result_combo.currentText()
            if not result_var or not equation:
                return ""

            html = f"""
            <html>
            <head>
                <title>{self.tr(REPORT_TITLE_HTML)}</title>
                <style>
                    body {{ font-family: sans-serif; margin: 20px; }}
                    .container {{ max-width: 800px; margin: auto; }}
                    .title {{ font-size: 20px; font-weight: bold; margin-top: 20px; margin-bottom: 10px; border-bottom: 1px solid #ccc; padding-bottom: 5px;}}
                    table {{ width: 100%; border-collapse: collapse; margin-bottom: 20px; }}
                    th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                    th {{ background-color: #f2f2f2; }}
                    .equation {{ font-family: 'Times New Roman', serif; font-size: 16px; padding: 10px; border: 1px solid #ccc; background-color: #f9f9f9; margin-bottom: 20px; }}
                </style>
            </head>
            <body>
            <div class="container">
                <div class="title">{self.tr(REPORT_MODEL_EQUATION)}</div>
                <div class="equation">{self.equation_formatter.format_equation(equation)}</div>
            """

            # 変数一覧テーブル
            html += f"""
            <div class="title">{self.tr(REPORT_VARIABLE_LIST)}</div>
            <table>
                <tr>
                    <th>{self.tr(REPORT_QUANTITY)}</th>
                    <th>{self.tr(REPORT_UNIT)}</th>
                    <th>{self.tr(REPORT_DEFINITION)}</th>
                    <th>{self.tr(REPORT_UNCERTAINTY_TYPE)}</th>
                </tr>
            """
            variables = getattr(self.parent, 'variables', [])
            # variables はリストまたは辞書を想定するが、どちらでも安全に扱えるよう正規化
            if isinstance(variables, dict):
                variable_names = list(variables.keys())
            elif isinstance(variables, (list, tuple)):
                variable_names = list(variables)
            else:
                variable_names = []

            variable_values = getattr(self.parent, 'variable_values', {})
            if not isinstance(variable_values, dict):
                variable_values = {}

            def get_variable_data(name):
                data = variable_values.get(name, {})
                return data if isinstance(data, dict) else {}

            for var_name in variable_names:
                var_data = get_variable_data(var_name)
                unit = var_data.get('unit', '-')
                definition = var_data.get('definition', '-')
                uncertainty_type = self.get_uncertainty_type_display(var_data.get('type', ''), var_name)
                html += f"""
                <tr>
                    <td>{var_name}</td>
                    <td>{unit}</td>
                    <td>{definition}</td>
                    <td>{uncertainty_type}</td>
                </tr>
                """
            html += "</table>"

            # 各変数の詳細
            html += f'<div class="title">{self.tr(REPORT_VARIABLE_DETAILS)}</div>'
            point_names = getattr(self.parent, 'value_names', [])
            for idx, point_name in enumerate(point_names):
                html += f'<h4>{self.tr(REPORT_CALIBRATION_POINT)}: {point_name}</h4>'
                for var_name in variable_names:
                    if var_name in self.parent.result_variables:
                        continue
                    try:
                        var_data = get_variable_data(var_name)
                        html += f"<h5>{var_name}</h5>"
                        uncertainty_type = var_data.get('type', '')
                        values_list = var_data.get('values', [])
                        if not isinstance(values_list, list):
                            values_list = []
                        value_item = values_list[idx] if idx < len(values_list) else None
                        if uncertainty_type == 'A':
                            if value_item:
                                description = value_item.get('description', '-')
                                html += f"<div>{self.tr(DETAIL_DESCRIPTION)}: {description}</div>"
                            else:
                                html += f"<div>{self.tr(DETAIL_DESCRIPTION)}: -</div>"
                        elif uncertainty_type == 'B':
                            half_width = var_data.get('half_width', '-')
                            distribution = var_data.get('distribution', '-')
                            html += f"<div>{self.tr(HALF_WIDTH)}: {half_width}, {self.tr(DISTRIBUTION)}: {distribution}</div>"
                            description = value_item.get('description', '-') if value_item else '-'
                            html += f"<div>{self.tr(DETAIL_DESCRIPTION)}: {description}</div>"
                        elif uncertainty_type == 'fixed':
                            fixed_value = var_data.get('fixed_value', '-')
                            html += f"<div>{self.tr(FIXED_VALUE)}: {fixed_value}</div>"
                            description = value_item.get('description', '-') if value_item else '-'
                            html += f"<div>{self.tr(DETAIL_DESCRIPTION)}: {description}</div>"
                        else:
                            html += f"<div>{self.tr(DETAIL_DESCRIPTION)}: -</div>"
                    except Exception as e:
                        html += f"<div>-</div>"

            # 不確かさのバジェット・計算結果（計算タブから取得）
            html += f'<div class="title">{self.tr(REPORT_UNCERTAINTY_BUDGET)}</div>'
            calc_tab = getattr(self.parent, 'uncertainty_calculation_tab', None)
            if calc_tab:
                for point_name in point_names:
                    idx = calc_tab.value_combo.findText(point_name)
                    if idx >= 0:
                        calc_tab.value_combo.setCurrentIndex(idx)
                        budget = []
                        for i in range(calc_tab.calibration_table.rowCount()):
                            budget.append({
                                'variable': calc_tab.calibration_table.item(i, 0).text() if calc_tab.calibration_table.item(i, 0) else '-',
                                'central_value': calc_tab.calibration_table.item(i, 1).text() if calc_tab.calibration_table.item(i, 1) else '-',
                                'standard_uncertainty': calc_tab.calibration_table.item(i, 2).text() if calc_tab.calibration_table.item(i, 2) else '-',
                                'dof': calc_tab.calibration_table.item(i, 3).text() if calc_tab.calibration_table.item(i, 3) else '-',
                                'distribution': calc_tab.calibration_table.item(i, 4).text() if calc_tab.calibration_table.item(i, 4) else '-',
                                'sensitivity': calc_tab.calibration_table.item(i, 5).text() if calc_tab.calibration_table.item(i, 5) else '-',
                                'contribution': calc_tab.calibration_table.item(i, 6).text() if calc_tab.calibration_table.item(i, 6) else '-',
                                'contribution_rate': calc_tab.calibration_table.item(i, 7).text() if calc_tab.calibration_table.item(i, 7) else '-'
                            })
                        if budget:
                            html += f"""
                            <table>
                                <tr>
                                    <th>{self.tr(REPORT_FACTOR)}</th>
                                    <th>{self.tr(REPORT_CENTRAL_VALUE)}</th>
                                    <th>{self.tr(REPORT_STANDARD_UNCERTAINTY)}</th>
                                    <th>{self.tr(REPORT_DOF)}</th>
                                    <th>{self.tr(REPORT_DISTRIBUTION)}</th>
                                    <th>{self.tr(REPORT_SENSITIVITY)}</th>
                                    <th>{self.tr(REPORT_CONTRIBUTION)}</th>
                                    <th>{self.tr(REPORT_CONTRIBUTION_RATE)}</th>
                                </tr>
                            """
                            for item in budget:
                                html += f"""
                                <tr>
                                    <td>{item['variable']}</td>
                                    <td>{item['central_value']}</td>
                                    <td>{item['standard_uncertainty']}</td>
                                    <td>{item['dof']}</td>
                                    <td>{item['distribution']}</td>
                                    <td>{item['sensitivity']}</td>
                                    <td>{item['contribution']}</td>
                                    <td>{item['contribution_rate']}</td>
                                </tr>
                                """
                            html += "</table>"
                        html += f"<div class='title'>{self.tr(REPORT_CALCULATION_RESULT)} ({self.tr(REPORT_CALIBRATION_POINT)}: {point_name})</div>"
                        html += f"<table>"
                        html += f"<tr><th>{self.tr(REPORT_ITEM)}</th><th>{self.tr(REPORT_VALUE)}</th></tr>"
                        html += f"<tr><td>{self.tr(REPORT_EQUATION)}</td><td>{self.equation_formatter.format_equation(equation)}</td></tr>"
                        html += f"<tr><td>{self.tr(REPORT_CENTRAL_VALUE)}</td><td>{calc_tab.central_value_label.text()}</td></tr>"
                        html += f"<tr><td>{self.tr(REPORT_COMBINED_UNCERTAINTY)}</td><td>{calc_tab.standard_uncertainty_label.text()}</td></tr>"
                        html += f"<tr><td>{self.tr(REPORT_EFFECTIVE_DOF)}</td><td>{calc_tab.effective_degrees_of_freedom_label.text()}</td></tr>"
                        html += f"<tr><td>{self.tr(REPORT_COVERAGE_FACTOR)}</td><td>{calc_tab.coverage_factor_label.text()}</td></tr>"
                        html += f"<tr><td>{self.tr(REPORT_EXPANDED_UNCERTAINTY)}</td><td>{calc_tab.expanded_uncertainty_label.text()}</td></tr>"
                        html += f"</table>"

            html += """
            </div>
            </body>
            </html>
            """
            return html

        except Exception as e:
            print(f"【エラー】HTML生成エラー: {str(e)}")
            print(traceback.format_exc())
            return self.tr(HTML_GENERATION_ERROR)

    def update_report(self):
        """レポートを更新するための外部インターフェース"""
        if self.result_combo.count() > 0:
            self.generate_report()

    def save_html_to_file(self, html, file_name):
        """HTMLをファイルに保存"""
        try:
            with open(file_name, 'w', encoding='utf-8') as f:
                f.write(html)

            QMessageBox.information(self, self.tr(SAVE_SUCCESS), self.tr(REPORT_SAVED))
        except Exception as e:
            print(f"【エラー】ファイル保存エラー: {str(e)}")
            print(traceback.format_exc())
            QMessageBox.warning(self, self.tr(SAVE_ERROR), self.tr(FILE_SAVE_ERROR))

    def get_uncertainty_type_display(self, type_code, var_name=None):
        """不確かさの種類のコードを表示用の文字列に変換"""
        # 計算結果変数の場合は「計算結果」と表示
        if var_name and hasattr(self.parent, 'result_variables') and var_name in self.parent.result_variables:
            return self.tr(CALCULATION_RESULT_DISPLAY)
            
        type_map = {
            'A': self.tr(TYPE_A_DISPLAY),
            'B': self.tr(TYPE_B_DISPLAY),
            'fixed': self.tr(FIXED_VALUE_DISPLAY)
        }
        return type_map.get(type_code, self.tr(UNKNOWN_TYPE))

    def save_report(self):
        """現在表示中のレポートをファイルに保存する"""
        html = self.report_display.toHtml()
        file_name, _ = QFileDialog.getSaveFileName(self, self.tr(SAVE_REPORT_DIALOG_TITLE), "", "HTML File (*.html);;All Files (*)")
        if file_name:
            self.save_html_to_file(html, file_name)