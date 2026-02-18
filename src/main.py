import sys
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPixmap
from PySide6.QtWidgets import QApplication, QSplashScreen

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from src.utils.language_manager import LanguageManager
else:
    from .utils.language_manager import LanguageManager


def _create_startup_splash(app: QApplication) -> QSplashScreen:
    pixmap = QPixmap(560, 200)
    pixmap.fill(QColor("#cfeeee"))

    painter = QPainter(pixmap)
    painter.setPen(QColor("#333333"))
    base_font = painter.font()
    title_font = QFont(base_font)
    title_font.setBold(True)
    if base_font.pointSizeF() > 0:
        title_font.setPointSizeF(base_font.pointSizeF() * 2.5)
    elif base_font.pixelSize() > 0:
        title_font.setPixelSize(int(base_font.pixelSize() * 2.5))

    logo_path = Path(__file__).resolve().parents[1] / "img" / "logo.png"
    logo = QPixmap(str(logo_path))
    if not logo.isNull():
        scaled_logo = logo.scaled(150, 150, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        x = pixmap.width() - scaled_logo.width() - 12
        y = pixmap.height() - scaled_logo.height() - 12
        painter.drawPixmap(x, y, scaled_logo)

    painter.setFont(title_font)
    painter.drawText(20, 56, "Calibration Uncertainty Tool")
    painter.setFont(base_font)
    painter.drawText(20, 96, "Starting application...")
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
    if __package__ in (None, ""):
        from src.main_window import MainWindow
    else:
        from .main_window import MainWindow

    window = MainWindow(language_manager)
    window.show()
    splash.finish(window)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()

