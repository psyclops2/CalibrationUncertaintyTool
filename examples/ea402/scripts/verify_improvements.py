r"""Recheck selected EA cases after evaluation-method changes; no automatic MC.

Run: venv\Scripts\python.exe examples\ea402\scripts\verify_improvements.py
Only current models are generated; unsupported source features remain documented.
"""
import copy
import json
import html
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from PySide6.QtWidgets import QApplication
from src.main_window import MainWindow
from examples.current_format import current_format
from src.utils.language_manager import LanguageManager
from src.utils.project_io import atomic_write_json, read_project
from examples.sample_presentation import enrich_project, ensure_sample_fonts
from sample_cases import cases
from ea_project_factory import make_project, s9_project, numerical_check

from paths import CURRENT_PROJECTS as PROJECTS, CURRENT_REPORTS as OUT


def write_index(records):
    body='<html lang="ja"><meta charset="utf-8"><title>EA-4/02 現行サンプル</title><style>body{font:15px sans-serif;margin:24px}table{border-collapse:collapse}td,th{border:1px solid #bbb;padding:7px}</style><h1>EA-4/02 現行サンプル</h1><p>全11事例。段階別のモデルを含み、二次伝播や原文の不整合などの未対応事項は各モデルと改良メモへ記録。</p><p><a href="../docs/improvements.md">採用条件と未対応事項</a></p><table><tr><th>モデル</th><th>結果</th><th>単位</th><th>中心値</th><th>u</th><th>k</th></tr>'
    for record in records:
        key=record['key']
        project=read_project(PROJECTS/(key+'.cutp'))
        for name,result in record['results'].items():
            values=[name,project['variable_values'][name].get('unit',''),f"{result['result_central_value']:.10g}",f"{result['result_standard_uncertainty']:.8g}",str(result['coverage_factor'])]
            body+='<tr><td><a href="../projects/'+key+'.cutp">'+key+'</a><br><a href="'+key+'_tool_report.html">レポート</a></td>'
            body+=''.join('<td>'+html.escape(value)+'</td>' for value in values)+'</tr>'
    (OUT/'index.html').write_text(body+'</table></html>',encoding='utf-8')


