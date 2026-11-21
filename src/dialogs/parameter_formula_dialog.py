"""Create a Type B formula, bind its arguments, then review every point."""
import copy
import re
from types import SimpleNamespace
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPlainTextEdit,
    QLineEdit, QPushButton, QStackedWidget, QWidget, QFormLayout, QComboBox,
    QTableWidget, QTableWidgetItem, QScrollArea, QMenu, QDialogButtonBox)
from src.utils.ui_translation import tr_ui
from src.utils.value_references import enable_references, new_id, evaluate_half_widths, ReferenceEvaluator, TOKEN, is_constant_reference
from src.utils.parameter_formula import argument_names, compile_formula, unpack_rule, mark_parameter_values, prune_parameter_values
from src.widgets.reference_expression_edit import address_label


class ParameterFormulaDialog(QDialog):
    def __init__(self, window, variable, point_id=None):
        super().__init__(window)
        self.window, self.variable = window, variable
        draft = SimpleNamespace(variables=window.variables, value_names=window.value_names,
                                value_references=copy.deepcopy(window.value_references))
        self.data = enable_references(draft)
        mark_parameter_values(self.data)
        self.ident = self.data['variables'][variable]
        self.editing_override = point_id
        self.input_points = [point_id] if point_id else self.data['points']
        self.base_rule = copy.deepcopy(self.data['rules'][self.ident] if self.ident in self.data['rules'] else self.legacy_rule())
        self.rule = copy.deepcopy(self.base_rule)
        if point_id:
            self.rule = dict(expression=self.base_rule.get('overrides', {}).get(point_id, self.base_rule['expression']),
                parameter_setup=copy.deepcopy(self.base_rule.get('override_setups', {}).get(point_id, self.base_rule.get('parameter_setup', {}))))
        formula, self.bindings = unpack_rule(self.rule)
        self.bindings = copy.deepcopy(self.bindings)
        if point_id:
            # A local formula may start from the base, but its manual inputs must
            # not mutate values used by the base or another point's formula.
            for binding in self.bindings.values():
                ident = binding.get('manual_id')
                if ident in self.data['values']:
                    replacement = new_id(); self.data['values'][replacement] = copy.deepcopy(self.data['values'][ident])
                    binding.update(manual_id=replacement, address='value:'+replacement)
        self.fields = {}
        self.point_names = dict(zip(self.data['points'], window.value_names))
        self.setWindowTitle(tr_ui('入力幅の計算式を設定'))
        self.resize(850, 700)
        layout = QVBoxLayout(self)
        info = window.variable_values[variable]
        width = tr_ui('拡張不確かさ') if info.get('distribution') == 'NORMAL_DISTRIBUTION' else tr_ui('半値幅')
        layout.addWidget(QLabel(tr_ui('量：{0} / 計算対象：{1} / 単位：{2}').format(variable, width, info.get('unit', ''))))
        self.steps = QLabel(); layout.addWidget(self.steps)
        self.pages = QStackedWidget(); layout.addWidget(self.pages, 1)
        page = QWidget(); form = QVBoxLayout(page)
        form.addWidget(QLabel(tr_ui('式に使う値を名前で記入し、次の画面で取得方法を指定します。')))
        self.formula = QPlainTextEdit(formula); form.addWidget(self.formula)
        functions = QPushButton(tr_ui('関数を挿入')); menu = QMenu(functions)
        for label, text in ((tr_ui('絶対値'), 'abs'), (tr_ui('平方根'), 'sqrt')):
            menu.addAction(label).triggered.connect(lambda _=False, name=text: self.insert_function(name))
        functions.setMenu(menu); form.addWidget(functions)
        self.names_label = QLabel(); form.addWidget(self.names_label)
        self.formula.textChanged.connect(self.show_names)
        self.pages.addWidget(page)
        self.binding_page = QScrollArea(); self.binding_page.setWidgetResizable(True)
        self.pages.addWidget(self.binding_page)
        page = QWidget(); body = QVBoxLayout(page)
        edit = QHBoxLayout()
        for label, index in ((tr_ui('式を変更'), 0), (tr_ui('入力の対応を変更'), 1)):
            button = QPushButton(label); button.clicked.connect(lambda _=False, i=index: self.go(i)); edit.addWidget(button)
        body.addLayout(edit)
        self.summary = QLabel(); self.summary.setWordWrap(True); body.addWidget(self.summary)
        self.direct = QPushButton(tr_ui('直接入力へ戻す'))
        self.direct.setFlat(True); self.direct.setMaximumWidth(200)
        self.direct.clicked.connect(self.use_direct_input); body.addWidget(self.direct)
        self.results = QTableWidget(); self.results.setEditTriggers(QTableWidget.NoEditTriggers); body.addWidget(self.results, 1)
        self.substitution = QLabel(); self.substitution.setWordWrap(True); body.addWidget(self.substitution)
        self.results.currentCellChanged.connect(lambda row, *_: self.show_substitution(row))
        self.pages.addWidget(page)
        if point_id:
            layout.addWidget(QLabel(tr_ui('適用する校正点：{0}').format(self.point_names[point_id])))
            self.direct.hide()
        else:
            button = QPushButton(tr_ui('点ごとの別式を編集'))
            button.clicked.connect(self.edit_overrides); layout.addWidget(button)
        self.error = QLabel(); self.error.setWordWrap(True); layout.addWidget(self.error)
        footer = QHBoxLayout(); layout.addLayout(footer)
        cancel = QPushButton(tr_ui('キャンセル')); cancel.clicked.connect(self.reject); footer.addWidget(cancel)
        footer.addStretch()
        self.back = QPushButton(tr_ui('戻る')); self.back.clicked.connect(lambda: self.go(self.pages.currentIndex()-1)); footer.addWidget(self.back)
        self.next = QPushButton(tr_ui('次へ')); self.next.clicked.connect(lambda: self.go(self.pages.currentIndex()+1)); footer.addWidget(self.next)
        self.apply = QPushButton(tr_ui('適用')); self.apply.clicked.connect(self.save); footer.addWidget(self.apply)
        for button in self.findChildren(QPushButton): button.setAutoDefault(False)
        self.show_names()
        self.go(2 if self.rule['expression'] else 0)

    def legacy_rule(self):
        """Offer old one-shot formulas for explicit adoption, without changing data."""
        values = self.window.variable_values[self.variable].get('values', [])
        if not any(value.get('calculation_formula') for value in values): return dict(expression='', overrides={})
        rules = []
        for value in values:
            text = value.get('calculation_formula') or str(value.get('half_width') or '0')
            try: names = argument_names(text)
            except (SyntaxError, ValueError): names = []
            bindings = {name: dict(kind='variable', address='variable:'+self.data['variables'][name]+':central_value:current')
                        for name in names if name in self.data['variables']}
            try: expression = compile_formula(text, bindings)
            except (ValueError, SyntaxError): expression = text
            rules.append(dict(expression=expression, parameter_setup=dict(formula=text, bindings=bindings)))
        rule = copy.deepcopy(rules[0]); rule['overrides'] = {}; rule['override_setups'] = {}
        for point, entry in zip(self.data['points'], rules):
            if entry['expression'] != rule['expression']:
                rule['overrides'][point] = entry['expression']; rule['override_setups'][point] = entry['parameter_setup']
        return rule

    def external_references(self):
        return [self.window.regressions, self.window.measurement_tables, self.window.variable_values]

    def show_names(self):
        try:
            self.names_label.setText(tr_ui('必要な入力：{0}').format(', '.join(argument_names(self.formula.toPlainText())) or tr_ui('なし')))
        except (SyntaxError, ValueError):
            self.names_label.setText(tr_ui('式の構文を確認してください。'))

    def insert_function(self, name):
        cursor = self.formula.textCursor()
        selected = cursor.selectedText()
        cursor.insertText(name + '(' + selected + ')')
        if not selected: cursor.movePosition(cursor.Left)
        self.formula.setTextCursor(cursor); self.formula.setFocus()

    def collect(self):
        for name, (kind, common, points, reference, quantity) in self.fields.items():
            mode = kind.currentData()
            binding = self.bindings.get(name, {})
            if mode in ('common', 'point'):
                ident = binding.get('manual_id') or new_id()
                entry = dict(name=self.variable + ' / ' + name, unit=self.data['values'].get(ident, {}).get('unit', ''), scope=mode,
                             expression=common.text().strip() if mode == 'common' else '', overrides={}, parameter_owner=self.ident)
                if mode == 'point':
                    entry['overrides'] = {p: points.item(i, 1).text().strip() for i, p in enumerate(self.input_points)}
                self.data['values'][ident] = entry
                binding = dict(kind=mode, manual_id=ident, address='value:' + ident)
            elif mode == 'variable':
                ident = quantity.currentData()
                binding = dict(kind=mode, address='variable:' + str(ident) + ':central_value:current')
            else:
                binding = dict(kind='reference', address=reference.currentData() or '')
            self.bindings[name] = binding

    def build_bindings(self):
        names = argument_names(self.formula.toPlainText())
        content = QWidget(); layout = QVBoxLayout(content)
        if not names: layout.addWidget(QLabel(tr_ui('この式には対応付けが必要な入力はありません。')))
        self.fields = {}
        for name in names:
            binding = self.bindings.get(name, {})
            group = QWidget(); form = QFormLayout(group)
            kind = QComboBox()
            for label, code in ((tr_ui('全点共通の数値'), 'common'), (tr_ui('校正点ごとの数値'), 'point'),
                                (tr_ui('登録済みの参照値'), 'reference'), (tr_ui('量の中心値'), 'variable')):
                kind.addItem(label, code)
            form.addRow(name, kind)
            common = QLineEdit(); form.addRow(tr_ui('値'), common)
            points = QTableWidget(len(self.input_points), 2)
            points.setHorizontalHeaderLabels([tr_ui('校正点'), tr_ui('値')]); points.setMaximumHeight(190)
            entry = self.data['values'].get(binding.get('manual_id'), {})
            common.setText(entry.get('expression', ''))
            for i, p in enumerate(self.input_points):
                item = QTableWidgetItem(self.point_names[p]); item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                points.setItem(i, 0, item)
                points.setItem(i, 1, QTableWidgetItem(entry.get('overrides', {}).get(p, '')))
            form.addRow(points)
            reference = QComboBox(); reference.addItem(tr_ui('選択してください'), '')
            for ident, value in self.data['values'].items():
                if is_constant_reference(self.data, ident): reference.addItem(value['name'], 'value:' + ident)
            address = binding.get('address', '')
            if address and reference.findData(address) < 0:
                reference.addItem(address_label(address, self.data, self.point_names), address)
            reference.setCurrentIndex(max(0, reference.findData(address)))
            form.addRow(tr_ui('参照値'), reference)
            quantity = QComboBox(); quantity.addItem(tr_ui('選択してください'), None)
            for var, ident in self.data['variables'].items():
                if self.window.variable_values.get(var, {}).get('type') != 'result': quantity.addItem(var, ident)
            if binding.get('kind') == 'variable': quantity.setCurrentIndex(quantity.findData(address.split(':')[1]))
            form.addRow(tr_ui('量'), quantity)
            def visibility(*_, k=kind, f=form, c=common, p=points, r=reference, q=quantity):
                for field, code in ((c, 'common'), (p, 'point'), (r, 'reference'), (q, 'variable')): f.setRowVisible(field, k.currentData() == code)
            kind.setCurrentIndex(max(0, kind.findData(binding.get('kind', 'common'))))
            kind.currentIndexChanged.connect(visibility); visibility()
            self.fields[name] = kind, common, points, reference, quantity
            layout.addWidget(group)
        layout.addStretch(); self.binding_page.setWidget(content)

    def draft(self):
        self.collect()
        names = argument_names(self.formula.toPlainText())
        bindings = {name: self.bindings[name] for name in names}
        rule = copy.deepcopy(self.rule)
        rule['expression'] = compile_formula(self.formula.toPlainText(), bindings)
        rule['parameter_setup'] = dict(formula=self.formula.toPlainText().strip(), bindings=copy.deepcopy(bindings))
        if self.editing_override:
            local = rule; rule = copy.deepcopy(self.base_rule)
            rule.setdefault('overrides', {})[self.editing_override] = local['expression']
            rule.setdefault('override_setups', {})[self.editing_override] = local['parameter_setup']
        data = copy.deepcopy(self.data); data['rules'][self.ident] = rule
        prune_parameter_values(data, self.external_references())
        return data

    def go(self, index):
        try:
            self.collect()
            argument_names(self.formula.toPlainText()) if index > 0 else None
            if index == 1: self.build_bindings()
            if index == 2:
                if not self.fields: self.build_bindings()
                self.review()
            self.pages.setCurrentIndex(index); self.error.clear()
            self.steps.setText((tr_ui('1. 計算式'), tr_ui('2. 入力の対応付け'), tr_ui('3. 計算結果の確認'))[index])
            self.back.setVisible(index > 0); self.next.setVisible(index < 2); self.apply.setVisible(index == 2)
        except (ValueError, SyntaxError, KeyError) as error:
            self.error.setText(tr_ui('入力を確認してください：{0}').format(str(error)))

    def review(self):
        data = self.draft(); proxy = SimpleNamespace(variable_values=copy.deepcopy(self.window.variable_values),
            regressions=self.window.regressions, measurement_tables=self.window.measurement_tables, value_references=data)
        self.review_data, self.review_proxy = data, proxy
        names = argument_names(self.formula.toPlainText())
        descriptions = []
        for name in names:
            binding = self.bindings[name]
            kind = binding.get('kind')
            label = tr_ui('全点共通の数値') if kind == 'common' else tr_ui('校正点ごとの数値') if kind == 'point' else address_label(binding['address'], data, self.point_names)
            descriptions.append(name + ' = ' + label)
        self.summary.setText(self.formula.toPlainText() + '\n' + '\n'.join(descriptions))
        self.results.setColumnCount(len(names)+4)
        self.results.setHorizontalHeaderLabels([tr_ui('校正点')] + names + [tr_ui('入力幅'), tr_ui('標準不確かさ'), tr_ui('状態')])
        self.review_points = [self.editing_override] if self.editing_override else data['points']
        self.results.setRowCount(len(self.review_points))
        results = evaluate_half_widths(data, proxy.variable_values, proxy)
        evaluator = ReferenceEvaluator(data, proxy.variable_values, proxy)
        self.failures = []
        for row, p in enumerate(self.review_points):
            i = data['points'].index(p)
            values = [self.point_names[p]]
            for name in names:
                try: values.append(str(evaluator.resolve(self.bindings[name]['address'], p)))
                except Exception: values.append(tr_ui('未入力・参照先を確認'))
            result = results[self.variable, i]
            message = re.sub(r'(?:value:[\w-]+(?::[\w-]+)?|variable:[\w-]+:central_value:[\w-]+)',
                lambda m: address_label(m[0], data, self.point_names), result['error'])
            values += ['--' if result['error'] else format(result['value'], '.10g'), '--' if result['error'] else format(result['uncertainty'], '.10g'), message or 'OK']
            if result['error']: self.failures.append(self.point_names[p] + ': ' + message)
            for col, value in enumerate(values): self.results.setItem(row, col, QTableWidgetItem(value))
            if not result['error']:
                self.results.item(row, len(names)+1).setToolTip(str(result['value']))
                self.results.item(row, len(names)+2).setToolTip(str(result['uncertainty']))
        self.results.resizeColumnsToContents(); self.results.selectRow(0); self.show_substitution(0)

    def show_substitution(self, row):
        if row < 0 or not hasattr(self, 'review_data'): return
        try:
            p = self.review_points[row]; rule = self.review_data['rules'][self.ident]
            expression = rule.get('overrides', {}).get(p, rule['expression'])
            evaluator = ReferenceEvaluator(self.review_data, self.review_proxy.variable_values, self.review_proxy)
            self.substitution.setText(TOKEN.sub(lambda m: '('+str(evaluator.resolve(m[1], p))+')', expression).replace('math.', ''))
        except Exception:
            self.substitution.clear()

    def edit_overrides(self):
        try:
            dialog = PointFormulaDialog(self, self.draft())
            if dialog.exec():
                self.data = copy.deepcopy(dialog.draft_window.value_references)
                self.base_rule = copy.deepcopy(self.data['rules'][self.ident])
                self.rule = copy.deepcopy(self.base_rule)
                formula, bindings = unpack_rule(self.rule)
                self.bindings = copy.deepcopy(bindings); self.fields = {}
                self.formula.setPlainText(formula); self.go(2)
        except Exception as error: self.error.setText(str(error))

    def save(self):
        try:
            self.review()
            if self.failures:
                self.error.setText('\n'.join(self.failures)); return
            self.window.value_references = self.review_data
            for value in self.window.variable_values[self.variable]['values']:
                value.pop('calculation_formula', None)
            self.window.refresh_references(); self.window.variables_tab.display_current_value()
            self.accept()
        except (ValueError, SyntaxError, KeyError) as error:
            self.error.setText(tr_ui('入力を確認してください：{0}').format(str(error)))

    def use_direct_input(self):
        # Keep the last evaluated widths, matching the existing direct-input action.
        data = copy.deepcopy(self.window.value_references)
        if data is not None:
            if self.editing_override:
                data['rules'][self.ident].get('overrides', {}).pop(self.editing_override, None)
                data['rules'][self.ident].get('override_setups', {}).pop(self.editing_override, None)
            else:
                data['rules'].pop(self.ident, None)
            prune_parameter_values(data, self.external_references())
            self.window.value_references = data
            self.window.refresh_references()
            self.window.variables_tab.display_current_value()
        for value in self.window.variable_values[self.variable]['values']:
            value.pop('calculation_formula', None)
        self.accept()


