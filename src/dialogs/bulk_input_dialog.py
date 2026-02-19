from decimal import Decimal, InvalidOperation

from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

from src.utils.translation_keys import (
    BULK_INPUT_APPLY,
    BULK_INPUT_CANCEL,
    BULK_INPUT_DIALOG_TITLE,
    BULK_INPUT_FIXED_VALUE_ROW,
    BULK_INPUT_INVALID_NUMBER,
    BULK_INPUT_INVALID_NUMBER_TITLE,
    BULK_INPUT_MODE_HINT,
    BULK_INPUT_ROW_CENTRAL_VALUE,
    BULK_INPUT_ROW_DISTRIBUTION,
    BULK_INPUT_ROW_HALF_WIDTH,
    NORMAL_DISTRIBUTION,
    RECTANGULAR_DISTRIBUTION,
    TRIANGULAR_DISTRIBUTION,
    U_DISTRIBUTION,
)
from src.utils.variable_utils import (
    create_empty_value_dict,
    get_distribution_divisor,
    get_distribution_translation_key,
)


class BulkInputDialog(QDialog):
    def __init__(self, main_window, parent=None):
        super().__init__(parent or main_window)
        self.main_window = main_window
        self._row_specs = []
        self._original_values = {}

        self.setMinimumSize(1000, 620)
        self._build_ui()
        self.retranslate_ui()
        self._load_from_model()

    def _build_ui(self):
        root = QVBoxLayout(self)

        header_layout = QHBoxLayout()
        self.hint_label = QLabel(self)
        header_layout.addWidget(self.hint_label)
        header_layout.addStretch()
        root.addLayout(header_layout)

        self.table = QTableWidget(self)
        root.addWidget(self.table)

        self.button_box = QDialogButtonBox(self)
        self.apply_button = self.button_box.addButton(QDialogButtonBox.Save)
        self.cancel_button = self.button_box.addButton(QDialogButtonBox.Cancel)
        self.apply_button.clicked.connect(self._on_apply_clicked)
        self.cancel_button.clicked.connect(self.reject)
        root.addWidget(self.button_box)

    def retranslate_ui(self):
        self.setWindowTitle(self.tr(BULK_INPUT_DIALOG_TITLE))
        self.hint_label.setText(self.tr(BULK_INPUT_MODE_HINT))
        self.apply_button.setText(self.tr(BULK_INPUT_APPLY))
        self.cancel_button.setText(self.tr(BULK_INPUT_CANCEL))

    def _distribution_options(self):
        return [
            (NORMAL_DISTRIBUTION, self.tr(NORMAL_DISTRIBUTION)),
            (RECTANGULAR_DISTRIBUTION, self.tr(RECTANGULAR_DISTRIBUTION)),
            (TRIANGULAR_DISTRIBUTION, self.tr(TRIANGULAR_DISTRIBUTION)),
            (U_DISTRIBUTION, self.tr(U_DISTRIBUTION)),
        ]

    def _build_row_specs(self):
        row_specs = []
        ordered_variables = list(dict.fromkeys(self.main_window.result_variables + self.main_window.variables))
        result_set = set(self.main_window.result_variables)
        for var_name in ordered_variables:
            if var_name in result_set:
                continue
            self.main_window.ensure_variable_initialized(var_name, is_result=False)
            var_info = self.main_window.variable_values.get(var_name, {})
            value_type = var_info.get("type", "A")
            if value_type == "B":
                row_specs.append(
                    {
                        "variable": var_name,
                        "value_type": "B",
                        "field": "central_value",
                        "label_key": BULK_INPUT_ROW_CENTRAL_VALUE,
                    }
                )
                row_specs.append(
                    {
                        "variable": var_name,
                        "value_type": "B",
                        "field": "half_width",
                        "label_key": BULK_INPUT_ROW_HALF_WIDTH,
                    }
                )
                row_specs.append(
                    {
                        "variable": var_name,
                        "value_type": "B",
                        "field": "distribution",
                        "label_key": BULK_INPUT_ROW_DISTRIBUTION,
                    }
                )
            elif value_type == "fixed":
                row_specs.append(
                    {
                        "variable": var_name,
                        "value_type": "fixed",
                        "field": "central_value",
                        "label_key": BULK_INPUT_FIXED_VALUE_ROW,
                    }
                )
        return row_specs

    def _row_header_text(self, spec):
        return f"{spec['variable']} {self.tr(spec['label_key'])}"

    def _load_from_model(self):
        value_names = list(getattr(self.main_window, "value_names", []))
        self._row_specs = self._build_row_specs()
        self._original_values = {}

        self.table.clear()
        self.table.setRowCount(len(self._row_specs))
        self.table.setColumnCount(len(value_names))
        self.table.setHorizontalHeaderLabels(value_names)
        self.table.setVerticalHeaderLabels([self._row_header_text(spec) for spec in self._row_specs])

        for row_index, spec in enumerate(self._row_specs):
            var_name = spec["variable"]
            var_info = self.main_window.variable_values.get(var_name, {})
            values = var_info.get("values", [])
            distribution = get_distribution_translation_key(var_info.get("distribution", NORMAL_DISTRIBUTION))
            if not distribution:
                distribution = NORMAL_DISTRIBUTION
            for col_index, _point_name in enumerate(value_names):
                value_info = values[col_index] if col_index < len(values) and isinstance(values[col_index], dict) else {}
                key = (row_index, col_index)
                if spec["field"] == "distribution":
                    combo = QComboBox(self.table)
                    for code, label in self._distribution_options():
                        combo.addItem(label, code)
                    row_distribution = distribution
                    combo_index = combo.findData(row_distribution)
                    if combo_index < 0:
                        combo_index = 0
                    combo.setCurrentIndex(combo_index)
                    self.table.setCellWidget(row_index, col_index, combo)
                    self._original_values[key] = row_distribution
                else:
                    value = value_info.get(spec["field"], "")
                    text = "" if value is None else str(value)
                    self.table.setItem(row_index, col_index, QTableWidgetItem(text))
                    self._original_values[key] = text

        self.table.resizeColumnsToContents()

    def _cell_text(self, row_index, col_index):
        item = self.table.item(row_index, col_index)
        if item is None:
            return ""
        return item.text().strip()

    def _cell_distribution(self, row_index, col_index):
        widget = self.table.cellWidget(row_index, col_index)
        if not isinstance(widget, QComboBox):
            return NORMAL_DISTRIBUTION
        data = widget.currentData()
        if not data:
            return NORMAL_DISTRIBUTION
        return data

    def _parse_decimal_or_raise(self, text, row_label, point_name):
        try:
            return Decimal(text)
        except (InvalidOperation, ValueError):
            raise ValueError(
                self.tr(BULK_INPUT_INVALID_NUMBER).format(
                    row_label=row_label,
                    point_name=point_name,
                    value=text,
                )
            )

    def _ensure_values(self, var_info):
        values = var_info.get("values", [])
        if not isinstance(values, list):
            values = []
        required = max(1, len(getattr(self.main_window, "value_names", [])))
        while len(values) < required:
            values.append(create_empty_value_dict())
        var_info["values"] = values
        return values

    def _apply_to_model(self):
        value_names = list(getattr(self.main_window, "value_names", []))
        if not value_names:
            return

        for row_index, spec in enumerate(self._row_specs):
            var_name = spec["variable"]
            var_info = self.main_window.variable_values.get(var_name, {})
            values = self._ensure_values(var_info)

            for col_index, point_name in enumerate(value_names):
                value_info = values[col_index]
                key = (row_index, col_index)

                if spec["field"] == "distribution":
                    new_distribution = self._cell_distribution(row_index, col_index)
                    old_distribution = self._original_values.get(key, NORMAL_DISTRIBUTION)
                    if new_distribution != old_distribution:
                        var_info["distribution"] = new_distribution
                        value_info["degrees_of_freedom"] = "inf"
                        if new_distribution == NORMAL_DISTRIBUTION:
                            value_info["divisor"] = "2"
                        else:
                            divisor = get_distribution_divisor(new_distribution) or ""
                            value_info["divisor"] = str(divisor)
                        var_info["divisor"] = value_info.get("divisor", "")
                    continue

                new_text = self._cell_text(row_index, col_index)
                old_text = self._original_values.get(key, "")

                if not new_text:
                    continue
                if new_text == old_text:
                    continue

                row_label = self._row_header_text(spec)
                self._parse_decimal_or_raise(new_text, row_label, point_name)
                value_info[spec["field"]] = new_text

                if spec["value_type"] != "B":
                    continue

                value_info["degrees_of_freedom"] = "inf"
                distribution = get_distribution_translation_key(
                    var_info.get("distribution", NORMAL_DISTRIBUTION)
                ) or NORMAL_DISTRIBUTION
                if distribution == NORMAL_DISTRIBUTION:
                    divisor = "2"
                else:
                    divisor = str(get_distribution_divisor(distribution) or "")
                value_info["divisor"] = divisor
                var_info["divisor"] = divisor

                half_width = str(value_info.get("half_width", "")).strip()
                if half_width and divisor:
                    half_width_dec = self._parse_decimal_or_raise(half_width, row_label, point_name)
                    divisor_dec = self._parse_decimal_or_raise(str(divisor), row_label, point_name)
                    if divisor_dec != 0:
                        value_info["standard_uncertainty"] = str(half_width_dec / divisor_dec)

            self.main_window.variable_values[var_name] = var_info

    def _on_apply_clicked(self):
        try:
            self._apply_to_model()
            self.accept()
        except ValueError as exc:
            QMessageBox.warning(self, self.tr(BULK_INPUT_INVALID_NUMBER_TITLE), str(exc))
