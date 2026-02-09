from PySide6.QtWidgets import (
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QGroupBox,
    QFormLayout,
    QGridLayout,
    QCheckBox,
    QListWidget,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QMessageBox,
    QTextEdit,
    QDialog,
    QDialogButtonBox,
)
from PySide6.QtCore import Qt
import math

from src.tabs.base_tab import BaseTab
from src.utils.translation_keys import *
from src.utils.app_logger import log_error
from src.utils.regression_utils import (
    calculate_linear_regression_parameters,
    calculate_significance_f,
    calculate_xy_averages,
    calculate_value_average,
    calculate_regression_sxx,
)


def _parse_float_for_sort(value):
    try:
        if value is None:
            return None
        if isinstance(value, (int, float)):
            return float(value)
        value_str = str(value).strip()
        if value_str in {"", "--"}:
            return None
        return float(value_str)
    except (TypeError, ValueError):
        return None


class NumericTableWidgetItem(QTableWidgetItem):
    def __init__(self, text="", numeric_value=None):
        super().__init__(text)
        self.setData(Qt.UserRole, numeric_value)

    def __lt__(self, other):
        left = self.data(Qt.UserRole)
        right = other.data(Qt.UserRole) if isinstance(other, QTableWidgetItem) else None
        if left is None and right is None:
            return super().__lt__(other)
        if left is None:
            return False
        if right is None:
            return True
        try:
            return float(left) < float(right)
        except (TypeError, ValueError):
            return super().__lt__(other)

