from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QTextBrowser, QDialogButtonBox
from PySide6.QtCore import Qt, Signal, Slot
import pkg_resources

class AboutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("About")
        self.setModal(True)
        self.resize(600, 500)
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout()
        
        # アプリケーション情報
        app_info = QLabel("不確かさ計算ツール")
        app_info.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(app_info)
        
        # バージョン情報
        version = "1.0.0"
        version_label = QLabel(f"Version: {version}")
        layout.addWidget(version_label)
        
        # ライセンス情報（GPL）
        license_text = QTextBrowser()
        license_text.setOpenExternalLinks(True)
        license_text.setHtml("""
            <p>このソフトウェアは <b>GNU General Public License v3</b> の下で公開されています。</p>
            <p>Copyright (C) 2024 psyclops2</p>
            <p>This program comes with <b>ABSOLUTELY NO WARRANTY</b>; for details, see the license.</p>
            <p>This is free software, and you are welcome to redistribute it under certain conditions.</p>
            <p>詳細については以下を参照してください：</p>
            <ul>
                <li><a href="https://www.gnu.org/licenses/gpl-3.0.html">https://www.gnu.org/licenses/gpl-3.0.html</a></li>
                <li><a href="https://github.com/psyclops2/CalibrationUncertaintyTool">プロジェクトの GitHub リポジトリ</a></li>
            </ul>
        """)
        layout.addWidget(license_text)
        
        # 使用ライブラリ情報
        libraries_text = QTextBrowser()
        libraries_text.setOpenExternalLinks(True)
        libraries_text.setHtml(self.get_libraries_info())
        layout.addWidget(libraries_text)

        # 閉じるボタン
        buttons = QDialogButtonBox(QDialogButtonBox.Close)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.setLayout(layout)
        
    def get_libraries_info(self):
        """使用しているライブラリの情報を取得"""
        used_libraries = {
            'pyside6': 'GUIフレームワーク',
            'sympy': '数式処理',
            'numpy': '数値計算'
        }

        libraries = []
        for package in pkg_resources.working_set:
            package_key = package.key.lower()
            if package_key in used_libraries:
                display_name = package.project_name
                description = used_libraries[package_key]
                libraries.append(
                    f"<p><b>{display_name}</b> - Version {package.version}<br>"
                    f"<i>{description}</i></p>"
                )
        
        return "<h3>主要な使用ライブラリ</h3>" + "".join(libraries)
