import copy
import json
import math
from types import SimpleNamespace

import numpy as np
import pytest
from PySide6.QtWidgets import QApplication, QMessageBox

from src.main_window import MainWindow
from src.utils.language_manager import LanguageManager
from src.utils.input_sources import evaluate_table, source_packet, statistical_state, effective_df
from src.utils.model_expression import variable_names, parse_expression, split_equations
from src.utils.coverage import student_factor
from src.utils.output_covariance import evaluate_outputs
from src.dialogs.input_source_dialog import InputSourceDialog
from src.dialogs.coverage_dialog import CoverageDialog
from src.dialogs.measurement_table_dialog import MeasurementTableDialog


@pytest.fixture
def window(monkeypatch):
    app=QApplication.instance() or QApplication([])
    monkeypatch.setattr(QMessageBox,'question',lambda *args:QMessageBox.Discard)
    window=MainWindow(LanguageManager())
    window._change_timer.stop();window._recovery_timer.stop()
    yield window
    window.hide();window.close()


def regression_project():
    xs=[1.521,2.012,2.512,3.003,3.507,3.999,4.513,5.002,5.503,6.010,6.511]
    ys=[-.171,-.169,-.166,-.159,-.164,-.165,-.156,-.157,-.159,-.161,-.160]
    return dict(last_equation='y=a',variables=['y','a'],result_variables=['y'],value_names=['p'],value_count=1,
        regressions={'curve':dict(id='curve1',x_unit='K',y_unit='K',data=[dict(x=x,y=y,ux=0) for x,y in zip(xs,ys)])},
        variable_values={'y':dict(type='result',unit='K',values=[{'coverage':{'method':'student','probability':.95}}]),
                         'a':dict(type='A',unit='K',values=[{'input_source':dict(kind='regression',model_id='curve1',x_expression='10')}])})


def test_math_functions_and_scientific_numbers_share_parser():
    assert variable_names('1e-6*x+sin(phi)+cos(phi)+exp(t)')==['phi','t','x']
    assert len(split_equations('a=atan2(y,x)\nb=sqrt(a)'))==2
    assert float(parse_expression('sin(pi/2)'))==pytest.approx(1)
    with pytest.raises(ValueError,match='未対応'):parse_expression('unknown(x)')
    with pytest.raises(ValueError):parse_expression('__import__("os").getcwd()')
    import sympy as sp
    x=sp.Symbol('x',real=True)
    assert sp.diff(parse_expression('abs(x)'),x).subs(x,-2)==-1


@pytest.mark.parametrize('df,p,expected',[(16,.99,2.9207816224251),(10,.9545,2.283681613299642),
    (4,.95,2.7764451051977943),(math.inf,.95,1.9599639845400536),(1000,.99,2.580754698065951)])
def test_student_quantile(df,p,expected):
    assert student_factor(df,p)==pytest.approx(expected,rel=1e-11)
    assert student_factor(16.74,.99,True)==pytest.approx(2.9207816224251)


def test_gum_h3_prediction_preserves_df_and_reload(window):
    assert window.load_data(regression_project(),show_message=False)
    result=window.calculation_results['y']['p']
    assert result['result_central_value']==pytest.approx(-.1493768127324773)
    assert result['result_standard_uncertainty']==pytest.approx(.004138595752854946)
    assert result['effective_df']==pytest.approx(9)
    assert result['coverage_factor']==pytest.approx(2.2621571627982053)
    saved=json.loads(json.dumps(window.get_save_data(),default=str))
    assert window.load_data(saved,show_message=False)
    assert window.calculation_results['y']['p']['effective_df']==pytest.approx(9)
    window.regressions['renamed']=window.regressions.pop('curve')
    assert source_packet(window,'a',0)['label'].startswith('回帰「renamed」')


def test_same_fit_predictions_keep_covariance_and_cancel(window):
    data=regression_project()
    data['last_equation']='y=a-b\nz=a+b'
    data['variables']+=['b','z'];data['result_variables']+=['z']
    data['variable_values']['b']=copy.deepcopy(data['variable_values']['a'])
    data['variable_values']['z']=dict(type='result',unit='K',values=[{}])
    assert window.load_data(data,show_message=False)
    tab=window.uncertainty_calculation_tab
    tab.result_combo.setCurrentText('y');tab.on_result_changed('y')
    assert window.calculation_results['y']['p']['result_standard_uncertainty']==pytest.approx(0,abs=1e-12)
    names,covariance,corr=evaluate_outputs(window,0)
    assert covariance[0,0]==pytest.approx(0,abs=1e-18)
    assert covariance[1,1]>0
    np.random.seed(42)
    samples=window.monte_carlo_tab._evaluate_result_samples('y',1000)
    assert np.std(samples)<1e-12