class PointFormulaDialog(QDialog):
    """Select a local formula; its editor is the same parameter-based editor."""
    def __init__(self, owner, data):
        super().__init__(owner)
        self.owner = owner
        self.draft_window = QWidget(self)
        for key, value in dict(variables=owner.window.variables, value_names=owner.window.value_names,
                current_value_index=owner.window.current_value_index, value_references=copy.deepcopy(data),
                variable_values=copy.deepcopy(owner.window.variable_values), regressions=owner.window.regressions,
                measurement_tables=owner.window.measurement_tables, refresh_references=lambda: None,
                variables_tab=SimpleNamespace(display_current_value=lambda: None)).items():
            setattr(self.draft_window, key, value)
        self.setWindowTitle(tr_ui('点ごとの別式を編集')); self.resize(500, 230)
        layout = QVBoxLayout(self)
        self.point = QComboBox()
        for ident, name in owner.point_names.items(): self.point.addItem(name, ident)
        self.point.setCurrentIndex(owner.window.current_value_index); layout.addWidget(self.point)
        self.status = QLabel(); layout.addWidget(self.status)
        edit = QPushButton(tr_ui('式を変更')); edit.clicked.connect(self.edit); layout.addWidget(edit)
        self.reset = QPushButton(tr_ui('この点を基本式に戻す')); self.reset.clicked.connect(self.reset_point); layout.addWidget(self.reset)
        self.point.currentIndexChanged.connect(self.refresh)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept); buttons.rejected.connect(self.reject); layout.addWidget(buttons)
        buttons.button(QDialogButtonBox.Cancel).setText(tr_ui('キャンセル'))
        for button in self.findChildren(QPushButton): button.setAutoDefault(False)
        self.refresh()

    def refresh(self):
        local = self.point.currentData() in self.draft_window.value_references['rules'][self.owner.ident].get('overrides', {})
        self.status.setText(tr_ui('この校正点だけ別の式') if local else tr_ui('全校正点の基本式'))
        self.reset.setEnabled(local)

    def edit(self):
        dialog = ParameterFormulaDialog(self.draft_window, self.owner.variable, self.point.currentData())
        if dialog.exec(): self.refresh()

    def reset_point(self):
        data = self.draft_window.value_references
        rule = data['rules'][self.owner.ident]
        rule.get('overrides', {}).pop(self.point.currentData(), None)
        rule.get('override_setups', {}).pop(self.point.currentData(), None)
        prune_parameter_values(data, self.owner.external_references()); self.refresh()
