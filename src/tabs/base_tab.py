"""
タブの基底クラス
翻訳機能を提供する基底クラス
"""

from PySide6.QtWidgets import QWidget
from src.i18n.translator import Translator

class BaseTab(QWidget):
    """タブの基底クラス"""
    
    def __init__(self, parent=None):
        """初期化"""
        super().__init__(parent)
        self.main_window = parent
        
        # 翻訳機能の初期化
        if hasattr(parent, 'translator'):
            self.translator = parent.translator
        else:
            # 親に翻訳機能がない場合はデフォルトの日本語を使用
            self.translator = Translator('ja')
    
    def tr(self, key):
        """翻訳キーに対応する文字列を取得"""
        return self.translator.translate(key, key)
    
    def retranslate_ui(self):
        """UIのテキストを現在の言語で更新"""
        # 継承先で実装
        pass
