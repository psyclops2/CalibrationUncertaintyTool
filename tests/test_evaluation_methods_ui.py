from decimal import Decimal

import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from src.dialogs.type_a_evaluation_dialog import TypeAEvaluationDialog
from src.main_window import MainWindow
from src.utils.language_manager import LanguageManager


@pytest.fixture
def window():
    app = QApplication.instance() or QApplication([])
    main = MainWindow(LanguageManager())
    main._change_timer.stop()
    main._recovery_timer.stop()
    yield main
    main.hide()
    main.close()


def project():
    return dict(last_equation='y=x', variables=['y', 'x'], result_variables=['y'],
                value_names=['first', 'second'], value_count=2, variable_values={
        'y': dict(type='result', unit='kg', values=[
            {'coverage': {'method': 'ea'}}, {'coverage': {'method': 'manual', 'k': '1.65', 'note': 'source approximation'}}]),
        'x': dict(type='A', unit='kg', values=[
            dict(evaluation_mode='pooled', measurements='10,30,20',
                 pooled_standard_deviation='25', pooled_degrees_of_freedom='inf'),
            dict(evaluation_mode='summary', central_value='10', standard_uncertainty='1', degrees_of_freedom='inf')])})


def test_methods_survive_save_reload_and_point_switch(window):
    assert window.load_data(project(), show_message=False)
    saved = window.get_save_data()
    assert saved['variable_values']['x']['values'][0]['evaluation_mode'] == 'pooled'
    assert window.load_data(saved, show_message=False)
    tab = window.uncertainty_calculation_tab
    tab.on_value_changed(0)
    assert window.calculation_results['y']['first']['coverage_factor'] == 2
    assert Decimal(window.variable_values['x']['values'][0]['standard_uncertainty']) == Decimal(25)/Decimal(3).sqrt()
    tab.on_value_changed(1)
    assert window.calculation_results['y']['second']['coverage_factor'] == 1.65
    window.report_tab.result_combo.setCurrentText('y')
    report = window.report_tab.generate_report_html('y=x')
    assert 'source approximation' in report


def test_pooled_dialog_and_display_keep_infinite_df(window):
    assert window.load_data(project(), show_message=False)
    value = window.variable_values['x']['values'][0]
    dialog = TypeAEvaluationDialog(value, window)
    dialog.accept()
    assert dialog.result_value['degrees_of_freedom'] == 'inf'
    tab = window.variables_tab
    for i in range(tab.variable_list.count()):
        item = tab.variable_list.item(i)
        if item.data(Qt.UserRole) == 'x':
            tab.variable_list.setCurrentItem(item)
            break
    tab.value_combo.setCurrentIndex(0)
    tab.display_current_value()
    assert tab.type_a_widgets['degrees_of_freedom'].text() == 'inf'
    assert 'プール' in tab.type_a_evaluation_button.text()
    tab.type_a_widgets['measurements'].setText('10,20,30,40')
    tab.handlers.on_measurements_focus_lost(None)
    assert window.variable_values['x']['values'][0]['standard_uncertainty'] == '12.5'
    assert window.variable_values['x']['values'][0]['degrees_of_freedom'] == 'inf'


def test_failed_evaluation_drops_previous_cached_result(window):
    assert window.load_data(project(), show_message=False)
    assert 'first' in window.calculation_results['y']
    window.variable_values['x']['values'][0]['pooled_standard_deviation'] = '-1'
    tab = window.uncertainty_calculation_tab
    tab.on_value_changed(0)
    assert tab.standard_uncertainty_label.text() == '--'
    assert 'first' not in window.calculation_results['y']


def test_staged_model_preserves_shared_error_cancellation(window):
    data = dict(last_equation='stage=x+e\ny=stage-x', variables=['stage','y','x','e'],
                result_variables=['stage','y'], value_names=['p'], value_count=1,
                variable_values={
                    'stage': dict(type='result', values=[{}]),
                    'y': dict(type='result', values=[{}]),
                    'x': dict(type='A', values=[dict(evaluation_mode='summary', central_value='10',
                              standard_uncertainty='2', degrees_of_freedom='inf')]),
                    'e': dict(type='A', values=[dict(evaluation_mode='summary', central_value='1',
                              standard_uncertainty='.3', degrees_of_freedom='inf')])})
    assert window.load_data(data, show_message=False)
    tab = window.uncertainty_calculation_tab
    tab.result_combo.setCurrentText('y')
    tab.on_result_changed('y')
    assert window.calculation_results['y']['p']['result_standard_uncertainty'] == pytest.approx(.3)
    window.variable_values['x']['values'][0]['central_value'] = '999'
    tab.on_result_changed('y')
    assert window.calculation_results['y']['p']['result_central_value'] == pytest.approx(1)
    assert window.calculation_results['y']['p']['result_standard_uncertainty'] == pytest.approx(.3)
    window.last_equation = 'stage=y\ny=stage'
    tab.on_result_changed('y')
    assert '循環' in tab.warning_label.text()
    assert 'p' not in window.calculation_results['y']
