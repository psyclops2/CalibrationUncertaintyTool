from src.utils.ui_translation import tr_ui
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QFormLayout, QComboBox,
                               QLineEdit, QLabel, QDialogButtonBox, QMessageBox, QCheckBox)
from src.utils.coverage import METHODS, validate_coverage


class CoverageDialog(QDialog):
    def __init__(self, settings, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr_ui('包含係数の評価方法（現在の結果・校正点）'))
        self.setMinimumWidth(520)
        self.settings = None
        layout = QVBoxLayout(self)
        hint = QLabel(tr_ui('出力分布が正規分布で近似できるか確認して方法を選択します。\nEA表にない自由度は下側の掲載値を使います（有限の自由度50超ではk=2.05）。\n係数の指定だけでは包含確率を検証したことにはなりません。'))
        hint.setWordWrap(True)
        layout.addWidget(hint)
        form = QFormLayout()
        layout.addLayout(form)
        self.method = QComboBox()
        for key, label in METHODS.items():
            self.method.addItem(tr_ui(label), key)
        self.method.setCurrentIndex(self.method.findData(settings.get('method', 'legacy')))
        self.factor = QLineEdit(str(settings.get('k', '2')))
        self.note = QLineEdit(settings.get('note', ''))
        self.probability = QComboBox()
        self.probability.setEditable(True)
        self.probability.addItems(['95','95.45','99'])
        self.probability.setCurrentText(f'{float(settings.get("probability",.95))*100:g}')
        self.floor_df = QCheckBox(tr_ui('有効自由度を下側の整数へ切り捨てる'))
        self.floor_df.setChecked(settings.get('floor_df',False))
        form.addRow(tr_ui('評価方法'), self.method)
        form.addRow(tr_ui('包含確率 [%]'),self.probability)
        form.addRow('',self.floor_df)
        form.addRow(tr_ui('指定する包含係数'), self.factor)
        form.addRow(tr_ui('採用根拠'), self.note)
        def update_fields():
            form.setRowVisible(self.factor,self.method.currentData()=='manual')
            form.setRowVisible(self.probability,self.method.currentData()=='student')
            form.setRowVisible(self.floor_df,self.method.currentData()=='student')
        self.method.currentIndexChanged.connect(update_fields)
        update_fields()
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def accept(self):
        settings = {'method': self.method.currentData(), 'note': self.note.text().strip()}
        if settings['method'] == 'manual':
            settings['k'] = self.factor.text().strip()
        try:
            if settings['method'] == 'student':
                settings.update(probability=float(self.probability.currentText())/100, floor_df=self.floor_df.isChecked())
            validate_coverage(settings)
        except (ValueError, TypeError) as error:
            QMessageBox.warning(self, tr_ui('包含係数を確認してください'), str(error))
            return
        self.settings = settings
        super().accept()
