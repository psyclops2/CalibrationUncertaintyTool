import sys
import json
from PySide6.QtWidgets import QApplication
from src.main_window import MainWindow
from src.utils.language_manager import LanguageManager

# QApplicationを作成
app = QApplication(sys.argv)

# MainWindowを作成
main_window = MainWindow(LanguageManager())

# テストデータを設定
main_window.last_equation = "A=CAL+MEA^2+CONST"
main_window.variables = ["A", "CONST", "CAL", "MEA"]
main_window.result_variables = ["A"]
main_window.value_count = 2
main_window.current_value_index = 2
main_window.value_names = ["1000V", "100V"]

# 保存データを取得
save_data = main_window.get_save_data()

# JSON構造を出力
print("JSON structure:")
print(json.dumps(save_data, indent=4, ensure_ascii=False))

# 最初のキーを確認
print("\nFirst key:", list(save_data.keys())[0]) 