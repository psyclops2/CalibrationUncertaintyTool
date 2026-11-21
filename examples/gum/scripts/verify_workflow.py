"""Rebuild Annex H using live regression/table sources and verify the new workflow."""
import copy
import csv
import json
import math
from pathlib import Path
import sys
import html

BASE=Path(__file__).resolve().parent.parent
ROOT=BASE.parent.parent
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(BASE/'scripts'))
import numpy as np
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication
from src.main_window import MainWindow
from examples.current_format import current_format
from src.utils.language_manager import LanguageManager
from src.utils.output_covariance import evaluate_outputs
from src.utils.project_io import atomic_write_json, read_project
from examples.sample_presentation import enrich_project, ensure_sample_fonts
from src.dialogs.input_source_dialog import InputSourceDialog
from src.dialogs.measurement_table_dialog import MeasurementTableDialog
from gum_project_factory import make_project
from cases import all_cases

PROJECTS=BASE/'projects';REPORTS=BASE/'reports'


def bind(project,name,source):
    value=project['variable_values'][name]['values'][0]
    value['direct_input']=copy.deepcopy(value)
    value['input_source']=source


def linked_project(case):
    project=make_project(case);key=case['key'];raw=case['raw']
    project['document_info']['version_info']='workflow sources / 2026-11-21'
    if key=='H1':
        project['variable_values']['l']['values'][0]['coverage']=dict(method='student',probability=.99,floor_df=True,note='GUM H.1.6; first-order budget, not second-order propagation')
    if key.startswith('H2'):
        columns=[dict(id='voltage',unit='V'),dict(id='current',unit='A'),dict(id='phase',unit='1')]
        rows=[dict(voltage=v,current=i,phase=p) for v,i,p in zip(raw['V'],raw['I_A'],raw['phase_rad'])]
        if key.endswith('approach2'):
            columns += [dict(id='rObs',unit='ohm',expression='voltage/current*cos(phase)'),
                        dict(id='xObs',unit='ohm',expression='voltage/current*sin(phase)'),
                        dict(id='zObs',unit='ohm',expression='voltage/current')]
        project['measurement_tables']={'h2-pairs':dict(name='GUM H.2 同時観測',columns=columns,rows=rows)}
        for name in case['variables']:bind(project,name,dict(kind='table',table_id='h2-pairs',column=name))
        project['correlation_coefficients']={}
        project['variable_values']['R']['values'][0]['include_output_covariance']=True
    if key=='H3':
        project['last_equation']='correction = prediction'
        project['variables']=['correction','prediction'];project['result_variables']=['correction']
        project['variable_values']={'correction':dict(type='result',unit='K',values=[{'coverage':dict(method='student',probability=.95)}]),
            'prediction':dict(type='A',unit='K',definition='Live OLS mean response at x=10 K (t=30 C)',values=[dict(input_source=dict(kind='regression',model_id='gum-h3-fit',x_expression='10'))])}
        project['correlation_coefficients']={};project.pop('value_references',None)
        project['regressions']['H3_thermometer']['id']='gum-h3-fit'
    if key.startswith('H4'):
        columns=[dict(id=name,unit='1') for name in ('cs','cb','cx','ts','tx')]
        columns += [dict(id='rateSample',unit='1/min',expression='(cx-cb)*exp(0.000125894*tx)/60'),
                    dict(id='rateStandard',unit='1/min',expression='(cs-cb)*exp(0.000125894*ts)/60'),
                    dict(id='ratio',unit='1',expression='rateSample/rateStandard')]
        rows=[dict(cs=cs,cb=cb,cx=cx,ts=ts,tx=tx) for cs,cb,cx,ts,tx in zip(raw['Cs'],raw['Cb'],raw['Cx'],raw['ts_min'],raw['tx_min'])]
        project['measurement_tables']={'h4-cycles':dict(name='GUM H.4 計数サイクル',columns=columns,rows=rows)}
        names=['ratio'] if key.endswith('approach2') else ['rateSample','rateStandard']
        for name in names:bind(project,name,dict(kind='table',table_id='h4-cycles',column=name))
        project['correlation_coefficients']={}
    if key=='H5':
        project['measurement_tables']={'h5-means':dict(name='GUM H.5 日平均（ANOVAは未実施）',columns=[dict(id='dailyMean',unit='V')],
            rows=[dict(dailyMean=value) for value in raw['daily_means_V']])}
        bind(project,'dailyMean',dict(kind='table',table_id='h5-means',column='dailyMean'))
    notes={
        'H1':'99%のt分位点を自動計算。二次の分散補正は未対応。',
        'H2_approach1':'同時観測表の平均・共分散を自動計算してR/X/Zへ伝播。関数名の式解析を修正済み。',
        'H2_approach2':'同時観測表内の派生列でR/X/Zを行ごとに計算し、平均と共分散を評価。',
        'H3':'回帰の平均応答を接続。予測値・u・自由度9を自動更新。x=10 Kはt=30 Cに相当し、外挿。xの不確かさを持つ回帰は未対応。',
        'H4_approach1':'元の計数表から補正計数率を派生列で計算し、平均・共分散を伝播。計数率の比を取るため同じmin単位を使用。',
        'H4_approach2':'元の計数表から補正計数率とサイクル比を派生列で計算し、比の平均を使用。',
        'H5':'原文の日平均10個を表で保持。ANOVA/F検定は未実施。',
        'H6':'評価済み統計量と参照式を使用。未提示の自由度infの仮定は継続。'}
    project['document_info']['description_markdown']=('JCGM 100:2008 Annex H / live sources\n'+notes[key]+
        '\nMCは自動実行しない。未対応事項は各モデルの条件として保持。')
    return project


