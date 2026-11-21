"""Build the requested 1/5/10 V comparison, with explicitly synthetic observations."""
import copy
from decimal import Decimal as D
import json
import os
from pathlib import Path
import sys

os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from PySide6.QtWidgets import QApplication
from src.main_window import MainWindow
from src.utils.language_manager import LanguageManager
from src.utils.project_io import read_project
from src.utils.parameter_formula import compile_formula, prune_parameter_values

BASE=Path(__file__).resolve().parent
POINTS=['p1','p5','p10']
DUT=[['1.0001','1.0002','1.0001','1.0000','1.0001'],
     ['5.0002','5.0003','5.0002','5.0001','5.0002'],
     ['10.002','10.003','10.002','10.001','10.002']]
REF=[['1.00001','1.00002','1.00000','1.00001','1.00001'],
     ['5.0000','5.0001','5.0000','4.9999','5.0000'],
     ['10.0001','10.0002','10.0001','10.0000','10.0001']]


def make_project():
    refs=dict(version=1,variables={},points=POINTS,values={},rules={})
    variables={}
    for name,readings,label in [('V_dut',DUT,'DUTの5回観測の平均'),('V_refIndcating',REF,'REFの5回観測の平均')]:
        variables[name]=dict(type='A',unit='V',definition=label,values=[dict(evaluation_mode='sample',measurements=','.join(row),
            description=label+'。動作確認用の仮データであり、実測値ではありません。平均の標準不確かさを観測列から求めます。',
            evaluation_note='動作確認用の仮の5観測。') for row in readings])
    definitions={
        'Vdut_digit':('DUTの表示分解能補正','resolution / 2'),
        'deltaV_refdigit':('REFの表示分解能補正','resolution / 2'),
        'deltaV_stability':('REFの経年変化補正','a * abs(reading) * 1e-6 + b * range * 1e-6')}
    for name,(label,formula) in definitions.items():
        variables[name]=dict(type='B',unit='V',definition=label,distribution='RECTANGULAR_DISTRIBUTION',divisor=str(D(3).sqrt()),
            values=[dict(central_value='0',divisor=str(D(3).sqrt()),degrees_of_freedom='inf',
                         description=label+'。中心値0、仕様の±限界を半値幅とする矩形分布。'+
                         ('表示刻みの1/2を半値幅とします。' if name!='deltaV_stability' else 'レンジ項とREFの観測平均に対する指示値項を加算します。')) for _ in POINTS])
        bindings = {}
        def manual(argument, values, unit):
            ident = name + '-' + argument
            pointwise = isinstance(values, list)
            refs['values'][ident] = dict(name=label+' / '+argument, unit=unit, parameter_owner=name,
                scope='point' if pointwise else 'common', expression='' if pointwise else values,
                overrides=dict(zip(POINTS, values)) if pointwise else {})
            bindings[argument] = dict(kind='point' if pointwise else 'common', manual_id=ident, address='value:'+ident)
        if name == 'Vdut_digit': manual('resolution', ['0.0001','0.0001','0.001'], 'V')
        elif name == 'deltaV_refdigit': manual('resolution', ['0.00001','0.0001','0.0001'], 'V')
        else:
            manual('a', '20', 'ppm')
            manual('b', ['100','50','50'], 'ppm')
            manual('range', ['1','10','10'], 'V')
            bindings['reading'] = dict(kind='variable', address='variable:V_refIndcating:central_value:current')
        refs['rules'][name] = dict(expression=compile_formula(formula, bindings), overrides={},
            parameter_setup=dict(formula=formula, bindings=bindings))
    for name,label in [('V','DUTと補正後REFの電圧差'),('V_ref','分解能・経年変化補正後のREF値')]:
        variables[name]=dict(type='result',unit='V',definition=label,values=[dict(coverage=dict(method='manual',k='2',note='本サンプルの表示条件としてk=2を指定。')) for _ in POINTS])
    refs['variables']={name:name for name in variables}
    description='''## 測定の概要

DUTとREFを各測定点で5回観測し、平均電圧の差を評価します。観測列は動作確認用の仮データです。仕様値・レンジ構成は利用者指定です。

| 測定点 | REFレンジ | DUTレンジ | REF分解能 | DUT分解能 |
|---|---|---|---|---|
| 1 V | 1 V | 5 V | 0.00001 V | 0.0001 V |
| 5 V | 10 V | 5 V | 0.0001 V | 0.0001 V |
| 10 V | 10 V | 50 V | 0.0001 V | 0.001 V |

## モデルと評価条件

V = (V_dut + Vdut_digit) − V_ref。
V_ref = V_refIndcating + deltaV_refdigit + deltaV_stability。

分解能補正と経年変化補正の中心値は0とします。分解能は表示刻みの±1/2、経年変化は仕様の±限界を半値幅とする矩形分布で評価します。Type Bの自由度は無限大、各5観測の平均の自由度は4、入力量間は無相関と仮定します。

REFの安定性半値幅は、1 Vレンジで100 ppm of range + 20 ppm of reading、10 Vレンジで50 ppm of range + 20 ppm of readingです。readingにはREFの5観測の平均の絶対値を使います。分解能はresolution / 2の式、安定性はa * abs(reading) * 1e-6 + b * range * 1e-6の式に引数を対応付けて計算します。aは全点共通の20 ppm、bは点別の100・50・50 ppm、rangeは点別の1・10・10 Vです。DUTレンジは測定条件として表に記録し、計算には各点の分解能を使います。

包含係数は本サンプルの表示条件としてk=2を指定しています。
'''
    return dict(document_info=dict(document_number='V-COMP-1-5-10',document_name='1 V・5 V・10 Vの電圧比較',description_markdown=description),
        last_equation='V = (V_dut + Vdut_digit) - V_ref\nV_ref = V_refIndcating + deltaV_refdigit + deltaV_stability',
        model_notation='workbench',variables=list(variables),result_variables=['V','V_ref'],variable_values=variables,
        value_names=['1 V','5 V','10 V'],value_count=3,current_value_index=0,value_references=refs,correlation_coefficients={},regressions={})


