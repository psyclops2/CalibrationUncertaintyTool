from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QComboBox, QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
    QGroupBox, QFormLayout, QSpinBox, QDoubleSpinBox, QCheckBox, QRadioButton,
    QButtonGroup, QSplitter, QFrame, QScrollArea, QGridLayout, QSizePolicy,
    QListWidget, QListWidgetItem, QTextEdit
)
from PySide6.QtCore import Qt, Signal, Slot
import traceback
from ..utils.variable_utils import (
    calculate_type_a_uncertainty,
    calculate_type_b_uncertainty,
    get_distribution_divisor,
    create_empty_value_dict,
    find_variable_item
)

class VariablesTab(QWidget):
    """量管理/量の値管理タブ"""
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.current_variable = None
        self.last_selected_variable = None  # 最後に選択された量を保持
        self.last_selected_value_index = 0  # 最後に選択された値のインデックスを保持
        self.setup_ui()
        
    def setup_ui(self):
        main_layout = QHBoxLayout()  # メインレイアウトを水平方向に変更
        
        # 左側のレイアウト（値の設定関連と量一覧）
        left_layout = QVBoxLayout()
        
        # 1. 値の数設定
        value_count_group = QGroupBox("校正点の数設定")
        value_count_layout = QHBoxLayout()
        value_count_label = QLabel("校正点の数:")
        self.value_count_spin = QSpinBox()
        self.value_count_spin.setMinimum(1)
        self.value_count_spin.setMaximum(10)
        self.value_count_spin.setValue(self.parent.value_count)
        self.value_count_spin.valueChanged.connect(self.on_value_count_changed)
        value_count_layout.addWidget(value_count_label)
        value_count_layout.addWidget(self.value_count_spin)
        value_count_layout.addStretch()
        value_count_group.setLayout(value_count_layout)
        left_layout.addWidget(value_count_group)
        
        # 2. 値の選択
        value_select_group = QGroupBox("校正点の選択")
        value_select_layout = QVBoxLayout()
        self.value_combo = QComboBox()
        self.value_combo.currentIndexChanged.connect(self.on_value_selected)
        value_select_layout.addWidget(self.value_combo)
        value_select_group.setLayout(value_select_layout)
        left_layout.addWidget(value_select_group)
        
        # 3. 量一覧
        variable_list_group = QGroupBox("量一覧/量の値の一覧")
        var_list_layout = QVBoxLayout()
        variable_info_layout = QHBoxLayout()
        var_label = QLabel("量モード:")
        self.mode_display = QLabel("未選択")
        variable_info_layout.addWidget(var_label)
        variable_info_layout.addWidget(self.mode_display)
        var_list_layout.addLayout(variable_info_layout)
        self.variable_list = QListWidget()
        self.variable_list.currentItemChanged.connect(self.on_variable_selected)
        var_list_layout.addWidget(self.variable_list)
        variable_list_group.setLayout(var_list_layout)
        left_layout.addWidget(variable_list_group)
        
        left_layout.addStretch()  # 下部に余白を追加
        
        # 右側のレイアウト（量詳細設定のみ）
        right_layout = QVBoxLayout()
        
        # 4. 量詳細設定
        self.settings_group = QGroupBox("量詳細設定/量の値詳細設定")
        settings_layout = QFormLayout()
        
        # 1段落目：単位
        self.unit_input = QLineEdit()
        self.unit_input.textChanged.connect(self.on_unit_changed)
        settings_layout.addRow("単位:", self.unit_input)
        
        # 定義フィールドを追加
        self.definition_input = QTextEdit()
        self.definition_input.setMaximumHeight(100)
        self.definition_input.textChanged.connect(self.on_definition_changed)
        settings_layout.addRow("定義:", self.definition_input)
        
        # 2段落目：不確かさ種類
        uncertainty_type_layout = QHBoxLayout()
        self.type_a_radio = QRadioButton("TypeA")
        self.type_b_radio = QRadioButton("TypeB")
        self.type_fixed_radio = QRadioButton("固定値")
        self.type_a_radio.toggled.connect(self.on_type_changed)
        self.type_b_radio.toggled.connect(self.on_type_changed)
        self.type_fixed_radio.toggled.connect(self.on_type_changed)
        uncertainty_type_layout.addWidget(self.type_a_radio)
        uncertainty_type_layout.addWidget(self.type_b_radio)
        uncertainty_type_layout.addWidget(self.type_fixed_radio)
        settings_layout.addRow("不確かさ種類:", uncertainty_type_layout)
        
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
        self.type_a_widgets['measurements'].setPlaceholderText("カンマ区切りで入力（例：1.2, 1.3, 1.4）")
        self.type_a_widgets['measurements'].focusOutEvent = lambda e: self.on_measurements_focus_lost(e)
        settings_layout.addRow("測定値:", self.type_a_widgets['measurements'])
        
        self.type_a_widgets['degrees_of_freedom'] = QLineEdit()
        self.type_a_widgets['degrees_of_freedom'].setReadOnly(True)
        settings_layout.addRow("自由度:", self.type_a_widgets['degrees_of_freedom'])
        
        self.type_a_widgets['central_value'] = QLineEdit()
        self.type_a_widgets['central_value'].setReadOnly(True)
        settings_layout.addRow("中央値:", self.type_a_widgets['central_value'])
        
        self.type_a_widgets['standard_uncertainty'] = QLineEdit()
        self.type_a_widgets['standard_uncertainty'].setReadOnly(True)
        settings_layout.addRow("標準不確かさ:", self.type_a_widgets['standard_uncertainty'])
        
        # 詳細説明フィールドを追加
        self.type_a_widgets['description'] = QTextEdit()
        self.type_a_widgets['description'].setMaximumHeight(100)
        self.type_a_widgets['description'].textChanged.connect(self.on_description_changed)
        settings_layout.addRow("詳細説明:", self.type_a_widgets['description'])
        
        # TypeB用のウィジェット
        self.type_b_widgets = {}
        
        self.type_b_widgets['distribution'] = QComboBox()
        self.type_b_widgets['distribution'].addItems(['正規分布', '矩形分布', '三角分布', 'U分布'])
        self.type_b_widgets['distribution'].currentIndexChanged.connect(self.on_distribution_changed)
        settings_layout.addRow("分布:", self.type_b_widgets['distribution'])
        
        self.type_b_widgets['divisor'] = QLineEdit()
        self.type_b_widgets['divisor'].textChanged.connect(self.on_divisor_changed)
        settings_layout.addRow("除数:", self.type_b_widgets['divisor'])
        
        self.type_b_widgets['degrees_of_freedom'] = QLineEdit()
        self.type_b_widgets['degrees_of_freedom'].textChanged.connect(self.on_degrees_of_freedom_changed)
        settings_layout.addRow("自由度:", self.type_b_widgets['degrees_of_freedom'])
        
        self.type_b_widgets['central_value'] = QLineEdit()
        self.type_b_widgets['central_value'].textChanged.connect(self.on_central_value_changed)
        settings_layout.addRow("中央値:", self.type_b_widgets['central_value'])
        
        self.type_b_widgets['half_width'] = QLineEdit()
        self.type_b_widgets['half_width'].focusOutEvent = lambda e: self.on_half_width_focus_lost(e)
        settings_layout.addRow("半値幅:", self.type_b_widgets['half_width'])
        
        self.type_b_widgets['standard_uncertainty'] = QLineEdit()
        self.type_b_widgets['standard_uncertainty'].setReadOnly(True)
        settings_layout.addRow("標準不確かさ:", self.type_b_widgets['standard_uncertainty'])
        
        # 詳細説明フィールドを追加
        self.type_b_widgets['description'] = QTextEdit()
        self.type_b_widgets['description'].setMaximumHeight(100)
        self.type_b_widgets['description'].textChanged.connect(self.on_description_changed)
        settings_layout.addRow("詳細説明:", self.type_b_widgets['description'])
        
        # 固定値用のウィジェット
        self.fixed_value_widgets = {}
        
        self.fixed_value_widgets['central_value'] = QLineEdit()
        self.fixed_value_widgets['central_value'].textChanged.connect(self.on_fixed_value_changed)
        settings_layout.addRow("中央値:", self.fixed_value_widgets['central_value'])
        
        # 詳細説明フィールドを追加
        self.fixed_value_widgets['description'] = QTextEdit()
        self.fixed_value_widgets['description'].setMaximumHeight(100)
        self.fixed_value_widgets['description'].textChanged.connect(self.on_description_changed)
        settings_layout.addRow("詳細説明:", self.fixed_value_widgets['description'])
        
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
        self.on_type_changed(True)  # 初期表示を設定
        
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
            if self.last_selected_variable:
                for i in range(self.variable_list.count()):
                    item = self.variable_list.item(i)
                    if item.data(Qt.UserRole) == self.last_selected_variable:
                        self.variable_list.setCurrentItem(item)
                        break
            
            print(f"【デバッグ】変数リストを更新: 計算結果量={result_vars}, 入力量={input_vars}")
            
        except Exception as e:
            print(f"【エラー】変数リスト更新エラー: {str(e)}")
            print(traceback.format_exc())
            QMessageBox.warning(self, "エラー", "変数リストの更新に失敗しました。")
            
    def on_variable_selected(self, current, previous):
        """量が選択された時の処理"""
        try:
            if current is None:
                self.settings_group.setEnabled(False)
                self.mode_display.setText("未選択")
                return
                
            var_name = current.data(Qt.UserRole)
            self.current_variable = var_name
            self.last_selected_variable = var_name  # 選択状態を保存
            is_result = var_name in self.parent.result_variables
            var_mode = "計算結果" if is_result else "入力量"
            self.mode_display.setText(var_mode)

            self.settings_group.setEnabled(True)

            # 量辞書の初期化
            if var_name not in self.parent.variable_values:
                self.parent.variable_values[var_name] = {
                    'values': [],
                    'unit': '',
                    'type': 'A'
                }

            # 値の数を設定
            self.value_count_spin.setValue(self.parent.value_count)

            # 値の選択コンボボックスのシグナルを一時的に切断
            self.value_combo.blockSignals(True)
            
            # 値の選択コンボボックスを更新
            self.update_value_combo()
            
            # 現在選択されている値のインデックスを設定
            self.value_combo.setCurrentIndex(self.parent.current_value_index)
            
            # 値の選択コンボボックスのシグナルを再接続
            self.value_combo.blockSignals(False)

            # 共通の設定を表示
            self.display_common_settings()

            # 現在の値の情報を表示
            self.display_current_value()

        except Exception as e:
            print(f"【エラー】量選択エラー: {str(e)}")
            print(traceback.format_exc())

    def display_common_settings(self):
        """共通の設定（単位、不確かさ種類、分布、除数）を表示"""
        try:
            if not self.current_variable:
                return

            var_info = self.parent.variable_values[self.current_variable]
            
            # 単位の設定
            self.unit_input.setText(var_info.get('unit', ''))
            
            # 定義の設定
            self.definition_input.setText(var_info.get('definition', ''))
            
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
            self.on_type_changed(True)
                
        except Exception as e:
            print(f"【エラー】共通設定表示エラー: {str(e)}")
            print(traceback.format_exc())
            
    def display_current_value(self):
        """現在選択されている値の情報を表示"""
        try:
            if not self.current_variable or self.value_combo.currentIndex() < 0:
                return
                
            var_info = self.parent.variable_values[self.current_variable]
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
                    'description': ''  # 詳細説明フィールドを追加
                })

            value_info = values[index]
            
            # 不確かさ種類に応じた値の設定
            uncertainty_type = var_info.get('type', 'A')
            
            if uncertainty_type == 'A':
                self.type_a_widgets['measurements'].setText(value_info.get('measurements', ''))
                self.type_a_widgets['degrees_of_freedom'].setText(str(value_info.get('degrees_of_freedom', 0)))
                self.type_a_widgets['central_value'].setText(str(value_info.get('central_value', '')))
                self.type_a_widgets['standard_uncertainty'].setText(str(value_info.get('standard_uncertainty', '')))
                self.type_a_widgets['description'].setText(value_info.get('description', ''))  # 詳細説明を設定
                
            elif uncertainty_type == 'B':
                self.type_b_widgets['central_value'].setText(str(value_info.get('central_value', '')))
                self.type_b_widgets['half_width'].setText(str(value_info.get('half_width', '')))
                self.type_b_widgets['standard_uncertainty'].setText(str(value_info.get('standard_uncertainty', '')))
                self.type_b_widgets['degrees_of_freedom'].setText(str(value_info.get('degrees_of_freedom', '')))
                self.type_b_widgets['description'].setText(value_info.get('description', ''))  # 詳細説明を設定
                
            else:  # fixed
                self.fixed_value_widgets['central_value'].setText(str(value_info.get('fixed_value', '')))
                self.fixed_value_widgets['description'].setText(value_info.get('description', ''))  # 詳細説明を設定
            
            # フィールドの表示を更新
            is_result = self.current_variable in self.parent.result_variables
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
            print(f"【エラー】値表示エラー: {str(e)}")
            print(traceback.format_exc())

    def on_value_changed(self):
        """値が変更された時の処理"""
        if self.current_variable and self.value_combo.currentIndex() >= 0:
            index = self.value_combo.currentIndex()
            if 'values' not in self.parent.variable_values[self.current_variable]:
                self.parent.variable_values[self.current_variable]['values'] = []
            
            # インデックスが範囲外の場合、新しい値を追加
            while len(self.parent.variable_values[self.current_variable]['values']) <= index:
                self.parent.variable_values[self.current_variable]['values'].append({
                    'value': '',
                    'type': 'A',
                    'unit': '',
                    'definition': '',
                    'stddev': '',
                    'sample_count': '',
                    'nominal_value': '',
                    'error_range': ''
                })
            
            self.parent.variable_values[self.current_variable]['values'][index]['value'] = self.value_input.text()

    def on_type_changed(self, checked):
        """不確かさ種類が変更されたときの処理"""
        if not checked:
            return
            
        try:
            if self.type_a_radio.isChecked():
                uncertainty_type = 'A'
                # TypeA用のウィジェットを表示・有効化
                for widget in self.type_a_widgets.values():
                    widget.setVisible(True)
                    widget.setEnabled(True)
                # TypeB用のウィジェットを非表示・無効化
                for widget in self.type_b_widgets.values():
                    widget.setVisible(False)
                    widget.setEnabled(False)
                # 固定値用のウィジェットを非表示・無効化
                for widget in self.fixed_value_widgets.values():
                    widget.setVisible(False)
                    widget.setEnabled(False)
                    
            elif self.type_b_radio.isChecked():
                uncertainty_type = 'B'
                # TypeA用のウィジェットを非表示・無効化
                for widget in self.type_a_widgets.values():
                    widget.setVisible(False)
                    widget.setEnabled(False)
                # TypeB用のウィジェットを表示・有効化
                for widget in self.type_b_widgets.values():
                    widget.setVisible(True)
                    widget.setEnabled(True)
                # 固定値用のウィジェットを非表示・無効化
                for widget in self.fixed_value_widgets.values():
                    widget.setVisible(False)
                    widget.setEnabled(False)
                    
            else:  # 固定値
                uncertainty_type = 'fixed'
                # TypeA用のウィジェットを非表示・無効化
                for widget in self.type_a_widgets.values():
                    widget.setVisible(False)
                    widget.setEnabled(False)
                # TypeB用のウィジェットを非表示・無効化
                for widget in self.type_b_widgets.values():
                    widget.setVisible(False)
                    widget.setEnabled(False)
                # 固定値用のウィジェットを表示・有効化
                for widget in self.fixed_value_widgets.values():
                    widget.setVisible(True)
                    widget.setEnabled(True)
                    
            if self.current_variable:
                # 量の不確かさ種類を更新
                self.parent.variable_values[self.current_variable]['type'] = uncertainty_type
                
            # フォームレイアウトの更新
            self.update_form_layout()
            
        except Exception as e:
            print(f"【エラー】不確かさ種類変更エラー: {str(e)}")
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

    def on_unit_changed(self):
        """単位が変更されたときの処理"""
        try:
            if self.current_variable:
                self.parent.variable_values[self.current_variable]['unit'] = self.unit_input.text()
        except Exception as e:
            print(f"【エラー】単位変更エラー: {str(e)}")
            print(traceback.format_exc())

    def on_definition_changed(self):
        """定義が変更されたときの処理"""
        try:
            if self.current_variable:
                self.parent.variable_values[self.current_variable]['definition'] = self.definition_input.toPlainText()
        except Exception as e:
            print(f"【エラー】定義変更エラー: {str(e)}")
            print(traceback.format_exc())

    def on_stddev_changed(self):
        if self.current_variable:
            self.parent.variable_values[self.current_variable]['stddev'] = self.stddev_input.text()

    def on_sample_count_changed(self):
        if self.current_variable:
            self.parent.variable_values[self.current_variable]['sample_count'] = self.sample_count_input.text()

    def on_nominal_value_changed(self):
        if self.current_variable:
            self.parent.variable_values[self.current_variable]['nominal_value'] = self.nominal_value_input.text()

    def on_error_range_changed(self):
        if self.current_variable:
            self.parent.variable_values[self.current_variable]['error_range'] = self.error_range_input.text()

    def on_value_count_changed(self, new_count):
        """値の数が変更された時の処理"""
        try:
            # 親クラスの値の数を更新
            self.parent.value_count = new_count
            
            # すべての量に対して値の数を更新
            for var_name in self.parent.variable_values:
                var_values = self.parent.variable_values[var_name].get('values', [])
                current_count = len(var_values)

                if new_count < current_count:
                    # 値を削除する場合
                    var_values = var_values[:new_count]
                elif new_count > current_count:
                    # 値を追加する場合
                    for _ in range(new_count - current_count):
                        # 既存の値の単位と定義を取得
                        unit = self.parent.variable_values[var_name].get('unit', '')
                        definition = self.parent.variable_values[var_name].get('definition', '')
                        var_values.append({
                            'value': '',
                            'type': 'A',
                            'unit': unit,  # 単位を保持
                            'definition': definition,  # 定義を保持
                            'stddev': '',
                            'sample_count': '',
                            'nominal_value': '',
                            'error_range': ''
                        })

                # 量辞書を更新
                self.parent.variable_values[var_name]['values'] = var_values

            # 値の選択コンボボックスを更新
            self.update_value_combo()

        except Exception as e:
            print(f"【エラー】値の数変更エラー: {str(e)}")
            print(traceback.format_exc())

    def update_value_combo(self):
        """値の選択コンボボックスを更新"""
        try:
            self.value_combo.blockSignals(True)
            self.value_combo.clear()
            
            if self.current_variable and self.current_variable in self.parent.variable_values:
                values = self.parent.variable_values[self.current_variable].get('values', [])
                for i in range(self.parent.value_count):  # value_countを使用
                    self.value_combo.addItem(f"校正点 {i+1}")
                    
                    # 必要に応じて値リストを拡張
                    if i >= len(values):
                        # 既存の値の単位と定義を取得
                        unit = self.parent.variable_values[self.current_variable].get('unit', '')
                        definition = self.parent.variable_values[self.current_variable].get('definition', '')
                        values.append({
                            'value': '',
                            'type': 'A',
                            'unit': unit,  # 単位を保持
                            'definition': definition,  # 定義を保持
                            'stddev': '',
                            'sample_count': '',
                            'nominal_value': '',
                            'error_range': ''
                        })
                
                # 値リストを更新
                self.parent.variable_values[self.current_variable]['values'] = values
                
                # 現在のインデックスを設定
                if self.parent.current_value_index < self.parent.value_count:
                    self.value_combo.setCurrentIndex(self.parent.current_value_index)
            
            self.value_combo.blockSignals(False)
            
        except Exception as e:
            print(f"【エラー】値の選択コンボボックス更新エラー: {str(e)}")
            print(traceback.format_exc())

    def on_value_selected(self, index):
        """値が選択された時の処理"""
        if index < 0:
            return

        try:
            # 親クラスの現在の値インデックスを更新
            self.parent.current_value_index = index
            self.last_selected_value_index = index  # 選択状態を保存
            
            # 現在の値の情報を表示
            self.display_current_value()

        except Exception as e:
            print(f"【エラー】値選択エラー: {str(e)}")
            print(traceback.format_exc())

    def update_uncertainty_type_fields(self, var_type):
        is_type_a = (var_type == "A")
        self.type_a_widgets['measurements'].setVisible(is_type_a)
        self.type_b_widgets['distribution'].setVisible(not is_type_a)
        self.type_fixed_radio.setVisible(not is_type_a)

        self.value_combo.setEnabled(True)
        self.type_a_radio.setEnabled(True)
        self.type_b_radio.setEnabled(True)
        self.type_fixed_radio.setEnabled(editable and not is_type_a)
        self.unit_input.setEnabled(editable)
        self.type_a_widgets['measurements'].setEnabled(editable and is_type_a)
        self.type_a_widgets['degrees_of_freedom'].setEnabled(editable and is_type_a)
        self.type_a_widgets['central_value'].setEnabled(editable and is_type_a)
        self.type_a_widgets['standard_uncertainty'].setEnabled(editable and is_type_a)
        self.type_b_widgets['distribution'].setEnabled(editable and not is_type_a)
        self.type_b_widgets['divisor'].setEnabled(editable and not is_type_a)
        self.type_b_widgets['central_value'].setEnabled(editable and not is_type_a)
        self.type_b_widgets['half_width'].setEnabled(editable and not is_type_a)
        self.type_b_widgets['standard_uncertainty'].setEnabled(editable and not is_type_a)
        self.fixed_value_widgets['central_value'].setEnabled(editable and not is_type_a)

    def on_measurements_focus_lost(self, event):
        """測定値入力からフォーカスが外れたときの処理"""
        try:
            if not self.current_variable or self.value_combo.currentIndex() < 0:
                return
                
            measurements_str = self.type_a_widgets['measurements'].text().strip()
            if not measurements_str:
                return
                
            # TypeA不確かさの計算
            degrees_of_freedom, central_value, standard_uncertainty, measurements_str = calculate_type_a_uncertainty(measurements_str)
            
            if degrees_of_freedom is not None:
                # 結果を表示
                self.type_a_widgets['degrees_of_freedom'].setText(str(degrees_of_freedom))
                self.type_a_widgets['central_value'].setText(f"{central_value:.6g}")
                self.type_a_widgets['standard_uncertainty'].setText(f"{standard_uncertainty:.6g}")
                
                # データを保存
                index = self.value_combo.currentIndex()
                if 'values' in self.parent.variable_values[self.current_variable]:
                    self.parent.variable_values[self.current_variable]['values'][index].update({
                        'measurements': measurements_str,
                        'degrees_of_freedom': degrees_of_freedom,
                        'central_value': central_value,
                        'standard_uncertainty': standard_uncertainty
                    })
            
        except Exception as e:
            print(f"【エラー】測定値計算エラー: {str(e)}")
            print(traceback.format_exc())
            
    def on_distribution_changed(self, index):
        """分布の種類が変更されたときの処理"""
        try:
            if not self.current_variable:
                return
                
            distribution = self.type_b_widgets['distribution'].currentText()
            
            # 分布の種類に応じて除数を設定
            divisor = get_distribution_divisor(distribution)
            
            self.type_b_widgets['divisor'].setText(divisor)
            self.type_b_widgets['divisor'].setReadOnly(distribution != '正規分布')
            
            # 量の分布と除数を更新
            self.parent.variable_values[self.current_variable]['distribution'] = distribution
            self.parent.variable_values[self.current_variable]['divisor'] = divisor
            
            # 半値幅が設定されている場合は標準不確かさを再計算
            half_width = self.type_b_widgets['half_width'].text().strip()
            if half_width and divisor:
                half_width, standard_uncertainty = calculate_type_b_uncertainty(half_width, divisor)
                if standard_uncertainty is not None:
                    self.type_b_widgets['standard_uncertainty'].setText(f"{standard_uncertainty:.6g}")
                    
                    # すべての値の標準不確かさを更新
                    for value_info in self.parent.variable_values[self.current_variable]['values']:
                        value_info['standard_uncertainty'] = standard_uncertainty
            
        except Exception as e:
            print(f"【エラー】分布変更エラー: {str(e)}")
            print(traceback.format_exc())
            
    def on_half_width_focus_lost(self, event):
        """半値幅入力からフォーカスが外れたときの処理"""
        try:
            if not self.current_variable or self.value_combo.currentIndex() < 0:
                return
                
            half_width_str = self.type_b_widgets['half_width'].text().strip()
            divisor = self.parent.variable_values[self.current_variable].get('divisor', '')
            
            if not half_width_str or not divisor:
                return
                
            half_width, standard_uncertainty = calculate_type_b_uncertainty(half_width_str, divisor)
            if standard_uncertainty is not None:
                self.type_b_widgets['standard_uncertainty'].setText(f"{standard_uncertainty:.6g}")
                
                # 現在の値の半値幅と標準不確かさを更新
                value_index = self.value_combo.currentIndex()
                if 'values' in self.parent.variable_values[self.current_variable]:
                    self.parent.variable_values[self.current_variable]['values'][value_index].update({
                        'half_width': half_width,
                        'standard_uncertainty': standard_uncertainty
                    })
            
        except Exception as e:
            print(f"【エラー】半値幅計算エラー: {str(e)}")
            print(traceback.format_exc())

    def on_divisor_changed(self):
        """除数が変更されたときの処理"""
        try:
            if not self.current_variable:
                return
                
            divisor = self.type_b_widgets['divisor'].text().strip()
            if not divisor:
                return
                
            # 量の除数を更新
            self.parent.variable_values[self.current_variable]['divisor'] = divisor
            
            # 現在の値の半値幅が設定されている場合は標準不確かさを再計算
            value_index = self.value_combo.currentIndex()
            if 'values' in self.parent.variable_values[self.current_variable]:
                value_info = self.parent.variable_values[self.current_variable]['values'][value_index]
                half_width = value_info.get('half_width', '')
                
                if half_width:
                    try:
                        half_width = float(half_width)
                        divisor = float(divisor)
                        standard_uncertainty = half_width / divisor
                        self.type_b_widgets['standard_uncertainty'].setText(f"{standard_uncertainty:.6g}")
                        value_info['standard_uncertainty'] = standard_uncertainty
                    except ValueError:
                        pass
            
        except Exception as e:
            print(f"【エラー】除数変更エラー: {str(e)}")
            print(traceback.format_exc())

    def on_central_value_changed(self):
        """中央値が変更されたときの処理"""
        try:
            if not self.current_variable or self.value_combo.currentIndex() < 0:
                return
                
            central_value = self.type_b_widgets['central_value'].text().strip()
            
            # データを保存
            value_index = self.value_combo.currentIndex()
            if 'values' in self.parent.variable_values[self.current_variable]:
                self.parent.variable_values[self.current_variable]['values'][value_index]['central_value'] = central_value
                
        except Exception as e:
            print(f"【エラー】中央値変更エラー: {str(e)}")
            print(traceback.format_exc())

    def on_fixed_value_changed(self):
        """固定値の中央値が変更されたときの処理"""
        try:
            if not self.current_variable or self.value_combo.currentIndex() < 0:
                return
                
            fixed_value = self.fixed_value_widgets['central_value'].text().strip()
            
            # データを保存
            value_index = self.value_combo.currentIndex()
            if 'values' in self.parent.variable_values[self.current_variable]:
                self.parent.variable_values[self.current_variable]['values'][value_index].update({
                    'fixed_value': fixed_value,
                    'central_value': fixed_value  # 固定値も中央値として保存
                })
                
        except Exception as e:
            print(f"【エラー】固定値変更エラー: {str(e)}")
            print(traceback.format_exc())

    def on_degrees_of_freedom_changed(self):
        """自由度が変更されたときの処理"""
        try:
            if not self.current_variable or self.value_combo.currentIndex() < 0:
                return
                
            degrees_of_freedom = self.type_b_widgets['degrees_of_freedom'].text().strip()
            
            # データを保存
            value_index = self.value_combo.currentIndex()
            if 'values' in self.parent.variable_values[self.current_variable]:
                self.parent.variable_values[self.current_variable]['values'][value_index]['degrees_of_freedom'] = degrees_of_freedom
                
        except Exception as e:
            print(f"【エラー】自由度変更エラー: {str(e)}")
            print(traceback.format_exc())

    def on_description_changed(self):
        """詳細説明が変更されたときの処理"""
        try:
            if not self.current_variable or self.value_combo.currentIndex() < 0:
                return
                
            # 現在選択されている値のインデックスを取得
            index = self.value_combo.currentIndex()
            
            # 現在の不確かさ種類を取得
            uncertainty_type = 'A'
            if self.type_b_radio.isChecked():
                uncertainty_type = 'B'
            elif self.type_fixed_radio.isChecked():
                uncertainty_type = 'fixed'
                
            # 不確かさ種類に応じた詳細説明を取得
            if uncertainty_type == 'A':
                description = self.type_a_widgets['description'].toPlainText()
            elif uncertainty_type == 'B':
                description = self.type_b_widgets['description'].toPlainText()
            else:  # fixed
                description = self.fixed_value_widgets['description'].toPlainText()
                
            # 値の辞書を取得
            var_info = self.parent.variable_values[self.current_variable]
            values = var_info.get('values', [])
            
            # インデックスが範囲外の場合、新しい値を追加
            while len(values) <= index:
                values.append({
                    'measurements': '',
                    'degrees_of_freedom': 0,
                    'central_value': '',
                    'standard_uncertainty': '',
                    'half_width': '',
                    'fixed_value': '',
                    'description': ''
                })
                
            # 詳細説明を保存
            values[index]['description'] = description
            
        except Exception as e:
            print(f"【エラー】詳細説明変更エラー: {str(e)}")
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
            
            # 最後に選択された量がある場合、それを選択
            if self.last_selected_variable:
                # 量リストから該当する量を探す
                item = find_variable_item(self.variable_list, self.last_selected_variable)
                if item:
                    self.variable_list.setCurrentItem(item)
            
            # 値の選択コンボボックスを更新
            self.update_value_combo()
            
            # 最後に選択された値のインデックスを設定
            if self.last_selected_value_index < self.value_combo.count():
                self.value_combo.setCurrentIndex(self.last_selected_value_index)
                
        except Exception as e:
            print(f"【エラー】選択状態の復元エラー: {str(e)}")
            print(traceback.format_exc())
