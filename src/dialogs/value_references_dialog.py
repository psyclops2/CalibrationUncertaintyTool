"""Manage explicitly registered shared values; width formulas have one editor."""
import copy
import re
from types import SimpleNamespace
from PySide6.QtCore import Qt,QTimer
from PySide6.QtWidgets import (QDialog,QVBoxLayout,QHBoxLayout,QFormLayout,QLabel,
    QTableWidget,QTableWidgetItem,QPushButton,QDialogButtonBox,QListWidget,
    QListWidgetItem,QLineEdit,QPlainTextEdit,QWidget,QSplitter)
from src.utils.ui_translation import tr_ui
from src.utils.value_references import (enable_references,new_id,evaluate_half_widths,
    ReferenceEvaluator,validate_references,is_constant_reference)
from src.widgets.reference_expression_edit import ReferenceExpressionEdit,address_label
from src.utils.parameter_formula import mark_parameter_values, prune_parameter_values


class ReferencePicker(QDialog):
    """Only project-wide constants may be used to define another constant."""
    def __init__(self, owner):
        super().__init__(owner); self.owner=owner; self.address=None
        self.setWindowTitle(tr_ui('参照する値を選択')); self.resize(700,430)
        layout=QVBoxLayout(self)
        self.search=QLineEdit(); self.search.setPlaceholderText(tr_ui('名前・説明で検索')); layout.addWidget(self.search)
        self.table=QTableWidget(0,4); self.table.setHorizontalHeaderLabels([tr_ui('名前'),tr_ui('値'),tr_ui('単位'),tr_ui('説明')])
        self.table.setSelectionBehavior(QTableWidget.SelectRows); self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers); self.table.horizontalHeader().setStretchLastSection(True); layout.addWidget(self.table)
        buttons=QDialogButtonBox(QDialogButtonBox.Ok|QDialogButtonBox.Cancel)
        self.insert_button=buttons.button(QDialogButtonBox.Ok); self.insert_button.setText(tr_ui('式に挿入')); self.insert_button.setEnabled(False)
        buttons.button(QDialogButtonBox.Cancel).setText(tr_ui('キャンセル'))
        buttons.accepted.connect(self.choose); buttons.rejected.connect(self.reject); layout.addWidget(buttons)
        self.table.itemSelectionChanged.connect(lambda:self.insert_button.setEnabled(self.table.currentRow()>=0))
        self.table.itemDoubleClicked.connect(lambda *_:self.choose()); self.search.textChanged.connect(self.populate); self.populate()

    def populate(self):
        self.table.setRowCount(0); self.insert_button.setEnabled(False)
        data=self.owner.capture(); proxy=self.owner.proxy(); evaluator=ReferenceEvaluator(data,proxy.variable_values,proxy)
        for ident,entry in data['values'].items():
            if not is_constant_reference(data,ident): continue
            name=entry['name']; description=entry.get('description','')
            if self.search.text().casefold() not in (name+' '+description).casefold(): continue
            try: value=str(evaluator.resolve('value:'+ident))
            except Exception: value=tr_ui('未評価')
            row=self.table.rowCount(); self.table.insertRow(row)
            for col,text in enumerate((name,value,entry.get('unit',''),description)): self.table.setItem(row,col,QTableWidgetItem(text))
            self.table.item(row,0).setData(Qt.UserRole,'value:'+ident)

    def choose(self):
        if self.table.currentRow()>=0:
            self.address=self.table.item(self.table.currentRow(),0).data(Qt.UserRole); self.accept()


