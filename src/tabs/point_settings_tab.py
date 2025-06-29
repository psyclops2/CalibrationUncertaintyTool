from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QTableWidget, QTableWidgetItem,
    QHeaderView, QPushButton, QMessageBox
)
from PySide6.QtCore import Qt, Signal, QObject

from src.tabs.base_tab import BaseTab
from src.utils.translation_keys import (
    POINT_SETTINGS_TAB_INFO, POINT_NAME, ADD_POINT, REMOVE_POINT, INDEX,
    CALIBRATION_POINT_NAME
)

class PointSettingsTab(BaseTab):
    """校正点設定タブ"""
    
    points_changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setup_ui()
        self.table.itemChanged.connect(self.on_item_changed)

    def retranslate_ui(self):
        """UI要素のテキストを現在の言語で更新する"""
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
        """テーブルの表示を更新"""
        self.table.blockSignals(True)
        self.table.setRowCount(0)
        
        # MainWindowのvalue_namesを取得
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
        """校正点を追加"""
        try:
            # 新しい校正点の名前を生成
            current_count = len(self.parent.value_names)
            new_point_name = f"{self.tr(CALIBRATION_POINT_NAME)} {current_count + 1}"
            
            # MainWindowのvalue_namesに追加
            self.parent.value_names.append(new_point_name)
            
            # テーブルを更新
            self.update_display()
            
            # 他のタブに変更を通知
            self.points_changed.emit()
            
            # 新しく追加された行を選択
            self.table.selectRow(current_count)
            
        except Exception as e:
            print(f"【エラー】校正点追加エラー: {str(e)}")
            QMessageBox.warning(self, "エラー", f"校正点の追加に失敗しました: {str(e)}")

    def remove_point(self):
        """選択された校正点を削除"""
        try:
            current_row = self.table.currentRow()
            if current_row < 0:
                QMessageBox.information(self, "情報", "削除する校正点を選択してください。")
                return
            
            # 最低1つの校正点は必要
            if len(self.parent.value_names) <= 1:
                QMessageBox.warning(self, "警告", "最低1つの校正点が必要です。")
                return
            
            # 確認ダイアログ
            point_name = self.parent.value_names[current_row]
            reply = QMessageBox.question(
                self, 
                "確認", 
                f"校正点「{point_name}」を削除しますか？\nこの操作は元に戻せません。",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                # MainWindowのvalue_namesから削除
                del self.parent.value_names[current_row]
                
                # テーブルを更新
                self.update_display()
                
                # 他のタブに変更を通知
                self.points_changed.emit()
                
                # 適切な行を選択（削除された行の次の行、または最後の行）
                if current_row < self.table.rowCount():
                    self.table.selectRow(current_row)
                elif self.table.rowCount() > 0:
                    self.table.selectRow(self.table.rowCount() - 1)
                    
        except Exception as e:
            print(f"【エラー】校正点削除エラー: {str(e)}")
            QMessageBox.warning(self, "エラー", f"校正点の削除に失敗しました: {str(e)}")

    def on_item_changed(self, item):
        """テーブルの項目が変更されたときの処理"""
        if item.column() == 1:
            self.save_names()

    def save_names(self):
        """校正点名を保存"""
        try:
            names = []
            for row in range(self.table.rowCount()):
                item = self.table.item(row, 1)
                if item:
                    names.append(item.text())
            
            # MainWindowのvalue_namesを更新
            if hasattr(self.parent, 'value_names'):
                self.parent.value_names = names
            
            # 他のタブに変更を通知
            self.points_changed.emit()
            
        except Exception as e:
            print(f"【エラー】校正点名保存エラー: {str(e)}")

    def showEvent(self, event):
        """タブが表示されたときの処理"""
        self.update_display()
        super().showEvent(event)