class RegressionTab(BaseTab):
    """回帰モデルタブ"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.current_model_name = None
        self._updating = False
        self._table_sort_state = {}
        self.setup_ui()

    def retranslate_ui(self):
        """UIのテキストを現在の言語で更新"""
        self.list_group.setTitle(self.tr(REGRESSION_LIST))
        self.details_group.setTitle(self.tr(REGRESSION_DETAILS))
        self.add_model_button.setText(self.tr(REGRESSION_ADD_MODEL))
        self.remove_model_button.setText(self.tr(REGRESSION_REMOVE_MODEL))
        self.copy_model_button.setText(self.tr(REGRESSION_COPY_MODEL))
        self.add_row_button.setText(self.tr(REGRESSION_ADD_ROW))
        self.remove_row_button.setText(self.tr(REGRESSION_REMOVE_ROW))
        self.import_csv_button.setText(self.tr(REGRESSION_IMPORT_CSV))

        self.name_label.setText(self.tr(REGRESSION_NAME) + ":")
        self.description_label.setText(self.tr(REGRESSION_DESCRIPTION) + ":")
        self.x_unit_label.setText(self.tr(REGRESSION_X_UNIT) + ":")
        self.y_unit_label.setText(self.tr(REGRESSION_Y_UNIT) + ":")

        self.data_group.setTitle(self.tr(REGRESSION_DATA))
        self.result_group.setTitle(self.tr(REGRESSION_RESULT))
        self.intercept_label.setText(self.tr(REGRESSION_INTERCEPT) + ":")
        self.slope_label.setText(self.tr(REGRESSION_SLOPE) + ":")
        self.u_beta_label.setText(self.tr(REGRESSION_U_BETA) + ":")
        self.significance_f_label.setText(self.tr(REGRESSION_SIGNIFICANCE_F) + ":")
        self.residual_variance_label.setText(self.tr(REGRESSION_RESIDUAL_VARIANCE) + ":")
        self.x_average_label.setText(self.tr(REGRESSION_X_AVERAGE) + ":")
        self.y_average_label.setText(self.tr(REGRESSION_Y_AVERAGE) + ":")
        self.ux_average_label.setText(self.tr(REGRESSION_UX_AVERAGE) + ":")
        self.uy_average_label.setText(self.tr(REGRESSION_UY_AVERAGE) + ":")
        self.inverse_group.setTitle(self.tr(REGRESSION_INVERSE_ESTIMATION))
        self._set_inverse_label_texts()
        self.inverse_add_row_button.setText(self.tr(REGRESSION_ADD_ROW))
        self.inverse_remove_row_button.setText(self.tr(REGRESSION_REMOVE_ROW))

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

        buttons_layout = QHBoxLayout()
        self.remove_model_button = QPushButton(self.tr(REGRESSION_REMOVE_MODEL))
        self.remove_model_button.clicked.connect(self.remove_model)
        self.copy_model_button = QPushButton(self.tr(REGRESSION_COPY_MODEL))
        self.copy_model_button.clicked.connect(self.copy_model)
        buttons_layout.addWidget(self.remove_model_button)
        buttons_layout.addWidget(self.copy_model_button)
        list_layout.addLayout(buttons_layout)

        self.list_group.setLayout(list_layout)
        main_layout.addWidget(self.list_group, 0.2)

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

        self.x_unit_label = QLabel(self.tr(REGRESSION_X_UNIT) + ":")
        self.x_unit_input = QLineEdit()
        self.x_unit_input.textChanged.connect(self.on_x_unit_changed)

        self.y_unit_label = QLabel(self.tr(REGRESSION_Y_UNIT) + ":")
        self.y_unit_input = QLineEdit()
        self.y_unit_input.textChanged.connect(self.on_y_unit_changed)

        unit_layout = QHBoxLayout()
        unit_layout.addWidget(self.x_unit_input)
        unit_layout.addWidget(self.y_unit_label)
        unit_layout.addWidget(self.y_unit_input)
        form_layout.addRow(self.x_unit_label, unit_layout)

        details_layout.addLayout(form_layout)

        self.data_group = QGroupBox(self.tr(REGRESSION_DATA))
        data_layout = QVBoxLayout()
        self.data_table = QTableWidget()
        self.data_table.setColumnCount(3)
        self.data_table.setHorizontalHeaderLabels(["x", "u(x)", "y"])
        self.data_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.data_table.itemChanged.connect(self.on_data_changed)
        self._init_header_sorting(self.data_table, "data")
        data_layout.addWidget(self.data_table)

        row_buttons_layout = QHBoxLayout()
        self.add_row_button = QPushButton(self.tr(REGRESSION_ADD_ROW))
        self.add_row_button.clicked.connect(self.add_data_row)
        self.remove_row_button = QPushButton(self.tr(REGRESSION_REMOVE_ROW))
        self.remove_row_button.clicked.connect(self.remove_data_row)
        self.import_csv_button = QPushButton(self.tr(REGRESSION_IMPORT_CSV))
        self.import_csv_button.clicked.connect(self.import_csv_data)
        row_buttons_layout.addWidget(self.add_row_button)
        row_buttons_layout.addWidget(self.remove_row_button)
        row_buttons_layout.addWidget(self.import_csv_button)
        row_buttons_layout.addStretch()
        data_layout.addLayout(row_buttons_layout)
        self.data_group.setLayout(data_layout)
        details_layout.addWidget(self.data_group)

        # 計算結果表示セクション
        self.result_group = QGroupBox(self.tr(REGRESSION_RESULT))
        result_layout = QGridLayout()
        
        self.intercept_label = QLabel(self.tr(REGRESSION_INTERCEPT) + ":")
        self.intercept_display = QLabel("--")
        result_layout.addWidget(self.intercept_label, 0, 0)
        result_layout.addWidget(self.intercept_display, 0, 1)
        
        self.slope_label = QLabel(self.tr(REGRESSION_SLOPE) + ":")
        self.slope_display = QLabel("--")
        result_layout.addWidget(self.slope_label, 1, 0)
        result_layout.addWidget(self.slope_display, 1, 1)

        self.significance_f_label = QLabel(self.tr(REGRESSION_SIGNIFICANCE_F) + ":")
        self.significance_f_display = QLabel("--")
        result_layout.addWidget(self.significance_f_label, 2, 0)
        result_layout.addWidget(self.significance_f_display, 2, 1)

        self.residual_variance_label = QLabel(self.tr(REGRESSION_RESIDUAL_VARIANCE) + ":")
        self.residual_variance_display = QLabel("--")
        result_layout.addWidget(self.residual_variance_label, 0, 2)
        result_layout.addWidget(self.residual_variance_display, 0, 3)

        self.x_average_label = QLabel(self.tr(REGRESSION_X_AVERAGE) + ":")
        self.x_average_display = QLabel("--")
        result_layout.addWidget(self.x_average_label, 1, 2)
        result_layout.addWidget(self.x_average_display, 1, 3)

        self.y_average_label = QLabel(self.tr(REGRESSION_Y_AVERAGE) + ":")
        self.y_average_display = QLabel("--")
        result_layout.addWidget(self.y_average_label, 2, 2)
        result_layout.addWidget(self.y_average_display, 2, 3)

        self.u_beta_label = QLabel(self.tr(REGRESSION_U_BETA) + ":")
        self.u_beta_display = QLabel("--")
        result_layout.addWidget(self.u_beta_label, 0, 4)
        result_layout.addWidget(self.u_beta_display, 0, 5)

        self.ux_average_label = QLabel(self.tr(REGRESSION_UX_AVERAGE) + ":")
        self.ux_average_display = QLabel("--")
        result_layout.addWidget(self.ux_average_label, 1, 4)
        result_layout.addWidget(self.ux_average_display, 1, 5)

        self.uy_average_label = QLabel(self.tr(REGRESSION_UY_AVERAGE) + ":")
        self.uy_average_display = QLabel("--")
        result_layout.addWidget(self.uy_average_label, 2, 4)
        result_layout.addWidget(self.uy_average_display, 2, 5)

        self.result_group.setLayout(result_layout)
        details_layout.addWidget(self.result_group)

        # 逆推定セクション
        self.inverse_group = QGroupBox(self.tr(REGRESSION_INVERSE_ESTIMATION))
        inverse_layout = QVBoxLayout()
        self.inverse_table = QTableWidget()
        self.inverse_table.setColumnCount(3)
        self.inverse_table.setRowCount(1)
        self.inverse_table.setHorizontalHeaderLabels(
            [self.tr(REGRESSION_Y0), self.tr(REGRESSION_X0), self.tr(REGRESSION_UX0)]
        )
        self.inverse_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.inverse_table.verticalHeader().setVisible(False)
        self.inverse_table.itemChanged.connect(self.on_inverse_table_changed)
        self._init_header_sorting(self.inverse_table, "inverse")

        self._ensure_inverse_row_items(0)
        inverse_layout.addWidget(self.inverse_table)

        inverse_buttons = QHBoxLayout()
        self.inverse_add_row_button = QPushButton(self.tr(REGRESSION_ADD_ROW))
        self.inverse_add_row_button.clicked.connect(self.add_inverse_row)
        self.inverse_remove_row_button = QPushButton(self.tr(REGRESSION_REMOVE_ROW))
        self.inverse_remove_row_button.clicked.connect(self.remove_inverse_row)
        inverse_buttons.addWidget(self.inverse_add_row_button)
        inverse_buttons.addWidget(self.inverse_remove_row_button)
        inverse_buttons.addStretch()
        inverse_layout.addLayout(inverse_buttons)
        self.inverse_group.setLayout(inverse_layout)
        details_layout.addWidget(self.inverse_group)

        self.details_group.setLayout(details_layout)
        main_layout.addWidget(self.details_group, 2)

        self.details_group.setEnabled(False)
        self.refresh_model_list()

    def _init_header_sorting(self, table, key):
        header = table.horizontalHeader()
        header.setSectionsClickable(True)
        header.setSortIndicatorShown(True)
        header.sectionClicked.connect(
            lambda column, t=table, k=key: self._toggle_table_sort(t, k, column)
        )
        self._table_sort_state.setdefault(key, {"column": -1, "order": Qt.AscendingOrder})

    def _toggle_table_sort(self, table, key, column):
        state = self._table_sort_state.get(key, {"column": -1, "order": Qt.AscendingOrder})
        if state["column"] == column:
            order = Qt.DescendingOrder if state["order"] == Qt.AscendingOrder else Qt.AscendingOrder
        else:
            order = Qt.AscendingOrder
        self._table_sort_state[key] = {"column": column, "order": order}
        table.sortItems(column, order)
        table.horizontalHeader().setSortIndicator(column, order)

    def _make_numeric_item(self, value, readonly=False):
        text = "" if value is None else str(value)
        item = NumericTableWidgetItem(text, _parse_float_for_sort(value))
        if readonly:
            self._set_readonly_item(item)
        return item

    @staticmethod
    def _set_item_numeric_sort_value(item, value):
        item.setData(Qt.UserRole, _parse_float_for_sort(value))

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
            "x_unit": "",
            "y_unit": "",
            "data": [],
            "inverse_y0s": [],
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
            self.x_unit_input.setText(model.get("x_unit", ""))
            self.y_unit_input.setText(model.get("y_unit", ""))
            self._populate_data_table(model.get("data", []))
            self._populate_inverse_table(model.get("inverse_y0s", []))
            self._update_regression_result(model)
        finally:
            self._updating = False

    def _populate_data_table(self, data):
        sort_state = self._table_sort_state.get("data", {"column": -1, "order": Qt.AscendingOrder})
        self.data_table.blockSignals(True)
        self.data_table.setRowCount(0)
        if not isinstance(data, list):
            data = []
        for row in data:
            row_index = self.data_table.rowCount()
            self.data_table.insertRow(row_index)
            x_value = row.get("x", "") if isinstance(row, dict) else ""
            ux_value = row.get("ux", "") if isinstance(row, dict) else ""
            y_value = row.get("y", "") if isinstance(row, dict) else ""
            x_item = self._make_numeric_item(x_value)
            ux_item = self._make_numeric_item(ux_value)
            y_item = self._make_numeric_item(y_value)
            self.data_table.setItem(row_index, 0, x_item)
            self.data_table.setItem(row_index, 1, ux_item)
            self.data_table.setItem(row_index, 2, y_item)
        self.data_table.blockSignals(False)
        if sort_state["column"] >= 0:
            self.data_table.sortItems(sort_state["column"], sort_state["order"])
            self.data_table.horizontalHeader().setSortIndicator(sort_state["column"], sort_state["order"])

    def _populate_inverse_table(self, y0_values):
        sort_state = self._table_sort_state.get("inverse", {"column": -1, "order": Qt.AscendingOrder})
        self.inverse_table.blockSignals(True)
        self.inverse_table.setRowCount(0)
        if not isinstance(y0_values, list) or not y0_values:
            y0_values = [""]
        for value in y0_values:
            row_index = self.inverse_table.rowCount()
            self.inverse_table.insertRow(row_index)
            y0_item = self._make_numeric_item("" if value is None else value)
            self.inverse_table.setItem(row_index, 0, y0_item)
            x0_item = self._make_numeric_item("--", readonly=True)
            self.inverse_table.setItem(row_index, 1, x0_item)
            ux0_item = self._make_numeric_item("--", readonly=True)
            self.inverse_table.setItem(row_index, 2, ux0_item)
        self.inverse_table.blockSignals(False)
        self._update_inverse_table()
        if sort_state["column"] >= 0:
            self.inverse_table.sortItems(sort_state["column"], sort_state["order"])
            self.inverse_table.horizontalHeader().setSortIndicator(sort_state["column"], sort_state["order"])

    def on_description_changed(self, text):
        if self._updating:
            return
        self._update_model_field("description", text)

    def on_x_unit_changed(self, text):
        if self._updating:
            return
        self._update_model_field("x_unit", text)

    def on_y_unit_changed(self, text):
        if self._updating:
            return
        self._update_model_field("y_unit", text)

    def on_data_changed(self, item):
        if self._updating:
            return
        if item is not None:
            self.data_table.blockSignals(True)
            try:
                self._set_item_numeric_sort_value(item, item.text())
            finally:
                self.data_table.blockSignals(False)
        self._update_model_field("data", self._collect_table_data())

    def add_data_row(self):
        if self._updating:
            return
        row_index = self.data_table.rowCount()
        self.data_table.insertRow(row_index)
        self.data_table.setItem(row_index, 0, self._make_numeric_item(""))
        self.data_table.setItem(row_index, 1, self._make_numeric_item(""))
        self.data_table.setItem(row_index, 2, self._make_numeric_item(""))
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
            ux_item = self.data_table.item(row, 1)
            y_item = self.data_table.item(row, 2)
            x_text = x_item.text().strip() if x_item else ""
            ux_text = ux_item.text().strip() if ux_item else ""
            y_text = y_item.text().strip() if y_item else ""
            data.append({
                "x": self._convert_number(x_text),
                "ux": self._convert_number(ux_text),
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

    @staticmethod
    def _parse_float(value):
        try:
            if value is None:
                return None
            if isinstance(value, (int, float)):
                return float(value)
            value_str = str(value).strip()
            if value_str == "":
                return None
            return float(value_str)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _set_readonly_item(item):
        item.setFlags(item.flags() & ~Qt.ItemIsEditable)

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
        # データが変更された場合は計算結果を更新
        if field in {"data"}:
            self._update_regression_result(model)
    
    def _update_regression_result(self, model):
        """回帰計算結果を更新"""
        try:
            slope_value = None
            residual_variance = None
            sxx = None
            data_count = None
            params = calculate_linear_regression_parameters(model)
            if params:
                slope, intercept, residual_std, degrees_of_freedom, data_count = params
                slope_value = slope
                u_beta_value = None
                ux_average_value = None
                uy_average_value = None
                # 切片α（intercept）を表示
                self.intercept_display.setText(f"{intercept:.12g}")
                # 傾きβ（slope）を表示
                self.slope_display.setText(f"{slope:.12g}")
                significance_f = calculate_significance_f(model, slope=slope, intercept=intercept)
                if significance_f is None:
                    self.significance_f_display.setText("--")
                else:
                    self.significance_f_display.setText(f"{significance_f:.12g}")
                residual_variance = residual_std ** 2
                self.residual_variance_display.setText(f"{residual_std:.12g}")
                sxx, x_mean_sxx, count_sxx = calculate_regression_sxx(model)
                if sxx is None or sxx == 0:
                    self.u_beta_display.setText("--")
                else:
                    u_beta = math.sqrt(residual_variance / sxx)
                    self.u_beta_display.setText(f"{u_beta:.12g}")
                    u_beta_value = u_beta
                ux_average = calculate_value_average(model, "ux")
                if ux_average is None:
                    self.ux_average_display.setText("--")
                else:
                    self.ux_average_display.setText(f"{ux_average:.12g}")
                    ux_average_value = ux_average
                if data_count:
                    uy_average = math.sqrt(residual_variance / data_count)
                    self.uy_average_display.setText(f"{uy_average:.12g}")
                    uy_average_value = uy_average
                else:
                    self.uy_average_display.setText("--")
            else:
                self.intercept_display.setText("--")
                self.slope_display.setText("--")
                self.u_beta_display.setText("--")
                self.significance_f_display.setText("--")
                self.residual_variance_display.setText("--")
                self.ux_average_display.setText("--")
                self.uy_average_display.setText("--")
            x_mean, y_mean = calculate_xy_averages(model)
            if x_mean is None:
                self.x_average_display.setText("--")
            else:
                self.x_average_display.setText(f"{x_mean:.12g}")
            if y_mean is None:
                self.y_average_display.setText("--")
            else:
                self.y_average_display.setText(f"{y_mean:.12g}")
            self._update_inverse_estimation(
                model,
                slope_value,
                u_beta=u_beta_value,
                ux_average=ux_average_value,
                uy_average=uy_average_value,
            )
        except Exception as e:
            log_error(f"回帰計算結果更新エラー: {str(e)}")
            self.intercept_display.setText("--")
            self.slope_display.setText("--")
            self.u_beta_display.setText("--")
            self.significance_f_display.setText("--")
            self.residual_variance_display.setText("--")
            self.x_average_display.setText("--")
            self.y_average_display.setText("--")
            self.ux_average_display.setText("--")
            self.uy_average_display.setText("--")
            self._update_inverse_estimation(model, None)

    def _update_inverse_estimation(self, model, slope, u_beta=None, ux_average=None, uy_average=None):
        x_mean, y_mean = calculate_xy_averages(model)
        self._inverse_slope = slope
        self._inverse_x_mean = x_mean
        self._inverse_y_mean = y_mean
        self._inverse_u_beta = u_beta
        self._inverse_ux_average = ux_average
        self._inverse_uy_average = uy_average
        self._update_inverse_table()

    def _update_inverse_table(self):
        self._updating = True
        try:
            for row in range(self.inverse_table.rowCount()):
                self._ensure_inverse_row_items(row)
                y0_item = self.inverse_table.item(row, 0)
                x0_item = self.inverse_table.item(row, 1)
                ux0_item = self.inverse_table.item(row, 2)
                y0_value = self._parse_float(y0_item.text() if y0_item else "")
                x0_value = self._calculate_inverse_x0(y0_value)
                ux0_value = self._calculate_inverse_ux0(y0_value)
                x0_text = "--" if x0_value is None else f"{x0_value:.12g}"
                x0_item.setText(x0_text)
                self._set_item_numeric_sort_value(x0_item, x0_text)
                if ux0_item is None:
                    ux0_item = self._make_numeric_item("--", readonly=True)
                    self.inverse_table.setItem(row, 2, ux0_item)
                ux0_text = "--" if ux0_value is None else f"{ux0_value:.12g}"
                ux0_item.setText(ux0_text)
                self._set_item_numeric_sort_value(ux0_item, ux0_text)
        finally:
            self._updating = False

    def _calculate_inverse_x0(self, y0_value):
        x_mean = getattr(self, "_inverse_x_mean", None)
        y_mean = getattr(self, "_inverse_y_mean", None)
        slope = getattr(self, "_inverse_slope", None)
        if y0_value is None or slope in (None, 0) or x_mean is None or y_mean is None:
            return None
        return ((y0_value - y_mean) / slope) + x_mean

    def _calculate_inverse_ux0(self, y0_value):
        y_mean = getattr(self, "_inverse_y_mean", None)
        slope = getattr(self, "_inverse_slope", None)
        u_beta = getattr(self, "_inverse_u_beta", None)
        ux_average = getattr(self, "_inverse_ux_average", None)
        uy_average = getattr(self, "_inverse_uy_average", None)
        if (
            y0_value is None
            or slope in (None, 0)
            or y_mean is None
            or u_beta is None
            or ux_average is None
            or uy_average is None
        ):
            return None
        term_uy = (uy_average ** 2) / (slope ** 2)
        term_beta = ((y0_value - y_mean) ** 2) * (u_beta ** 2) / (slope ** 4)
        term_ux = ux_average ** 2
        variance = term_uy + term_beta + term_ux
        if variance < 0:
            return None
        return math.sqrt(variance)

    def _ensure_inverse_row_items(self, row):
        y0_item = self.inverse_table.item(row, 0)
        if y0_item is None:
            y0_item = self._make_numeric_item("")
            self.inverse_table.setItem(row, 0, y0_item)
        x0_item = self.inverse_table.item(row, 1)
        if x0_item is None:
            x0_item = self._make_numeric_item("--", readonly=True)
            self.inverse_table.setItem(row, 1, x0_item)
        ux0_item = self.inverse_table.item(row, 2)
        if ux0_item is None:
            ux0_item = self._make_numeric_item("--", readonly=True)
            self.inverse_table.setItem(row, 2, ux0_item)

    def on_inverse_table_changed(self, item):
        if self._updating or item.column() != 0:
            return
        self.inverse_table.blockSignals(True)
        try:
            self._set_item_numeric_sort_value(item, item.text())
        finally:
            self.inverse_table.blockSignals(False)
        x0_item = self.inverse_table.item(item.row(), 1)
        ux0_item = self.inverse_table.item(item.row(), 2)
        if x0_item is None or ux0_item is None:
            return
        y0_value = self._parse_float(item.text())
        x0_value = self._calculate_inverse_x0(y0_value)
        ux0_value = self._calculate_inverse_ux0(y0_value)
        self._updating = True
        try:
            x0_text = "--" if x0_value is None else f"{x0_value:.12g}"
            ux0_text = "--" if ux0_value is None else f"{ux0_value:.12g}"
            x0_item.setText(x0_text)
            ux0_item.setText(ux0_text)
            self._set_item_numeric_sort_value(x0_item, x0_text)
            self._set_item_numeric_sort_value(ux0_item, ux0_text)
        finally:
            self._updating = False
        self._update_inverse_model_data()

    def add_inverse_row(self):
        if self._updating:
            return
        row_index = self.inverse_table.rowCount()
        self.inverse_table.insertRow(row_index)
        self._ensure_inverse_row_items(row_index)
        self._update_inverse_model_data()

    def remove_inverse_row(self):
        if self._updating:
            return
        current_row = self.inverse_table.currentRow()
        if current_row < 0:
            current_row = self.inverse_table.rowCount() - 1
        if current_row < 0:
            return
        self.inverse_table.removeRow(current_row)
        self._update_inverse_model_data()

    def _collect_inverse_y0s(self):
        values = []
        for row in range(self.inverse_table.rowCount()):
            item = self.inverse_table.item(row, 0)
            text = item.text().strip() if item else ""
            values.append(self._convert_number(text))
        return values

    def _update_inverse_model_data(self):
        if self._updating or not self.current_model_name:
            return
        regressions = getattr(self.parent, "regressions", {})
        model = regressions.get(self.current_model_name)
        if not isinstance(model, dict):
            return
        model["inverse_y0s"] = self._collect_inverse_y0s()
        regressions[self.current_model_name] = model
        self.parent.regressions = regressions

    def _set_inverse_label_texts(self):
        if not hasattr(self, "inverse_table"):
            return
        self.inverse_table.setHorizontalHeaderLabels(
            [self.tr(REGRESSION_Y0), self.tr(REGRESSION_X0), self.tr(REGRESSION_UX0)]
        )

    def _notify_regressions_updated(self):
        if hasattr(self.parent, "variables_tab"):
            self.parent.variables_tab.update_regression_model_options()

    def copy_model(self):
        """回帰モデルを複製"""
        current_item = self.model_list.currentItem()
        if not current_item:
            return
        original_name = current_item.text()
        regressions = getattr(self.parent, "regressions", {})
        original_model = regressions.get(original_name)
        if not isinstance(original_model, dict):
            return
        
        # 新しい名前を生成
        base_name = original_name
        counter = 1
        new_name = f"{base_name}_copy{counter}"
        while new_name in regressions:
            counter += 1
            new_name = f"{base_name}_copy{counter}"
        
        # モデルを複製
        import copy
        regressions[new_name] = copy.deepcopy(original_model)
        self.parent.regressions = regressions
        self.refresh_model_list()
        items = self.model_list.findItems(new_name, Qt.MatchExactly)
        if items:
            self.model_list.setCurrentItem(items[0])
        self._notify_regressions_updated()

    def import_csv_data(self):
        """CSV形式でデータをインポート"""
        if not self.current_model_name:
            QMessageBox.information(self, self.tr(MESSAGE_INFO), self.tr(REGRESSION_SELECT_MODEL_FIRST))
            return
        
        dialog = QDialog(self)
        dialog.setWindowTitle(self.tr(REGRESSION_IMPORT_CSV))
        layout = QVBoxLayout()
        
        label = QLabel(self.tr(REGRESSION_CSV_INSTRUCTION))
        layout.addWidget(label)
        
        text_edit = QTextEdit()
        text_edit.setPlaceholderText("x, u(x), y\nまたは\nx, y")
        layout.addWidget(text_edit)
        
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        
        dialog.setLayout(layout)
        
        if dialog.exec_() == QDialog.Accepted:
            csv_text = text_edit.toPlainText().strip()
            if not csv_text:
                return
            
            try:
                lines = csv_text.split('\n')
                new_data = []
                for line in lines:
                    line = line.strip()
                    if not line:
                        continue
                    parts = [p.strip() for p in line.split(',')]
                    if len(parts) < 2:
                        continue
                    try:
                        x_val = float(parts[0])
                        if len(parts) >= 3:
                            ux_val = float(parts[1])
                            y_val = float(parts[2])
                            new_data.append({"x": x_val, "ux": ux_val, "y": y_val})
                        else:
                            y_val = float(parts[1])
                            new_data.append({"x": x_val, "y": y_val})
                    except ValueError:
                        QMessageBox.warning(self, self.tr(MESSAGE_WARNING), 
                                          self.tr(REGRESSION_CSV_PARSE_ERROR).format(line=line))
                        return
                
                if len(new_data) < 2:
                    QMessageBox.warning(self, self.tr(MESSAGE_WARNING), 
                                      self.tr(REGRESSION_CSV_MIN_DATA_POINTS))
                    return
                
                # データを設定
                regressions = getattr(self.parent, "regressions", {})
                model = regressions.get(self.current_model_name)
                if isinstance(model, dict):
                    model["data"] = new_data
                    regressions[self.current_model_name] = model
                    self.parent.regressions = regressions
                    self._populate_data_table(new_data)
                    self._notify_regressions_updated()
                    QMessageBox.information(self, self.tr(MESSAGE_SUCCESS), 
                                          self.tr(REGRESSION_CSV_IMPORT_SUCCESS))
            except Exception as e:
                QMessageBox.critical(self, self.tr(MESSAGE_ERROR), 
                                   f"{self.tr(REGRESSION_CSV_IMPORT_ERROR)}: {str(e)}")

    def showEvent(self, event):
        self.refresh_model_list()
        super().showEvent(event)
