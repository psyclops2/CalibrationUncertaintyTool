import copy
from decimal import Decimal

import pytest
from PySide6.QtWidgets import QApplication
from src.main_window import MainWindow
from src.utils.value_references import ReferenceEvaluator, evaluate_half_widths, validate_references
from src.dialogs.value_references_dialog import ValueReferencesDialog
from src.dialogs.parameter_formula_dialog import ParameterFormulaDialog


@pytest.fixture
def model():
    data = {"version":1,"variables":{"x":"x","e":"e"},"points":["p1","p2"],
            "values":{"a":{"name":"reading ppm","expression":"20"},
                      "b":{"name":"range ppm","expression":"5"},
                      "range":{"name":"range V","expression":"10","scope":"point","overrides":{"p2":"100"}}},
            "rules":{"e":{"expression":"abs(@{variable:x:central_value:current})*@{value:a}*1e-6+@{value:range}*@{value:b}*1e-6"}}}
    variables = {"x":{"type":"fixed","unit":"V","values":[{"central_value":"3"},{"central_value":"-8"}]},
                 "e":{"type":"B","unit":"V","divisor":"2","values":[{"central_value":"0"},{"central_value":"0"}]}}
    return data,variables


def test_point_aware_ppm_and_source_changes(model):
    data,variables = model
    result = evaluate_half_widths(data,variables)
    assert result['e',0]['value'] == Decimal('0.000110')
    assert result['e',1]['value'] == Decimal('0.000660')
    variables['x']['values'][0]['central_value'] = '4'
    assert evaluate_half_widths(data,variables)['e',0]['value'] == Decimal('0.000130')
    data['values']['a']['expression'] = '40'
    assert evaluate_half_widths(data,variables)['e',0]['value'] == Decimal('0.000210')


@pytest.mark.parametrize('expression', ['@{value:a}', '@{value:missing}', '1/0','-1','NaN','__import__("os")'])
def test_bad_expression_blocks_old_result(model,expression):
    data,variables=model
    data['values']['a']['expression']='@{value:a}'
    data['rules']['e']['expression']=expression
    result=evaluate_half_widths(data,variables)['e',0]
    assert result['error']
    assert result['value'] is None


def test_current_point_not_available_in_common_value(model):
    data,variables=model
    data['values']['a']['expression']='@{variable:x:central_value:current}'
    assert evaluate_half_widths(data,variables)['e',0]['error']


def test_fixed_point_survives_reorder_and_reports_deletion(model):
    data,variables=model
    evaluator=ReferenceEvaluator(data,variables)
    assert evaluator.resolve('variable:x:central_value:p1','p2')==3
    data['points'].reverse()
    for entry in variables.values():entry['values'].reverse()
    assert ReferenceEvaluator(data,variables).resolve('variable:x:central_value:p1','p2')==3
    data['points'].remove('p1')
    with pytest.raises(ValueError):
        ReferenceEvaluator(data,variables).resolve('variable:x:central_value:p1','p2')


def test_abs_retains_decimal_precision(model):
    data,variables=model
    value='-1.123456789012345678901234567'
    variables['x']['values'][0]['central_value']=value
    assert ReferenceEvaluator(data,variables).expression('abs(@{variable:x:central_value:current})','p1')==Decimal(value).copy_abs()


@pytest.fixture
def window(model):
    app=QApplication.instance() or QApplication([])
    window=MainWindow()
    refs,variables=model
    payload={'variables':['Y','x','e'],'result_variables':['Y'],'last_equation':'Y = x + e',
             'value_names':['P1','P2'],'value_count':2,'variable_values':copy.deepcopy(variables),
             'value_references':copy.deepcopy(refs)}
    assert window.load_data(payload,show_message=False)
    yield window
    window.hide();window.close()


def test_consumers_and_save_reload(window):
    handler=window.uncertainty_calculation_tab.value_handler
    assert Decimal(handler.get_standard_uncertainty('e'))==Decimal('.000055')
    window.variable_values['x']['values'][0]['central_value']='4'
    assert Decimal(handler.get_standard_uncertainty('e'))==Decimal('.000065')
    payload=window.get_save_data()
    assert window.load_data(payload,show_message=False)
    assert window.value_references==payload['value_references']
    window.value_references['values']['a']['expression']='@{value:missing}'
    with pytest.raises(ValueError):handler.get_standard_uncertainty('e')
    assert window.variable_values['e']['values'][0]['standard_uncertainty']==''
    assert window.get_save_data()['value_references']['values']['a']['expression']=='@{value:missing}'