def main():
    app=QApplication.instance() or QApplication([]);lang=LanguageManager();lang.current_language='ja';lang.load_language()
    MainWindow._offer_recovery=lambda self:None
    window=MainWindow(lang);window._change_timer.stop();window._recovery_timer.stop()
    try:
        assert window.load_data(make_project(),show_message=False)
        tab=window.uncertainty_calculation_tab;records=[]
        for i in range(3):
            tab.value_handler.current_value_index=i
            tab.result_combo.setCurrentText('V');tab.on_result_changed('V')
            assert not tab.warning_label.text(),tab.warning_label.text()
            value=copy.deepcopy(window.calculation_results['V'][window.value_names[i]])
            means=[sum(map(D,rows[i]))/5 for rows in [DUT,REF]]
            ua2=[sum((D(x)-avg)**2 for x in rows[i])/20 for rows,avg in zip([DUT,REF],means)]
            dut_width=D('0.0005') if i==2 else D('0.00005')
            ref_width=D('0.000005') if i==0 else D('0.00005')
            stability=(D(1)*100 if i==0 else D(10)*50)*D('1e-6')+abs(means[1])*20*D('1e-6')
            variance=sum(ua2)+(dut_width**2+ref_width**2+stability**2)/3
            assert abs(D(str(value['result_central_value']))-(means[0]-means[1]))<D('1e-15')
            assert abs(D(str(value['result_standard_uncertainty']))-variance.sqrt())<D('1e-15')
            for name,width in [('Vdut_digit',dut_width),('deltaV_refdigit',ref_width),('deltaV_stability',stability)]:
                assert D(window.variable_values[name]['values'][i]['half_width'])==width
            records.append(dict(point=window.value_names[i],dut_half_width=str(dut_width),ref_half_width=str(ref_width),stability_half_width=str(stability),results=value))
        assert len(window.value_references['values']) == 5
        assert not prune_parameter_values(copy.deepcopy(window.value_references))
        from src.dialogs.parameter_formula_dialog import ParameterFormulaDialog
        for name in ('Vdut_digit', 'deltaV_refdigit', 'deltaV_stability'):
            dialog = ParameterFormulaDialog(window, name)
            assert dialog.pages.currentIndex() == 2 and not dialog.failures
            assert 'input_' not in dialog.formula.toPlainText()
            dialog.save()
            assert dialog.result() == dialog.DialogCode.Accepted
        path=BASE/'voltage_comparison.cutp';window._write_save_data_to_path(path)
        assert window.load_data(read_project(path),show_message=False)
        for i,record in enumerate(records):
            tab.value_handler.current_value_index=i;tab.on_result_changed('V')
            assert window.calculation_results['V'][record['point']]==record['results']
        (BASE/'verification.json').write_text(json.dumps(records,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        print(path)
        for record in records:print(record['point'],record['dut_half_width'],record['ref_half_width'],record['stability_half_width'],record['results']['result_standard_uncertainty'])
    finally:window.hide();window.close()


if __name__=='__main__':main()
