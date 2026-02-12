from PySide6.QtWidgets import (
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QPushButton,
    QMessageBox,
)
from PySide6.QtCore import Qt, Signal

from src.tabs.base_tab import BaseTab
from src.utils.app_logger import log_error
from src.utils.translation_keys import (
    POINT_SETTINGS_TAB_INFO,
    POINT_NAME,
    ADD_POINT,
    REMOVE_POINT,
    INDEX,
    CALIBRATION_POINT_NAME,
    MESSAGE_WARNING,
    MESSAGE_INFO,
    MESSAGE_CONFIRM,
    POINT_SELECT_TO_REMOVE,
    POINT_MIN_ONE_REQUIRED,
    POINT_REMOVE_CONFIRM,
    POINT_ADD_FAILED,
    POINT_REMOVE_FAILED,
)


class PointSettingsTab(BaseTab):
    """Calibration point settings tab."""

    points_changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setup_ui()
        self.table.itemChanged.connect(self.on_item_changed)

    def retranslate_ui(self):
        self.info_label.setText(self.tr(POINT_SETTINGS_TAB_INFO))
        self.table.setHorizontalHeaderLabels([self.tr(INDEX), self.tr(POINT_NAME)])
        self.add_button.setText(self.tr(ADD_POINT))
        self.remove_button.setText(self.tr(REMOVE_POINT))

    def setup_ui(self):
        layout = QVBoxLayout(self)

        self.info_label = QLabel(self.tr(POINT_SETTINGS_TAB_INFO))
        layout.addWidget(self.info_label)

        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels([self.tr(INDEX), self.tr(POINT_NAME)])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        layout.addWidget(self.table)

        button_layout = QHBoxLayout()
        self.add_button = QPushButton(self.tr(ADD_POINT))
        self.remove_button = QPushButton(self.tr(REMOVE_POINT))
        button_layout.addWidget(self.add_button)
        button_layout.addWidget(self.remove_button)
        button_layout.addStretch()
        layout.addLayout(button_layout)

        self.add_button.clicked.connect(self.add_point)
        self.remove_button.clicked.connect(self.remove_point)

    def update_display(self):
        self.table.blockSignals(True)
        self.table.setRowCount(0)

        value_names = getattr(self.parent, "value_names", [])

        for i, name in enumerate(value_names):
            self.table.insertRow(i)
            index_item = QTableWidgetItem(str(i + 1))
            index_item.setFlags(index_item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(i, 0, index_item)
            self.table.setItem(i, 1, QTableWidgetItem(name))

        self.table.blockSignals(False)

    def add_point(self):
        try:
            current_count = len(self.parent.value_names)
            new_point_name = f"{self.tr(CALIBRATION_POINT_NAME)} {current_count + 1}"

            self.parent.value_names.append(new_point_name)
            self.update_display()
            self.points_changed.emit()
            self.table.selectRow(current_count)

        except Exception as e:
            log_error(f"Point add error: {str(e)}")
            QMessageBox.warning(self, self.tr(MESSAGE_WARNING), f"{self.tr(POINT_ADD_FAILED)}: {str(e)}")

    def remove_point(self):
        try:
            current_row = self.table.currentRow()
            if current_row < 0:
                QMessageBox.information(self, self.tr(MESSAGE_INFO), self.tr(POINT_SELECT_TO_REMOVE))
                return

            if len(self.parent.value_names) <= 1:
                QMessageBox.warning(self, self.tr(MESSAGE_WARNING), self.tr(POINT_MIN_ONE_REQUIRED))
                return

            point_name = self.parent.value_names[current_row]
            reply = QMessageBox.question(
                self,
                self.tr(MESSAGE_CONFIRM),
                self.tr(POINT_REMOVE_CONFIRM).format(point_name=point_name),
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )

            if reply == QMessageBox.Yes:
                del self.parent.value_names[current_row]
                self.update_display()
                self.points_changed.emit()

                if current_row < self.table.rowCount():
                    self.table.selectRow(current_row)
                elif self.table.rowCount() > 0:
                    self.table.selectRow(self.table.rowCount() - 1)

        except Exception as e:
            log_error(f"Point remove error: {str(e)}")
            QMessageBox.warning(self, self.tr(MESSAGE_WARNING), f"{self.tr(POINT_REMOVE_FAILED)}: {str(e)}")

    def on_item_changed(self, item):
        if item.column() == 1:
            self.save_names()

    def save_names(self):
        try:
            names = []
            for row in range(self.table.rowCount()):
                item = self.table.item(row, 1)
                if item:
                    names.append(item.text())

            if hasattr(self.parent, "value_names"):
                self.parent.value_names = names

            self.points_changed.emit()

        except Exception as e:
            log_error(f"Point name save error: {str(e)}")

    def showEvent(self, event):
        self.update_display()
        super().showEvent(event)