def main():
    OUT.mkdir(exist_ok=True)
    app = QApplication.instance() or QApplication([])
    ensure_sample_fonts()
    language = LanguageManager()
    language.current_language = 'ja'
    language.load_language()
    MainWindow._offer_recovery = lambda self: None
    window = MainWindow(language)
    window._change_timer.stop()
    window._recovery_timer.stop()
    samples = {case['key']: case for case in cases()}
    projects = []
    for key in ('S2', 'S3', 'S4_raw', 'S5_temperature', 'S5_emf', 'S6', 'S7', 'S10', 'S11', 'S12_average', 'S13_raw_temperature'):
        case = samples[key]
        project = make_project(case)
        description = project['document_info']['description_markdown']
        description = description.replace('pooled_type_a_presaved', 'Type A評価方法を保存済み')
        if key == 'S12_average':
            description = description.replace('coverage_df_threshold', 'EA表E.1を明示選択')
        project['document_info']['description_markdown'] = description
        result = project['result_variables'][0]
        if key in ('S10', 'S11'):
            project['variable_values'][result]['values'][0]['coverage'] = {
                'method': 'manual', 'k': str(case['expected']['k']),
                'note': f'EA-4/02 {key}：原文の非正規分布に基づく係数を指定。Toolが係数を推定したものではない。'}
        if key == 'S12_average':
            project['variable_values'][result]['values'][0]['coverage'] = {
                'method': 'ea', 'note': 'EA-4/02 表E.1。νeff=10.33を10へ切り捨て、k=2.28。'}
        projects.append((key, project))
    s9 = s9_project()
    s9['variable_values']['Ex']['values'][0]['coverage'] = {
        'method': 'manual', 'k': '1.65',
        'note': 'EA-4/02 S9：支配的な矩形分布による近似。混合出力分布をToolが自動評価した係数ではない。'}
    projects.append(('S9', s9))
    probability=make_project(samples['S12_average'])
    probability['document_info']['document_number']='EA402-S12-probability'
    probability['document_info']['document_name']='水道メーター・平均指示誤差（包含確率から計算）'
    probability['document_info']['description_markdown']='EA-4/02 S12: 95.45%と有効自由度の下側整数からt分位点を数値計算する。掲載表の丸め係数2.28とは別方式。単回uは原文の評価済み値を使用。'
    probability['variable_values']['exav']['values'][0]['coverage']=dict(method='student',probability=.9545,floor_df=True,note='Numerical t quantile; separate from rounded Table E.1')
    projects.append(('S12_probability',probability))

    # Use the existing multi-equation feature instead of copying a rounded u.
    volume = make_project(samples['S12_volume'])
    single = samples['S12_single']
    for name in ('indication', 'resStart', 'resEnd'):
        volume['variable_values'][name] = copy.deepcopy(single['variables'][name])
    volume['variable_values']['ex'] = {'type': 'result', 'unit': '1', 'values': [{}]}
    volume['last_equation'] += '\nex = (indication + resEnd - resStart)/vx - 1'
    volume['result_variables'] = ['vx', 'ex']
    volume['document_info']['document_number'] = 'EA402-S12-staged'
    volume['document_info']['document_name'] = '水道メーター・体積から単回誤差までの段階計算'
    volume['document_info']['description_markdown'] = (
        'EA-4/02 S12の体積と単回誤差を複数式で計算する例。\n'
        '中間結果vxを元の入力へ展開し、丸めた標準不確かさは転記しない。\n'
        '原文: https://www.accredia.it/wp-content/uploads/2013/09/EA-4-02_2022-incertezza-nelle-tarature.pdf\n'
        '圧力はkPa、圧縮率は1/kPaで数値をそろえた。単位検証の接頭辞対応は未完。')
    volume['variables'] = list(volume['variable_values'])
    volume['value_references'] = None
    # Rebuild a reference registry so the imported Type B widths are evaluated.
    refs = {'version': 1, 'variables': {name: name for name in volume['variables']},
            'points': ['point1'], 'values': {}, 'rules': {}}
    for name, info in volume['variable_values'].items():
        if info['type'] == 'B':
            value = info['values'][0]
            refs['values'][name+'Width'] = {'name': name+' half width', 'scope': 'common',
                'unit': info['unit'], 'expression': str(value['half_width'])}
            refs['rules'][name] = {'expression': '@{value:'+name+'Width}', 'overrides': {}}
    volume['value_references'] = refs
    projects.append(('S12_staged', volume))

    records = []
    try:
        for key, project in projects:
            enrich_project(project, 'ea402', key)
            assert window.load_data(current_format(project), show_message=False), key
            results = {}
            independent = {}
            tab = window.uncertainty_calculation_tab
            for result in project['result_variables']:
                tab.result_combo.setCurrentText(result)
                tab.on_result_changed(result)
                assert not tab.warning_label.text(), (key, tab.warning_label.text())
                results[result] = copy.deepcopy(window.calculation_results[result][window.value_names[0]])
                if key in samples and result==project['result_variables'][0]:
                    check=numerical_check(samples[key],window.variable_values)
                    import math
                    assert math.isclose(results[result]['result_standard_uncertainty'],check['u'],rel_tol=1e-3,abs_tol=1e-12)
                    independent[result]=check
            if key == 'S12_average':
                assert results['exav']['coverage_factor'] == 2.28
            if key == 'S12_probability':
                assert abs(results['exav']['coverage_factor']-2.283681613299642)<1e-10
            if key == 'S2':
                value = window.variable_values['diff']['values'][0]
                assert value['evaluation_mode'] == 'pooled'
            window._write_save_data_to_path(str(PROJECTS/(key+'.cutp')))
            assert window.load_data(read_project(PROJECTS/(key+'.cutp')), show_message=False)
            for result in project['result_variables']:
                tab.result_combo.setCurrentText(result)
                tab.on_result_changed(result)
                actual = window.calculation_results[result][window.value_names[0]]
                assert actual == results[result], (key, result, 'save/reload changed results')
            window.report_tab.result_combo.setCurrentText(project['result_variables'][-1])
            report = window.report_tab.generate_report_html(project['last_equation'])
            (OUT/(key+'_tool_report.html')).write_text(report, encoding='utf-8')
            if key == 'S4_raw':
                tab.check_first_order_approximation()
                assert 'deltaAlpha' in tab.approximation_label.text()
                diagnostic = tab.approximation_label.text()
            else:
                diagnostic = ''
            records.append({'key': key, 'results': results, 'independent': independent, 'diagnostic': diagnostic,
                            'save_reload': True, 'mc_automatically_run': False})
            if key in ('S2', 'S4_raw', 'S12_average'):
                window.tab_widget.setCurrentWidget(tab)
                window.resize(1500, 950)
                tab.calibration_table.resizeColumnsToContents()
                # Render the QWidget directly without changing the user's active app.
                window.ensurePolished()
                window.grab().save(str(OUT/(key+'_preview.png')))
            print(key, {name: result['coverage_factor'] for name, result in results.items()}, flush=True)
        atomic_write_json(OUT/'verification.json', records)
        write_index(records)
    finally:
        window.hide()
        window.close()


if __name__ == '__main__':
    main()
