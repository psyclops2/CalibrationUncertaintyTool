import sys
import os
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTranslator, QLocale
from src.main_window import MainWindow
from src.utils.language_manager import LanguageManager

def main():
    """アプリケーションのエントリーポイント"""
    app = QApplication(sys.argv)
    
    # 言語設定の初期化と適用
    language_manager = LanguageManager()



    language_manager.load_language()
    
    # メインウィンドウの作成と表示
    window = MainWindow(language_manager)
    window.show()
    
    # アプリケーションの実行
    sys.exit(app.exec())

if __name__ == "__main__":
    main()