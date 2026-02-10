import json
import sys

try:
    from PySide6.QtWidgets import QApplication

    from src.main_window import MainWindow
    from src.utils.language_manager import LanguageManager
except ImportError:
    QApplication = None


def _print_save_data_structure():
    if QApplication is None:
        raise SystemExit("PySide6 is not available.")

    app = QApplication(sys.argv)
    main_window = MainWindow(LanguageManager())

    main_window.last_equation = "A=CAL+MEA^2+CONST"
    main_window.variables = ["A", "CONST", "CAL", "MEA"]
    main_window.result_variables = ["A"]
    main_window.value_count = 2
    main_window.current_value_index = 2
    main_window.value_names = ["1000V", "100V"]

    save_data = main_window.get_save_data()
    print("JSON structure:")
    print(json.dumps(save_data, indent=4, ensure_ascii=False))
    print("\nFirst key:", list(save_data.keys())[0])


if __name__ == "__main__":
    _print_save_data_structure()

