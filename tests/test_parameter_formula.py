import copy
from decimal import Decimal
from tests.test_value_references import model, window
from src.dialogs.parameter_formula_dialog import ParameterFormulaDialog
from src.utils.parameter_formula import argument_names, compile_formula
from src.utils.value_references import evaluate_half_widths
from src.utils.project_io import write_project, read_project


def test_arguments_and_safe_compilation():
    assert argument_names('a*abs(reading)*1e-6+b*range*1e-6') == ['a', 'b', 'range', 'reading']
    assert argument_names('sqrt(x^2)+math.sin(x)') == ['x']
    assert argument_names('2e-6') == []
    assert compile_formula('x+x', {'x': {'address': 'value:x'}}) == '@{value:x}+@{value:x}'


def setup_formula(window):
    dialog = ParameterFormulaDialog(window, 'e')
    dialog.go(0)
    dialog.formula.setPlainText('a*abs(reading)*1e-6+b*range*1e-6')
    dialog.go(1)
    for name, text in [('a', '20'), ('b', '5')]:
        fields = dialog.fields[name]
        fields[0].setCurrentIndex(fields[0].findData('common')); fields[1].setText(text)
    fields = dialog.fields['range']; fields[0].setCurrentIndex(fields[0].findData('point'))
    for i, value in enumerate(['10', '100']): fields[2].item(i, 1).setText(value)
    fields = dialog.fields['reading']; fields[0].setCurrentIndex(fields[0].findData('variable'))
    fields[4].setCurrentIndex(fields[4].findData('x'))
    return dialog


def test_create_update_reload_and_reorder(window, tmp_path):
    dialog = setup_formula(window); dialog.go(2)
    assert not dialog.failures
    assert Decimal(dialog.results.item(0, 5).text()) == Decimal('.000110')
    dialog.save(); assert dialog.result() == dialog.DialogCode.Accepted
    for suffix in ('json', 'cutp'):
        path = tmp_path / ('sample.' + suffix)
        write_project(path, window.get_save_data())
        assert window.load_data(read_project(path), show_message=False)
    reopened = ParameterFormulaDialog(window, 'e')
    assert reopened.pages.currentIndex() == 2
    assert reopened.formula.toPlainText() == 'a*abs(reading)*1e-6+b*range*1e-6'
    reopened.reject()
    window.variable_values['x']['values'][0]['central_value'] = '4'
    window.refresh_references()
    assert Decimal(window.variable_values['e']['values'][0]['half_width']) == Decimal('.000130')
    window.point_settings_tab.update_display(); window.point_settings_tab.table.selectRow(0)
    window.point_settings_tab.move_point_down()
    assert evaluate_half_widths(window.value_references, window.variable_values)['e', 0]['value'] == Decimal('.000660')


def test_cancel_invalid_and_partial_edit(window):
    original = copy.deepcopy(window.get_save_data())
    dialog = setup_formula(window)
    dialog.fields['range'][2].item(1, 1).setText('')
    dialog.go(2); assert dialog.failures
    dialog.save(); assert dialog.result() != dialog.DialogCode.Accepted
    dialog.go(1); dialog.fields['range'][2].item(1, 1).setText('100')
    dialog.go(0); dialog.formula.setPlainText('a*abs(reading)*1e-6+b*range*1e-6+extra')
    dialog.go(1)
    assert dialog.fields['a'][1].text() == '20'
    assert dialog.fields['range'][2].item(1, 1).text() == '100'
    assert dialog.fields['extra'][1].text() == ''
    dialog.reject(); assert window.get_save_data() == original


def test_legacy_override_and_constant_formula(window):
    window.value_references['rules']['e']['overrides'] = {'p2': '.25'}
    dialog = ParameterFormulaDialog(window, 'e')
    assert not dialog.failures
    assert Decimal(dialog.results.item(1, dialog.results.columnCount()-3).text()) == Decimal('.25')
    dialog.go(0); dialog.formula.setPlainText('2e-6'); dialog.go(1); dialog.go(2); dialog.save()
    assert window.value_references['rules']['e']['overrides'] == {'p2': '.25'}
    assert Decimal(window.variable_values['e']['values'][0]['half_width']) == Decimal('2e-6')


def test_legacy_constants_and_override_edit_cancel(window, monkeypatch):
    from src.dialogs.parameter_formula_dialog import PointFormulaDialog
    window.value_references['rules']['e']['overrides'] = {'p2': '.25'}
    before = copy.deepcopy(window.get_save_data())
    dialog = ParameterFormulaDialog(window, 'e')
    def edit_point(browser):
        inner = ParameterFormulaDialog(browser.draft_window, 'e', 'p1')
        inner.go(0); inner.formula.setPlainText('.5'); inner.go(1); inner.go(2); inner.save()
        assert inner.result() == inner.DialogCode.Accepted
        browser.accept(); return browser.result()
    monkeypatch.setattr(PointFormulaDialog, 'exec', edit_point)
    dialog.edit_overrides()
    assert not dialog.error.text()
    assert dialog.rule['overrides']['p1'] == '.5'
    dialog.reject()
    assert window.get_save_data() == before
    assert argument_names('math.pi + math.sqrt(4)') == []