def test_unknown_correlated_df_keeps_u_and_does_not_invent_k(window):
    data=regression_project();data['last_equation']='y=a+b';data['variables']+=['b']
    for name in ('a','b'):
        data['variable_values'][name]=dict(type='A',unit='K',values=[dict(evaluation_mode='summary',central_value='1',standard_uncertainty='.1',degrees_of_freedom='9')])
    data['correlation_coefficients']={'a':{'b':-.93},'b':{'a':-.93}}
    assert window.load_data(data,show_message=False)
    result=window.calculation_results['y']['p']
    assert result['result_standard_uncertainty']>0
    assert result['effective_df'] is None and result['coverage_factor'] is None and result['expanded_uncertainty'] is None
    assert '未評価' in window.uncertainty_calculation_tab.evaluation_note_label.text()


def test_paired_columns_and_derived_rows_are_not_unpaired():
    table=dict(columns=[dict(id='v'),dict(id='i'),dict(id='r',expression='v/i')],
        rows=[dict(v='4',i='2'),dict(v='9',i='3'),dict(v='16',i='4')])
    ids,means,cov,df=evaluate_table(table)
    assert means[2]==3
    assert cov[2,2]==pytest.approx(1/3)
    assert df==2
    table['rows'][1]['i']=''
    with pytest.raises(ValueError,match='観測組全体'):evaluate_table(table)
    table['rows'][1]['excluded']=True
    assert evaluate_table(table)[3]==1


def test_table_binding_gum_electrical_model(window):
    data=regression_project();data['regressions']={}
    v=[5.007,4.994,5.005,4.990,4.999];current=[.019663,.019639,.019640,.019685,.019678];phase=[1.0456,1.0438,1.0468,1.0428,1.0433]
    data['measurement_tables']={'t1':dict(name='同時測定',columns=[dict(id='voltage',unit='V'),dict(id='current',unit='A'),dict(id='phase',unit='1')],rows=[dict(voltage=a,current=b,phase=c) for a,b,c in zip(v,current,phase)])}
    data['last_equation']='R=voltage/current*cos(phase)\nX=voltage/current*sin(phase)\nZ=voltage/current'
    data['variables']=['R','X','Z','voltage','current','phase'];data['result_variables']=['R','X','Z']
    data['variable_values']={name:dict(type='result',unit='ohm',values=[{}]) for name in ('R','X','Z')}
    for name,unit in [('voltage','V'),('current','A'),('phase','1')]:
        data['variable_values'][name]=dict(type='A',unit=unit,values=[{'input_source':dict(kind='table',table_id='t1',column=name)}])
    assert window.load_data(data,show_message=False)
    tab=window.uncertainty_calculation_tab
    tab.result_combo.setCurrentText('R');tab.on_result_changed('R')
    result=window.calculation_results['R']['p']
    assert result['result_central_value']==pytest.approx(127.732,abs=.001)
    assert result['result_standard_uncertainty']==pytest.approx(.071,abs=.001)
    assert result['effective_df']==pytest.approx(4)
    names,cov,corr=evaluate_outputs(window,0)
    assert corr[0,1]==pytest.approx(-.588,abs=.002)
    window.variable_values['R']['values'][0]['include_output_covariance']=True
    window.report_tab.result_combo.setCurrentText('R')
    report=window.report_tab.generate_report_html(data['last_equation'])
    assert '出力間の共分散' in report and '同時測定' in report


def test_source_dialog_cancel_detach_and_freeze(window):
    assert window.load_data(regression_project(),show_message=False)
    before=copy.deepcopy(window.get_save_data())
    dialog=InputSourceDialog(window,'a',0)
    dialog.x_expression.setText('20');dialog.reject()
    assert window.get_save_data()==before
    dialog=InputSourceDialog(window,'a',0)
    dialog.kind.setCurrentIndex(dialog.kind.findData('direct'));dialog.freeze.setChecked(True);dialog.accept()
    assert 'input_source' not in dialog.result_value
    assert dialog.result_value['evaluation_mode']=='summary'
    assert '固定した時点' in dialog.result_value['evaluation_note']


def test_uncertain_x_and_deleted_model_are_not_ignored(window):
    assert window.load_data(regression_project(),show_message=False)
    window.regressions['curve']['data'][0]['ux']='.1'
    with pytest.raises(ValueError,match='xに不確かさ'):source_packet(window,'a',0)
    window.regressions={}
    tab=window.uncertainty_calculation_tab;tab.on_result_changed('y')
    assert '見つかりません' in tab.warning_label.text()
    assert 'p' not in window.calculation_results.get('y',{})


def test_coverage_dialog_student_and_table_editor(window):
    dialog=CoverageDialog(dict(method='student',probability=.99,floor_df=True),window)
    dialog.accept()
    assert dialog.settings==dict(method='student',probability=.99,floor_df=True,note='')
    editor=MeasurementTableDialog(dict(name='pairs',columns=[dict(id='x',unit='V',expression='')],rows=[dict(x='1'),dict(x='3')]),window)
    editor.accept()
    assert editor.result_table['rows'][1]['x']=='3'


