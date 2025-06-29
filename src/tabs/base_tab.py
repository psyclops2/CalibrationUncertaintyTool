"""
タブの基底クラス
翻訳機能を提供する基底クラス
"""

from PySide6.QtWidgets import QWidget


class BaseTab(QWidget):
    """タブの基底クラス"""
    
    def __init__(self, parent=None):
        """初期化"""
        super().__init__(parent)
        self.main_window = parent
        

    
    def retranslate_ui(self):
        """UIのテキストを現在の言語で更新"""
        # 継承先で実装
        pass
