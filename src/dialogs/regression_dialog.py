import csv
import io
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QComboBox,
    QCheckBox, QTextEdit, QPushButton, QMessageBox, QFormLayout
)
from PySide6.QtCore import Qt
from ..utils.translation_keys import *


class RegressionDialog(QDialog):
    def __init__(self, parent=None, regression_id="", regression_data=None, existing_ids=None):
        super().__init__(parent)
        self.existing_ids = set(existing_ids or [])
        self.original_id = regression_id
        self.result_data = None
        self.setWindowTitle(self.tr(REGRESSION_DIALOG_TITLE))
        self._setup_ui()
        self._load_data(regression_id, regression_data or {})

    def _setup_ui(self):
        layout = QVBoxLayout()
        form_layout = QFormLayout()

        self.regression_id_input = QLineEdit()
        self.description_input = QLineEdit()

        self.mode_combo = QComboBox()
        self.mode_combo.addItem("time")
        self.mode_combo.addItem("generic")

        self.x_unit_input = QLineEdit()
        self.y_unit_input = QLineEdit()

        self.use_weights_check = QCheckBox(self.tr(REGRESSION_USE_WEIGHTS))
        self.invert_check = QCheckBox(self.tr(REGRESSION_INVERT))

        self.data_input = QTextEdit()
        self.data_input.setAcceptRichText(False)
        self.data_input.setPlaceholderText(self.tr(REGRESSION_DATA_PLACEHOLDER))
        self.data_input.setMinimumHeight(160)

        form_layout.addRow(self.tr(REGRESSION_ID), self.regression_id_input)
        form_layout.addRow(self.tr(REGRESSION_DESCRIPTION), self.description_input)
        form_layout.addRow(self.tr(REGRESSION_MODE), self.mode_combo)
        form_layout.addRow(self.tr(REGRESSION_X_UNIT), self.x_unit_input)
        form_layout.addRow(self.tr(REGRESSION_Y_UNIT), self.y_unit_input)
        form_layout.addRow("", self.use_weights_check)
        form_layout.addRow("", self.invert_check)
        form_layout.addRow(self.tr(REGRESSION_DATA), self.data_input)

        layout.addLayout(form_layout)

        button_layout = QHBoxLayout()
        self.ok_button = QPushButton(self.tr(BUTTON_SAVE))
        self.cancel_button = QPushButton(self.tr(BUTTON_CANCEL))
        self.ok_button.clicked.connect(self._on_accept)
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addStretch()
        button_layout.addWidget(self.ok_button)
        button_layout.addWidget(self.cancel_button)
        layout.addLayout(button_layout)

        self.setLayout(layout)

    def _load_data(self, regression_id, regression_data):
        self.regression_id_input.setText(regression_id)
        self.description_input.setText(regression_data.get("description", ""))
        mode = regression_data.get("mode", "generic")
        mode_index = self.mode_combo.findText(mode)
        if mode_index >= 0:
            self.mode_combo.setCurrentIndex(mode_index)
        self.x_unit_input.setText(regression_data.get("x_unit", ""))
        self.y_unit_input.setText(regression_data.get("y_unit", ""))
        self.use_weights_check.setChecked(bool(regression_data.get("use_weights", False)))
        self.invert_check.setChecked(bool(regression_data.get("invert", False)))

        rows = []
        for item in regression_data.get("data", []):
            if not isinstance(item, dict):
                continue
            x_val = item.get("x", "")
            y_val = item.get("y", "")
            ux_val = item.get("ux")
            uy_val = item.get("uy")
            if ux_val is not None or uy_val is not None:
                rows.append(f"{x_val}, {y_val}, {ux_val or ''}, {uy_val or ''}")
            else:
                rows.append(f"{x_val}, {y_val}")
        self.data_input.setPlainText("\n".join(rows))

    def _parse_data(self):
        text = self.data_input.toPlainText().strip()
        if not text:
            return []

        data = []
        reader = csv.reader(io.StringIO(text))
        for row_index, row in enumerate(reader, start=1):
            if not any(cell.strip() for cell in row):
                continue
            if len(row) not in (2, 4):
                raise ValueError(self.tr(REGRESSION_PARSE_ERROR).format(row=row_index))
            try:
                x_val = float(row[0].strip())
                y_val = float(row[1].strip())
            except ValueError as exc:
                raise ValueError(self.tr(REGRESSION_PARSE_ERROR).format(row=row_index)) from exc
            entry = {"x": x_val, "y": y_val}
            if len(row) == 4:
                ux_text = row[2].strip()
                uy_text = row[3].strip()
                if ux_text:
                    entry["ux"] = float(ux_text)
                if uy_text:
                    entry["uy"] = float(uy_text)
            data.append(entry)

        if len(data) < 2:
            raise ValueError(self.tr(REGRESSION_INVALID_DATA))
        return data

    def _on_accept(self):
        regression_id = self.regression_id_input.text().strip()
        if not regression_id:
            QMessageBox.warning(self, self.tr(MESSAGE_ERROR), self.tr(REGRESSION_ID_REQUIRED))
            return

        if regression_id != self.original_id and regression_id in self.existing_ids:
            QMessageBox.warning(self, self.tr(MESSAGE_ERROR), self.tr(REGRESSION_DUPLICATE_ID))
            return

        try:
            data = self._parse_data()
        except ValueError as exc:
            QMessageBox.warning(self, self.tr(MESSAGE_ERROR), str(exc))
            return

        self.result_data = {
            "id": regression_id,
            "description": self.description_input.text().strip(),
            "mode": self.mode_combo.currentText().strip(),
            "x_unit": self.x_unit_input.text().strip(),
            "y_unit": self.y_unit_input.text().strip(),
            "use_weights": self.use_weights_check.isChecked(),
            "invert": self.invert_check.isChecked(),
            "data": data,
        }
        self.accept()

    def get_result(self):
        return self.result_data
