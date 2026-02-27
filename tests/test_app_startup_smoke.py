import pytest

try:
    from PySide6.QtWidgets import QApplication
    from src.main_window import MainWindow
    from src.utils.language_manager import LanguageManager
except ImportError:
    pytest.skip("PySide6 is not available", allow_module_level=True)


@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_main_window_can_be_created_and_closed(qapp):
    window = MainWindow(LanguageManager())
    try:
        assert window.tab_widget.count() > 0
    finally:
        window.close()