def test_source_navigation_keeps_draft_and_returns_to_point(window,monkeypatch):
    import src.dialogs.input_source_dialog as module
    assert window.load_data(regression_project(),show_message=False)
    tab=window.variables_tab
    for i in range(tab.variable_list.count()):
        item=tab.variable_list.item(i)
        if item.data(256)=='a':tab.variable_list.setCurrentItem(item);break
    visited=[]
    class NavigateDialog(InputSourceDialog):
        def exec(self):
            visited.append(self.x_expression.text())
            if len(visited)==1:
                self.x_expression.setText('12')
                self.navigate_model_id=self.regression.currentData()
            return 0
    monkeypatch.setattr(module,'InputSourceDialog',NavigateDialog)
    tab.edit_input_source()
    assert window.tab_widget.currentWidget()==window.regression_tab
    window.regression_tab.return_to_input_button.click()
    assert visited==['10','12']
    assert window.tab_widget.currentWidget()==tab
    assert tab.handlers.current_variable=='a'


def test_mc_is_explicit_reproducible_and_invalidated_on_edit(window,monkeypatch):
    from PySide6.QtGui import QShowEvent
    assert window.load_data(regression_project(),show_message=False)
    mc=window.monte_carlo_tab
    calls=[]
    original=mc._evaluate_result_samples
    def sample(*args):calls.append(args);return original(*args)
    monkeypatch.setattr(mc,'_evaluate_result_samples',sample)
    mc.showEvent(QShowEvent())
    assert calls==[]
    mc.samples_spin.setValue(1000);mc.seed_edit.setText('12345')
    mc.run_simulation()
    first=copy.deepcopy(mc._trial_record)
    assert first['seed']==12345 and first['finite_samples']==1000
    assert first['first_order_u']==pytest.approx(.004138595752854946)
    mc.run_simulation()
    assert mc._trial_record['standard_uncertainty']==first['standard_uncertainty']
    assert mc._trial_record['equal_tail_95_interval']==first['equal_tail_95_interval']
    window._check_modified()
    assert mc._trial_record is not None
    window.regressions['curve']['data'][0]['y']+=.001
    window._check_modified()
    assert mc._trial_record is None and not mc.save_trial_button.isEnabled()
    assert len(calls)==2


def test_variable_gui_applies_source_and_restores_direct_input(window,monkeypatch):
    import src.dialogs.input_source_dialog as module
    data=regression_project()
    original=dict(evaluation_mode='summary',central_value='9',standard_uncertainty='2',degrees_of_freedom='inf')
    data['variable_values']['a']['values'][0]=original
    assert window.load_data(data,show_message=False)
    tab=window.variables_tab
    for i in range(tab.variable_list.count()):
        if tab.variable_list.item(i).data(256)=='a':tab.variable_list.setCurrentRow(i);break
    class ApplyDialog(InputSourceDialog):
        mode='regression'
        def exec(self):
            self.kind.setCurrentIndex(self.kind.findData(self.mode))
            self.x_expression.setText('10');self.accept()
            return 1 if self.result_value is not None else 0
    monkeypatch.setattr(module,'InputSourceDialog',ApplyDialog)
    tab.edit_input_source()
    value=window.variable_values['a']['values'][0]
    assert value['input_source']['kind']=='regression'
    assert value['direct_input']['central_value']=='9'
    assert '回帰' in tab.input_source_button.text()
    assert tab.type_a_measurements_container.isHidden()
    ApplyDialog.mode='direct';tab.edit_input_source()
    restored=window.variable_values['a']['values'][0]
    assert 'input_source' not in restored and restored['central_value']=='9'


def test_fixed_x_reference_checks_units_and_source_identity(window):
    data=regression_project()
    data['variables'].append('target')
    data['variable_values']['target']=dict(type='fixed',unit='K',values=[dict(central_value='10')])
    data['value_references']=dict(version=1,variables={name:name for name in data['variables']},points=['p1'],values={},rules={})
    data['variable_values']['a']['values'][0]['input_source']['x_expression']='@{variable:target:central_value:current}'
    assert window.load_data(data,show_message=False)
    packet=source_packet(window,'a',0)
    assert packet['label'].startswith('回帰「curve」')
    window.variable_values['target']['unit']='m'
    with pytest.raises(ValueError,match='単位'):source_packet(window,'a',0)


def test_reading_linked_values_at_another_point_is_not_a_model_edit(window):
    data=regression_project()
    data['value_names']=['p','p2'];data['value_count']=2
    for info in data['variable_values'].values():info['values'].append(copy.deepcopy(info['values'][0]))
    assert window.load_data(data,show_message=False)
    assert not window._check_modified()
    window.uncertainty_calculation_tab.on_value_changed(1)
    assert not window._check_modified()
    saved=window.get_save_data()['variable_values']['a']['values'][1]
    assert saved['input_source']['kind']=='regression'
    assert 'central_value' not in saved and 'standard_uncertainty' not in saved


def test_regression_covariance_remains_stable_at_large_x_offset(window):
    data=regression_project()
    for row in data['regressions']['curve']['data']:row['x']+=1e9
    data['variable_values']['a']['values'][0]['input_source']['x_expression']='1000000010'
    assert window.load_data(data,show_message=False)
    result=window.calculation_results['y']['p']
    assert result['result_standard_uncertainty']==pytest.approx(.004138595752854946,rel=1e-6)
    assert result['effective_df']==pytest.approx(9)