def write_index(records):
    body='<html lang="ja"><meta charset="utf-8"><title>GUM 接続機能での再試算</title><style>body{font:15px sans-serif;margin:24px}td,th{border:1px solid #bbb;padding:7px}table{border-collapse:collapse}p{max-width:1000px;line-height:1.7}</style><h1>入力元接続による再試算</h1><p>回帰と同時観測表を接続した8モデル。H.1の二次伝播、H.5のANOVA、未提示の自由度の評価は未対応。MCは自動実行しない。</p><p><a href="../docs/workflow-results.md">確認内容・制約</a></p><table><tr><th>モデル</th><th>結果</th><th>単位</th><th>中心値</th><th>u</th><th>自由度</th><th>k</th></tr>'
    for record in records:
        key=record['key']
        project=read_project(PROJECTS/(key+'.cutp'))
        for name,result in record['results'].items():
            df=result['effective_df']
            values=[name,project['variable_values'][name].get('unit',''),f'{result["result_central_value"]:.10g}',
                    f'{result["result_standard_uncertainty"]:.9g}','未評価' if df is None else '∞' if df>=1e100 else f'{df:.7g}',
                    '--' if result['coverage_factor'] is None else f'{result["coverage_factor"]:.8g}']
            body+='<tr><td><a href="../projects/'+key+'.cutp">'+key+'</a><br><a href="'+key+'_'+name+'_tool.html">レポート</a></td>'
            body+=''.join('<td>'+html.escape(value)+'</td>' for value in values)+'</tr>'
    (REPORTS/'index.html').write_text(body+'</table><p><a href="verification.json">保存・再読込と入力変更の検証記録</a></p></html>',encoding='utf-8')


