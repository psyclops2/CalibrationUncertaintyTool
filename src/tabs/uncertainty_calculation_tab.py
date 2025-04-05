from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                           QComboBox, QTableWidget, QTableWidgetItem, QGroupBox,
                           QHeaderView, QMessageBox)
from PyQt5.QtCore import Qt
import traceback

from src.utils.equation_handler import EquationHandler
from src.utils.value_handler import ValueHandler
from src.utils.uncertainty_calculator import UncertaintyCalculator
from src.utils.number_formatter import format_number_str

class UncertaintyCalculationTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        print("【デバッグ】UncertaintyCalculationTab初期化")
        if self.parent:
            print(f"【デバッグ】親ウィンドウの属性: {dir(self.parent)}")
            print(f"【デバッグ】model_equation_tab: {hasattr(self.parent, 'model_equation_tab')}")
            print(f"【デバッグ】variables_tab: {hasattr(self.parent, 'variables_tab')}")
        
        # ユーティリティクラスの初期化
        self.equation_handler = EquationHandler(parent)
        self.value_handler = ValueHandler(parent)
        self.uncertainty_calculator = UncertaintyCalculator(parent)
        
        self.setup_ui()
        # 初期表示時にプルダウンを更新
        self.update_result_combo()
        self.update_value_combo()
        
    def setup_ui(self):
        """UIの設定"""
        print("【デバッグ】setup_ui開始")
        main_layout = QHBoxLayout()
        
        # 左側のレイアウト（1/4）
        left_layout = QVBoxLayout()
        
        # 計算結果選択
        result_group = QGroupBox("計算結果の選択")
        result_group.setMaximumHeight(200)
        result_layout = QVBoxLayout()
                
        self.result_combo = QComboBox()
        self.result_combo.currentTextChanged.connect(self.on_result_changed)
        result_layout.addWidget(QLabel("計算結果:"))
        result_layout.addWidget(self.result_combo)
        
        # 値の選択
        self.value_combo = QComboBox()
        self.value_combo.currentIndexChanged.connect(self.on_value_changed)
        result_layout.addWidget(QLabel("校正点:"))
        result_layout.addWidget(self.value_combo)
        
        result_group.setLayout(result_layout)
        left_layout.addWidget(result_group)
        
        left_layout.addStretch(1)
        
        # 右側のレイアウト（3/4）
        right_layout = QVBoxLayout()
        
        # 校正値表示
        calibration_group = QGroupBox("校正値")
        calibration_layout = QVBoxLayout()
        
        self.calibration_table = QTableWidget()
        self.calibration_table.setColumnCount(8)
        headers = [
            "量", "中央値", "標準不確かさ", "自由度", "分布", "感度係数", "寄与不確かさ", "寄与率"
        ]
        self.calibration_table.setHorizontalHeaderLabels(headers)
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
        
        calibration_group.setLayout(calibration_layout)
        right_layout.addWidget(calibration_group)
        
        # 計算結果表示
        result_display_group = QGroupBox("計算結果")
        result_display_layout = QVBoxLayout()
        
        # 中央値表示
        central_value_layout = QHBoxLayout()
        central_value_layout.addWidget(QLabel("中央値:"))
        self.central_value_label = QLabel("")
        central_value_layout.addWidget(self.central_value_label)
        result_display_layout.addLayout(central_value_layout)
        
        # 合成標準不確かさ表示
        standard_uncertainty_layout = QHBoxLayout()
        standard_uncertainty_layout.addWidget(QLabel("合成標準不確かさ:"))
        self.standard_uncertainty_label = QLabel("")
        standard_uncertainty_layout.addWidget(self.standard_uncertainty_label)
        result_display_layout.addLayout(standard_uncertainty_layout)
        
        # 有効自由度表示
        effective_degrees_of_freedom_layout = QHBoxLayout()
        effective_degrees_of_freedom_layout.addWidget(QLabel("有効自由度:"))
        self.effective_degrees_of_freedom_label = QLabel("")
        effective_degrees_of_freedom_layout.addWidget(self.effective_degrees_of_freedom_label)
        result_display_layout.addLayout(effective_degrees_of_freedom_layout)
        
        # 包含係数表示
        coverage_factor_layout = QHBoxLayout()
        coverage_factor_layout.addWidget(QLabel("包含係数:"))
        self.coverage_factor_label = QLabel("")
        coverage_factor_layout.addWidget(self.coverage_factor_label)
        result_display_layout.addLayout(coverage_factor_layout)
        
        # 拡張不確かさ表示
        expanded_uncertainty_layout = QHBoxLayout()
        expanded_uncertainty_layout.addWidget(QLabel("拡張不確かさ:"))
        self.expanded_uncertainty_label = QLabel("")
        expanded_uncertainty_layout.addWidget(self.expanded_uncertainty_label)
        result_display_layout.addLayout(expanded_uncertainty_layout)
        
        result_display_group.setLayout(result_display_layout)
        right_layout.addWidget(result_display_group)
        
        # メインレイアウトに左右のレイアウトを追加
        main_layout.addLayout(left_layout, 1)  # 左側のレイアウト（幅の比率1）
        main_layout.addLayout(right_layout, 3)  # 右側のレイアウト（幅の比率3）
        
        self.setLayout(main_layout)
        print("【デバッグ】setup_ui完了")
        
    def update_result_combo(self):
        """計算結果の選択肢を更新"""
        try:
            print("【デバッグ】update_result_combo開始")
            self.result_combo.clear()
            
            # 親ウィンドウから計算結果変数を取得
            if hasattr(self.parent, 'result_variables'):
                result_vars = self.parent.result_variables
                print(f"【デバッグ】計算結果変数: {result_vars}")
                
                # 計算結果変数をmodel_equation_tab.pyの順序に合わせる
                for var in self.parent.variables:
                    if var in result_vars:
                        self.result_combo.addItem(var)
            else:
                print("【デバッグ】親ウィンドウにresult_variables属性なし")
                
        except Exception as e:
            print(f"【エラー】計算結果選択肢更新エラー: {str(e)}")
            print(traceback.format_exc())
        
    def update_value_combo(self):
        """校正点の選択肢を更新"""
        try:
            print("【デバッグ】update_value_combo開始")
            self.value_combo.clear()
            
            # 親ウィンドウから校正点の数を取得
            if hasattr(self.parent, 'value_count'):
                value_count = self.parent.value_count
                print(f"【デバッグ】校正点の数: {value_count}")
                for i in range(value_count):
                    self.value_combo.addItem(f"校正点 {i+1}")
            else:
                print("【デバッグ】親ウィンドウにvalue_count属性なし")
                
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
        try:
            print(f"【デバッグ】感度係数計算開始: {equation}")
            # 式を解析
            left_side, right_side = equation.split('=', 1)
            left_side = left_side.strip()
            right_side = right_side.strip()
            
            # 変数を抽出
            variables = self.equation_handler.get_variables_from_equation(right_side)
            print(f"【デバッグ】抽出された変数: {variables}")
            
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
                print(f"【デバッグ】変数処理開始: {var}")
                # 変数名
                self.calibration_table.setItem(i, 0, QTableWidgetItem(var))
                
                # 中央値
                central_value = self.value_handler.get_central_value(var)
                print(f"【デバッグ】中央値: {central_value}")
                self.calibration_table.setItem(i, 1, QTableWidgetItem(str(central_value)))
                
                # 標準不確かさ
                standard_uncertainty = self.value_handler.get_standard_uncertainty(var)
                print(f"【デバッグ】標準不確かさ: {standard_uncertainty}")
                self.calibration_table.setItem(i, 2, QTableWidgetItem(format_number_str(standard_uncertainty)))
                
                # 自由度
                degrees_of_freedom = self.value_handler.get_degrees_of_freedom(var)
                print(f"【デバッグ】自由度: {degrees_of_freedom}")
                self.calibration_table.setItem(i, 3, QTableWidgetItem(str(degrees_of_freedom)))
                degrees_of_freedom_list.append(degrees_of_freedom)
                
                # 分布
                distribution = self.value_handler.get_distribution(var)
                print(f"【デバッグ】分布: {distribution}")
                self.calibration_table.setItem(i, 4, QTableWidgetItem(distribution))
                
                # 感度係数
                sensitivity = self.equation_handler.calculate_sensitivity(right_side, var, variables, self.value_handler)
                print(f"【デバッグ】感度係数: {sensitivity}")
                self.calibration_table.setItem(i, 5, QTableWidgetItem(format_number_str(sensitivity)))
                
                # 寄与不確かさ
                try:
                    if standard_uncertainty and sensitivity:
                        contribution = float(standard_uncertainty) * float(sensitivity)
                        print(f"【デバッグ】寄与不確かさ: {contribution}")
                        self.calibration_table.setItem(i, 6, QTableWidgetItem(format_number_str(contribution)))
                        contributions.append(contribution)
                    else:
                        print(f"【デバッグ】寄与不確かさ計算スキップ: standard_uncertainty={standard_uncertainty}, sensitivity={sensitivity}")
                        self.calibration_table.setItem(i, 6, QTableWidgetItem(""))
                        contributions.append(0)
                except (ValueError, TypeError) as e:
                    print(f"【デバッグ】寄与不確かさ計算エラー: {str(e)}")
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
                self.central_value_label.setText(str(result_central_value))
                
                # 合成標準不確かさの表示
                self.standard_uncertainty_label.setText(format_number_str(result_standard_uncertainty))
                
                # 有効自由度の計算
                effective_df = self.uncertainty_calculator.calculate_effective_degrees_of_freedom(
                    result_standard_uncertainty, contributions, degrees_of_freedom_list
                )
                self.effective_degrees_of_freedom_label.setText(f"{effective_df:.2f}")
                
                # 包含係数の計算
                coverage_factor = self.uncertainty_calculator.get_coverage_factor(effective_df)
                self.coverage_factor_label.setText(f"{coverage_factor:.3f}")
                
                # 拡張不確かさの計算
                expanded_uncertainty = coverage_factor * result_standard_uncertainty
                self.expanded_uncertainty_label.setText(format_number_str(expanded_uncertainty))
                
            except Exception as e:
                print(f"【エラー】計算結果表示エラー: {str(e)}")
                print(traceback.format_exc())
                
        except Exception as e:
            print(f"【エラー】感度係数計算エラー: {str(e)}")
            print(traceback.format_exc()) 