def test_dialog_cancel_does_not_change_model(window):
    original=copy.deepcopy(window.value_references)
    dialog=ValueReferencesDialog(window)
    dialog.add_value()
    dialog.reject()
    assert window.value_references==original


def test_schema_rejects_duplicate_ids(model):
    refs,_=model
    refs['points']=['p1','p1']
    with pytest.raises(ValueError):validate_references(refs,2)


def test_shared_values_manager_has_no_second_formula_editor(window):
    dialog=ValueReferencesDialog(window)
    dialog.preview()
    assert not hasattr(dialog, 'formula') and not hasattr(dialog, 'tabs')
    assert dialog.value_preview.text()
    dialog.save()
    assert window.value_references['rules']['e'].get('overrides',{})=={}


def test_constants_editor_has_no_point_settings_and_renames_without_changing_legacy(window):
    before=copy.deepcopy(window.value_references['values']['range'])
    dialog=ValueReferencesDialog(window)
    assert not hasattr(dialog,'point') and not hasattr(dialog,'value_scope') and not hasattr(dialog,'value_override')
    dialog.value_list.setCurrentRow(2)
    assert not dialog.value_expression.isEnabled() and dialog.legacy_notice.isVisibleTo(dialog)
    dialog.value_list.setCurrentRow(0); dialog.value_name.setText('renamed coefficient'); dialog.save()
    assert window.value_references['values']['range']==before
    assert window.value_references['values']['a']['name']=='renamed coefficient'


def test_readable_expression_roundtrip_and_cursor_insertion(window):
    dialog=ValueReferencesDialog(window)
    original=window.value_references['rules']['e']['expression']
    dialog.value_expression.set_expression(original,dialog.data,dialog.point_names)
    assert '@{' not in dialog.value_expression.toPlainText()
    assert 'reading ppm' in dialog.value_expression.toPlainText()
    assert dialog.value_expression.expression()==original
    dialog.value_expression.setPlainText('1 + 2')
    cursor=dialog.value_expression.textCursor();cursor.setPosition(4);dialog.value_expression.setTextCursor(cursor)
    dialog.value_expression.insert_reference('value:a',dialog.data,dialog.point_names)
    assert dialog.value_expression.expression()=='1 + @{value:a}2'
    dialog.reject()


def test_rule_point_override_is_separate_from_base(window):
    base=window.value_references['rules']['e']['expression']
    dialog=ParameterFormulaDialog(window, 'e', 'p1')
    dialog.go(0); dialog.formula.setPlainText('0.1'); dialog.go(1); dialog.go(2); dialog.save()
    rule=window.value_references['rules']['e']
    assert rule['expression']==base and rule['overrides']['p1']=='0.1'
    assert Decimal(window.variable_values['e']['values'][1]['half_width'])==Decimal('.000660')


def test_formula_function_names_and_duplicate_reference_names(window):
    dialog=ValueReferencesDialog(window)
    editor=dialog.value_expression
    editor.set_expression('math.sqrt(@{value:a}) + @{value:b}',dialog.data,dialog.point_names)
    assert 'math.' not in editor.toPlainText()
    assert editor.expression()=='math.sqrt(@{value:a}) + @{value:b}'
    dialog.data['values']['b']['name']=dialog.data['values']['a']['name']
    editor.set_expression('@{value:a}+@{value:b}',dialog.data,dialog.point_names)
    assert len(editor.bindings)==2
    assert editor.expression()=='@{value:a}+@{value:b}'
    dialog.data['values']['a']['name']='math.sqrt coefficient'
    editor.set_expression('math.sqrt(@{value:a})',dialog.data,dialog.point_names)
    assert '【math.sqrt coefficient】' in editor.toPlainText()
    assert editor.expression()=='math.sqrt(@{value:a})'
    dialog.reject()


def test_constant_picker_does_not_offer_quantities_or_points(window):
    from src.dialogs.value_references_dialog import ReferencePicker
    dialog=ValueReferencesDialog(window);picker=ReferencePicker(dialog)
    assert not hasattr(picker,'kind') and not hasattr(picker,'point')
    assert picker.table.rowCount()==2
    picker.table.selectRow(0);picker.choose()
    assert picker.address=='value:a'
    dialog.reject()


