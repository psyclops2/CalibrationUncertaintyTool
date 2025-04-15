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

class ReportTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        print("【デバッグ】ReportTab初期化")
        
        # ユーティリティクラスの初期化
        self.equation_handler = EquationHandler(parent)
        self.value_handler = ValueHandler(parent)
        self.uncertainty_calculator = UncertaintyCalculator(parent)
        
        self.setup_ui()
        
    def setup_ui(self):
        """UIの設定"""
        print("【デバッグ】setup_ui開始")
        main_layout = QVBoxLayout()
        
        # 選択部分のレイアウト
        selection_layout = QHBoxLayout()
        
        # 計算結果選択
        self.result_combo = QComboBox()
        self.result_combo.currentTextChanged.connect(self.on_result_changed)
        selection_layout.addWidget(QLabel("計算結果:"))
        selection_layout.addWidget(self.result_combo)
        
        # レポート生成ボタン
        self.generate_button = QPushButton("レポート生成")
        self.generate_button.clicked.connect(self.generate_report)
        selection_layout.addWidget(self.generate_button)
        
        # レポート保存ボタン
        self.save_button = QPushButton("レポート保存")
        self.save_button.clicked.connect(self.save_report)
        selection_layout.addWidget(self.save_button)
        
        selection_layout.addStretch()
        main_layout.addLayout(selection_layout)
        
        # レポート表示部分
        self.report_display = QTextEdit()
        self.report_display.setReadOnly(True)
        main_layout.addWidget(self.report_display)
        
        self.setLayout(main_layout)
        print("【デバッグ】setup_ui完了")
        
    def update_variable_list(self, variables=None, result_variables=None):
        """変数リストの更新（メインウィンドウからの呼び出し用）"""
        try:
            print("【デバッグ】update_variable_list開始")
            self.result_combo.clear()
            
            # 引数で渡された場合はそれを使用
            if result_variables:
                print(f"【デバッグ】引数から計算結果変数取得: {result_variables}")
                self.result_combo.addItems(result_variables)
            # 親ウィンドウから計算結果変数を取得
            elif hasattr(self.parent, 'result_variables'):
                result_vars = self.parent.result_variables
                print(f"【デバッグ】親ウィンドウから計算結果変数取得: {result_vars}")
                self.result_combo.addItems(result_vars)
            else:
                print("【デバッグ】計算結果変数が見つかりません")
                
            # レポートの更新
            self.generate_report()
            
        except Exception as e:
            print(f"【エラー】変数リスト更新エラー: {str(e)}")
            print(traceback.format_exc())
            
    def on_result_changed(self, result_var):
        """計算結果が変更されたときの処理"""
        if not result_var:
            return
            
        try:
            self.generate_report()
        except Exception as e:
            print(f"【エラー】計算結果変更エラー: {str(e)}")
            print(traceback.format_exc())
            
    def generate_report(self):
        """レポートを生成して表示"""
        try:
            print("【デバッグ】レポート生成開始")
            
            # 選択された計算結果変数を取得
            result_var = self.result_combo.currentText()
            if not result_var:
                print("【デバッグ】計算結果が未選択")
                return
                
            # 選択された計算結果変数の式を取得
            equation = self.equation_handler.get_target_equation(result_var)
            if not equation:
                print("【デバッグ】式が取得できません")
                return
                
            # レポートのHTMLを生成
            html = self.generate_report_html(equation)
            
            # レポートを表示
            self.report_display.setHtml(html)
            print("【デバッグ】レポート生成完了")
            
        except Exception as e:
            print(f"【エラー】レポート生成エラー: {str(e)}")
            print(traceback.format_exc())
            QMessageBox.warning(self, "エラー", "レポートの生成中にエラーが発生しました。")
            
    def generate_report_html(self, equation):
        """レポートのHTMLを生成"""
        try:
            print(f"【デバッグ】HTML生成開始: {equation}")
            
            # HTMLのヘッダー部分
            html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 20px; }}
                    table {{ border-collapse: collapse; width: 100%; margin: 10px 0; }}
                    th, td {{ border: 1px solid black; padding: 8px; text-align: left; }}
                    th {{ background-color: #f2f2f2; }}
                    .section {{ margin: 20px 0; }}
                    .title {{ font-size: 1.2em; font-weight: bold; margin: 10px 0; }}
                </style>
            </head>
            <body>
            """
            
            # 値の数を取得
            value_count = self.parent.value_count if hasattr(self.parent, 'value_count') else 1
            
            # 変数リストテーブルを追加（値1の計算結果の前）
            html += """
            <div class="section">
                <div class="title">量リスト</div>
                <table class="data-table">
                    <tr>
                        <th>量</th>
                        <th>単位</th>
                        <th>定義</th>
                        <th>不確かさの種類</th>
                    </tr>
            """
            
            # 入力変数を追加
            input_vars = sorted([var for var in self.parent.variables if var not in self.parent.result_variables])
            for var in input_vars:
                var_info = self.parent.variable_values.get(var, {})
                unit = var_info.get('unit', '')
                definition = var_info.get('definition', '')
                html += f"""
                    <tr>
                        <td>{var}</td>
                        <td>{unit}</td>
                        <td>{definition}</td>
                        <td>{self.get_uncertainty_type_display(var_info.get('type', 'A'), var)}</td>
                    </tr>
                """
            
            # 計算結果変数を追加
            result_vars = sorted(self.parent.result_variables)
            for var in result_vars:
                var_info = self.parent.variable_values.get(var, {})
                unit = var_info.get('unit', '')
                definition = var_info.get('definition', '')
                html += f"""
                    <tr>
                        <td>{var}</td>
                        <td>{unit}</td>
                        <td>{definition}</td>
                        <td>{self.get_uncertainty_type_display(var_info.get('type', 'A'), var)}</td>
                    </tr>
                """
            
            html += """
                </table>
            </div>
            """
            
            # 各値について計算
            for value_index in range(value_count):
                print(f"【デバッグ】値{value_index + 1}の処理開始")
                
                # ValueHandlerの現在の値インデックスを更新
                self.value_handler.current_value_index = value_index
                
                # 式を解析
                left_side, right_side = equation.split('=', 1)
                left_side = left_side.strip()
                right_side = right_side.strip()
                
                # 変数を抽出
                variables = self.equation_handler.get_variables_from_equation(right_side)
                print(f"【デバッグ】抽出された変数: {variables}")
                
                # 各変数の情報を収集
                contributions = []  # 寄与不確かさを保存するリスト
                degrees_of_freedom_list = []  # 自由度を保存するリスト
                variable_data = []  # 変数データを保存するリスト
                
                for var in variables:
                    print(f"【デバッグ】変数処理開始: {var}")
                    data = {}
                    data['name'] = var
                    
                    # 中央値
                    data['central_value'] = self.value_handler.get_central_value(var)
                    print(f"【デバッグ】中央値: {data['central_value']}")
                    
                    # 標準不確かさ
                    data['standard_uncertainty'] = self.value_handler.get_standard_uncertainty(var)
                    print(f"【デバッグ】標準不確かさ: {data['standard_uncertainty']}")
                    
                    # 自由度
                    data['degrees_of_freedom'] = self.value_handler.get_degrees_of_freedom(var)
                    print(f"【デバッグ】自由度: {data['degrees_of_freedom']}")
                    degrees_of_freedom_list.append(data['degrees_of_freedom'])
                    
                    # 分布
                    data['distribution'] = self.value_handler.get_distribution(var)
                    print(f"【デバッグ】分布: {data['distribution']}")
                    
                    # 感度係数
                    data['sensitivity'] = self.equation_handler.calculate_sensitivity(right_side, var, variables, self.value_handler)
                    print(f"【デバッグ】感度係数: {data['sensitivity']}")
                    
                    # 寄与不確かさ
                    try:
                        if data['standard_uncertainty'] and data['sensitivity']:
                            contribution = float(data['standard_uncertainty']) * float(data['sensitivity'])
                            print(f"【デバッグ】寄与不確かさ: {contribution}")
                            data['contribution'] = contribution
                            contributions.append(contribution)
                        else:
                            print(f"【デバッグ】寄与不確かさ計算スキップ")
                            data['contribution'] = 0
                            contributions.append(0)
                    except (ValueError, TypeError) as e:
                        print(f"【デバッグ】寄与不確かさ計算エラー: {str(e)}")
                        data['contribution'] = 0
                        contributions.append(0)
                    
                    variable_data.append(data)
                
                # 合成標準不確かさの計算
                result_standard_uncertainty = self.uncertainty_calculator.calculate_combined_uncertainty(contributions)
                
                # 寄与率の計算
                contribution_rates = self.uncertainty_calculator.calculate_contribution_rates(contributions)
                for data, rate in zip(variable_data, contribution_rates):
                    data['contribution_rate'] = rate
                
                # 計算結果の取得
                result_central_value = self.equation_handler.calculate_result_central_value(right_side, variables, self.value_handler)
                
                # 有効自由度の計算
                effective_df = self.uncertainty_calculator.calculate_effective_degrees_of_freedom(
                    result_standard_uncertainty, contributions, degrees_of_freedom_list
                )
                
                # 包含係数の計算
                coverage_factor = self.uncertainty_calculator.get_coverage_factor(effective_df)
                
                # 拡張不確かさの計算
                expanded_uncertainty = coverage_factor * result_standard_uncertainty
                
                # 値ごとのセクションを追加
                html += f"""
                <div class="section">
                    <div class="title">値{value_index + 1}の計算結果</div>
                    
                    <div class="section">
                        <div class="title">不確かさ予算表</div>
                        <table>
                            <tr>
                                <th>変数</th>
                                <th>中央値</th>
                                <th>標準不確かさ</th>
                                <th>自由度</th>
                                <th>分布</th>
                                <th>感度係数</th>
                                <th>寄与不確かさ</th>
                                <th>寄与率</th>
                            </tr>
                """
                
                # 変数データの追加
                for data in variable_data:
                    html += f"""
                            <tr>
                                <td>{data['name']}</td>
                                <td>{data['central_value']}</td>
                                <td>{format_number_str(data['standard_uncertainty'])}</td>
                                <td>{data['degrees_of_freedom']}</td>
                                <td>{data['distribution']}</td>
                                <td>{format_number_str(data['sensitivity'])}</td>
                                <td>{format_number_str(data['contribution'])}</td>
                                <td>{data['contribution_rate']:.2f}%</td>
                            </tr>
                    """
                
                html += f"""
                        </table>
                    </div>
                    
                    <div class="section">
                        <div class="title">計算結果</div>
                        <table>
                            <tr>
                                <th>項目</th>
                                <th>値</th>
                            </tr>
                            <tr>
                                <td>計算式</td>
                                <td>{equation}</td>
                            </tr>
                            <tr>
                                <td>中央値</td>
                                <td>{result_central_value}</td>
                            </tr>
                            <tr>
                                <td>合成標準不確かさ</td>
                                <td>{format_number_str(result_standard_uncertainty)}</td>
                            </tr>
                            <tr>
                                <td>有効自由度</td>
                                <td>{effective_df:.2f}</td>
                            </tr>
                            <tr>
                                <td>包含係数</td>
                                <td>{coverage_factor:.3f}</td>
                            </tr>
                            <tr>
                                <td>拡張不確かさ</td>
                                <td>{format_number_str(expanded_uncertainty)}</td>
                            </tr>
                        </table>
                    </div>
                </div>
                """
            
            # HTMLのフッター部分
            html += """
            </body>
            </html>
            """
            
            return html
            
        except Exception as e:
            print(f"【エラー】HTML生成エラー: {str(e)}")
            print(traceback.format_exc())
            return "<html><body><h1>エラーが発生しました</h1></body></html>"
            
    def save_report(self):
        """レポートをHTMLファイルとして保存"""
        try:
            print("【デバッグ】レポート保存開始")
            
            # 保存先のファイル名を取得
            file_name, _ = QFileDialog.getSaveFileName(
                self,
                "レポートの保存",
                "",
                "HTMLファイル (*.html)"
            )
            
            if not file_name:
                print("【デバッグ】保存がキャンセルされました")
                return
                
            # 現在表示中のHTMLを取得して保存
            html = self.report_display.toHtml()
            self.save_html_to_file(html, file_name)
            
        except Exception as e:
            print(f"【エラー】レポート保存エラー: {str(e)}")
            print(traceback.format_exc())
            QMessageBox.warning(self, "エラー", "レポートの保存中にエラーが発生しました。")
            
    def save_html_to_file(self, html, file_name):
        """HTMLをファイルに保存"""
        try:
            with open(file_name, 'w', encoding='utf-8') as f:
                f.write(html)
            print(f"【デバッグ】レポートを保存しました: {file_name}")
            QMessageBox.information(self, "成功", "レポートを保存しました。")
        except Exception as e:
            print(f"【エラー】ファイル保存エラー: {str(e)}")
            print(traceback.format_exc())
            QMessageBox.warning(self, "エラー", "ファイルの保存中にエラーが発生しました。")

    def get_uncertainty_type_display(self, type_code, var_name=None):
        """不確かさの種類のコードを表示用の文字列に変換"""
        # 計算結果変数の場合は「計算結果」と表示
        if var_name and var_name in self.parent.result_variables:
            return '計算結果'
            
        type_map = {
            'A': 'Type A',
            'B': 'Type B',
            'fixed': '固定値'
        }
        return type_map.get(type_code, '未知') 