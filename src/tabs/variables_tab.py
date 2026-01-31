from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QComboBox, QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
    QGroupBox, QFormLayout, QSpinBox, QDoubleSpinBox, QCheckBox, QRadioButton,
    QButtonGroup, QSplitter, QFrame, QScrollArea, QGridLayout, QSizePolicy,
    QListWidget, QListWidgetItem, QTextEdit
)
from PySide6.QtCore import Qt, Signal, Slot
from ..utils.config_loader import ConfigLoader
import traceback
from ..utils.variable_utils import (
    calculate_type_a_uncertainty,
    calculate_type_b_uncertainty,
    get_distribution_divisor,
    get_distribution_translation_key,
    create_empty_value_dict,
    find_variable_item
)
from ..utils.calculation_utils import evaluate_formula
from .variables_tab_handlers import VariablesTabHandlers
from .base_tab import BaseTab
from ..utils.translation_keys import *

class VariablesTab(BaseTab):
    """量管理/量の値管理タブ"""
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.handlers = VariablesTabHandlers(self)
        self.setup_ui()

    def retranslate_ui(self):
        """UIのテキストを現在の言語で更新"""
        # グループボックスのタイトル
        self.value_select_group.setTitle(self.tr(CALIBRATION_POINT_SELECTION))
        self.variable_list_group.setTitle(self.tr(VARIABLE_LIST_AND_VALUES))
        self.settings_group.setTitle(self.tr(VARIABLE_DETAIL_SETTINGS))
        
        # ラベル
        self.var_label.setText(self.tr(VARIABLE_MODE) + ":")
        if self.mode_display.text() == self.tr(NOT_SELECTED, "未選択"):
            self.mode_display.setText(self.tr(NOT_SELECTED))
            
        self.nominal_value_label.setText(self.tr(LABEL_NOMINAL_VALUE) + ":")
        self.unit_label.setText(self.tr(LABEL_UNIT) + ":")
        self.definition_label.setText(self.tr(LABEL_DEFINITION) + ":")
        self.uncertainty_type_label.setText(self.tr(UNCERTAINTY_TYPE) + ":")
        self.value_source_label.setText(self.tr(VALUE_SOURCE) + ":")
        # value_source_comboの項目は既に設定済み
        
        # ラジオボタン
        self.type_a_radio.setText(self.tr(TYPE_A))
        self.type_b_radio.setText(self.tr(TYPE_B))
        self.type_fixed_radio.setText(self.tr(FIXED_VALUE))
        
        # TypeA用ウィジェット
        self.type_a_widgets['measurements'].setPlaceholderText(self.tr(MEASUREMENT_VALUES_PLACEHOLDER))
        self.measurement_values_label.setText(self.tr(MEASUREMENT_VALUES) + ":")
        self.degrees_of_freedom_label_a.setText(self.tr(DEGREES_OF_FREEDOM) + ":")
        self.central_value_label_a.setText(self.tr(CENTRAL_VALUE) + ":")
        self.standard_uncertainty_label_a.setText(self.tr(STANDARD_UNCERTAINTY) + ":")
        self.detail_description_label_a.setText(self.tr(DETAIL_DESCRIPTION) + ":")

        # 回帰モデル用ウィジェット
        
        # TypeB用ウィジェット
        # 分布コンボボックスの項目を更新
        current_distribution = self.type_b_widgets['distribution'].currentData()
        self.type_b_widgets['distribution'].clear()
        for code, label in self.get_distribution_options():
            self.type_b_widgets['distribution'].addItem(label, code)
        if current_distribution:
            index = self.type_b_widgets['distribution'].findData(current_distribution)
            if index >= 0:
                self.type_b_widgets['distribution'].setCurrentIndex(index)
        if self.type_b_widgets['distribution'].currentIndex() < 0:
            self.type_b_widgets['distribution'].setCurrentIndex(0)
        
        self.distribution_label.setText(self.tr(DISTRIBUTION) + ":")
        self.divisor_label.setText(self.tr(DIVISOR) + ":")
        self.degrees_of_freedom_label_b.setText(self.tr(DEGREES_OF_FREEDOM) + ":")
        self.central_value_label_b.setText(self.tr(CENTRAL_VALUE) + ":")
        self.half_width_label.setText(self.tr(HALF_WIDTH) + ":")
        self.type_b_widgets['calculation_formula'].setPlaceholderText(self.tr(CALCULATION_FORMULA))
        self.type_b_widgets['calculate_button'].setText(self.tr(CALCULATE))
        self.standard_uncertainty_label_b.setText(self.tr(STANDARD_UNCERTAINTY) + ":")
        self.detail_description_label_b.setText(self.tr(DETAIL_DESCRIPTION) + ":")
        
        # 固定値用ウィジェット
        self.central_value_label_fixed.setText(self.tr(CENTRAL_VALUE) + ":")
        self.detail_description_label_fixed.setText(self.tr(DETAIL_DESCRIPTION) + ":")
        
        # 変数リストを更新
        self.update_variable_list(self.parent.variables, self.parent.result_variables)

    def setup_ui(self):
        main_layout = QHBoxLayout()  # メインレイアウトを水平方向に変更
        
        # 左側のレイアウト（値の設定関連と量一覧）
        left_layout = QVBoxLayout()
        
        # 1. 値の選択（校正点設定タブで管理された校正点から選択）
        self.value_select_group = QGroupBox(self.tr(CALIBRATION_POINT_SELECTION))
        value_select_layout = QVBoxLayout()
        self.value_combo = QComboBox()
        self.value_combo.currentIndexChanged.connect(self.handlers.on_value_selected)
        value_select_layout.addWidget(self.value_combo)
        self.value_select_group.setLayout(value_select_layout)
        left_layout.addWidget(self.value_select_group)
        
        # 2. 量一覧
        self.variable_list_group = QGroupBox(self.tr(VARIABLE_LIST_AND_VALUES))
        var_list_layout = QVBoxLayout()
        variable_info_layout = QHBoxLayout()
        self.var_label = QLabel(self.tr(VARIABLE_MODE) + ":")
        self.mode_display = QLabel(self.tr(NOT_SELECTED))
        variable_info_layout.addWidget(self.var_label)
        variable_info_layout.addWidget(self.mode_display)
        var_list_layout.addLayout(variable_info_layout)
        self.variable_list = QListWidget()
        self.variable_list.currentItemChanged.connect(self.handlers.on_variable_selected)
        var_list_layout.addWidget(self.variable_list)
        self.variable_list_group.setLayout(var_list_layout)
        left_layout.addWidget(self.variable_list_group)
        
        left_layout.addStretch()  # 下部に余白を追加
        
        # 右側のレイアウト（量詳細設定のみ）
        right_layout = QVBoxLayout()
        
        # 4. 量詳細設定
        self.settings_group = QGroupBox(self.tr(VARIABLE_DETAIL_SETTINGS))
        settings_layout = QFormLayout()
        
        # 呼び値フィールドの追加
        self.nominal_value_input = QLineEdit()
        self.nominal_value_input.textChanged.connect(self.handlers.on_nominal_value_changed)
        self.nominal_value_label = QLabel(self.tr(LABEL_NOMINAL_VALUE) + ":")
        settings_layout.addRow(self.nominal_value_label, self.nominal_value_input)
        
        # 単位
        self.unit_input = QLineEdit()
        self.unit_input.textChanged.connect(self.handlers.on_unit_changed)
        self.unit_label = QLabel(self.tr(LABEL_UNIT) + ":")
        settings_layout.addRow(self.unit_label, self.unit_input)
        
        # 定義フィールドを追加
        self.definition_input = QTextEdit()
        self.definition_input.setMaximumHeight(100)
        self.definition_input.textChanged.connect(self.handlers.on_definition_changed)
        self.definition_label = QLabel(self.tr(DEFINITION) + ":")
        settings_layout.addRow(self.definition_label, self.definition_input)
        
        # 2段落目：不確かさ種類
        uncertainty_type_layout = QHBoxLayout()
        self.type_a_radio = QRadioButton(self.tr(TYPE_A))
        self.type_b_radio = QRadioButton(self.tr(TYPE_B))
        self.type_fixed_radio = QRadioButton(self.tr(FIXED_VALUE))
        self.type_a_radio.toggled.connect(self.handlers.on_type_changed)
        self.type_b_radio.toggled.connect(self.handlers.on_type_changed)
        self.type_fixed_radio.toggled.connect(self.handlers.on_type_changed)
        uncertainty_type_layout.addWidget(self.type_a_radio)
        uncertainty_type_layout.addWidget(self.type_b_radio)
        uncertainty_type_layout.addWidget(self.type_fixed_radio)
        self.uncertainty_type_label = QLabel(self.tr(UNCERTAINTY_TYPE) + ":")
        settings_layout.addRow(self.uncertainty_type_label, uncertainty_type_layout)

        # 値のソース選択（校正点ごと）
        self.value_source_label = QLabel(self.tr(VALUE_SOURCE) + ":")
        self.value_source_combo = QComboBox()
        self.value_source_combo.addItem(self.tr(SOURCE_MANUAL), 'manual')
        self.value_source_combo.currentIndexChanged.connect(self.handlers.on_value_source_changed)
        settings_layout.addRow(self.value_source_label, self.value_source_combo)
        
        # 区切り線を追加
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setLineWidth(2)
        separator.setStyleSheet("QFrame { background-color: red; }") 
        settings_layout.addRow("", separator)
        
        # TypeA用のウィジェット
        self.type_a_widgets = {}
        
        self.type_a_widgets['measurements'] = QLineEdit()
        self.type_a_widgets['measurements'].setPlaceholderText(self.tr(MEASUREMENT_VALUES_PLACEHOLDER))
        self.type_a_widgets['measurements'].focusOutEvent = lambda e: self.handlers.on_measurements_focus_lost(e)
        self.type_a_widgets['measurements'].textChanged.connect(self.handlers.on_measurements_changed)
        self.measurement_values_label = QLabel(self.tr(MEASUREMENT_VALUES) + ":")
        settings_layout.addRow(self.measurement_values_label, self.type_a_widgets['measurements'])
        
        self.type_a_widgets['degrees_of_freedom'] = QLineEdit()
        self.type_a_widgets['degrees_of_freedom'].setReadOnly(True)
        self.type_a_widgets['degrees_of_freedom'].textChanged.connect(self.handlers.on_type_a_degrees_of_freedom_changed)
        self.degrees_of_freedom_label_a = QLabel(self.tr(DEGREES_OF_FREEDOM) + ":")
        settings_layout.addRow(self.degrees_of_freedom_label_a, self.type_a_widgets['degrees_of_freedom'])
        
        self.type_a_widgets['central_value'] = QLineEdit()
        self.type_a_widgets['central_value'].setReadOnly(True)
        self.type_a_widgets['central_value'].textChanged.connect(self.handlers.on_type_a_central_value_changed)
        self.central_value_label_a = QLabel(self.tr(CENTRAL_VALUE) + ":")
        settings_layout.addRow(self.central_value_label_a, self.type_a_widgets['central_value'])
        
        self.type_a_widgets['standard_uncertainty'] = QLineEdit()
        self.type_a_widgets['standard_uncertainty'].setReadOnly(True)
        self.type_a_widgets['standard_uncertainty'].textChanged.connect(self.handlers.on_type_a_standard_uncertainty_changed)
        self.standard_uncertainty_label_a = QLabel(self.tr(STANDARD_UNCERTAINTY) + ":")
        settings_layout.addRow(self.standard_uncertainty_label_a, self.type_a_widgets['standard_uncertainty'])
        
        # 詳細説明フィールドを追加
        self.type_a_widgets['description'] = QTextEdit()
        self.type_a_widgets['description'].setMaximumHeight(100)
        self.type_a_widgets['description'].textChanged.connect(self.handlers.on_type_a_description_changed)
        self.detail_description_label_a = QLabel(self.tr(DETAIL_DESCRIPTION) + ":")
        settings_layout.addRow(self.detail_description_label_a, self.type_a_widgets['description'])

        self.regression_widgets = {}

        # 回帰モデル用のウィジェット

        # xの取り方
        # 将来拡張用: self.regression_widgets['x_mode'].addItem(self.tr(REGRESSION_X_MODE_VARIABLE), 'variable')

        
        # TypeB用のウィジェット
        self.type_b_widgets = {}
        
        self.type_b_widgets['distribution'] = QComboBox()
        for code, label in self.get_distribution_options():
            self.type_b_widgets['distribution'].addItem(label, code)
        self.type_b_widgets['distribution'].currentIndexChanged.connect(self.handlers.on_distribution_changed)
        self.distribution_label = QLabel(self.tr(DISTRIBUTION) + ":")
        settings_layout.addRow(self.distribution_label, self.type_b_widgets['distribution'])
        
        self.type_b_widgets['divisor'] = QLineEdit()
        self.type_b_widgets['divisor'].textChanged.connect(self.handlers.on_divisor_changed)
        self.divisor_label = QLabel(self.tr(DIVISOR) + ":")
        settings_layout.addRow(self.divisor_label, self.type_b_widgets['divisor'])
        
        self.type_b_widgets['degrees_of_freedom'] = QLineEdit()
        self.type_b_widgets['degrees_of_freedom'].textChanged.connect(self.handlers.on_type_b_degrees_of_freedom_changed)
        self.degrees_of_freedom_label_b = QLabel(self.tr(DEGREES_OF_FREEDOM) + ":")
        settings_layout.addRow(self.degrees_of_freedom_label_b, self.type_b_widgets['degrees_of_freedom'])
        
        self.type_b_widgets['central_value'] = QLineEdit()
        self.type_b_widgets['central_value'].textChanged.connect(self.handlers.on_type_b_central_value_changed)
        self.central_value_label_b = QLabel(self.tr(CENTRAL_VALUE) + ":")
        settings_layout.addRow(self.central_value_label_b, self.type_b_widgets['central_value'])
        
        # 半値幅の入力欄とその他のウィジェットを含むレイアウト
        half_width_layout = QHBoxLayout()
        self.type_b_widgets['half_width'] = QLineEdit()
        self.type_b_widgets['half_width'].focusOutEvent = lambda e: self.handlers.on_half_width_focus_lost(e)
        self.type_b_widgets['half_width'].textChanged.connect(self.handlers.on_type_b_half_width_changed)
        half_width_layout.addWidget(self.type_b_widgets['half_width'])
        
        # 計算式の入力欄
        self.type_b_widgets['calculation_formula'] = QLineEdit()
        self.type_b_widgets['calculation_formula'].setPlaceholderText(self.tr(CALCULATION_FORMULA))
        self.type_b_widgets['calculation_formula'].textChanged.connect(self.handlers.on_calculation_formula_changed)
        half_width_layout.addWidget(self.type_b_widgets['calculation_formula'])
        
        # 計算ボタン
        self.type_b_widgets['calculate_button'] = QPushButton(self.tr(CALCULATE))
        self.type_b_widgets['calculate_button'].clicked.connect(self.handlers.on_calculate_button_clicked)
        half_width_layout.addWidget(self.type_b_widgets['calculate_button'])
        
        half_width_layout.addStretch()
        self.half_width_label = QLabel(self.tr(HALF_WIDTH) + ":")
        settings_layout.addRow(self.half_width_label, half_width_layout)
        
        self.type_b_widgets['standard_uncertainty'] = QLineEdit()
        self.type_b_widgets['standard_uncertainty'].setReadOnly(True)
        self.type_b_widgets['standard_uncertainty'].textChanged.connect(self.handlers.on_type_b_standard_uncertainty_changed)
        self.standard_uncertainty_label_b = QLabel(self.tr(STANDARD_UNCERTAINTY) + ":")
        settings_layout.addRow(self.standard_uncertainty_label_b, self.type_b_widgets['standard_uncertainty'])
        
        # 詳細説明フィールドを追加
        self.type_b_widgets['description'] = QTextEdit()
        self.type_b_widgets['description'].setMaximumHeight(100)
        self.type_b_widgets['description'].textChanged.connect(self.handlers.on_type_b_description_changed)
        self.detail_description_label_b = QLabel(self.tr(DETAIL_DESCRIPTION) + ":")
        settings_layout.addRow(self.detail_description_label_b, self.type_b_widgets['description'])
        
        # 固定値用のウィジェット
        self.fixed_value_widgets = {}
        
        self.fixed_value_widgets['central_value'] = QLineEdit()
        self.fixed_value_widgets['central_value'].textChanged.connect(self.handlers.on_fixed_value_central_value_changed)
        self.central_value_label_fixed = QLabel(self.tr(CENTRAL_VALUE) + ":")
        settings_layout.addRow(self.central_value_label_fixed, self.fixed_value_widgets['central_value'])
        
        # 詳細説明フィールドを追加
        self.fixed_value_widgets['description'] = QTextEdit()
        self.fixed_value_widgets['description'].setMaximumHeight(100)
        self.fixed_value_widgets['description'].textChanged.connect(self.handlers.on_fixed_value_description_changed)
        self.detail_description_label_fixed = QLabel(self.tr(DETAIL_DESCRIPTION) + ":")
        settings_layout.addRow(self.detail_description_label_fixed, self.fixed_value_widgets['description'])
        
        self.settings_group.setLayout(settings_layout)
        self.settings_group.setEnabled(False)
        right_layout.addWidget(self.settings_group)
        
        # 右側のレイアウトを上詰めにする
        right_layout.addStretch()
        
        # メインレイアウトに左右のレイアウトを追加
        main_layout.addLayout(left_layout, 1)  # 左側のレイアウト（幅の比率1）
        main_layout.addLayout(right_layout, 3)  # 右側のレイアウト（幅の比率3）
        
        self.setLayout(main_layout)
        
        # 初期状態ではTypeAを選択し、ウィジェットの表示/非表示を設定
        self.type_a_radio.setChecked(True)
        # 初期状態のウィジェット表示/非表示を設定（クリア処理なし）
        is_result = False  # 初期状態では入力量として扱う
        editable = True
        for widget in self.type_a_widgets.values():
            widget.setVisible(True)
            widget.setEnabled(editable)
        for widget in self.type_b_widgets.values():
            widget.setVisible(False)
            widget.setEnabled(False)
        for widget in self.fixed_value_widgets.values():
            widget.setVisible(False)
            widget.setEnabled(False)
        
    def update_variable_list(self, variables, result_variables):
        """変数リストを更新"""
        try:
            self.variable_list.clear()
            
            # 量を計算結果量と入力量に分類
            input_vars = [var for var in variables if var not in result_variables]
            result_vars = [var for var in variables if var in result_variables]
            
            # 計算結果量を先に、入力量を後に表示
            for var in result_vars:
                item = QListWidgetItem(f"{var} [計算結果]")
                item.setData(Qt.UserRole, var)
                self.variable_list.addItem(item)
            
            for var in input_vars:
                item = QListWidgetItem(f"{var} [入力]")
                item.setData(Qt.UserRole, var)
                self.variable_list.addItem(item)
            
            # 前回選択していた変数が存在する場合は、それを選択状態に戻す
            if self.handlers.last_selected_variable:
                for i in range(self.variable_list.count()):
                    item = self.variable_list.item(i)
                    if item.data(Qt.UserRole) == self.handlers.last_selected_variable:
                        self.variable_list.setCurrentItem(item)
                        break
            

            
        except Exception as e:
            print(f"【エラー】変数リスト更新エラー: {str(e)}")
            print(traceback.format_exc())
            QMessageBox.warning(self, "エラー", "変数リストの更新に失敗しました。")
            
    def display_common_settings(self):
        """共通の設定（単位、不確かさ種類、分布、除数）を表示"""
        try:
            if not self.handlers.current_variable:
                return

            var_info = self.parent.variable_values[self.handlers.current_variable]
            
            # 呼び値の設定
            nominal_value = var_info.get('nominal_value', '')
            self.nominal_value_input.setText(nominal_value)
            
            # 単位の設定
            unit = var_info.get('unit', '')
            self.unit_input.setText(unit)
            
            # 定義の設定
            definition = var_info.get('definition', '')
            self.definition_input.setText(definition)

            # 不確かさ種類の設定
            uncertainty_type = var_info.get('type', 'A')
            if uncertainty_type not in ('A', 'B', 'fixed'):
                uncertainty_type = 'A'
                var_info['type'] = 'A'
            if getattr(self.handlers, 'current_variable_is_result', False):
                uncertainty_type = 'result'
            
            # 現在の校正点の値のソースを取得
            values = var_info.get('values', [])
            value_index = self.value_combo.currentIndex()
            if 0 <= value_index < len(values):
                value_info = values[value_index]
                source = value_info.get('source', 'manual')
                self.value_source_combo.blockSignals(True)
                index = self.value_source_combo.findData(source)
                if index >= 0:
                    self.value_source_combo.setCurrentIndex(index)
                else:
                    self.value_source_combo.setCurrentIndex(0)
                self.value_source_combo.blockSignals(False)
            else:
                self.value_source_combo.blockSignals(True)
                self.value_source_combo.setCurrentIndex(0)
                self.value_source_combo.blockSignals(False)

            if uncertainty_type == 'A':
                self.type_a_radio.setChecked(True)
            elif uncertainty_type == 'B':
                self.type_b_radio.setChecked(True)
            elif uncertainty_type == 'fixed':
                self.type_fixed_radio.setChecked(True)

            # TypeBの場合、分布と除数の設定
            if uncertainty_type == 'B':
                distribution = get_distribution_translation_key(
                    var_info.get('distribution', NORMAL_DISTRIBUTION)
                ) or NORMAL_DISTRIBUTION
                var_info['distribution'] = distribution
                self.type_b_widgets['distribution'].blockSignals(True)
                index = self.type_b_widgets['distribution'].findData(distribution)
                if index >= 0:
                    self.type_b_widgets['distribution'].setCurrentIndex(index)
                else:
                    self.type_b_widgets['distribution'].setCurrentIndex(0)
                self.type_b_widgets['distribution'].blockSignals(False)

                # 分布に応じた除数を設定（正規分布は保存済みの値を優先）
                values = var_info.get('values', []) if isinstance(var_info.get('values', []), list) else []
                value_index = self.value_combo.currentIndex()
                divisor = ''
                if 0 <= value_index < len(values):
                    divisor = values[value_index].get('divisor', '')
                if not divisor:
                    divisor = var_info.get('divisor', '')
                if not divisor:
                    divisor = get_distribution_divisor(distribution)

                self.type_b_widgets['divisor'].setText(divisor)
                self.type_b_widgets['divisor'].setReadOnly(distribution != NORMAL_DISTRIBUTION)


            # 不確かさ種類に応じたウィジェットの表示を更新
            self.handlers.update_widget_visibility(uncertainty_type)
                
        except Exception as e:
            print(f"【エラー】共通設定表示エラー: {str(e)}")
            print(traceback.format_exc())

    def display_current_value(self):
        """現在選択されている値の情報を表示"""
        if not hasattr(self, 'value_combo') or not hasattr(self, 'handlers') or not self.handlers.current_variable:
            return
            
        try:
            current_var = self.handlers.current_variable
            print(f"[DEBUG] display_current_value: 開始 - 変数={current_var}")
            
            # 変数の辞書が存在することを確認
            if current_var not in self.parent.variable_values:
                print(f"[DEBUG] display_current_value: 変数の辞書が存在しないため作成 - {current_var}")
                # 完全に新しい辞書を作成（前の変数の値の影響を受けないように）
                self.parent.variable_values[current_var] = {
                    'values': [create_empty_value_dict()],
                    'unit': '',
                    'type': 'A',
                    'definition': ''
                }
                
            var_info = self.parent.variable_values[current_var]
            
            # valuesが存在しない、またはリストでない場合は初期化
            if 'values' not in var_info or not isinstance(var_info['values'], list):
                print(f"[DEBUG] display_current_value: valuesリストが不正なため初期化")
                var_info['values'] = []
                
            values = var_info['values']

            # 値のリストが空の場合はデフォルト値を追加
            if not values:
                print(f"[DEBUG] display_current_value: 値のリストが空のため初期化")
                values.append(create_empty_value_dict())

            # 校正点の数に合わせて値のリストを拡張
            required_values = self.value_combo.count()
            if len(values) < required_values:
                print(f"[DEBUG] display_current_value: 値リストを校正点数に合わせて拡張 - 現在 {len(values)} -> 必要 {required_values}")
                for _ in range(required_values - len(values)):
                    values.append(create_empty_value_dict())

            # 現在のインデックスを取得（範囲外の場合は0にリセット）
            index = self.value_combo.currentIndex()
            if index < 0 or index >= len(values):
                print(f"[DEBUG] display_current_value: インデックスが範囲外のため0にリセット - index={index}, length={len(values)}")
                index = 0
                if self.value_combo.count() > 0:
                    self.value_combo.setCurrentIndex(0)
            
            # 現在の値を取得
            value_info = values[index]
            print(f"[DEBUG] display_current_value: 辞書から取得した値={value_info}")
            print(f"[DEBUG] display_current_value: 使用する値のインデックス={index}, 値の総数={len(values)}")
            
            # 計算結果変数は値入力をスキップし、単位などの共通設定のみ扱う
            if getattr(self.handlers, 'current_variable_is_result', False):
                self.handlers.update_widget_visibility('result')
                return

            # 値のソースを確認
            source = value_info.get('source', 'manual') or 'manual'
            if source != 'manual':
                source = 'manual'
                value_info['source'] = 'manual'
            
            # 不確かさ種類を取得（デフォルトはA）
            uncertainty_type = var_info.get('type', 'A')
            
            # 値のソースに応じてウィジェットの表示を更新
            self.handlers.update_widget_visibility(uncertainty_type)
            
            print(f"[DEBUG] display_current_value: 復元開始 - 変数={current_var}, source={source}, type={uncertainty_type}, value_index={index}")
            
            # 値をセット（ウィジェットの表示/非表示は既に設定済み）
            if source == 'regression':
                # 回帰式の場合の表示処理は既にupdate_widget_visibility_for_sourceで行われている
                pass
            elif uncertainty_type == 'A':
                # 辞書から値を取得（読み取り専用）
                measurements = value_info.get('measurements', '')
                degrees_of_freedom = value_info.get('degrees_of_freedom', 0)
                if degrees_of_freedom == '':
                    degrees_of_freedom = 0
                try:
                    degrees_of_freedom = int(float(degrees_of_freedom))
                except (ValueError, TypeError):
                    degrees_of_freedom = 0
                central_value = value_info.get('central_value', '')
                standard_uncertainty = value_info.get('standard_uncertainty', '')
                description = value_info.get('description', '')
                
                # ウィジェットに値を設定
                self.type_a_widgets['measurements'].setText(str(measurements))
                self.type_a_widgets['degrees_of_freedom'].setText(str(degrees_of_freedom))
                
                # 数値の表示精度を統一
                if isinstance(central_value, (int, float)) or (isinstance(central_value, str) and central_value.replace('.', '', 1).isdigit()):
                    central_value = f"{float(central_value):.15g}"
                self.type_a_widgets['central_value'].setText(str(central_value))
                
                if isinstance(standard_uncertainty, (int, float)) or (isinstance(standard_uncertainty, str) and standard_uncertainty.replace('.', '', 1).isdigit()):
                    standard_uncertainty = f"{float(standard_uncertainty):.15g}"
                self.type_a_widgets['standard_uncertainty'].setText(str(standard_uncertainty))
                
                self.type_a_widgets['description'].setText(str(description))
                
                print(f"[DEBUG] TypeA復元: measurements='{measurements}', degrees_of_freedom='{degrees_of_freedom}', central_value='{central_value}', description='{description}'")
                
            elif uncertainty_type == 'B':
                # 辞書から値を取得（読み取り専用）
                central_value = value_info.get('central_value', '')
                half_width = value_info.get('half_width', '')
                standard_uncertainty = value_info.get('standard_uncertainty', '')
                degrees_of_freedom = value_info.get('degrees_of_freedom', 0)
                description = value_info.get('description', '')
                calculation_formula = value_info.get('calculation_formula', '')
                divisor = value_info.get('divisor', '')
                if not divisor:
                    divisor = var_info.get('divisor', '')
                if not divisor:
                    distribution = get_distribution_translation_key(
                        var_info.get('distribution', NORMAL_DISTRIBUTION)
                    ) or NORMAL_DISTRIBUTION
                    var_info['distribution'] = distribution
                    divisor = get_distribution_divisor(distribution)
                if degrees_of_freedom == '' or degrees_of_freedom == 0:
                    degrees_of_freedom = 'inf'
                    value_info['degrees_of_freedom'] = degrees_of_freedom
                
                # ウィジェットに値を設定
                if isinstance(central_value, (int, float)) or (isinstance(central_value, str) and central_value.replace('.', '', 1).isdigit()):
                    central_value = f"{float(central_value):.15g}"
                self.type_b_widgets['central_value'].setText(str(central_value))
                
                if isinstance(half_width, (int, float)) or (isinstance(half_width, str) and half_width.replace('.', '', 1).isdigit()):
                    half_width = f"{float(half_width):.15g}"
                self.type_b_widgets['half_width'].setText(str(half_width))
                
                if isinstance(standard_uncertainty, (int, float)) or (isinstance(standard_uncertainty, str) and standard_uncertainty.replace('.', '', 1).isdigit()):
                    standard_uncertainty = f"{float(standard_uncertainty):.15g}"
                self.type_b_widgets['standard_uncertainty'].setText(str(standard_uncertainty))
                
                self.type_b_widgets['degrees_of_freedom'].setText(str(degrees_of_freedom))
                self.type_b_widgets['description'].setText(str(description))
                self.type_b_widgets['calculation_formula'].setText(str(calculation_formula))
                self.type_b_widgets['divisor'].setText(str(divisor))
                distribution = get_distribution_translation_key(
                    var_info.get('distribution', NORMAL_DISTRIBUTION)
                ) or NORMAL_DISTRIBUTION
                var_info['distribution'] = distribution
                self.type_b_widgets['divisor'].setReadOnly(distribution != NORMAL_DISTRIBUTION)
                
                print(f"[DEBUG] TypeB復元: central_value='{central_value}', half_width='{half_width}', degrees_of_freedom='{degrees_of_freedom}', description='{description}', divisor='{divisor}'")

            # 値のソースが回帰式の場合
            source = value_info.get('source', 'manual')
            if source == 'regression':
                regression_id = value_info.get('regression_id', '')
                regression_x_mode = value_info.get('regression_x_mode', 'fixed')
                regression_x_value = value_info.get('regression_x_value', '')
                
                self.update_regression_model_options()
                model_index = self.regression_widgets['model'].findText(regression_id)
                if model_index >= 0:
                    self.regression_widgets['model'].setCurrentIndex(model_index)
                else:
                    self.regression_widgets['model'].setCurrentIndex(0)
                
                # xの取り方を設定
                x_mode_index = self.regression_widgets['x_mode'].findData(regression_x_mode)
                if x_mode_index >= 0:
                    self.regression_widgets['x_mode'].setCurrentIndex(x_mode_index)
                else:
                    self.regression_widgets['x_mode'].setCurrentIndex(1)  # デフォルトは固定値
                
                # xの値を設定（固定値の場合のみ）
                if regression_x_mode == 'fixed':
                    self.regression_widgets['x_value'].setText(str(regression_x_value))
                elif regression_x_mode == 'point_name':
                    # 校正点名を数値として使う場合は、現在の校正点名を表示
                    point_name = self.value_combo.currentText()
                    try:
                        point_value = float(point_name)
                        self.regression_widgets['x_value'].setText(str(point_value))
                    except ValueError:
                        self.regression_widgets['x_value'].setText('')

                print(f"[DEBUG] Regression復元: id='{regression_id}', x_mode='{regression_x_mode}', x_value='{regression_x_value}'")

            elif uncertainty_type == 'fixed':  # fixed
                # 辞書から値を取得（読み取り専用）
                fixed_value = value_info.get('fixed_value', '')
                description = value_info.get('description', '')
                
                # ウィジェットに値を設定
                if isinstance(fixed_value, (int, float)) or (isinstance(fixed_value, str) and fixed_value.replace('.', '', 1).isdigit()):
                    fixed_value = f"{float(fixed_value):.15g}"
                self.fixed_value_widgets['central_value'].setText(str(fixed_value))
                self.fixed_value_widgets['description'].setText(str(description))
                
                print(f"[DEBUG] Fixed復元: fixed_value='{fixed_value}', description='{description}'")
                    
            # フォームレイアウトの更新
            self.update_form_layout()
            print(f"[DEBUG] display_current_value: 復元完了")

        except Exception as e:
            print(f"【エラー】現在値の表示エラー: {str(e)}")
            print(traceback.format_exc())

    def update_value_combo(self):
        """値の選択コンボボックスを更新（校正点設定タブの情報を参照）"""
        try:
            self.value_combo.blockSignals(True)
            self.value_combo.clear()
            
            # 校正点設定タブで管理された校正点リストを取得
            value_names = getattr(self.parent, 'value_names', [])
            
            # 校正点リストから項目を追加
            for name in value_names:
                self.value_combo.addItem(name)
            
            # 現在のインデックスを設定（範囲内の場合のみ）
            if 0 <= self.parent.current_value_index < len(value_names):
                self.value_combo.setCurrentIndex(self.parent.current_value_index)
            
            self.value_combo.blockSignals(False)
            
        except Exception as e:
            print(f"【エラー】値の選択コンボボックス更新エラー: {str(e)}")
            print(traceback.format_exc())

    def update_regression_model_options(self):
        """回帰モデル選択肢を更新"""
        if not hasattr(self, 'regression_widgets'):
            return
        model_combo = self.regression_widgets.get('model')
        if not model_combo:
            return
        model_combo.blockSignals(True)
        model_combo.clear()
        model_combo.addItem("")
        regressions = getattr(self.parent, 'regressions', {})
        if isinstance(regressions, dict):
            for name in regressions.keys():
                model_combo.addItem(name)
        model_combo.blockSignals(False)

    def update_form_layout(self):
        """フォームレイアウトを更新して、非表示のウィジェットを詰める"""
        try:
            # 単位と定義のフィールドは常に表示
            self.unit_input.setVisible(True)
            self.definition_input.setVisible(True)
            
            # 現在の不確かさ種類を取得
            uncertainty_type = 'A'
            if self.type_b_radio.isChecked():
                uncertainty_type = 'B'
            elif self.type_fixed_radio.isChecked():
                uncertainty_type = 'fixed'
                
            # フォームレイアウトを取得
            form_layout = self.settings_group.layout()
            if not isinstance(form_layout, QFormLayout):
                return
                
            # 各ウィジェットの表示状態を確認し、非表示の場合は行全体を非表示にする
            for i in range(form_layout.rowCount()):
                label_item = form_layout.itemAt(i, QFormLayout.LabelRole)
                field_item = form_layout.itemAt(i, QFormLayout.FieldRole)
                
                if label_item and field_item:
                    label_widget = label_item.widget()
                    field_widget = field_item.widget()
                    
                    # ラベルとフィールドの両方が存在する場合
                    if label_widget and field_widget:
                        # 単位と定義のフィールドは常に表示
                        if field_widget in [self.unit_input, self.definition_input]:
                            label_widget.setVisible(True)
                            field_widget.setVisible(True)
                        # その他のフィールドは不確かさ種類に応じて表示/非表示
                        else:
                            if not field_widget.isVisible():
                                label_widget.setVisible(False)
                                field_widget.setVisible(False)
                            else:
                                label_widget.setVisible(True)
                                field_widget.setVisible(True)

                            if label_widget and field_item:
                                field_layout = field_item.layout()
                                if field_layout:
                                    any_visible = False
                                    for j in range(field_layout.count()):
                                        sub_item = field_layout.itemAt(j)
                                        sub_widget = sub_item.widget() if sub_item else None
                                        if sub_widget and sub_widget.isVisible():
                                            any_visible = True
                                            break
                                    label_widget.setVisible(any_visible)
        
        except Exception as e:
            print(f"【エラー】フォームレイアウト更新エラー: {str(e)}")
            print(traceback.format_exc())

    def get_distribution_options(self):
        """分布コンボボックスの選択肢を取得"""
        return [
            (NORMAL_DISTRIBUTION, self.tr(NORMAL_DISTRIBUTION)),
            (RECTANGULAR_DISTRIBUTION, self.tr(RECTANGULAR_DISTRIBUTION)),
            (TRIANGULAR_DISTRIBUTION, self.tr(TRIANGULAR_DISTRIBUTION)),
            (U_DISTRIBUTION, self.tr(U_DISTRIBUTION)),
        ]

    def showEvent(self, event):
        """タブが表示されたときのイベントハンドラ"""
        super().showEvent(event)
        self.restore_selection_state()
        
    def restore_selection_state(self):
        """選択状態を復元する"""
        try:
            # 量リストを更新
            self.update_variable_list(self.parent.variables, self.parent.result_variables)
            
            # 選択状態がNoneや不正値の場合は最初の変数・値を自動で選択
            if not self.handlers.last_selected_variable and self.variable_list.count() > 0:
                first_item = self.variable_list.item(0)
                if first_item:
                    self.handlers.last_selected_variable = first_item.data(Qt.UserRole)
            item = find_variable_item(self.variable_list, self.handlers.last_selected_variable)
            if item:
                self.variable_list.setCurrentItem(item)

            self.update_value_combo()
            target_index = self.parent.current_value_index
            if (not isinstance(target_index, int) or
                target_index < 0 or
                target_index >= self.value_combo.count()):
                target_index = 0

            if self.value_combo.count() > 0:
                self.value_combo.blockSignals(True)
                self.handlers.last_selected_value_index = target_index
                self.parent.current_value_index = target_index
                self.value_combo.setCurrentIndex(target_index)
                self.value_combo.blockSignals(False)

            self.display_common_settings()
            self.display_current_value()
                
        except Exception as e:
            print(f"【エラー】選択状態の復元エラー: {str(e)}")
            print(traceback.format_exc())