def test_invalid_formula_is_not_saved_and_direct_mode_is_explicit(window):
    original=copy.deepcopy(window.value_references)
    dialog=ParameterFormulaDialog(window,'e');dialog.go(0);dialog.formula.setPlainText('1/0')
    dialog.go(1);dialog.go(2);dialog.save()
    assert dialog.result()!=dialog.DialogCode.Accepted
    assert window.value_references==original
    assert dialog.failures
    dialog.use_direct_input()
    assert 'e' not in window.value_references['rules']


def test_reference_button_opens_selected_quantity(window,monkeypatch):
    opened=[]
    monkeypatch.setattr(window,'open_value_references',lambda variable=None:opened.append(variable))
    tab=window.variables_tab
    for index in range(tab.variable_list.count()):
        if tab.variable_list.item(index).data(256)=='e':tab.variable_list.setCurrentRow(index);break
    window.variables_tab.type_b_widgets['reference_button'].click()
    assert opened==['e']


def test_constant_expression_rejects_point_dependencies_and_can_be_corrected(window):
    original=copy.deepcopy(window.value_references)
    dialog=ValueReferencesDialog(window)
    dialog.value_expression.set_expression('@{value:range}',dialog.data,dialog.point_names);dialog.save()
    assert dialog.error.text() and window.value_references==original
    dialog.value_expression.setPlainText('30');dialog.save()
    assert dialog.result()==dialog.DialogCode.Accepted
    assert window.value_references['values']['a']['scope']=='common'
    assert Decimal(window.variable_values['e']['values'][0]['half_width'])==Decimal('.000140')
    assert Decimal(window.variable_values['e']['values'][1]['half_width'])==Decimal('.000740')


def test_unused_invalid_value_is_reported_before_saving(window):
    original=copy.deepcopy(window.value_references)
    dialog=ValueReferencesDialog(window)
    dialog.add_value();dialog.value_expression.setPlainText('1/0');dialog.save()
    assert dialog.error.text()
    assert window.value_references==original
    dialog.reject()


def test_old_one_shot_formula_is_adopted_only_on_apply(window):
    window.value_references['rules'].clear()
    for i,value in enumerate(window.variable_values['e']['values']):
        value['calculation_formula']='abs(x)/10'
    original=copy.deepcopy(window.get_save_data())
    dialog=ParameterFormulaDialog(window,'e')
    assert dialog.formula.toPlainText()=='abs(x)/10'
    assert not dialog.failures
    dialog.reject();assert window.get_save_data()==original
    dialog=ParameterFormulaDialog(window,'e');dialog.save()
    assert all('calculation_formula' not in value for value in window.variable_values['e']['values'])
    assert Decimal(window.variable_values['e']['values'][0]['half_width'])==Decimal('.3')
    assert 'calculation_formula' not in window.variables_tab.type_b_widgets
    assert 'calculate_button' not in window.variables_tab.type_b_widgets


def test_point_reorder_integration(window):
    refs=window.value_references
    window.point_settings_tab.update_display()
    window.point_settings_tab.table.selectRow(0)
    window.point_settings_tab.move_point_down()
    assert refs['points']==['p2','p1']
    window.refresh_references()
    assert Decimal(window.variable_values['e']['values'][0]['half_width'])==Decimal('.000660')
    assert Decimal(window.variable_values['e']['values'][1]['half_width'])==Decimal('.000110')


def test_source_deletion_and_new_name_do_not_rebind(window):
    window.variables.remove('x')
    window.prune_variable_values()
    window.variables.append('x')
    window.variable_values['x']={'type':'fixed','values':[{'central_value':'9'},{'central_value':'9'}]}
    from src.utils.value_references import enable_references
    enable_references(window)
    assert window.value_references['variables']['x']!='x'
    window.refresh_references()
    assert window.reference_errors['e',0]


def test_references_do_not_run_monte_carlo_automatically(window,monkeypatch):
    def fail():raise AssertionError('Must not run simulation')
    monkeypatch.setattr(window.monte_carlo_tab,'run_simulation',fail)
    window.value_references['values']['a']['expression']='30'
    window.refresh_references()
    assert Decimal(window.variable_values['e']['values'][0]['half_width'])==Decimal('.000140')


def test_common_cannot_implicitly_read_point_value(model):
    refs,variables=model
    refs['values']['a']['expression']='@{value:range}'
    assert evaluate_half_widths(refs,variables)['e',0]['error']
    refs['values']['a']['expression']='@{value:range:p2}'
    assert ReferenceEvaluator(refs,variables).resolve('value:a')==100
