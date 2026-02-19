from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QComboBox, QTableWidget, QTableWidgetItem, QHeaderView,
                             QGroupBox, QFormLayout, QDoubleSpinBox,
                             QAbstractItemView)
from PySide6.QtCore import Qt, Signal, Slot
import traceback

from src.utils.equation_handler import EquationHandler
from src.utils.value_handler import ValueHandler
from src.utils.uncertainty_calculator import UncertaintyCalculator
from src.utils.number_formatter import (
    format_central_value_with_uncertainty,
    format_standard_uncertainty,
    format_expanded_uncertainty,
    format_contribution_rate,
    format_coverage_factor,
    format_number_str,
)
from src.tabs.base_tab import BaseTab
from src.utils.translation_keys import *
from src.utils.variable_utils import get_distribution_translation_key
from src.utils.app_logger import log_error
from src.utils.budget_error_utils import (
    to_budget_float,
    summarize_budget_issues,
    detect_zero_denominator_terms,
    build_zero_denominator_hint,
)

class UncertaintyCalculationTab(BaseTab):
    UNIT_PLACEHOLDER = '-'

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self._updating_table = False  # Flag to prevent recursive updates
        self._last_budget_error_message = None

        if self.parent:
            pass

        # ユーティリティクラスの初期化
        self.equation_handler = EquationHandler(parent)
        self.value_handler = ValueHandler(parent)
        self.uncertainty_calculator = UncertaintyCalculator(parent)

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

            # 校正点ごとに単位が保存されている場合は現在の校正点の単位を使用
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

        # すでに同じ単位やプレースホルダーが付いている場合は重ね付けしない
        if unit and value_text.rstrip().endswith(unit):
            return value_text
        if value_text.rstrip().endswith(UncertaintyCalculationTab.UNIT_PLACEHOLDER):
            return value_text

        display_unit = unit if unit else UncertaintyCalculationTab.UNIT_PLACEHOLDER
        return f"{value_text} {display_unit}"

    def _set_display_only_item(self, row, column, value_text, unit):
        """表示専用セルを設定する共通関数（単位付与を一元化）"""
        display_text = "--" if value_text in [None, ""] else str(value_text)
        display_text = self._format_with_unit(display_text, unit)
        item = QTableWidgetItem(display_text)
        item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
        self.calibration_table.setItem(row, column, item)

    def _clear_calculation_display(self):
        """Clear table/result labels to avoid showing stale values."""
        self.calibration_table.setRowCount(0)
        self.central_value_label.setText('--')
        self.standard_uncertainty_label.setText('--')
        self.effective_degrees_of_freedom_label.setText('--')
        self.coverage_factor_label.setText('--')
        self.expanded_uncertainty_label.setText('--')
        self.warning_label.clear()
        self.warning_label.hide()

    def _show_budget_error_message(self, issues):
        message = summarize_budget_issues(issues)
        if not message:
            self._last_budget_error_message = None
            self.warning_label.clear()
            self.warning_label.hide()
            return
        if message == self._last_budget_error_message:
            return
        self._last_budget_error_message = message
        self.warning_label.setText(message)
        self.warning_label.show()

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

                # Prefer the EditRole (raw value) to avoid including display units
                edit_value = item.data(Qt.EditRole)
                value_to_save = str(edit_value) if edit_value is not None else item.text()

                if item.column() == 1:  # Central value
                    value_handler.update_variable_value(var, 'central_value', value_to_save)
                elif item.column() == 2:  # Standard uncertainty
                    value_handler.update_variable_value(var, 'standard_uncertainty', value_to_save)
                elif item.column() == 3:  # Degrees of freedom
                    value_handler.update_variable_value(var, 'degrees_of_freedom', value_to_save)
                elif item.column() == 4:  # Distribution
                    value_handler.update_variable_value(var, 'distribution', get_distribution_translation_key(value_to_save))
                
                # Recalculate to update everything
                result_var = self.result_combo.currentText()
                if result_var:
                    equation = self.equation_handler.get_target_equation(result_var)
                    if equation:
                        self._updating_table = True
                        self.calculate_sensitivity_coefficients(equation)
                        self._updating_table = False
                        
            except Exception as e:
                log_error(f"テーブル値更新エラー: {str(e)}", details=traceback.format_exc())
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
        self.warning_label = QLabel("")
        self.warning_label.setWordWrap(True)
        self.warning_label.setStyleSheet("color: #c62828;")
        self.warning_label.hide()
        right_layout.addWidget(self.warning_label)
        right_layout.addWidget(self.result_display_group)
        
        # メインレイアウトに左右のレイアウトを追加
        main_layout.addLayout(left_layout, 1)  # 左側のレイアウト（幅の比率1）
        main_layout.addLayout(right_layout, 3)  # 右側のレイアウト（幅の比率3）
        
        self.setLayout(main_layout)
        
        # テーブルを表示専用に設定
        self.calibration_table.setEditTriggers(QAbstractItemView.NoEditTriggers)

        
    def update_result_combo(self):
        """計算結果の選択肢を更新"""
        try:
            self.result_combo.blockSignals(True)
            self.result_combo.clear()
            
            # 親ウィンドウから計算結果変数を取得
            if hasattr(self.parent, 'result_variables'):
                result_vars = self.parent.result_variables

                
                # 計算結果変数をmodel_equation_tab.pyの順序に合わせる
                for var in self.parent.variables:
                    if var in result_vars:
                        self.result_combo.addItem(var)
                if self.result_combo.count() == 0:
                    self._clear_calculation_display()
            else:
                self._clear_calculation_display()

            self.result_combo.blockSignals(False)
                
        except Exception as e:
            log_error(f"計算結果選択肢更新エラー: {str(e)}", details=traceback.format_exc())
        
    def update_value_combo(self):
        """校正点の選択肢を更新"""
        try:
            self.value_combo.blockSignals(True)
            self.value_combo.clear()
            
            value_names = getattr(self.parent, 'value_names', [])
            for name in value_names:
                self.value_combo.addItem(name)

            current_index = getattr(self.parent, 'current_value_index', 0)
            if isinstance(current_index, int) and 0 <= current_index < len(value_names):
                self.value_combo.setCurrentIndex(current_index)
            elif self.value_combo.count() > 0:
                self.value_combo.setCurrentIndex(0)
            self.value_combo.blockSignals(False)
                
        except Exception as e:
            log_error(f"校正点選択肢更新エラー: {str(e)}", details=traceback.format_exc())
            
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
            log_error(f"計算結果変更エラー: {str(e)}", details=traceback.format_exc())
            
    def on_value_changed(self, index):
        """校正点が変更されたときの処理"""
        if index < 0:
            return
            
        try:
            # ValueHandlerの現在の校正点インデックスを更新
            self.value_handler.current_value_index = index
            if self.parent:
                self.parent.current_value_index = index
            
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
            log_error(f"校正点変更エラー: {str(e)}", details=traceback.format_exc())
            

    
    def calculate_sensitivity_coefficients(self, equation):
        """感度係数を計算して表示"""
        # If we're already updating, skip to prevent recursion
        if self._updating_table:
            return

        try:
            # Set updating flag
            self._updating_table = True
            self._clear_calculation_display()

            # 式を解析
            left_side, right_side = equation.split('=', 1)
            left_side = left_side.strip()
            right_side = right_side.strip()
            result_var = left_side
            result_unit = self._get_unit(result_var)
            
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
            budget_issues = []
            point_name = self.value_combo.currentText() or f"index={self.value_handler.current_value_index}"
            zero_denominator_terms = detect_zero_denominator_terms(
                right_side, variables, self.value_handler
            )
            zero_denominator_hint = build_zero_denominator_hint(zero_denominator_terms)

            for i, var in enumerate(ordered_variables):

                unit = self._get_unit(var)
                var_info = self.parent.variable_values.get(var, {}) if self.parent else {}

                # 変数名
                self.calibration_table.setItem(i, 0, QTableWidgetItem(var))
                
                # 中央値
                central_value = self.value_handler.get_central_value(var)
                if (
                    central_value is None
                    or (isinstance(central_value, str) and central_value.strip() == "")
                ):
                    self._set_display_only_item(i, 1, "--", unit)
                    self._set_display_only_item(i, 2, "--", unit)  # 標準不確かさ
                    self.calibration_table.setItem(i, 3, QTableWidgetItem('--'))  # 自由度
                    self.calibration_table.setItem(i, 4, QTableWidgetItem('--'))  # 分布
                    self.calibration_table.setItem(i, 5, QTableWidgetItem('--'))  # 感度係数
                    self._set_display_only_item(i, 6, "--", result_unit)  # 寄与不確かさ
                    contributions.append(0)
                    degrees_of_freedom_list.append(0)
                    continue

                try:
                    central_value_float = float(central_value)
                except (TypeError, ValueError):
                    self._set_display_only_item(i, 1, "--", unit)
                    self._set_display_only_item(i, 2, "--", unit)  # 標準不確かさ
                    self.calibration_table.setItem(i, 3, QTableWidgetItem('--'))  # 自由度
                    self.calibration_table.setItem(i, 4, QTableWidgetItem('--'))  # 分布
                    self.calibration_table.setItem(i, 5, QTableWidgetItem('--'))  # 感度係数
                    self._set_display_only_item(i, 6, "--", result_unit)  # 寄与不確かさ
                    contributions.append(0)
                    degrees_of_freedom_list.append(0)
                    continue

                self._set_display_only_item(i, 1, str(central_value), unit)

                # 標準不確かさ
                standard_uncertainty = self.value_handler.get_standard_uncertainty(var)
                standard_uncertainty_display = format_standard_uncertainty(standard_uncertainty)
                self._set_display_only_item(i, 2, standard_uncertainty_display, unit)
                
                # 自由度
                degrees_of_freedom = self.value_handler.get_degrees_of_freedom(var)
                df_item = QTableWidgetItem(str(degrees_of_freedom))
                self.calibration_table.setItem(i, 3, df_item)
                degrees_of_freedom_list.append(degrees_of_freedom)
                
                # 分布
                distribution_key = get_distribution_translation_key(self.value_handler.get_distribution(var))
                distribution_label = self.tr(distribution_key) if distribution_key else '--'
                distribution_item = QTableWidgetItem(distribution_label)
                self.calibration_table.setItem(i, 4, distribution_item)
                
                # 感度係数
                sensitivity = self.equation_handler.calculate_sensitivity(right_side, var, variables, self.value_handler)
                sensitivity_float, sensitivity_issue = to_budget_float(
                    sensitivity,
                    field_name="Sensitivity",
                    variable_name=var,
                    point_name=point_name,
                )
                if sensitivity_issue:
                    if zero_denominator_hint and (
                        "0除算" in sensitivity_issue.reason
                        or "無限大" in sensitivity_issue.reason
                        or "複素無限大" in sensitivity_issue.reason
                    ):
                        sensitivity_issue.hint = zero_denominator_hint
                    budget_issues.append(sensitivity_issue)
                    self.calibration_table.setItem(i, 5, QTableWidgetItem('--'))
                    self._set_display_only_item(i, 6, "--", result_unit)
                    contributions.append(0)
                    continue
                self.calibration_table.setItem(i, 5, QTableWidgetItem(format_number_str(sensitivity_float)))
                
                # 寄与不確かさ
                try:
                    if standard_uncertainty and sensitivity_float:
                        contribution = float(standard_uncertainty) * sensitivity_float
                        contribution_display = format_standard_uncertainty(contribution)
                        self._set_display_only_item(i, 6, contribution_display, result_unit)
                        contributions.append(contribution)
                    else:
                        self._set_display_only_item(i, 6, "--", result_unit)
                        contributions.append(0)
                except (ValueError, TypeError) as e:
                    self._set_display_only_item(i, 6, "--", result_unit)
                    contributions.append(0)
            
            # 合成標準不確かさの計算
            result_standard_uncertainty = self.uncertainty_calculator.calculate_combined_uncertainty_with_correlation(
                contributions,
                ordered_variables,
                getattr(self.parent, "correlation_coefficients", {}),
            )
            
            # 寄与率の計算と表示
            contribution_rates = self.uncertainty_calculator.calculate_contribution_rates(contributions)
            for i, rate in enumerate(contribution_rates):
                self.calibration_table.setItem(i, 7, QTableWidgetItem(format_contribution_rate(rate)))
            
            # 計算結果を表示
            try:
                # 中央値の計算
                result_central_value = self.equation_handler.calculate_result_central_value(
                    right_side, variables, self.value_handler
                )
                result_central_value, result_issue = to_budget_float(
                    result_central_value,
                    field_name="Result central value",
                    variable_name=result_var,
                    point_name=point_name,
                )
                if result_issue:
                    if zero_denominator_hint and (
                        "0除算" in result_issue.reason
                        or "無限大" in result_issue.reason
                        or "複素無限大" in result_issue.reason
                    ):
                        result_issue.hint = zero_denominator_hint
                    budget_issues.append(result_issue)
                    self._clear_calculation_display()
                    self._show_budget_error_message(budget_issues)
                    return

                result_unit = self._get_unit(result_var)

                # 合成標準不確かさの表示
                standard_uncertainty_display = format_standard_uncertainty(result_standard_uncertainty)
                self.standard_uncertainty_label.setText(self._format_with_unit(standard_uncertainty_display, result_unit))
                
                # 有効自由度の計算
                effective_df = self.uncertainty_calculator.calculate_effective_degrees_of_freedom(
                    result_standard_uncertainty, contributions, degrees_of_freedom_list
                )
                self.effective_degrees_of_freedom_label.setText(format_number_str(float(effective_df)))
                
                # 包含係数の計算
                coverage_factor = self.uncertainty_calculator.get_coverage_factor(effective_df)
                self.coverage_factor_label.setText(format_coverage_factor(float(coverage_factor)))
                
                # 拡張不確かさの計算
                expanded_uncertainty = coverage_factor * result_standard_uncertainty
                expanded_uncertainty_display = format_expanded_uncertainty(expanded_uncertainty)
                self.expanded_uncertainty_label.setText(self._format_with_unit(expanded_uncertainty_display, result_unit))

                # 拡張不確かさの桁に合わせて中央値を更新
                central_value_display = format_central_value_with_uncertainty(result_central_value, expanded_uncertainty)
                self.central_value_label.setText(self._format_with_unit(central_value_display, result_unit))

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
                        'distribution': (
                            get_distribution_translation_key(self.value_handler.get_distribution(var))
                            or ''
                        ),
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

                self._show_budget_error_message(budget_issues)
            except Exception as e:
                log_error(f"計算結果表示エラー: {str(e)}", details=traceback.format_exc())
                
        except Exception as e:
            log_error(f"感度係数計算エラー: {str(e)}", details=traceback.format_exc())
            self._clear_calculation_display()
        finally:
            # Always reset the updating flag
            self._updating_table = False
