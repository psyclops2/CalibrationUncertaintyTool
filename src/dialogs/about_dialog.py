from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QTextBrowser, QDialogButtonBox

class AboutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("About / このソフトについて")
        self.setModal(True)
        self.resize(600, 500)
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout()
        
        # アプリケーション情報
        app_info = QLabel("不確かさ計算ツール / Uncertainty Calculation Tool")
        app_info.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(app_info)
        
        # バージョン情報
        version = "1.0.0"
        version_label = QLabel(f"Version / バージョン: {version}")
        layout.addWidget(version_label)
        
        # 自作コードのライセンス情報（MIT License）
        license_text = QTextBrowser()
        license_text.setOpenExternalLinks(True)
        license_text.setHtml("""
            <h3>License / ライセンス</h3>
            <p>This software is licensed under the <b>MIT License</b>.<br>
            このソフトウェアは <b>MIT License</b> の下で公開されています。</p>
            <ul>
                <li><a href="https://opensource.org/licenses/MIT">https://opensource.org/licenses/MIT</a></li>
                <li><a href="https://github.com/psyclops2/CalibrationUncertaintyTool">Project GitHub Repository / プロジェクト GitHub リポジトリ</a></li>
            </ul>
        """)
        layout.addWidget(license_text)
        
        # 使用ライブラリ情報（必要最小限、和英併記）
        libraries_text = QTextBrowser()
        libraries_text.setOpenExternalLinks(True)
        libraries_text.setHtml("""
            <h3>Used Libraries / 使用ライブラリ</h3>
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
            <p>For full third-party notices, see <b>THIRD_PARTY_LICENSES.md</b>.<br>
            詳細は <b>THIRD_PARTY_LICENSES.md</b> を参照してください。</p>
        """)
        layout.addWidget(libraries_text)

        # 閉じるボタン
        buttons = QDialogButtonBox(QDialogButtonBox.Close)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.setLayout(layout)
