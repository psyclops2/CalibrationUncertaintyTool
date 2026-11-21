"""Plain Markdown editor with portable image insertion."""
from src.utils.ui_translation import tr_ui
from PySide6.QtWidgets import QTextEdit, QFileDialog, QMessageBox, QInputDialog, QPushButton
from PySide6.QtGui import QImage, QAction
from PySide6.QtCore import QEvent
from src.utils.image_assets import import_image


class ImageDescriptionEdit(QTextEdit):
    def __init__(self, project):
        super().__init__()
        self.project = project
        self.setAcceptRichText(False)
        self.setPlaceholderText(tr_ui('説明文（画像は「画像を挿入」またはCtrl+V）'))
        self.setToolTip(tr_ui('「画像を挿入」でPNG・JPEGを選択できます。画像もプロジェクトに保存します。'))
        self.insert_image_button = QPushButton(tr_ui('画像を挿入…'), self)
        self.insert_image_button.setToolTip(tr_ui('画像ファイルを選択し、説明文のカーソル位置へ挿入します'))
        self.insert_image_button.clicked.connect(self.insert_image_file)
        self._position_image_button()

    def retranslate_ui(self):
        self.setPlaceholderText(tr_ui('説明文（画像は「画像を挿入」またはCtrl+V）'))
        self.setToolTip(tr_ui('「画像を挿入」でPNG・JPEGを選択できます。画像もプロジェクトに保存します。'))
        self.insert_image_button.setText(tr_ui('画像を挿入…'))
        self.insert_image_button.setToolTip(tr_ui('画像ファイルを選択し、説明文のカーソル位置へ挿入します'))
        self._position_image_button()

    def changeEvent(self, event):
        if event.type() == QEvent.LanguageChange and hasattr(self,'insert_image_button'):
            self.retranslate_ui()
        super().changeEvent(event)

    def _position_image_button(self):
        button = self.insert_image_button
        button.resize(button.sizeHint())
        self.setViewportMargins(0, button.height() + 7, 0, 0)
        button.move(max(3, self.width() - button.width() - 6), 3)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, 'insert_image_button'):
            self._position_image_button()

    def canInsertFromMimeData(self, source):
        return source.hasImage() or super().canInsertFromMimeData(source)

    def insertFromMimeData(self, source):
        if source.hasImage():
            self.insert_image(QImage(source.imageData()))
        else:
            super().insertFromMimeData(source)

    def insert_image(self, image):
        try:
            if image.isNull():
                raise ValueError(tr_ui('画像を読み込めません。'))
            caption, accepted = QInputDialog.getText(self, tr_ui('画像の説明'), tr_ui('キャプション・出典（省略可）'))
            if not accepted:
                return
            ident = import_image(self.project.image_assets, image)
            caption = caption.replace('\\', '\\\\').replace('[', '\\[').replace(']', '\\]')
            self.insertPlainText(f'\n![{caption}](asset:{ident})\n')
        except ValueError as error:
            QMessageBox.warning(self, tr_ui('画像の挿入'), str(error))

    def insert_image_file(self):
        path, _ = QFileDialog.getOpenFileName(self, tr_ui('画像ファイルを挿入'), '', 'Images (*.png *.jpg *.jpeg)')
        if path:
            self.insert_image(QImage(path))

    def contextMenuEvent(self, event):
        menu = self.createStandardContextMenu()
        menu.addSeparator()
        action = QAction(tr_ui('画像ファイルを挿入…'), menu)
        action.triggered.connect(self.insert_image_file)
        menu.addAction(action)
        menu.exec(event.globalPos())
