from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QTextBrowser
import pkg_resources

class AboutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("About")
        self.setModal(True)
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout()
        
        # アプリケーション情報
        app_info = QLabel("不確かさ計算ツール")
        app_info.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(app_info)
        
        # バージョン情報
        version = "1.0.0"  # バージョン番号を設定
        version_label = QLabel(f"Version: {version}")
        layout.addWidget(version_label)
        
        # ライセンス情報
        license_text = QTextBrowser()
        license_text.setOpenExternalLinks(True)
        license_text.setHtml("""
            <p>このソフトウェアはMITライセンスの下で公開されています。</p>
            <p>Copyright (c) 2024</p>
            <p>Permission is hereby granted, free of charge, to any person obtaining a copy
            of this software and associated documentation files (the "Software"), to deal
            in the Software without restriction, including without limitation the rights
            to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
            copies of the Software, and to permit persons to whom the Software is
            furnished to do so, subject to the following conditions:</p>
            <p>The above copyright notice and this permission notice shall be included in all
            copies or substantial portions of the Software.</p>
            <p>THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
            IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
            FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
            AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
            LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
            OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
            SOFTWARE.</p>
        """)
        layout.addWidget(license_text)
        
        # 使用ライブラリ情報
        libraries_text = QTextBrowser()
        libraries_text.setOpenExternalLinks(True)
        libraries_text.setHtml(self.get_libraries_info())
        layout.addWidget(libraries_text)
        
        self.setLayout(layout)
        
    def get_libraries_info(self):
        """使用しているライブラリの情報を取得"""
        # 実際に使用している主要なライブラリのリスト
        used_libraries = {
            'PyQt5': 'GUIフレームワーク',
            'pyqt5': 'GUIフレームワーク',  # 小文字バージョンも追加
            'sympy': '数式処理',
            'numpy': '数値計算'
        }
        
        libraries = []
        for package in pkg_resources.working_set:
            # パッケージ名を小文字に変換して比較
            package_key = package.key.lower()
            if package_key in [k.lower() for k in used_libraries.keys()]:
                # 元の大文字小文字を保持した表示名を使用
                display_name = package.key
                description = used_libraries.get(package_key, used_libraries.get(package_key.capitalize(), ''))
                libraries.append(
                    f"<p><b>{display_name}</b> - Version {package.version}<br>"
                    f"<i>{description}</i></p>"
                )
        
        return "<h3>主要な使用ライブラリ</h3>" + "".join(libraries) 