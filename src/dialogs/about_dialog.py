from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPainter, QPixmap
from PySide6.QtWidgets import QDialog, QDialogButtonBox, QLabel, QTextBrowser, QVBoxLayout
from src.utils.ui_translation import tr_ui


class AboutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr_ui('このソフトについて'))
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

        app_info = QLabel("CAlibration uncertainty Tool")
        app_info.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(app_info)

        version = "1.00.01"
        version_label = QLabel(tr_ui('バージョン：')+version)
        layout.addWidget(version_label)

        license_text = self._make_transparent_text_browser(
            f"""
            <h3>{tr_ui('ライセンス')}</h3>
            <p>{tr_ui('本体はMITライセンスです。第三者のライブラリ・資料には各権利者の条件が適用されます。')}</p>
            <ul>
                <li><a href=\"https://opensource.org/licenses/MIT\">https://opensource.org/licenses/MIT</a></li>
                <li><a href=\"https://github.com/psyclops2/CalibrationUncertaintyTool\">{tr_ui('プロジェクトのリポジトリ')}</a></li>
            </ul>
            """
        )
        layout.addWidget(license_text)

        libraries_text = self._make_transparent_text_browser(
            f"""
            <h3>{tr_ui('依存ライブラリ')}</h3>
            <ul>
                <li>PySide6 / Qt / Shiboken6<br>
                    <a href='https://doc.qt.io/qt-6/licensing.html'>{tr_ui('Qtのライセンス・モジュール別条件')}</a>
                </li>
                <li>SymPy (BSD 3-Clause)<br>
                    <a href='https://opensource.org/licenses/BSD-3-Clause'>https://opensource.org/licenses/BSD-3-Clause</a>
                </li>
                <li>NumPy (BSD 3-Clause; {tr_ui('同梱コードの表示も参照')})<br>
                    <a href='https://opensource.org/licenses/BSD-3-Clause'>https://opensource.org/licenses/BSD-3-Clause</a>
                </li>
                <li>Python-Markdown (BSD 3-Clause)<br>
                    <a href='https://python-markdown.github.io/'>https://python-markdown.github.io/</a>
                </li>
                <li>mpmath (BSD 3-Clause)</li>
            </ul>
            <p><a href='{(Path(__file__).resolve().parents[2]/'THIRD_PARTY_LICENSES.md').as_uri()}'>{tr_ui('第三者ライセンス表示')}</a></p>
            """
        )
        layout.addWidget(libraries_text)

        buttons = QDialogButtonBox(QDialogButtonBox.Close)
        buttons.button(QDialogButtonBox.Close).setText(tr_ui('閉じる'))
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.setLayout(layout)