def main():
    PROJECTS.mkdir(parents=True,exist_ok=True);REPORTS.mkdir(parents=True,exist_ok=True)
    app=QApplication.instance() or QApplication([])
    ensure_sample_fonts()
    language=LanguageManager();language.current_language='ja';language.load_language()
    MainWindow._offer_recovery=lambda self:None
    window=MainWindow(language);window._change_timer.stop();window._recovery_timer.stop()
    window.setAttribute(Qt.WA_DontShowOnScreen,True)
    window.show();app.processEvents()
    records=[]
    try:
        for case in all_cases():
            key=case['key'];print('Verifying',key,flush=True)
            project=linked_project(case)
            enrich_project(project,'gum',key)
            assert window.load_data(current_format(project),show_message=False)
            tab=window.uncertainty_calculation_tab
            results={};source_comparison={}
            for result in case['expected']:
                tab.result_combo.setCurrentText(result);tab.on_result_changed(result)
                assert not tab.warning_label.text(),(key,tab.warning_label.text())
                actual=copy.deepcopy(window.calculation_results[result][key]);results[result]=actual
                source=case['expected'][result]
                # Printed numbers are comparison evidence, not a 2.5%-wide
                # numerical oracle. audit_numerics.py checks the supplied
                # model independently at high precision after generation.
                source_comparison[result]=dict(published=source,
                    central_delta=actual['result_central_value']-source['value'],
                    standard_uncertainty_delta=actual['result_standard_uncertainty']-source['u'])
            if key=='H3':assert abs(results['correction']['effective_df']-9)<1e-10
            if key.startswith('H2'):assert abs(results['R']['effective_df']-4)<1e-10
            names,covariance,correlation=evaluate_outputs(window,0,list(case['expected']))
            if key.startswith('H2'):assert abs(correlation[0,1]+.588)<.002
            # Actual input edits must update the estimates and invalidate existing MC results.
            edited=False
            if key=='H3':
                model=window.regressions['H3_thermometer'];old=model['data'][0]['y']
                model['data'][0]['y']=float(old)+.001;tab.on_result_changed('correction')
                assert window.calculation_results['correction'][key]['result_central_value']!=results['correction']['result_central_value']
                model['data'][0]['y']=old;edited=True
            if key.startswith('H2'):
                row=window.measurement_tables['h2-pairs']['rows'][0];old=row['voltage']
                row['voltage']=float(old)+.01;tab.result_combo.setCurrentText('R');tab.on_result_changed('R')
                assert window.calculation_results['R'][key]['result_central_value']!=results['R']['result_central_value']
                row['voltage']=old;edited=True
            window._write_save_data_to_path(str(PROJECTS/(key+'.cutp')))
            assert window.load_data(read_project(PROJECTS/(key+'.cutp')),show_message=False)
            for result in results:
                tab.result_combo.setCurrentText(result);tab.on_result_changed(result)
                assert window.calculation_results[result][key] == results[result], (key, result, 'save/reload changed results')
                window.report_tab.result_combo.setCurrentText(result)
                report=window.report_tab.generate_report_html(window.last_equation)
                (REPORTS/(key+'_'+result+'_tool.html')).write_text(report,encoding='utf-8')
            records.append(dict(key=key,results=results,source_comparison=source_comparison,output_names=names,covariance=covariance.tolist(),
                correlation=[[float(value) if np.isfinite(value) else None for value in row] for row in correlation],
                save_reload=True,source_edit_checked=edited,mc_auto_run=False))
            if key in ('H2_approach1','H3'):
                window.tab_widget.setCurrentWidget(tab);window.resize(1500,950);tab.calibration_table.resizeColumnsToContents()
                window.ensurePolished();window.grab().save(str(REPORTS/(key+'_calculation.png')))
            if key=='H3':
                dialog=InputSourceDialog(window,'prediction',0);assert dialog.preview()
                dialog.ensurePolished();dialog.grab().save(str(REPORTS/'H3_input_source.png'))
                dialog.reject()
                variables=window.variables_tab
                window.tab_widget.setCurrentWidget(variables)
                for i in range(variables.variable_list.count()):
                    if variables.variable_list.item(i).data(Qt.UserRole)=='prediction':
                        variables.variable_list.setCurrentRow(i);break
                variables.display_current_value();app.processEvents()
                window.grab().save(str(REPORTS/'H3_variable_input.png'))
            if key=='H2_approach1':
                dialog=MeasurementTableDialog(window.measurement_tables['h2-pairs']);dialog.preview()
                dialog.ensurePolished();dialog.grab().save(str(REPORTS/'H2_measurement_table.png'));dialog.reject()
        atomic_write_json(REPORTS/'verification.json',records)
        with (REPORTS/'comparison.csv').open('w',encoding='utf-8-sig',newline='') as stream:
            writer=csv.writer(stream);writer.writerow(['case','result','value','u','df','k'])
            for record in records:
                for name,result in record['results'].items():writer.writerow([record['key'],name,result['result_central_value'],result['result_standard_uncertainty'],result['effective_df'],result['coverage_factor']])
        write_index(records)
        # EA S12: the probability method is separate from the rounded EA table method.
        ea=read_project(ROOT/'examples/ea402/projects/S12_probability.cutp')
        assert window.load_data(ea,show_message=False)
        actual=window.calculation_results['exav'][window.value_names[0]]
        assert abs(actual['coverage_factor']-2.283681613299642)<1e-10
        atomic_write_json(ROOT/'examples/ea402/reports/S12_probability_comparison.json',actual)
        print('Verified 8 GUM models and EA S12 probability method',flush=True)
    finally:
        window.hide();window.close()


if __name__=='__main__':main()
