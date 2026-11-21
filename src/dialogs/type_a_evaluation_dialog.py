"""Point-specific Type A evaluation settings."""
from src.utils.ui_translation import tr_ui
from decimal import DecimalException

from PySide6.QtWidgets import (
    QComboBox, QDialog, QDialogButtonBox, QFormLayout, QLabel, QLineEdit,
    QMessageBox, QVBoxLayout,
)
from src.utils.variable_utils import TYPE_A_MODES, evaluate_type_a_value


class TypeAEvaluationDialog(QDialog):
    def __init__(self, value, parent=None):
        super().__init__(parent)
        self.original = dict(value)
        self.result_value = None
        self.setWindowTitle(tr_ui('Type Aの評価方法'))
        self.setMinimumWidth(480)
        layout = QVBoxLayout(self)
        hint = QLabel(tr_ui('観測列は元の入力欄に保持します。プール標準偏差の自由度は、\n今回の観測数ではなく、標準偏差を推定したデータに基づき指定します。'))
        hint.setWordWrap(True)
        layout.addWidget(hint)
        self.form = QFormLayout()
        layout.addLayout(self.form)
        self.mode = QComboBox()
        for key, label in TYPE_A_MODES.items():
            self.mode.addItem(tr_ui(label), key)
        self.mode.setCurrentIndex(max(0, self.mode.findData(value.get('evaluation_mode', 'sample'))))
        self.form.addRow(tr_ui('評価方法'), self.mode)
        self.fields = {}
        for key, label in (
            ('pooled_standard_deviation', tr_ui('プール標準偏差（量と同じ単位）')),
            ('pooled_degrees_of_freedom', tr_ui('プール標準偏差の自由度')),
            ('central_value', tr_ui('評価済み中心値')),
            ('standard_uncertainty', tr_ui('評価済み標準不確かさ')),
            ('degrees_of_freedom', tr_ui('評価済み自由度')),
            ('evaluation_note', tr_ui('評価の根拠')),
        ):
            field = QLineEdit(str(value.get(key, '')))
            self.fields[key] = field
            self.form.addRow(label, field)
        self.mode.currentIndexChanged.connect(self.update_fields)
        self.update_fields()
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def update_fields(self):
        mode = self.mode.currentData()
        for key, field in self.fields.items():
            visible = (key == 'evaluation_note' or
                       (key.startswith('pooled_') and mode == 'pooled') or
                       (key in ('central_value', 'standard_uncertainty', 'degrees_of_freedom') and mode == 'summary'))
            self.form.setRowVisible(field, visible)

    def accept(self):
        value = dict(self.original)
        value['evaluation_mode'] = self.mode.currentData()
        for key, field in self.fields.items():
            if key == 'evaluation_note' or (key.startswith('pooled_') and value['evaluation_mode'] == 'pooled') or (
                    key in ('central_value', 'standard_uncertainty', 'degrees_of_freedom') and value['evaluation_mode'] == 'summary'):
                value[key] = field.text().strip()
        try:
            self.result_value = evaluate_type_a_value(value)
        except (ValueError, DecimalException) as error:
            QMessageBox.warning(self, tr_ui('入力を確認してください'), str(error))
            return
        super().accept()
