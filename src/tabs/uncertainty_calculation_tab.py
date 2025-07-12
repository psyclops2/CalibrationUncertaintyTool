from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QComboBox, QTableWidget, QTableWidgetItem, QHeaderView,
                             QGroupBox, QFormLayout, QDoubleSpinBox, QMessageBox)
from PySide6.QtCore import Qt, Signal, Slot
import traceback

from src.utils.equation_handler import EquationHandler
from src.utils.value_handler import ValueHandler
from src.utils.uncertainty_calculator import UncertaintyCalculator
from src.utils.number_formatter import format_number_str
from src.tabs.base_tab import BaseTab
from src.utils.translation_keys import *

class UncertaintyCalculationTab(BaseTab):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self._updating_table = False  # Flag to prevent recursive updates

        if self.parent:
            pass

        # ユーティリティクラスの初期化
        self.equation_handler = EquationHandler(parent)
        self.value_handler = ValueHandler(parent)
        self.uncertainty_calculator = UncertaintyCalculator(parent)
        
        self.setup_ui()

    def retranslate_ui(self):
        """UIのテキストを現在の言語で更新"""
        self.result_group.setTitle(self.tr(RESULT_SELECTION))
        self.result_variable_label.setText(self.tr(RESULT_VARIABLE) + ":")
        self.calibration_point_label.setText(self.tr(CALIBRATION_POINT) + ":")
        self.calibration_group.setTitle(self.tr(CALIBRATION_VALUE))
        self.headers = [
            self.tr(VARIABLE),
            self.tr(CENTRAL_VALUE),
            self.tr(STANDARD_UNCERTAINTY),
            self.tr(DEGREES_OF_FREEDOM),
            self.tr(DISTRIBUTION),
            self.tr(SENSITIVITY_COEFFICIENT),
            self.tr(CONTRIBUTION_UNCERTAINTY),
            self.tr(CONTRIBUTION_RATE)
        ]
        self.calibration_table.setHorizontalHeaderLabels(self.headers)
        self.result_display_group.setTitle(self.tr(CALCULATION_RESULT))
        self.central_value_text.setText(self.tr(CENTRAL_VALUE) + ":")
        self.combined_uncertainty_text.setText(self.tr(COMBINED_STANDARD_UNCERTAINTY) + ":")
        self.effective_dof_text.setText(self.tr(EFFECTIVE_DEGREES_OF_FREEDOM) + ":")
        self.coverage_factor_text.setText(self.tr(COVERAGE_FACTOR) + ":")
        self.expanded_uncertainty_text.setText(self.tr(EXPANDED_UNCERTAINTY) + ":")

        # 初期表示時にプルダウンを更新
        self.update_result_combo()
        self.update_value_combo()
        
    def on_table_item_changed(self, item):
        """Handle changes to table items"""
        # Skip if we're the ones updating the table
        if self._updating_table:
            return
            
        if item.column() in [1, 2, 3, 4]:  # Columns with editable values
            row = item.row()
            var_item = self.calibration_table.item(row, 0)
            if not var_item:
                return
                
            var = var_item.text()  # Get variable name
            
            # Get the value handler
            value_handler = self.value_handler
            
            try:
                # Block signals to prevent recursion
                self.calibration_table.blockSignals(True)
                
                if item.column() == 1:  # Central value
                    value_handler.update_variable_value(var, 'central_value', item.text())
                elif item.column() == 2:  # Standard uncertainty
                    value_handler.update_variable_value(var, 'standard_uncertainty', item.text())
                elif item.column() == 3:  # Degrees of freedom
                    value_handler.update_variable_value(var, 'degrees_of_freedom', item.text())
                elif item.column() == 4:  # Distribution
                    value_handler.update_variable_value(var, 'distribution', item.text())
                
                # Recalculate to update everything
                result_var = self.result_combo.currentText()
                if result_var:
                    equation = self.equation_handler.get_target_equation(result_var)
                    if equation:
                        self._updating_table = True
                        self.calculate_sensitivity_coefficients(equation)
                        self._updating_table = False
                        
            except Exception as e:
                print(f"【エラー】テーブル値更新エラー: {str(e)}")
                print(traceback.format_exc())
            finally:
                # Always unblock signals
                self.calibration_table.blockSignals(False)

    def setup_ui(self):
        """UIの設定"""
        main_layout = QHBoxLayout()
        
        # 左側のレイアウト（1/4）
        left_layout = QVBoxLayout()
        
        # 計算結果選択
        self.result_group = QGroupBox(self.tr(RESULT_SELECTION))
        self.result_group.setMaximumHeight(200)
        result_layout = QVBoxLayout()
                
        self.result_combo = QComboBox()
        self.result_combo.currentTextChanged.connect(self.on_result_changed)
        self.result_variable_label = QLabel(self.tr(RESULT_VARIABLE) + ":")
        result_layout.addWidget(self.result_variable_label)
        result_layout.addWidget(self.result_combo)
        
        # 値の選択
        self.value_combo = QComboBox()
        self.value_combo.currentIndexChanged.connect(self.on_value_changed)
        self.calibration_point_label = QLabel(self.tr(CALIBRATION_POINT) + ":")
        result_layout.addWidget(self.calibration_point_label)
        result_layout.addWidget(self.value_combo)
        
        self.result_group.setLayout(result_layout)
        left_layout.addWidget(self.result_group)
        
        left_layout.addStretch(1)
        
        # 右側のレイアウト（3/4）
        right_layout = QVBoxLayout()
        
        # 校正値表示
        self.calibration_group = QGroupBox(self.tr(CALIBRATION_VALUE))
        calibration_layout = QVBoxLayout()
        
        self.calibration_table = QTableWidget()
        self.calibration_table.setColumnCount(8)
        self.headers = [
            self.tr(VARIABLE),
            self.tr(CENTRAL_VALUE),
            self.tr(STANDARD_UNCERTAINTY),
            self.tr(DEGREES_OF_FREEDOM),
            self.tr(DISTRIBUTION),
            self.tr(SENSITIVITY_COEFFICIENT),
            self.tr(CONTRIBUTION_UNCERTAINTY),
            self.tr(CONTRIBUTION_RATE)
        ]
        self.calibration_table.setHorizontalHeaderLabels(self.headers)
        # ユーザーが手動で調整できるように変更
        self.calibration_table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        # 初期のカラム幅を設定
        self.calibration_table.setColumnWidth(0, 100)  # 量
        self.calibration_table.setColumnWidth(1, 100)  # 中央値
        self.calibration_table.setColumnWidth(2, 100)  # 標準不確かさ
        self.calibration_table.setColumnWidth(3, 80)   # 自由度
        self.calibration_table.setColumnWidth(4, 100)  # 分布
        self.calibration_table.setColumnWidth(5, 100)  # 感度係数
        self.calibration_table.setColumnWidth(6, 100)  # 寄与不確かさ
        self.calibration_table.setColumnWidth(7, 80)   # 寄与率
        calibration_layout.addWidget(self.calibration_table)
        
        self.calibration_group.setLayout(calibration_layout)
        right_layout.addWidget(self.calibration_group)
        
        # 計算結果表示
        self.result_display_group = QGroupBox(self.tr(CALCULATION_RESULT))
        result_display_layout = QFormLayout()
        
        # 中央値
        self.central_value_label = QLabel("")
        self.central_value_text = QLabel(self.tr(CENTRAL_VALUE) + ":")
        result_display_layout.addRow(self.central_value_text, self.central_value_label)
        
        # 合成標準不確かさ
        self.standard_uncertainty_label = QLabel("")
        self.combined_uncertainty_text = QLabel(self.tr(COMBINED_STANDARD_UNCERTAINTY) + ":")
        result_display_layout.addRow(self.combined_uncertainty_text, self.standard_uncertainty_label)
        
        # 有効自由度
        self.effective_degrees_of_freedom_label = QLabel("")
        self.effective_dof_text = QLabel(self.tr(EFFECTIVE_DEGREES_OF_FREEDOM) + ":")
        result_display_layout.addRow(self.effective_dof_text, self.effective_degrees_of_freedom_label)
        
        # 包含係数
        self.coverage_factor_label = QLabel("")
        self.coverage_factor_text = QLabel(self.tr(COVERAGE_FACTOR) + ":")
        result_display_layout.addRow(self.coverage_factor_text, self.coverage_factor_label)
        
        # 拡張不確かさ
        self.expanded_uncertainty_label = QLabel("")
        self.expanded_uncertainty_text = QLabel(self.tr(EXPANDED_UNCERTAINTY) + ":")
        result_display_layout.addRow(self.expanded_uncertainty_text, self.expanded_uncertainty_label)
        
        self.result_display_group.setLayout(result_display_layout)
        right_layout.addWidget(self.result_display_group)
        
        # メインレイアウトに左右のレイアウトを追加
        main_layout.addLayout(left_layout, 1)  # 左側のレイアウト（幅の比率1）
        main_layout.addLayout(right_layout, 3)  # 右側のレイアウト（幅の比率3）
        
        self.setLayout(main_layout)
        
        # Connect the itemChanged signal
        self.calibration_table.itemChanged.connect(self.on_table_item_changed)

        
    def update_result_combo(self):
        """計算結果の選択肢を更新"""
        try:

            self.result_combo.clear()
            
            # 親ウィンドウから計算結果変数を取得
            if hasattr(self.parent, 'result_variables'):
                result_vars = self.parent.result_variables

                
                # 計算結果変数をmodel_equation_tab.pyの順序に合わせる
                for var in self.parent.variables:
                    if var in result_vars:
                        self.result_combo.addItem(var)
            else:
                pass

                
        except Exception as e:
            print(f"【エラー】計算結果選択肢更新エラー: {str(e)}")
            print(traceback.format_exc())
        
    def update_value_combo(self):
        """校正点の選択肢を更新"""
        try:

            self.value_combo.clear()
            
            value_names = getattr(self.parent, 'value_names', [])
            for name in value_names:
                self.value_combo.addItem(name)
                
        except Exception as e:
            print(f"【エラー】校正点選択肢更新エラー: {str(e)}")
            print(traceback.format_exc())
            
    def on_result_changed(self, result_var):
        """計算結果が変更されたときの処理"""
        if not result_var:
            return
            
        try:
            # 選択された計算結果変数の式を取得
            equation = self.equation_handler.get_target_equation(result_var)
            if not equation:
                return
                
            # 偏微分と感度係数の計算
            self.calculate_sensitivity_coefficients(equation)
            
        except Exception as e:
            print(f"【エラー】計算結果変更エラー: {str(e)}")
            print(traceback.format_exc())
            
    def on_value_changed(self, index):
        """校正点が変更されたときの処理"""
        if index < 0:
            return
            
        try:
            # ValueHandlerの現在の校正点インデックスを更新
            self.value_handler.current_value_index = index
            
            # 現在選択されている計算結果変数を取得
            result_var = self.result_combo.currentText()
            if not result_var:
                return
                
            # 選択された計算結果変数の式を取得
            equation = self.equation_handler.get_target_equation(result_var)
            if not equation:
                return
                
            # 偏微分と感度係数の計算
            self.calculate_sensitivity_coefficients(equation)
            
        except Exception as e:
            print(f"【エラー】校正点変更エラー: {str(e)}")
            print(traceback.format_exc())
            

    
    def calculate_sensitivity_coefficients(self, equation):
        """感度係数を計算して表示"""
        # If we're already updating, skip to prevent recursion
        if self._updating_table:
            return
            
        try:
            # Set updating flag
            self._updating_table = True

            # 式を解析
            left_side, right_side = equation.split('=', 1)
            left_side = left_side.strip()
            right_side = right_side.strip()
            
            # 変数を抽出
            variables = self.equation_handler.get_variables_from_equation(right_side)

            
            # 親ウィンドウの変数リストの順序に合わせる
            ordered_variables = []
            for var in self.parent.variables:
                if var in variables:
                    ordered_variables.append(var)
            
            # テーブルを更新
            self.calibration_table.setRowCount(len(ordered_variables))
            
            # 各変数について処理
            contributions = []  # 寄与不確かさを保存するリスト
            degrees_of_freedom_list = []
            
            for i, var in enumerate(ordered_variables):

                # 変数名
                self.calibration_table.setItem(i, 0, QTableWidgetItem(var))
                
                # 中央値
                central_value = self.value_handler.get_central_value(var)
                if central_value == '' or central_value is None:
                    self.calibration_table.setItem(i, 1, QTableWidgetItem('--'))
                    self.calibration_table.setItem(i, 2, QTableWidgetItem('--'))  # 標準不確かさ
                    self.calibration_table.setItem(i, 3, QTableWidgetItem('--'))  # 自由度
                    self.calibration_table.setItem(i, 4, QTableWidgetItem('--'))  # 分布
                    self.calibration_table.setItem(i, 5, QTableWidgetItem('--'))  # 感度係数
                    self.calibration_table.setItem(i, 6, QTableWidgetItem('--'))  # 寄与不確かさ
                    contributions.append(0)
                    degrees_of_freedom_list.append(0)
                    continue
                else:
                    self.calibration_table.setItem(i, 1, QTableWidgetItem(format_number_str(float(central_value))))
                
                # 標準不確かさ
                standard_uncertainty = self.value_handler.get_standard_uncertainty(var)
                self.calibration_table.setItem(i, 2, QTableWidgetItem(format_number_str(standard_uncertainty)))
                
                # 自由度
                degrees_of_freedom = self.value_handler.get_degrees_of_freedom(var)
                self.calibration_table.setItem(i, 3, QTableWidgetItem(str(degrees_of_freedom)))
                degrees_of_freedom_list.append(degrees_of_freedom)
                
                # 分布
                distribution = self.value_handler.get_distribution(var)
                self.calibration_table.setItem(i, 4, QTableWidgetItem(distribution))
                
                # 感度係数
                sensitivity = self.equation_handler.calculate_sensitivity(right_side, var, variables, self.value_handler)
                self.calibration_table.setItem(i, 5, QTableWidgetItem(format_number_str(float(sensitivity))))
                
                # 寄与不確かさ
                try:
                    if standard_uncertainty and sensitivity:
                        contribution = float(standard_uncertainty) * float(sensitivity)
                        self.calibration_table.setItem(i, 6, QTableWidgetItem(format_number_str(contribution)))
                        contributions.append(contribution)
                    else:
                        self.calibration_table.setItem(i, 6, QTableWidgetItem(""))
                        contributions.append(0)
                except (ValueError, TypeError) as e:
                    self.calibration_table.setItem(i, 6, QTableWidgetItem(""))
                    contributions.append(0)
            
            # 合成標準不確かさの計算
            result_standard_uncertainty = self.uncertainty_calculator.calculate_combined_uncertainty(contributions)
            
            # 寄与率の計算と表示
            contribution_rates = self.uncertainty_calculator.calculate_contribution_rates(contributions)
            for i, rate in enumerate(contribution_rates):
                self.calibration_table.setItem(i, 7, QTableWidgetItem(f"{rate:.2f}%"))
            
            # 計算結果を表示
            try:
                # 中央値の計算
                result_central_value = self.equation_handler.calculate_result_central_value(right_side, variables, self.value_handler)
                try:
                    self.central_value_label.setText(format_number_str(float(result_central_value)))
                except (ValueError, TypeError):
                    self.central_value_label.setText('--')
                    self.standard_uncertainty_label.setText('--')
                    self.effective_degrees_of_freedom_label.setText('--')
                    self.coverage_factor_label.setText('--')
                    self.expanded_uncertainty_label.setText('--')
                    return
                
                # 合成標準不確かさの表示
                self.standard_uncertainty_label.setText(format_number_str(result_standard_uncertainty))
                
                # 有効自由度の計算
                effective_df = self.uncertainty_calculator.calculate_effective_degrees_of_freedom(
                    result_standard_uncertainty, contributions, degrees_of_freedom_list
                )
                self.effective_degrees_of_freedom_label.setText(format_number_str(float(effective_df)))
                
                # 包含係数の計算
                coverage_factor = self.uncertainty_calculator.get_coverage_factor(effective_df)
                self.coverage_factor_label.setText(format_number_str(float(coverage_factor)))
                
                # 拡張不確かさの計算
                expanded_uncertainty = coverage_factor * result_standard_uncertainty
                self.expanded_uncertainty_label.setText(format_number_str(expanded_uncertainty))

                # --- ここで計算結果をMainWindowに保存 ---
                result_var = self.result_combo.currentText()
                point_name = self.value_combo.currentText()
                # バジェット情報を作成
                budget = []
                for i, var in enumerate(ordered_variables):
                    budget.append({
                        'variable': var,
                        'central_value': self.calibration_table.item(i, 1).text() if self.calibration_table.item(i, 1) else '',
                        'standard_uncertainty': self.calibration_table.item(i, 2).text() if self.calibration_table.item(i, 2) else '',
                        'dof': self.calibration_table.item(i, 3).text() if self.calibration_table.item(i, 3) else '',
                        'distribution': self.calibration_table.item(i, 4).text() if self.calibration_table.item(i, 4) else '',
                        'sensitivity': self.calibration_table.item(i, 5).text() if self.calibration_table.item(i, 5) else '',
                        'contribution': self.calibration_table.item(i, 6).text() if self.calibration_table.item(i, 6) else '',
                        'contribution_rate': float(self.calibration_table.item(i, 7).text().replace('%','')) if self.calibration_table.item(i, 7) and self.calibration_table.item(i, 7).text().replace('%','').replace('.','',1).isdigit() else 0.0
                    })
                # MainWindowに保存
                if not hasattr(self.parent, 'calculation_results'):
                    self.parent.calculation_results = {}
                if result_var not in self.parent.calculation_results:
                    self.parent.calculation_results[result_var] = {}
                self.parent.calculation_results[result_var][point_name] = {
                    'budget': budget,
                    'result_central_value': result_central_value,
                    'result_standard_uncertainty': result_standard_uncertainty,
                    'effective_df': effective_df,
                    'coverage_factor': coverage_factor,
                    'expanded_uncertainty': expanded_uncertainty,
                }
                # --- ここまで ---

            except Exception as e:
                print(f"【エラー】計算結果表示エラー: {str(e)}")
                print(traceback.format_exc())
                
        except Exception as e:
            print(f"【エラー】感度係数計算エラー: {str(e)}")
            print(traceback.format_exc())
        finally:
            # Always reset the updating flag
            self._updating_table = False 