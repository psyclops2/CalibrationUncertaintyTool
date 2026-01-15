from PySide6.QtWidgets import (
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QGroupBox,
    QFormLayout,
    QComboBox,
    QCheckBox,
    QListWidget,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QMessageBox,
)
from PySide6.QtCore import Qt

from src.tabs.base_tab import BaseTab
from src.utils.translation_keys import *


class RegressionTab(BaseTab):
    """回帰モデルタブ"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.current_model_name = None
        self._updating = False
        self.setup_ui()

    def retranslate_ui(self):
        """UIのテキストを現在の言語で更新"""
        self.list_group.setTitle(self.tr(REGRESSION_LIST))
        self.details_group.setTitle(self.tr(REGRESSION_DETAILS))
        self.add_model_button.setText(self.tr(REGRESSION_ADD_MODEL))
        self.remove_model_button.setText(self.tr(REGRESSION_REMOVE_MODEL))
        self.add_row_button.setText(self.tr(REGRESSION_ADD_ROW))
        self.remove_row_button.setText(self.tr(REGRESSION_REMOVE_ROW))

        self.name_label.setText(self.tr(REGRESSION_NAME) + ":")
        self.description_label.setText(self.tr(REGRESSION_DESCRIPTION) + ":")
        self.mode_label.setText(self.tr(REGRESSION_MODE) + ":")
        self.x_unit_label.setText(self.tr(REGRESSION_X_UNIT) + ":")
        self.y_unit_label.setText(self.tr(REGRESSION_Y_UNIT) + ":")
        self.use_weights_checkbox.setText(self.tr(REGRESSION_USE_WEIGHTS))
        self.invert_checkbox.setText(self.tr(REGRESSION_INVERT))

        self.data_group.setTitle(self.tr(REGRESSION_DATA))

    def setup_ui(self):
        main_layout = QHBoxLayout(self)

        # 左側: 回帰モデル一覧
        self.list_group = QGroupBox(self.tr(REGRESSION_LIST))
        list_layout = QVBoxLayout()

        self.model_list = QListWidget()
        self.model_list.currentItemChanged.connect(self.on_model_selected)
        list_layout.addWidget(self.model_list)

        add_layout = QHBoxLayout()
        self.new_model_name_input = QLineEdit()
        self.add_model_button = QPushButton(self.tr(REGRESSION_ADD_MODEL))
        self.add_model_button.clicked.connect(self.add_model)
        add_layout.addWidget(self.new_model_name_input)
        add_layout.addWidget(self.add_model_button)
        list_layout.addLayout(add_layout)

        self.remove_model_button = QPushButton(self.tr(REGRESSION_REMOVE_MODEL))
        self.remove_model_button.clicked.connect(self.remove_model)
        list_layout.addWidget(self.remove_model_button)

        self.list_group.setLayout(list_layout)
        main_layout.addWidget(self.list_group, 1)

        # 右側: 回帰モデル詳細
        self.details_group = QGroupBox(self.tr(REGRESSION_DETAILS))
        details_layout = QVBoxLayout()

        form_layout = QFormLayout()
        self.name_label = QLabel(self.tr(REGRESSION_NAME) + ":")
        self.name_display = QLineEdit()
        self.name_display.setReadOnly(True)
        form_layout.addRow(self.name_label, self.name_display)

        self.description_label = QLabel(self.tr(REGRESSION_DESCRIPTION) + ":")
        self.description_input = QLineEdit()
        self.description_input.textChanged.connect(self.on_description_changed)
        form_layout.addRow(self.description_label, self.description_input)

        self.mode_label = QLabel(self.tr(REGRESSION_MODE) + ":")
        self.mode_input = QComboBox()
        self.mode_input.setEditable(True)
        self.mode_input.addItems(["generic", "time"])
        self.mode_input.currentTextChanged.connect(self.on_mode_changed)
        form_layout.addRow(self.mode_label, self.mode_input)

        self.x_unit_label = QLabel(self.tr(REGRESSION_X_UNIT) + ":")
        self.x_unit_input = QLineEdit()
        self.x_unit_input.textChanged.connect(self.on_x_unit_changed)
        form_layout.addRow(self.x_unit_label, self.x_unit_input)

        self.y_unit_label = QLabel(self.tr(REGRESSION_Y_UNIT) + ":")
        self.y_unit_input = QLineEdit()
        self.y_unit_input.textChanged.connect(self.on_y_unit_changed)
        form_layout.addRow(self.y_unit_label, self.y_unit_input)

        self.use_weights_checkbox = QCheckBox(self.tr(REGRESSION_USE_WEIGHTS))
        self.use_weights_checkbox.toggled.connect(self.on_use_weights_changed)
        form_layout.addRow("", self.use_weights_checkbox)

        self.invert_checkbox = QCheckBox(self.tr(REGRESSION_INVERT))
        self.invert_checkbox.toggled.connect(self.on_invert_changed)
        form_layout.addRow("", self.invert_checkbox)

        details_layout.addLayout(form_layout)

        self.data_group = QGroupBox(self.tr(REGRESSION_DATA))
        data_layout = QVBoxLayout()
        self.data_table = QTableWidget()
        self.data_table.setColumnCount(2)
        self.data_table.setHorizontalHeaderLabels(["x", "y"])
        self.data_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.data_table.itemChanged.connect(self.on_data_changed)
        data_layout.addWidget(self.data_table)

        row_buttons_layout = QHBoxLayout()
        self.add_row_button = QPushButton(self.tr(REGRESSION_ADD_ROW))
        self.add_row_button.clicked.connect(self.add_data_row)
        self.remove_row_button = QPushButton(self.tr(REGRESSION_REMOVE_ROW))
        self.remove_row_button.clicked.connect(self.remove_data_row)
        row_buttons_layout.addWidget(self.add_row_button)
        row_buttons_layout.addWidget(self.remove_row_button)
        row_buttons_layout.addStretch()
        data_layout.addLayout(row_buttons_layout)
        self.data_group.setLayout(data_layout)
        details_layout.addWidget(self.data_group)

        self.details_group.setLayout(details_layout)
        main_layout.addWidget(self.details_group, 2)

        self.details_group.setEnabled(False)
        self.refresh_model_list()

    def refresh_model_list(self):
        """回帰モデル一覧を更新"""
        self.model_list.blockSignals(True)
        self.model_list.clear()
        for name in self._get_model_names():
            self.model_list.addItem(name)
        self.model_list.blockSignals(False)

    def _get_model_names(self):
        if not self.parent:
            return []
        regressions = getattr(self.parent, "regressions", {})
        if not isinstance(regressions, dict):
            return []
        return list(regressions.keys())

    def add_model(self):
        """回帰モデルを追加"""
        name = self.new_model_name_input.text().strip()
        if not name:
            QMessageBox.information(self, self.tr(MESSAGE_INFO), self.tr(REGRESSION_NAME_REQUIRED))
            return
        regressions = getattr(self.parent, "regressions", {})
        if name in regressions:
            QMessageBox.warning(self, self.tr(MESSAGE_WARNING), self.tr(REGRESSION_NAME_DUPLICATE))
            return

        regressions[name] = {
            "description": "",
            "mode": "generic",
            "x_unit": "",
            "y_unit": "",
            "use_weights": False,
            "invert": False,
            "data": [],
        }
        self.parent.regressions = regressions
        self.refresh_model_list()
        items = self.model_list.findItems(name, Qt.MatchExactly)
        if items:
            self.model_list.setCurrentItem(items[0])
        self.new_model_name_input.clear()
        self._notify_regressions_updated()

    def remove_model(self):
        """回帰モデルを削除"""
        current_item = self.model_list.currentItem()
        if not current_item:
            return
        name = current_item.text()
        reply = QMessageBox.question(
            self,
            self.tr(MESSAGE_CONFIRM),
            self.tr(REGRESSION_REMOVE_CONFIRM).format(name=name),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return
        regressions = getattr(self.parent, "regressions", {})
        if name in regressions:
            del regressions[name]
        self.parent.regressions = regressions
        self.refresh_model_list()
        self.details_group.setEnabled(False)
        self.current_model_name = None
        self._notify_regressions_updated()

    def on_model_selected(self, current, previous):
        """モデル選択時の処理"""
        if current is None:
            self.current_model_name = None
            self.details_group.setEnabled(False)
            return
        self.current_model_name = current.text()
        self.load_model_details(self.current_model_name)

    def load_model_details(self, name):
        """モデル詳細をUIに反映"""
        regressions = getattr(self.parent, "regressions", {})
        model = regressions.get(name, {})
        self._updating = True
        try:
            self.details_group.setEnabled(True)
            self.name_display.setText(name)
            self.description_input.setText(model.get("description", ""))
            mode = model.get("mode", "generic")
            if self.mode_input.findText(mode) < 0:
                self.mode_input.addItem(mode)
            self.mode_input.setCurrentText(mode)
            self.x_unit_input.setText(model.get("x_unit", ""))
            self.y_unit_input.setText(model.get("y_unit", ""))
            self.use_weights_checkbox.setChecked(bool(model.get("use_weights", False)))
            self.invert_checkbox.setChecked(bool(model.get("invert", False)))
            self._populate_data_table(model.get("data", []))
        finally:
            self._updating = False

    def _populate_data_table(self, data):
        self.data_table.blockSignals(True)
        self.data_table.setRowCount(0)
        if not isinstance(data, list):
            data = []
        for row in data:
            row_index = self.data_table.rowCount()
            self.data_table.insertRow(row_index)
            x_item = QTableWidgetItem(str(row.get("x", "")) if isinstance(row, dict) else "")
            y_item = QTableWidgetItem(str(row.get("y", "")) if isinstance(row, dict) else "")
            self.data_table.setItem(row_index, 0, x_item)
            self.data_table.setItem(row_index, 1, y_item)
        self.data_table.blockSignals(False)

    def on_description_changed(self, text):
        if self._updating:
            return
        self._update_model_field("description", text)

    def on_mode_changed(self, text):
        if self._updating:
            return
        self._update_model_field("mode", text)

    def on_x_unit_changed(self, text):
        if self._updating:
            return
        self._update_model_field("x_unit", text)

    def on_y_unit_changed(self, text):
        if self._updating:
            return
        self._update_model_field("y_unit", text)

    def on_use_weights_changed(self, checked):
        if self._updating:
            return
        self._update_model_field("use_weights", bool(checked))

    def on_invert_changed(self, checked):
        if self._updating:
            return
        self._update_model_field("invert", bool(checked))

    def on_data_changed(self, item):
        if self._updating:
            return
        self._update_model_field("data", self._collect_table_data())

    def add_data_row(self):
        if self._updating:
            return
        row_index = self.data_table.rowCount()
        self.data_table.insertRow(row_index)
        self.data_table.setItem(row_index, 0, QTableWidgetItem(""))
        self.data_table.setItem(row_index, 1, QTableWidgetItem(""))
        self._update_model_field("data", self._collect_table_data())

    def remove_data_row(self):
        if self._updating:
            return
        current_row = self.data_table.currentRow()
        if current_row < 0:
            return
        self.data_table.removeRow(current_row)
        self._update_model_field("data", self._collect_table_data())

    def _collect_table_data(self):
        data = []
        for row in range(self.data_table.rowCount()):
            x_item = self.data_table.item(row, 0)
            y_item = self.data_table.item(row, 1)
            x_text = x_item.text().strip() if x_item else ""
            y_text = y_item.text().strip() if y_item else ""
            data.append({
                "x": self._convert_number(x_text),
                "y": self._convert_number(y_text),
            })
        return data

    @staticmethod
    def _convert_number(value):
        if value == "":
            return ""
        try:
            return float(value)
        except ValueError:
            return value

    def _update_model_field(self, field, value):
        if not self.current_model_name:
            return
        regressions = getattr(self.parent, "regressions", {})
        model = regressions.get(self.current_model_name)
        if not isinstance(model, dict):
            return
        model[field] = value
        regressions[self.current_model_name] = model
        self.parent.regressions = regressions
        self._notify_regressions_updated()

    def _notify_regressions_updated(self):
        if hasattr(self.parent, "variables_tab"):
            self.parent.variables_tab.update_regression_model_options()

    def showEvent(self, event):
        self.refresh_model_list()
        super().showEvent(event)
