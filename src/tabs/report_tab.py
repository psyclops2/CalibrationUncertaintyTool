import csv
import io
import os
import traceback
import sympy as sp
import numpy as np
import html as html_lib
import textwrap
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QComboBox, 
                             QPushButton, QFileDialog, QTextEdit, QLabel, QMessageBox)
from PySide6.QtCore import Qt, Signal, Slot
from src.utils.equation_handler import EquationHandler
from src.utils.value_handler import ValueHandler
from src.utils.uncertainty_calculator import UncertaintyCalculator
from src.tabs.base_tab import BaseTab
from src.utils.translation_keys import *
from src.utils.variable_utils import get_distribution_translation_key
from src.utils.equation_formatter import EquationFormatter
from src.utils.regression_utils import calculate_linear_regression_parameters

class ReportTab(BaseTab):
    UNIT_PLACEHOLDER = '-'

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent

        
        # ユーティリティクラスの初期化
        self.equation_handler = EquationHandler(parent)
        self.value_handler = ValueHandler(parent)
        self.uncertainty_calculator = UncertaintyCalculator(parent)
        self.equation_formatter = EquationFormatter(parent)

        self.setup_ui()

    def _get_unit(self, var_name):
        """変数の単位を取得（校正点ごとの単位があればそれも参照）"""
        try:
            if not self.parent:
                return ''

            var_info = self.parent.variable_values.get(var_name, {})
            unit = var_info.get('unit', '').strip()
            if unit:
                return unit

            value_index = getattr(self.value_handler, 'current_value_index', None)
            if isinstance(value_index, int):
                values = var_info.get('values', [])
                if 0 <= value_index < len(values):
                    return values[value_index].get('unit', '').strip()

            return ''
        except Exception:
            return ''

    @staticmethod
    def _format_with_unit(value_text, unit):
        """値に単位を付与して表示用文字列を返す（値や単位が空の場合はそのまま）"""
        if not value_text or value_text in ['--', '-']:
            return value_text

        unit = unit.strip()
        if unit and value_text.rstrip().endswith(unit):
            return value_text

        display_unit = unit if unit else ReportTab.UNIT_PLACEHOLDER
        if value_text.rstrip().endswith(ReportTab.UNIT_PLACEHOLDER):
            return value_text

        return f"{value_text} {display_unit}"

    @staticmethod
    def _format_multiline_cell(text, placeholder='-'):
        """HTMLのセル表示用に改行を保持してエスケープする。"""
        if text is None:
            return placeholder
        raw_text = str(text)
        if not raw_text.strip():
            return placeholder
        normalized = raw_text.replace('\r\n', '\n').replace('\r', '\n')
        escaped = html_lib.escape(normalized)
        return escaped.replace('\n', '<br>')

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

            document_info = getattr(self.parent, 'document_info', {}) or {}
            if hasattr(self.parent, 'document_info_tab'):
                document_info = self.parent.document_info_tab.get_document_info()

            doc_number = html_lib.escape(document_info.get('document_number', ''))
            doc_name = html_lib.escape(document_info.get('document_name', ''))
            version_info = html_lib.escape(document_info.get('version_info', ''))
            description_html = document_info.get('description_html', '') or ""
            description_display = description_html if description_html.strip() else "-"
            revision_rows = self.get_revision_rows(document_info)

            html = textwrap.dedent(f"""
                <html>
                <head>
                    <title>{self.tr(REPORT_TITLE_HTML)}</title>
                    <style>
                        body {{ font-family: sans-serif; margin: 20px; }}
                        .container {{ max-width: 800px; margin: auto; }}
                        .title {{ font-size: 20px; font-weight: bold; margin-top: 20px; margin-bottom: 10px; border-bottom: 1px solid #ccc; padding-bottom: 5px;}}
                        table {{ width: 100%; border-collapse: collapse; margin-bottom: 20px; }}
                        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                        .equation {{ font-family: 'Times New Roman', serif; font-size: 16px; padding: 10px; border: 1px solid #ccc; margin-bottom: 20px; }}
                        .doc-table th {{ width: 180px; }}
                        .subtitle {{ font-size: 20px; font-weight: bold; margin-top: 10px; margin-bottom: 6px; }}
                        .description-body {{ border: 1px solid #ddd; padding: 10px; }}
                        .revision-table {{ width: 100%; border-collapse: collapse; margin-top: 10px; }}
                        .revision-table th, .revision-table td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                    </style>
                </head>
                <body>
                <div class="container">
                    <div class="title">{self.tr(REPORT_DOCUMENT_INFO)}</div>
                    <table class="doc-table">
                        <tr><th>{self.tr(DOCUMENT_NUMBER)}</th><td>{doc_number or '-'}</td></tr>
                        <tr><th>{self.tr(DOCUMENT_NAME)}</th><td>{doc_name or '-'}</td></tr>
                        <tr><th>{self.tr(VERSION_INFO)}</th><td>{version_info or '-'}</td></tr>
                    </table>
                    <div class="subtitle">{self.tr(DESCRIPTION_LABEL)}</div>
                    <div class="description-body">{description_display}</div>
                    <div class="title">{self.tr(REPORT_MODEL_EQUATION)}</div>
                    <div class="equation">{self.equation_formatter.format_equation(equation)}</div>
                """).strip()

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
                unit = var_data.get('unit', '') or self.UNIT_PLACEHOLDER
                definition = self._format_multiline_cell(var_data.get('definition', ''))
                uncertainty_type = self.get_uncertainty_type_display(var_data.get('type', ''), var_name)
                safe_var_name = html_lib.escape(str(var_name))
                safe_unit = html_lib.escape(str(unit))
                html += f"""
                <tr>
                    <td>{safe_var_name}</td>
                    <td>{safe_unit}</td>
                    <td>{definition}</td>
                    <td>{uncertainty_type}</td>
                </tr>
                """
            html += "</table>"

            # 回帰モデル一覧セクション
            point_names = getattr(self.parent, 'value_names', [])
            calc_tab = getattr(self.parent, 'uncertainty_calculation_tab', None)

            for idx, point_name in enumerate(point_names):
                self.value_handler.current_value_index = idx
                html += f'<div class="title">{self.tr(REPORT_CALIBRATION_POINT)}: {point_name}</div>'

                # 各変数の詳細
                html += f'<h4>{self.tr(REPORT_VARIABLE_DETAILS)}</h4>'
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
                            distribution_key = get_distribution_translation_key(distribution)
                            distribution_label = self.tr(distribution_key) if distribution_key else distribution
                            html += f"<div>{self.tr(HALF_WIDTH)}: {half_width}, {self.tr(DISTRIBUTION)}: {distribution_label}</div>"
                            description = value_item.get('description', '-') if value_item else '-'
                            html += f"<div>{self.tr(DETAIL_DESCRIPTION)}: {description}</div>"
                        elif uncertainty_type == 'fixed':
                            fixed_value = value_item.get('central_value', '-') if value_item else '-'
                            html += f"<div>{self.tr(FIXED_VALUE)}: {fixed_value}</div>"
                            description = value_item.get('description', '-') if value_item else '-'
                            html += f"<div>{self.tr(DETAIL_DESCRIPTION)}: {description}</div>"
                        elif uncertainty_type == 'regression':
                            regression_model = value_item.get('regression_model', '-') if value_item else '-'
                            regression_x = value_item.get('regression_x', '-') if value_item else '-'
                            html += f"<div>{self.tr(REGRESSION_MODEL)}: {regression_model}</div>"
                            html += f"<div>{self.tr(REGRESSION_X_VALUE)}: {regression_x}</div>"
                        else:
                            html += f"<div>{self.tr(DETAIL_DESCRIPTION)}: -</div>"
                    except Exception:
                        html += f"<div>-</div>"

                # 不確かさのバジェット（計算タブから取得）
                html += f'<h4>{self.tr(REPORT_UNCERTAINTY_BUDGET)}</h4>'
                if calc_tab:
                    value_idx = calc_tab.value_combo.findText(point_name)
                    if value_idx >= 0:
                        calc_tab.value_combo.setCurrentIndex(value_idx)
                        budget = []
                        for i in range(calc_tab.calibration_table.rowCount()):
                            variable_name = calc_tab.calibration_table.item(i, 0).text() if calc_tab.calibration_table.item(i, 0) else '-'
                            unit = self._get_unit(variable_name)
                            budget.append({
                                'variable': variable_name,
                                'central_value': self._format_with_unit(
                                    calc_tab.calibration_table.item(i, 1).text() if calc_tab.calibration_table.item(i, 1) else '-',
                                    unit,
                                ),
                                'standard_uncertainty': self._format_with_unit(
                                    calc_tab.calibration_table.item(i, 2).text() if calc_tab.calibration_table.item(i, 2) else '-',
                                    unit,
                                ),
                                'dof': calc_tab.calibration_table.item(i, 3).text() if calc_tab.calibration_table.item(i, 3) else '-',
                                'distribution': (
                                    self.tr(get_distribution_translation_key(self.value_handler.get_distribution(variable_name)))
                                    if variable_name
                                    else '-'
                                ) or '-',
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

                        # 計算結果
                        html += f"<h4>{self.tr(REPORT_CALCULATION_RESULT)}</h4>"
                        html += f"<table>"
                        html += f"<tr><th>{self.tr(REPORT_ITEM)}</th><th>{self.tr(REPORT_VALUE)}</th></tr>"
                        html += f"<tr><td>{self.tr(REPORT_EQUATION)}</td><td>{self.equation_formatter.format_equation(equation)}</td></tr>"
                        html += f"<tr><td>{self.tr(REPORT_CENTRAL_VALUE)}</td><td>{calc_tab.central_value_label.text()}</td></tr>"
                        html += f"<tr><td>{self.tr(REPORT_COMBINED_UNCERTAINTY)}</td><td>{calc_tab.standard_uncertainty_label.text()}</td></tr>"
                        html += f"<tr><td>{self.tr(REPORT_EFFECTIVE_DOF)}</td><td>{calc_tab.effective_degrees_of_freedom_label.text()}</td></tr>"
                        html += f"<tr><td>{self.tr(REPORT_COVERAGE_FACTOR)}</td><td>{calc_tab.coverage_factor_label.text()}</td></tr>"
                        html += f"<tr><td>{self.tr(REPORT_EXPANDED_UNCERTAINTY)}</td><td>{calc_tab.expanded_uncertainty_label.text()}</td></tr>"
                        html += f"</table>"

            html += f'<div class="title">{self.tr(REPORT_REVISION_HISTORY)}</div>'
            html += "<table class=\"revision-table\">"
            html += "<tr>"
            html += f"<th>{self.tr(REVISION_VERSION)}</th>"
            html += f"<th>{self.tr(REVISION_DESCRIPTION)}</th>"
            html += f"<th>{self.tr(REVISION_AUTHOR)}</th>"
            html += f"<th>{self.tr(REVISION_CHECKER)}</th>"
            html += f"<th>{self.tr(REVISION_APPROVER)}</th>"
            html += f"<th>{self.tr(REVISION_DATE)}</th>"
            html += "</tr>"
            if revision_rows:
                for row in revision_rows:
                    html += "<tr>"
                    html += f"<td>{html_lib.escape(row.get('version', '') or '-')}</td>"
                    html += f"<td>{html_lib.escape(row.get('description', '') or '-')}</td>"
                    html += f"<td>{html_lib.escape(row.get('author', '') or '-')}</td>"
                    html += f"<td>{html_lib.escape(row.get('checker', '') or '-')}</td>"
                    html += f"<td>{html_lib.escape(row.get('approver', '') or '-')}</td>"
                    html += f"<td>{html_lib.escape(row.get('date', '') or '-')}</td>"
                    html += "</tr>"
            else:
                html += "<tr><td colspan=\"6\">-</td></tr>"
            html += "</table>"

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

    def get_revision_rows(self, document_info):
        """改訂履歴の入力内容をパースしてリストで返却"""
        if hasattr(self.parent, 'document_info_tab'):
            return self.parent.document_info_tab.parse_revision_history()
        if isinstance(document_info, dict):
            return self.parse_revision_history_text(document_info.get('revision_history', ''))
        return []

    def parse_revision_history_text(self, text):
        rows = []
        reader = csv.reader(io.StringIO(text or ""))
        for row in reader:
            if not any(cell.strip() for cell in row):
                continue
            version, description, author, checker, approver, date = (
                row + ["", "", "", "", "", ""]
            )[:6]
            rows.append({
                'version': version.strip(),
                'description': description.strip(),
                'author': author.strip(),
                'checker': checker.strip(),
                'approver': approver.strip(),
                'date': date.strip()
            })
        return rows

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
            'fixed': self.tr(FIXED_VALUE_DISPLAY),
            'regression': self.tr(REGRESSION_VALUE_DISPLAY)
        }
        return type_map.get(type_code, self.tr(UNKNOWN_TYPE))

    def save_report(self):
        """現在表示中のレポートをファイルに保存する"""
        html = self.report_display.toHtml()
        file_name, _ = QFileDialog.getSaveFileName(self, self.tr(SAVE_REPORT_DIALOG_TITLE), "", "HTML File (*.html);;All Files (*)")
        if file_name:
            self.save_html_to_file(html, file_name)
