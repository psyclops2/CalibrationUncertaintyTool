import sys
from PySide6.QtWidgets import QApplication
from src.main_window import MainWindow

def main():
    """アプリケーションのエントリーポイント"""
    app = QApplication(sys.argv)
    
    # メインウィンドウの作成と表示
    window = MainWindow()
    window.show()
    
    # アプリケーションの実行
    sys.exit(app.exec())

if __name__ == "__main__":
    main() 