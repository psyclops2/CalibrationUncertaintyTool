from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPainter, QPixmap
from PySide6.QtWidgets import QDialog, QDialogButtonBox, QLabel, QTextBrowser, QVBoxLayout


class AboutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("About")
        self.setModal(True)
        self.resize(600, 500)

        self._background_color = QColor("#cfeeee")
        self._logo = self._load_logo()
        self.setup_ui()

    def _load_logo(self) -> QPixmap:
        logo_path = Path(__file__).resolve().parents[2] / "img" / "logo.png"
        return QPixmap(str(logo_path))

    def _make_transparent_text_browser(self, html: str) -> QTextBrowser:
        browser = QTextBrowser()
        browser.setOpenExternalLinks(True)
        browser.setHtml(html)
        browser.setStyleSheet("background: transparent; border: none;")
        browser.viewport().setAutoFillBackground(False)
        browser.setFrameStyle(0)
        return browser

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), self._background_color)

        if not self._logo.isNull():
            scaled_logo = self._logo.scaled(150, 150, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            x = self.width() - scaled_logo.width() - 12
            y = 12
            painter.drawPixmap(x, y, scaled_logo)

        super().paintEvent(event)

    def setup_ui(self):
        layout = QVBoxLayout()

        app_info = QLabel("Uncertainty Calculation Tool")
        app_info.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(app_info)

        version = "1.0.0"
        version_label = QLabel(f"Version: {version}")
        layout.addWidget(version_label)

        license_text = self._make_transparent_text_browser(
            """
            <h3>License</h3>
            <p>This software is licensed under the <b>MIT License</b>.</p>
            <ul>
                <li><a href=\"https://opensource.org/licenses/MIT\">https://opensource.org/licenses/MIT</a></li>
                <li><a href=\"https://github.com/psyclops2/CalibrationUncertaintyTool\">Project GitHub Repository</a></li>
            </ul>
            """
        )
        layout.addWidget(license_text)

        libraries_text = self._make_transparent_text_browser(
            """
            <h3>Used Libraries</h3>
            <ul>
                <li>PySide6 (LGPLv3)<br>
                    <a href='https://www.gnu.org/licenses/lgpl-3.0.html'>https://www.gnu.org/licenses/lgpl-3.0.html</a>
                </li>
                <li>SymPy (BSD 3-Clause)<br>
                    <a href='https://opensource.org/licenses/BSD-3-Clause'>https://opensource.org/licenses/BSD-3-Clause</a>
                </li>
                <li>NumPy (BSD 3-Clause)<br>
                    <a href='https://opensource.org/licenses/BSD-3-Clause'>https://opensource.org/licenses/BSD-3-Clause</a>
                </li>
                <li>Python-Markdown (BSD 3-Clause)<br>
                    <a href='https://python-markdown.github.io/'>https://python-markdown.github.io/</a>
                </li>
            </ul>
            <p>For full third-party notices, see <b>THIRD_PARTY_LICENSES.md</b>.</p>
            """
        )
        layout.addWidget(libraries_text)

        buttons = QDialogButtonBox(QDialogButtonBox.Close)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.setLayout(layout)