def test_partial_edit_does_not_leave_empty_unused_parameters(window):
    dialog = setup_formula(window)
    dialog.go(0); dialog.formula.setPlainText('abs(a)+abs(reading)'); dialog.go(1)
    dialog.fields['a'][0].setCurrentIndex(dialog.fields['a'][0].findData('variable'))
    dialog.fields['a'][4].setCurrentIndex(dialog.fields['a'][4].findData('x'))
    dialog.go(2); dialog.save()
    assert dialog.result() == dialog.DialogCode.Accepted
    assert all(e['expression'] or e.get('overrides') for e in window.value_references['values'].values())
    widths = [v['half_width'] for v in window.variable_values['e']['values']]
    reopened = ParameterFormulaDialog(window, 'e'); reopened.use_direct_input()
    assert 'e' not in window.value_references['rules']
    assert [v['half_width'] for v in window.variable_values['e']['values']] == widths


def test_private_inputs_are_not_shared_values_and_removed_after_reopen(window):
    from src.dialogs.value_references_dialog import ValueReferencesDialog, ReferencePicker
    dialog = setup_formula(window); dialog.go(2); dialog.save()
    owned = {i for i, e in window.value_references['values'].items() if e.get('parameter_owner')}
    assert len(owned) == 3
    manager = ValueReferencesDialog(window)
    assert manager.value_list.count() == 3
    picker = ReferencePicker(manager); assert picker.table.rowCount() == 2
    picker.reject(); manager.reject()
    editor = ParameterFormulaDialog(window, 'e'); editor.go(0)
    editor.formula.setPlainText('abs(reading)'); editor.go(1); editor.go(2); editor.save()
    assert not (owned & window.value_references['values'].keys())
    assert set(window.value_references['values']) == {'a', 'b', 'range'}


def test_cleanup_follows_dependencies_and_keeps_shared_or_external_uses(window):
    from src.utils.parameter_formula import prune_parameter_values
    dialog = setup_formula(window); dialog.go(2); dialog.save()
    private = window.value_references['rules']['e']['parameter_setup']['bindings']['a']['manual_id']
    refs = window.value_references
    refs['values']['shared'] = dict(name='Shared alias', expression='@{value:'+private+'}')
    refs['values']['cycle1'] = dict(name='Unused 1', parameter_owner='e', expression='@{value:cycle2}')
    refs['values']['cycle2'] = dict(name='Unused 2', parameter_owner='e', expression='@{value:cycle1}')
    dialog = ParameterFormulaDialog(window, 'e'); dialog.use_direct_input()
    assert private in window.value_references['values']
    assert not {'cycle1', 'cycle2'} & window.value_references['values'].keys()
    assert len(window.value_references['values']) == 5
    refs = window.value_references
    del refs['values']['shared']
    assert not prune_parameter_values(refs, {'x_expression': '@{value:'+private+'}'})
    assert private in refs['values']
    assert prune_parameter_values(refs) == {private}


def test_local_formula_reuses_editor_without_changing_base_manual_inputs(window):
    from src.dialogs.parameter_formula_dialog import PointFormulaDialog
    dialog = setup_formula(window); dialog.go(2); dialog.save()
    original = copy.deepcopy(window.value_references['rules']['e'])
    editor = ParameterFormulaDialog(window, 'e', 'p1'); editor.go(1)
    editor.fields['a'][1].setText('40'); editor.go(2); editor.save()
    assert not editor.failures
    assert window.value_references['rules']['e']['expression'] == original['expression']
    assert Decimal(window.variable_values['e']['values'][1]['half_width']) == Decimal('.000660')
    assert Decimal(window.variable_values['e']['values'][0]['half_width']) == Decimal('.000170')
    browser = PointFormulaDialog(ParameterFormulaDialog(window, 'e'), window.value_references)
    browser.reset_point(); browser.accept()
    assert 'p1' not in browser.draft_window.value_references['rules']['e'].get('overrides', {})
    assert len([e for e in browser.draft_window.value_references['values'].values() if e.get('parameter_owner')]) == 3
    browser.reject()


def test_voltage_sample_uses_named_parameters_only(window):
    from examples.voltage_comparison.build_sample import make_project
    data = make_project()
    assert len(data['value_references']['values']) == 5
    assert all(e.get('parameter_owner') for e in data['value_references']['values'].values())
    assert window.load_data(data, show_message=False)
    for name in ('Vdut_digit', 'deltaV_refdigit', 'deltaV_stability'):
        dialog = ParameterFormulaDialog(window, name)
        assert dialog.pages.currentIndex() == 2 and not dialog.failures
        assert 'input_' not in dialog.formula.toPlainText()
        dialog.reject()


def test_point_deletion_removes_point_values_and_local_inputs(window, monkeypatch):
    from PySide6.QtWidgets import QMessageBox
    dialog = setup_formula(window); dialog.go(2); dialog.save()
    local = ParameterFormulaDialog(window, 'e', 'p1'); local.go(1)
    local.fields['a'][1].setText('40'); local.go(2); local.save()
    monkeypatch.setattr(QMessageBox, 'question', lambda *args: QMessageBox.Yes)
    window.point_settings_tab.update_display(); window.point_settings_tab.table.selectRow(0)
    window.point_settings_tab.remove_point()
    refs = window.value_references
    assert refs['points'] == ['p2']
    assert len([e for e in refs['values'].values() if e.get('parameter_owner')]) == 3
    assert 'p1' not in refs['rules']['e']['overrides']
    assert 'p1' not in refs['rules']['e']['override_setups']
    assert all('p1' not in e.get('overrides', {}) for e in refs['values'].values())


def test_removing_target_quantity_removes_rule_and_private_inputs(window):
    dialog = setup_formula(window); dialog.go(2); dialog.save()
    window.variables.remove('e'); window.prune_variable_values()
    assert 'e' not in window.value_references['rules']
    assert not any(e.get('parameter_owner') for e in window.value_references['values'].values())

