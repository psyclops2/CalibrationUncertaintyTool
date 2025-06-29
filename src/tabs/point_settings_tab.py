from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QTableWidget, QTableWidgetItem,
    QHeaderView, QPushButton
)
from PySide6.QtCore import Qt, Signal, QObject

from src.utils.translation_keys import (
    POINT_SETTINGS_TAB_INFO, POINT_NAME, ADD_POINT, REMOVE_POINT
)

class PointSettingsTab(QWidget):
    """校正点設定タブ"""
    
    points_changed = Signal()
    point_count_changed = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setup_ui()
        self.table.itemChanged.connect(self.on_item_changed)

    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        info_label = QLabel(self.tr(POINT_SETTINGS_TAB_INFO))
        layout.addWidget(info_label)
        
        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels([self.tr("インデックス"), self.tr(POINT_NAME)])
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

    def tr(self, key, **kwargs):
        if self.parent:
            return self.parent.tr(key, **kwargs)
        return QObject().tr(key)

    def update_display(self):
        self.table.blockSignals(True)
        self.table.setRowCount(0)
        value_names = getattr(self.parent, 'value_names', [])
        for i, name in enumerate(value_names):
            self.table.insertRow(i)
            index_item = QTableWidgetItem(str(i + 1))
            index_item.setFlags(index_item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(i, 0, index_item)
            name_item = QTableWidgetItem(name)
            self.table.setItem(i, 1, name_item)
        self.table.blockSignals(False)

    def add_point(self):
        new_count = self.table.rowCount() + 1
        self.point_count_changed.emit(new_count)

    def remove_point(self):
        current_row = self.table.currentRow()
        if current_row < 0:
            return
        new_count = self.table.rowCount() - 1
        if new_count > 0:
            self.point_count_changed.emit(new_count)

    def on_item_changed(self, item):
        if item.column() == 1:
            self.save_names()

    def save_names(self):
        names = []
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 1)
            if item:
                names.append(item.text())
        
        if hasattr(self.parent, 'value_names'):
            self.parent.value_names = names
        
        self.points_changed.emit()

    def showEvent(self, event):
        self.update_display()
        super().showEvent(event)
