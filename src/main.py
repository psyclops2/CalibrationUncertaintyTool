import sys

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPainter, QPixmap
from PySide6.QtWidgets import QApplication, QSplashScreen

from src.utils.language_manager import LanguageManager


def _create_startup_splash(app: QApplication) -> QSplashScreen:
    pixmap = QPixmap(440, 120)
    pixmap.fill(QColor("#f4f4f4"))

    painter = QPainter(pixmap)
    painter.setPen(QColor("#333333"))
    painter.drawText(20, 44, "Calibration Uncertainty Tool")
    painter.drawText(20, 78, "Starting application...")
    painter.end()

    splash = QSplashScreen(pixmap)
    splash.setWindowFlag(Qt.WindowStaysOnTopHint, True)
    splash.show()
    splash.showMessage("Initializing...", Qt.AlignBottom | Qt.AlignLeft, QColor("#333333"))
    app.processEvents()
    return splash


def main():
    app = QApplication(sys.argv)
    splash = _create_startup_splash(app)
    # Debug only:
    # import time
    # time.sleep(2.0)
    # app.processEvents()

    splash.showMessage("Loading language settings...", Qt.AlignBottom | Qt.AlignLeft, QColor("#333333"))
    app.processEvents()
    language_manager = LanguageManager()
    language_manager.load_language()

    splash.showMessage("Creating main window...", Qt.AlignBottom | Qt.AlignLeft, QColor("#333333"))
    app.processEvents()
    from src.main_window import MainWindow

    window = MainWindow(language_manager)
    window.show()
    splash.finish(window)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
