"""Recalculate the supplied S05_1, S05_2 and S07 PDF conditions in memory."""
import json
import math
import os
from pathlib import Path
import sys

os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from PySide6.QtWidgets import QApplication
from src.main_window import MainWindow
from src.utils.language_manager import LanguageManager
from src.utils.project_io import read_project


def main():
    app=QApplication.instance() or QApplication([])
    language=LanguageManager();language.load_language()
    MainWindow._offer_recovery=lambda self:None
    window=MainWindow(language);window._change_timer.stop();window._recovery_timer.stop()
    records=[]
    try:
        for key,result in [('S5_temperature','tx'),('S5_emf','vx'),('S7','lx')]:
            p=read_project(ROOT/'examples/ea402/projects'/f'{key}.cutp')
            values=p['variable_values']
            def df(name,number):values[name]['values'][0]['degrees_of_freedom']=str(number)
            if key=='S5_temperature':
                df('ts',9);df('cert',100);df('vcal',100)
                contributions=[.1,.15,.077,.077*.5/math.sqrt(3),.077*2/math.sqrt(3),(.077/.189)*.1/math.sqrt(3),.3/math.sqrt(3),1/math.sqrt(3)]
                denominator=.1**4/9+.15**4/100+.077**4/100
                expected_y=1000.5
            elif key=='S5_emf':
                df('vobs',9);df('vcal',100);df('tempDeviation',100)
                values['tempDeviation']['values'][0]['central_value']='0.5'
                contributions=[1.6e-6,1e-6,.5e-6/math.sqrt(3),2e-6/math.sqrt(3),5e-6/math.sqrt(3),.641/26000,.1/math.sqrt(3)/39000]
                denominator=(1.6e-6)**4/9+(1e-6)**4/100+(.641/26000)**4/100
                expected_y=.036248+.5/26000
            else:
                for name in ['cert','nullA','nullB']:df(name,100)
                p['value_references']['rules']['mismatch']['expression']='0.0283'
                readings=[30.033,30.058,30.018,30.052]
                avg=sum(readings)/4
                ua=math.sqrt(sum((x-avg)**2 for x in readings)/12)
                contributions=[ua,.0025,.002/math.sqrt(3),.0283/math.sqrt(2),.003/math.sqrt(3),.0005/math.sqrt(3),.0005/math.sqrt(3),.002,.002]
                denominator=ua**4/3+.0025**4/100+2*.002**4/100
                expected_y=avg+.003
            variance=sum(x*x for x in contributions)
            assert window.load_data(p,show_message=False)
            tab=window.uncertainty_calculation_tab
            tab.result_combo.setCurrentText(result);tab.on_result_changed(result)
            actual=window.calculation_results[result][window.value_names[0]]
            for field,expected in [('result_central_value',expected_y),('result_standard_uncertainty',math.sqrt(variance)),('effective_df',variance**2/denominator)]:
                assert math.isclose(actual[field],expected,rel_tol=1e-11,abs_tol=1e-15),(key,field,actual[field],expected)
            records.append(dict(model=key,**{k:v for k,v in actual.items() if k!='budget'}))
            print(key,records[-1],flush=True)
        (ROOT/'examples/workbench-verification.json').write_text(json.dumps(records,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    finally:
        window.hide();window.close()


if __name__=='__main__':main()
