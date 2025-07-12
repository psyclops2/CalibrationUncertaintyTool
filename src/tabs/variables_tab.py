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
        
        # TypeB用ウィジェット
        # 分布コンボボックスの項目を更新
        current_index = self.type_b_widgets['distribution'].currentIndex()
        self.type_b_widgets['distribution'].clear()
        self.type_b_widgets['distribution'].addItems([
            self.tr(NORMAL_DISTRIBUTION),
            self.tr(RECTANGULAR_DISTRIBUTION),
            self.tr(TRIANGULAR_DISTRIBUTION),
            self.tr(U_DISTRIBUTION)
        ])
        self.type_b_widgets['distribution'].setCurrentIndex(current_index)
        
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
        self.measurement_values_label = QLabel(self.tr(MEASUREMENT_VALUES) + ":")
        settings_layout.addRow(self.measurement_values_label, self.type_a_widgets['measurements'])
        
        self.type_a_widgets['degrees_of_freedom'] = QLineEdit()
        self.type_a_widgets['degrees_of_freedom'].setReadOnly(True)
        self.degrees_of_freedom_label_a = QLabel(self.tr(DEGREES_OF_FREEDOM) + ":")
        settings_layout.addRow(self.degrees_of_freedom_label_a, self.type_a_widgets['degrees_of_freedom'])
        
        self.type_a_widgets['central_value'] = QLineEdit()
        self.type_a_widgets['central_value'].setReadOnly(True)
        self.central_value_label_a = QLabel(self.tr(CENTRAL_VALUE) + ":")
        settings_layout.addRow(self.central_value_label_a, self.type_a_widgets['central_value'])
        
        self.type_a_widgets['standard_uncertainty'] = QLineEdit()
        self.type_a_widgets['standard_uncertainty'].setReadOnly(True)
        self.standard_uncertainty_label_a = QLabel(self.tr(STANDARD_UNCERTAINTY) + ":")
        settings_layout.addRow(self.standard_uncertainty_label_a, self.type_a_widgets['standard_uncertainty'])
        
        # 詳細説明フィールドを追加
        self.type_a_widgets['description'] = QTextEdit()
        self.type_a_widgets['description'].setMaximumHeight(100)
        self.type_a_widgets['description'].textChanged.connect(self.handlers.on_description_changed)
        self.detail_description_label_a = QLabel(self.tr(DETAIL_DESCRIPTION) + ":")
        settings_layout.addRow(self.detail_description_label_a, self.type_a_widgets['description'])
        
        # TypeB用のウィジェット
        self.type_b_widgets = {}
        
        self.type_b_widgets['distribution'] = QComboBox()
        self.type_b_widgets['distribution'].addItems([
            self.tr(NORMAL_DISTRIBUTION),
            self.tr(RECTANGULAR_DISTRIBUTION),
            self.tr(TRIANGULAR_DISTRIBUTION),
            self.tr(U_DISTRIBUTION)
        ])
        self.type_b_widgets['distribution'].currentIndexChanged.connect(self.handlers.on_distribution_changed)
        self.distribution_label = QLabel(self.tr(DISTRIBUTION) + ":")
        settings_layout.addRow(self.distribution_label, self.type_b_widgets['distribution'])
        
        self.type_b_widgets['divisor'] = QLineEdit()
        self.type_b_widgets['divisor'].textChanged.connect(self.handlers.on_divisor_changed)
        self.divisor_label = QLabel(self.tr(DIVISOR) + ":")
        settings_layout.addRow(self.divisor_label, self.type_b_widgets['divisor'])
        
        self.type_b_widgets['degrees_of_freedom'] = QLineEdit()
        self.type_b_widgets['degrees_of_freedom'].textChanged.connect(self.handlers.on_degrees_of_freedom_changed)
        self.degrees_of_freedom_label_b = QLabel(self.tr(DEGREES_OF_FREEDOM) + ":")
        settings_layout.addRow(self.degrees_of_freedom_label_b, self.type_b_widgets['degrees_of_freedom'])
        
        self.type_b_widgets['central_value'] = QLineEdit()
        self.type_b_widgets['central_value'].textChanged.connect(self.handlers.on_central_value_changed)
        self.central_value_label_b = QLabel(self.tr(CENTRAL_VALUE) + ":")
        settings_layout.addRow(self.central_value_label_b, self.type_b_widgets['central_value'])
        
        # 半値幅の入力欄とその他のウィジェットを含むレイアウト
        half_width_layout = QHBoxLayout()
        self.type_b_widgets['half_width'] = QLineEdit()
        self.type_b_widgets['half_width'].focusOutEvent = lambda e: self.handlers.on_half_width_focus_lost(e)
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
        self.standard_uncertainty_label_b = QLabel(self.tr(STANDARD_UNCERTAINTY) + ":")
        settings_layout.addRow(self.standard_uncertainty_label_b, self.type_b_widgets['standard_uncertainty'])
        
        # 詳細説明フィールドを追加
        self.type_b_widgets['description'] = QTextEdit()
        self.type_b_widgets['description'].setMaximumHeight(100)
        self.type_b_widgets['description'].textChanged.connect(self.handlers.on_description_changed)
        self.detail_description_label_b = QLabel(self.tr(DETAIL_DESCRIPTION) + ":")
        settings_layout.addRow(self.detail_description_label_b, self.type_b_widgets['description'])
        
        # 固定値用のウィジェット
        self.fixed_value_widgets = {}
        
        self.fixed_value_widgets['central_value'] = QLineEdit()
        self.fixed_value_widgets['central_value'].textChanged.connect(self.handlers.on_fixed_value_changed)
        self.central_value_label_fixed = QLabel(self.tr(CENTRAL_VALUE) + ":")
        settings_layout.addRow(self.central_value_label_fixed, self.fixed_value_widgets['central_value'])
        
        # 詳細説明フィールドを追加
        self.fixed_value_widgets['description'] = QTextEdit()
        self.fixed_value_widgets['description'].setMaximumHeight(100)
        self.fixed_value_widgets['description'].textChanged.connect(self.handlers.on_description_changed)
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
        
        # 初期状態ではTypeAを選択
        self.type_a_radio.setChecked(True)
        self.handlers.on_type_changed(True)  # 初期表示を設定
        
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
            if uncertainty_type == 'A':
                self.type_a_radio.setChecked(True)
            elif uncertainty_type == 'B':
                self.type_b_radio.setChecked(True)
            else:  # fixed
                self.type_fixed_radio.setChecked(True)
            
            # TypeBの場合、分布と除数の設定
            if uncertainty_type == 'B':
                distribution = var_info.get('distribution', '正規分布')
                self.type_b_widgets['distribution'].setCurrentText(distribution)
                
                # 分布に応じた除数を設定
                divisor = get_distribution_divisor(distribution)
                
                self.type_b_widgets['divisor'].setText(divisor)
                self.type_b_widgets['divisor'].setReadOnly(distribution != '正規分布')
            
            # 不確かさ種類に応じたウィジェットの表示を更新
            self.handlers.on_type_changed(True)
                
        except Exception as e:
            print(f"【エラー】共通設定表示エラー: {str(e)}")
            print(traceback.format_exc())
            
    def display_current_value(self):
        """現在選択されている値の情報を表示"""
        try:
            if not self.handlers.current_variable or self.value_combo.currentIndex() < 0:
                return
                
            var_info = self.parent.variable_values[self.handlers.current_variable]
            values = var_info.get('values', [])
            index = self.value_combo.currentIndex()

            # インデックスが範囲外の場合、新しい値を追加
            while len(values) <= index:
                values.append({
                    'measurements': '',
                    'degrees_of_freedom': 0,
                    'central_value': '',
                    'standard_uncertainty': '',
                    'half_width': '',
                    'fixed_value': '',
                    'description': '',
                    'calculation_formula': ''
                })

            value_info = values[index]
            
            # 不確かさ種類に応じた値の設定
            uncertainty_type = var_info.get('type', 'A')
            
            if uncertainty_type == 'A':
                self.type_a_widgets['measurements'].setText(value_info.get('measurements', ''))
                self.type_a_widgets['degrees_of_freedom'].setText(str(value_info.get('degrees_of_freedom', 0)))
                # 数値の表示精度を統一
                central_value = value_info.get('central_value', '')
                if isinstance(central_value, (int, float)) and central_value != '':
                    central_value = f"{float(central_value):.15g}"
                self.type_a_widgets['central_value'].setText(str(central_value))
                
                standard_uncertainty = value_info.get('standard_uncertainty', '')
                if isinstance(standard_uncertainty, (int, float)) and standard_uncertainty != '':
                    standard_uncertainty = f"{float(standard_uncertainty):.15g}"
                self.type_a_widgets['standard_uncertainty'].setText(str(standard_uncertainty))
                self.type_a_widgets['description'].setText(value_info.get('description', ''))
                
            elif uncertainty_type == 'B':
                central_value = value_info.get('central_value', '')
                if isinstance(central_value, (int, float)) and central_value != '':
                    central_value = f"{float(central_value):.15g}"
                self.type_b_widgets['central_value'].setText(str(central_value))
                
                half_width = value_info.get('half_width', '')
                if isinstance(half_width, (int, float)) and half_width != '':
                    half_width = f"{float(half_width):.15g}"
                self.type_b_widgets['half_width'].setText(str(half_width))
                
                standard_uncertainty = value_info.get('standard_uncertainty', '')
                if isinstance(standard_uncertainty, (int, float)) and standard_uncertainty != '':
                    standard_uncertainty = f"{float(standard_uncertainty):.15g}"
                self.type_b_widgets['standard_uncertainty'].setText(str(standard_uncertainty))
                
                self.type_b_widgets['degrees_of_freedom'].setText(str(value_info.get('degrees_of_freedom', '')))
                self.type_b_widgets['description'].setText(value_info.get('description', ''))
                self.type_b_widgets['calculation_formula'].setText(value_info.get('calculation_formula', ''))
                
            else:  # fixed
                fixed_value = value_info.get('fixed_value', '')
                if isinstance(fixed_value, (int, float)) and fixed_value != '':
                    fixed_value = f"{float(fixed_value):.15g}"
                self.fixed_value_widgets['central_value'].setText(str(fixed_value))
                self.fixed_value_widgets['description'].setText(value_info.get('description', ''))
            
            # フィールドの表示を更新
            is_result = self.handlers.current_variable in self.parent.result_variables
            editable = not is_result
            self.unit_input.setEnabled(True)  # 計算結果量でも単位を編集可能に
            self.definition_input.setEnabled(True)  # 計算結果量でも定義を編集可能に
            self.type_a_radio.setEnabled(editable)
            self.type_b_radio.setEnabled(editable)
            self.type_fixed_radio.setEnabled(editable)
            
            # 不確かさ種類に応じたウィジェットの表示を更新
            if uncertainty_type == 'A':
                for widget in self.type_a_widgets.values():
                    widget.setVisible(True)
                    widget.setEnabled(editable)
                for widget in self.type_b_widgets.values():
                    widget.setVisible(False)
                    widget.setEnabled(False)
                for widget in self.fixed_value_widgets.values():
                    widget.setVisible(False)
                    widget.setEnabled(False)
            elif uncertainty_type == 'B':
                for widget in self.type_a_widgets.values():
                    widget.setVisible(False)
                    widget.setEnabled(False)
                for widget in self.type_b_widgets.values():
                    widget.setVisible(True)
                    widget.setEnabled(editable)
                for widget in self.fixed_value_widgets.values():
                    widget.setVisible(False)
                    widget.setEnabled(False)
            else:  # fixed
                for widget in self.type_a_widgets.values():
                    widget.setVisible(False)
                    widget.setEnabled(False)
                for widget in self.type_b_widgets.values():
                    widget.setVisible(False)
                    widget.setEnabled(False)
                for widget in self.fixed_value_widgets.values():
                    widget.setVisible(True)
                    widget.setEnabled(editable)
                    
            # フォームレイアウトの更新
            self.update_form_layout()

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
                            
        except Exception as e:
            print(f"【エラー】フォームレイアウト更新エラー: {str(e)}")
            print(traceback.format_exc())

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
            if (not isinstance(self.handlers.last_selected_value_index, int) or
                self.handlers.last_selected_value_index < 0 or
                self.handlers.last_selected_value_index >= self.value_combo.count()):
                self.handlers.last_selected_value_index = 0
            if self.value_combo.count() > 0:
                self.value_combo.setCurrentIndex(self.handlers.last_selected_value_index)
            
            self.display_common_settings()
            self.display_current_value()
                
        except Exception as e:
            print(f"【エラー】選択状態の復元エラー: {str(e)}")
            print(traceback.format_exc())
