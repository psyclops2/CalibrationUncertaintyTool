from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QBrush
from PySide6.QtWidgets import QGroupBox, QLabel, QTableWidget, QTableWidgetItem, QVBoxLayout, QHeaderView, QMessageBox

from .base_tab import BaseTab
from ..utils.translation_keys import *


class CorrelationTab(BaseTab):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self._updating_table = False
        self._input_variables = []
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()

        self.matrix_group = QGroupBox(self.tr(CORRELATION_MATRIX_INPUT))
        group_layout = QVBoxLayout()

        self.description_label = QLabel(self.tr(CORRELATION_MATRIX_DESCRIPTION))
        self.description_label.setWordWrap(True)
        group_layout.addWidget(self.description_label)

        self.matrix_table = QTableWidget()
        self.matrix_table.setEditTriggers(QTableWidget.DoubleClicked | QTableWidget.EditKeyPressed)
        self.matrix_table.setSelectionBehavior(QTableWidget.SelectItems)
        self.matrix_table.horizontalHeader().setStretchLastSection(False)
        self.matrix_table.horizontalHeader().setSectionResizeMode(QHeaderView.Fixed)
        self.matrix_table.horizontalHeader().setDefaultSectionSize(72)
        self.matrix_table.horizontalHeader().setMinimumSectionSize(72)
        self.matrix_table.verticalHeader().setDefaultSectionSize(28)
        self.matrix_table.setStyleSheet(
            "QHeaderView::section { background-color: #eeeeee; }"
        )
        self.matrix_table.itemChanged.connect(self._on_item_changed)
        group_layout.addWidget(self.matrix_table)

        self.empty_label = QLabel(self.tr(CORRELATION_NO_INPUT_VARIABLES))
        self.empty_label.setAlignment(Qt.AlignCenter)
        group_layout.addWidget(self.empty_label)

        self.matrix_group.setLayout(group_layout)
        layout.addWidget(self.matrix_group)
        self.setLayout(layout)

        self.refresh_matrix()

    def retranslate_ui(self):
        self.matrix_group.setTitle(self.tr(CORRELATION_MATRIX_INPUT))
        self.description_label.setText(self.tr(CORRELATION_MATRIX_DESCRIPTION))
        self.empty_label.setText(self.tr(CORRELATION_NO_INPUT_VARIABLES))

    def _get_input_variables(self):
        variables = getattr(self.parent, "variables", [])
        result_variables = set(getattr(self.parent, "result_variables", []))
        return [var_name for var_name in variables if var_name not in result_variables]

    def _ensure_default_matrix(self, input_variables):
        existing_matrix = getattr(self.parent, "correlation_coefficients", {})
        if not isinstance(existing_matrix, dict):
            existing_matrix = {}

        normalized_matrix = {}
        for row_var in input_variables:
            row_data = existing_matrix.get(row_var, {})
            if not isinstance(row_data, dict):
                row_data = {}
            normalized_matrix[row_var] = {}
            for col_var in input_variables:
                if row_var == col_var:
                    normalized_matrix[row_var][col_var] = 1.0
                    continue

                value = row_data.get(col_var, None)
                if value is None:
                    reverse_data = existing_matrix.get(col_var, {})
                    if isinstance(reverse_data, dict):
                        value = reverse_data.get(row_var, 0.0)
                    else:
                        value = 0.0
                try:
                    normalized_matrix[row_var][col_var] = float(value)
                except (TypeError, ValueError):
                    normalized_matrix[row_var][col_var] = 0.0

        for row_index, row_var in enumerate(input_variables):
            for col_var in input_variables[row_index + 1:]:
                symmetric_value = normalized_matrix[row_var][col_var]
                normalized_matrix[col_var][row_var] = symmetric_value

        self.parent.correlation_coefficients = normalized_matrix
        return normalized_matrix

    def refresh_matrix(self):
        self._updating_table = True
        input_variables = self._get_input_variables()
        self._input_variables = input_variables
        matrix = self._ensure_default_matrix(input_variables)

        has_inputs = len(input_variables) > 0
        self.matrix_table.setVisible(has_inputs)
        self.empty_label.setVisible(not has_inputs)

        if not has_inputs:
            self.matrix_table.clear()
            self.matrix_table.setRowCount(0)
            self.matrix_table.setColumnCount(0)
            self._updating_table = False
            return

        self.matrix_table.setRowCount(len(input_variables))
        self.matrix_table.setColumnCount(len(input_variables))
        self.matrix_table.setHorizontalHeaderLabels(input_variables)
        self.matrix_table.setVerticalHeaderLabels(input_variables)
        for column_index in range(len(input_variables)):
            self.matrix_table.setColumnWidth(column_index, 72)

        for row_index, row_var in enumerate(input_variables):
            for col_index, col_var in enumerate(input_variables):
                value = matrix[row_var][col_var]
                item = QTableWidgetItem(f"{value:g}")
                item.setTextAlignment(Qt.AlignCenter)
                base_flags = Qt.ItemIsEnabled | Qt.ItemIsSelectable
                if col_index > row_index:
                    item.setFlags(base_flags | Qt.ItemIsEditable)
                    item.setBackground(QBrush(QColor("#ffffff")))
                    item.setForeground(QBrush(QColor("#000000")))
                else:
                    item.setFlags(base_flags)
                    item.setBackground(QBrush(QColor("#7a7a7a")))
                    item.setForeground(QBrush(QColor("#ffffff")))
                self.matrix_table.setItem(row_index, col_index, item)
        self._updating_table = False

    def _on_item_changed(self, item):
        if self._updating_table:
            return

        row_index = item.row()
        col_index = item.column()
        if row_index < 0 or col_index < 0:
            return
        if row_index >= len(self._input_variables) or col_index >= len(self._input_variables):
            return

        row_var = self._input_variables[row_index]
        col_var = self._input_variables[col_index]
        matrix = getattr(self.parent, "correlation_coefficients", {})
        if not isinstance(matrix, dict):
            matrix = {}

        self._updating_table = True
        try:
            if row_index == col_index:
                item.setText("1")
                return

            if col_index < row_index:
                mirror_item = self.matrix_table.item(col_index, row_index)
                mirror_text = mirror_item.text() if mirror_item is not None else "0"
                item.setText(mirror_text)
                return

            try:
                value = float(item.text())
            except (TypeError, ValueError):
                value = matrix.get(row_var, {}).get(col_var, 0.0)
                item.setText(f"{float(value):g}")
                return

            if value > 1 or value < -1:
                previous_value = matrix.get(row_var, {}).get(col_var, 0.0)
                QMessageBox.warning(
                    self,
                    self.tr(MESSAGE_WARNING),
                    self.tr(CORRELATION_VALUE_MAX_ERROR),
                )
                item.setText(f"{float(previous_value):g}")
                return

            matrix.setdefault(row_var, {})
            matrix.setdefault(col_var, {})
            matrix[row_var][col_var] = value
            matrix[col_var][row_var] = value
            self.parent.correlation_coefficients = matrix

            item.setText(f"{value:g}")
            mirror_item = self.matrix_table.item(col_index, row_index)
            if mirror_item is not None:
                mirror_item.setText(f"{value:g}")
        finally:
            self._updating_table = False
