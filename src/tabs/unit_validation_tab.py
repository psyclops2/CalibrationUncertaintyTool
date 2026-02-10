from __future__ import annotations

from PySide6.QtCore import Qt, Slot
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

from src.tabs.base_tab import BaseTab
from src.utils.unit_validator import (
    STATUS_ERROR,
    STATUS_OK,
    STATUS_WARN,
    render_dimension,
    validate_main_window_units,
)


class UnitValidationTab(BaseTab):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setup_ui()

    def setup_ui(self):
        root_layout = QVBoxLayout(self)

        controls_layout = QHBoxLayout()
        self.summary_label = QLabel("")
        self.refresh_button = QPushButton("")
        self.refresh_button.clicked.connect(self.refresh)
        controls_layout.addWidget(self.summary_label)
        controls_layout.addStretch(1)
        controls_layout.addWidget(self.refresh_button)
        root_layout.addLayout(controls_layout)

        self.variable_group = QGroupBox("")
        variable_layout = QVBoxLayout()
        self.variable_table = QTableWidget()
        self.variable_table.setColumnCount(5)
        self.variable_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.variable_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.variable_table.setSelectionMode(QTableWidget.SingleSelection)
        self.variable_table.setAlternatingRowColors(True)
        self.variable_table.verticalHeader().setVisible(False)
        variable_layout.addWidget(self.variable_table)
        self.variable_group.setLayout(variable_layout)
        root_layout.addWidget(self.variable_group)

        self.equation_group = QGroupBox("")
        equation_layout = QVBoxLayout()
        self.equation_table = QTableWidget()
        self.equation_table.setColumnCount(5)
        self.equation_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.equation_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.equation_table.setSelectionMode(QTableWidget.SingleSelection)
        self.equation_table.setAlternatingRowColors(True)
        self.equation_table.verticalHeader().setVisible(False)
        equation_layout.addWidget(self.equation_table)
        self.equation_group.setLayout(equation_layout)
        root_layout.addWidget(self.equation_group)

        self.retranslate_ui()

    def retranslate_ui(self):
        self.refresh_button.setText(self._t("検証実行", "Validate"))
        self.variable_group.setTitle(self._t("変数単位", "Variable Units"))
        self.equation_group.setTitle(self._t("式整合性", "Equation Consistency"))
        self.variable_table.setHorizontalHeaderLabels(
            [
                self._t("変数", "Variable"),
                self._t("単位", "Unit"),
                self._t("次元", "Dimension"),
                self._t("判定", "Status"),
                self._t("メッセージ", "Message"),
            ]
        )
        self.equation_table.setHorizontalHeaderLabels(
            [
                self._t("式", "Equation"),
                self._t("左辺次元", "LHS Dimension"),
                self._t("右辺次元", "RHS Dimension"),
                self._t("判定", "Status"),
                self._t("メッセージ", "Message"),
            ]
        )
        self._set_summary_text(0, 0, 0)

    @Slot()
    def refresh(self):
        report = validate_main_window_units(self.parent)
        self._fill_variable_table(report.variable_items)
        self._fill_equation_table(report.equation_items)
        self._set_summary_text(report.ok_count, report.warn_count, report.error_count)

    def _fill_variable_table(self, items):
        self.variable_table.setRowCount(len(items))
        for row, item in enumerate(items):
            self._set_table_item(self.variable_table, row, 0, item.name)
            self._set_table_item(self.variable_table, row, 1, item.unit or "-")
            self._set_table_item(self.variable_table, row, 2, render_dimension(item.dimension))
            self._set_table_item(self.variable_table, row, 3, item.status)
            self._set_table_item(self.variable_table, row, 4, item.message)
        self.variable_table.resizeColumnsToContents()

    def _fill_equation_table(self, items):
        self.equation_table.setRowCount(len(items))
        for row, item in enumerate(items):
            self._set_table_item(self.equation_table, row, 0, item.equation or "-")
            self._set_table_item(self.equation_table, row, 1, render_dimension(item.lhs_dimension))
            self._set_table_item(self.equation_table, row, 2, render_dimension(item.rhs_dimension))
            self._set_table_item(self.equation_table, row, 3, item.status)
            self._set_table_item(self.equation_table, row, 4, item.message)
        self.equation_table.resizeColumnsToContents()

    def _set_table_item(self, table, row: int, column: int, value: str):
        item = QTableWidgetItem(value)
        item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
        if value in {STATUS_OK, STATUS_WARN, STATUS_ERROR}:
            color = {
                STATUS_OK: "#2e7d32",
                STATUS_WARN: "#ed6c02",
                STATUS_ERROR: "#d32f2f",
            }[value]
            item.setForeground(QColor(color))
        table.setItem(row, column, item)

    def _set_summary_text(self, ok_count: int, warn_count: int, error_count: int):
        summary_template = self._t(
            "集計: OK={ok_count}, WARN={warn_count}, ERROR={error_count}",
            "Summary: OK={ok_count}, WARN={warn_count}, ERROR={error_count}",
        )
        summary = summary_template.format(ok_count=ok_count, warn_count=warn_count, error_count=error_count)
        self.summary_label.setText(summary)

    def _t(self, ja_text: str, en_text: str) -> str:
        current_language = getattr(getattr(self.parent, "language_manager", None), "current_language", "ja")
        return ja_text if current_language == "ja" else en_text