class ValueReferencesDialog(QDialog):
    """Shared reference values only; private formula inputs stay in their editor."""
    def __init__(self, window):
        super().__init__(window)
        self.window = window
        draft = SimpleNamespace(variables=window.variables, value_names=window.value_names,
                                value_references=copy.deepcopy(window.value_references))
        self.data = enable_references(draft)
        mark_parameter_values(self.data)
        self.legacy_ids = {i for i, e in self.data['values'].items() if not e.get('parameter_owner') and not is_constant_reference(self.data, i)}
        self.point_names = dict(zip(self.data['points'], window.value_names))
        self._loading = True
        self._value_ident = None
        self.setWindowTitle(tr_ui('参照値')); self.resize(850, 650)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(tr_ui('物理定数など、すべての式・校正点で同じ値を使う参照値を登録します。')))
        split = QSplitter(); layout.addWidget(split, 1)
        left = QWidget(); side = QVBoxLayout(left)
        self.value_list = QListWidget(); side.addWidget(self.value_list)
        row = QHBoxLayout(); side.addLayout(row)
        add = QPushButton(tr_ui('追加')); add.clicked.connect(lambda: self.add_value()); row.addWidget(add)
        delete = QPushButton(tr_ui('削除')); delete.clicked.connect(self.delete_value); row.addWidget(delete)
        split.addWidget(left)
        self.value_panel = QWidget(); detail = QFormLayout(self.value_panel)
        self.value_name = QLineEdit(); self.value_unit = QLineEdit()
        detail.addRow(tr_ui('名前'), self.value_name); detail.addRow(tr_ui('単位'), self.value_unit)
        self.value_expression = ReferenceExpressionEdit(); detail.addRow(tr_ui('値または式'), self.value_expression)
        button = QPushButton(tr_ui('参照する値を挿入…')); button.clicked.connect(lambda: self.pick_reference(self.value_expression)); detail.addRow(button)
        self.value_description = QPlainTextEdit(); self.value_description.setMaximumHeight(80); detail.addRow(tr_ui('説明'), self.value_description)
        self.legacy_notice = QLabel(tr_ui('旧形式の点別・測定値参照は保持しています。変更は対象量の入力の対応付けで行ってください。'))
        self.legacy_notice.setWordWrap(True); self.legacy_notice.hide(); detail.addRow(self.legacy_notice)
        self.value_preview = QLabel(); self.value_preview.setWordWrap(True); detail.addRow(self.value_preview)
        split.addWidget(self.value_panel); split.setSizes([250, 550])
        self.error = QLabel(); self.error.setWordWrap(True); layout.addWidget(self.error)
        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.Save).setText(tr_ui('保存')); buttons.button(QDialogButtonBox.Cancel).setText(tr_ui('キャンセル'))
        buttons.accepted.connect(self.save); buttons.rejected.connect(self.reject); layout.addWidget(buttons)
        self.timer = QTimer(self); self.timer.setSingleShot(True); self.timer.setInterval(300); self.timer.timeout.connect(self.preview)
        self.finished.connect(lambda *_: self.timer.stop())
        for button in self.findChildren(QPushButton): button.setAutoDefault(False)
        self.value_list.currentItemChanged.connect(self.change_value)
        for field in (self.value_name, self.value_unit, self.value_expression, self.value_description):
            field.textChanged.connect(self.schedule_preview)
        for ident, entry in self.data['values'].items():
            if not entry.get('parameter_owner'): self._append_value(ident, entry)
        self._loading = False
        if self.value_list.count(): self.value_list.setCurrentRow(0)
        else: self.value_panel.setEnabled(False)

    def proxy(self):
        return SimpleNamespace(variable_values=copy.deepcopy(self.window.variable_values), regressions=copy.deepcopy(self.window.regressions),
            measurement_tables=copy.deepcopy(self.window.measurement_tables), value_references=self.capture())

    def _append_value(self, ident, entry):
        item = QListWidgetItem(entry['name'] if is_constant_reference(self.data, ident) else entry['name'] + tr_ui('（旧形式・読取専用）')); item.setData(Qt.UserRole, ident); self.value_list.addItem(item)

    def commit_value(self):
        if self._loading or not self._value_ident or self._value_ident in self.legacy_ids: return
        entry = self.data['values'][self._value_ident]
        entry.update(name=self.value_name.text().strip(), unit=self.value_unit.text().strip(), expression=self.value_expression.expression(),
                     scope='common', description=self.value_description.toPlainText())
        for i in range(self.value_list.count()):
            item = self.value_list.item(i)
            if item.data(Qt.UserRole) == self._value_ident: item.setText(entry['name'])

    def capture(self):
        self.commit_value(); data = copy.deepcopy(self.data)
        return data

    def load_value(self):
        self._loading = True
        item = self.value_list.currentItem(); self._value_ident = item.data(Qt.UserRole) if item else None
        self.value_panel.setEnabled(bool(item)); entry = self.data['values'].get(self._value_ident, {})
        self.value_name.setText(entry.get('name', '')); self.value_unit.setText(entry.get('unit', ''))
        self.value_expression.set_expression(entry.get('expression', ''), self.data, self.point_names)
        self.value_description.setPlainText(entry.get('description', ''))
        legacy = self._value_ident in self.legacy_ids
        for widget in (self.value_name, self.value_unit, self.value_expression, self.value_description): widget.setEnabled(not legacy)
        self.legacy_notice.setVisible(legacy); self._loading = False

    def change_value(self, *_):
        if self._loading: return
        self.commit_value(); self.load_value(); self.schedule_preview()

    def add_value(self):
        self.capture(); ident = new_id(); entry = dict(name=tr_ui('新しい参照値'), expression='', scope='common', unit='', overrides={})
        self.data['values'][ident] = entry; self._append_value(ident, entry); self.value_list.setCurrentRow(self.value_list.count()-1)
        self.value_name.setFocus(); self.value_name.selectAll()

    def delete_value(self):
        if not self._value_ident: return
        self.capture(); ident = self._value_ident; self._value_ident = None; self.data['values'].pop(ident)
        self.value_list.takeItem(self.value_list.currentRow()); self.load_value(); self.schedule_preview()

    def pick_reference(self, editor):
        self.capture(); picker = ReferencePicker(self)
        if picker.exec(): editor.insert_reference(picker.address, self.data, self.point_names)

    def schedule_preview(self, *_):
        if self._loading: return
        self.value_preview.clear(); self.timer.start()

    def display_error(self, message):
        return re.sub(r'(?:value:[\w-]+(?::[\w-]+)?|variable:[\w-]+:central_value:[\w-]+)',
            lambda m: address_label(m[0], self.data, self.point_names), message)

    def preview(self):
        self.timer.stop(); self.error.clear()
        if not self._value_ident or not is_constant_reference(self.data, self._value_ident): self.value_preview.clear(); return
        try:
            data = self.capture(); value = ReferenceEvaluator(data, self.window.variable_values, self.proxy()).resolve('value:'+self._value_ident)
            self.value_preview.setText(tr_ui('値：{0} {1}').format(format(value, '.10g'), self.value_unit.text()))
            self.value_preview.setToolTip(str(value))
        except Exception as error: self.value_preview.setText(self.display_error(str(error)))

    def save(self):
        try:
            data = self.capture(); proxy = self.proxy()
            prune_parameter_values(data, [proxy.regressions, proxy.measurement_tables, proxy.variable_values])
            validate_references(data, len(self.window.value_names))
            for ident, entry in data['values'].items():
                if entry.get('parameter_owner'): continue
                original = self.window.value_references and self.window.value_references['values'].get(ident)
                if not is_constant_reference(data, ident) and entry != original:
                    raise ValueError(tr_ui('参照値の式には全点共通の参照値だけを使用できます。'))
            evaluator = ReferenceEvaluator(data, proxy.variable_values, proxy)
            for ident, entry in data['values'].items():
                if entry.get('parameter_owner') or not is_constant_reference(data, ident): continue
                if not entry['name'].strip(): raise ValueError(tr_ui('参照値の名前を入力してください。'))
                for point in [None]:
                    try: evaluator.resolve('value:'+ident, point)
                    except Exception as error: raise ValueError(entry['name']+': '+self.display_error(str(error))) from error
            failures = [self.window.value_names[i]+': '+r['error'] for (_, i), r in evaluate_half_widths(data, proxy.variable_values, proxy).items() if r['error']]
            if failures: raise ValueError('\n'.join(failures))
            self.window.value_references = data; self.window.refresh_references(); self.window.variables_tab.display_current_value(); self.accept()
        except Exception as error: self.error.setText(self.display_error(str(error)))


