import csv
import io
from PySide6.QtCore import Signal
from PySide6.QtWidgets import QFormLayout, QLabel, QLineEdit, QTextEdit, QVBoxLayout

from src.tabs.base_tab import BaseTab
from src.utils.translation_keys import (
    DESCRIPTION_LABEL,
    DOCUMENT_NAME,
    DOCUMENT_NUMBER,
    DOCUMENT_INFO_TAB,
    REVISION_HISTORY,
    REVISION_HISTORY_INSTRUCTION,
    REVISION_HISTORY_PLACEHOLDER,
    VERSION_INFO,
)


class DocumentInfoTab(BaseTab):
    """レポート用の文書情報や改訂履歴を入力するタブ"""

    info_changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()

        form_layout = QFormLayout()

        self.document_number_label = QLabel(self.tr(DOCUMENT_NUMBER))
        self.document_name_label = QLabel(self.tr(DOCUMENT_NAME))
        self.version_label = QLabel(self.tr(VERSION_INFO))

        self.document_number_edit = QLineEdit()
        self.document_name_edit = QLineEdit()
        self.version_edit = QLineEdit()

        form_layout.addRow(self.document_number_label, self.document_number_edit)
        form_layout.addRow(self.document_name_label, self.document_name_edit)
        form_layout.addRow(self.version_label, self.version_edit)
        layout.addLayout(form_layout)

        self.description_label = QLabel(self.tr(DESCRIPTION_LABEL))
        self.description_edit = QTextEdit()
        layout.addWidget(self.description_label)
        layout.addWidget(self.description_edit)

        self.revision_label = QLabel(self.tr(REVISION_HISTORY))
        self.revision_description = QLabel(self.tr(REVISION_HISTORY_INSTRUCTION))
        self.revision_edit = QTextEdit()
        self.revision_edit.setPlaceholderText(self.tr(REVISION_HISTORY_PLACEHOLDER))

        layout.addWidget(self.revision_label)
        layout.addWidget(self.revision_description)
        layout.addWidget(self.revision_edit)

        layout.addStretch()
        self.setLayout(layout)

        self._connect_signals()

    def _connect_signals(self):
        for line_edit in (self.document_number_edit, self.document_name_edit, self.version_edit):
            line_edit.editingFinished.connect(self._on_info_changed)
        self.description_edit.textChanged.connect(self._on_info_changed)
        self.revision_edit.textChanged.connect(self._on_info_changed)

    def retranslate_ui(self):
        self.parent.tab_widget.setTabText(
            self.parent.tab_widget.indexOf(self), self.tr(DOCUMENT_INFO_TAB)
        )
        self.description_label.setText(self.tr(DESCRIPTION_LABEL))
        self.revision_label.setText(self.tr(REVISION_HISTORY))
        self.revision_description.setText(self.tr(REVISION_HISTORY_INSTRUCTION))
        self.revision_edit.setPlaceholderText(self.tr(REVISION_HISTORY_PLACEHOLDER))
        self.document_number_label.setText(self.tr(DOCUMENT_NUMBER))
        self.document_name_label.setText(self.tr(DOCUMENT_NAME))
        self.version_label.setText(self.tr(VERSION_INFO))

    def get_document_info(self):
        return {
            "document_number": self.document_number_edit.text(),
            "document_name": self.document_name_edit.text(),
            "version_info": self.version_edit.text(),
            "description_html": self._get_description_html(),
            "revision_history": self.revision_edit.toPlainText(),
        }

    def set_document_info(self, info):
        self.document_number_edit.blockSignals(True)
        self.document_name_edit.blockSignals(True)
        self.version_edit.blockSignals(True)
        self.description_edit.blockSignals(True)
        self.revision_edit.blockSignals(True)

        self.document_number_edit.setText(info.get("document_number", ""))
        self.document_name_edit.setText(info.get("document_name", ""))
        self.version_edit.setText(info.get("version_info", ""))
        self.description_edit.setHtml(info.get("description_html", ""))
        self.revision_edit.setPlainText(info.get("revision_history", ""))

        self.document_number_edit.blockSignals(False)
        self.document_name_edit.blockSignals(False)
        self.version_edit.blockSignals(False)
        self.description_edit.blockSignals(False)
        self.revision_edit.blockSignals(False)

        self._on_info_changed()

    def parse_revision_history(self):
        return self._parse_revision_text(self.revision_edit.toPlainText())

    @staticmethod
    def _parse_revision_text(text):
        rows = []
        reader = csv.reader(io.StringIO(text))
        for row in reader:
            if not any(cell.strip() for cell in row):
                continue
            version, description, date = (row + ["", "", ""])[:3]
            rows.append(
                {
                    "version": version.strip(),
                    "description": description.strip(),
                    "date": date.strip(),
                }
            )
        return rows

    def _get_description_html(self):
        if not self.description_edit.toPlainText().strip():
            return ""
        return self.description_edit.toPlainText()

    def _on_info_changed(self):
        if hasattr(self.parent, "document_info"):
            self.parent.document_info = self.get_document_info()
        self.info_changed.emit()
