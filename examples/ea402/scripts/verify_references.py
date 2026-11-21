"""Exercise saved S9 references via actual input widgets and the editor dialog."""
import json
import sys
from decimal import Decimal
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT))
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication
from src.main_window import MainWindow
from src.utils.language_manager import LanguageManager
from src.dialogs.value_references_dialog import ValueReferencesDialog
from src.dialogs.parameter_formula_dialog import ParameterFormulaDialog
from src.utils.project_io import atomic_write_json, read_project
from examples.sample_presentation import ensure_sample_fonts

from paths import CURRENT_PROJECTS as PROJECTS, CURRENT_REPORTS as OUT
app=QApplication([])
ensure_sample_fonts()
language=LanguageManager();language.current_language='ja';assert language.load_language()
MainWindow._offer_recovery=lambda self:None
w=MainWindow(language);w._change_timer.stop();w._recovery_timer.stop()
payload=read_project(PROJECTS/'S9.cutp')
checks=[]
try:
    for setting,ppm,offset,expected in [('100','100','0.001','0.011'),('200','100','0.001','0.021'),('100','200','0.001','0.021'),('100','100','0.002','0.012')]:
        assert w.load_data(payload,show_message=False)
        tab=w.variables_tab
        for i in range(tab.variable_list.count()):
            item=tab.variable_list.item(i)
            if item.data(Qt.UserRole)=='Vs':tab.variable_list.setCurrentItem(item)
        # Edit the setting in the existing variable input, not the half-width.
        tab.type_b_widgets['central_value'].setText(setting)
        dialog=ValueReferencesDialog(w)
        for row in range(dialog.value_list.count()):
            ident=dialog.value_list.item(row).data(Qt.UserRole)
            if ident in ('spec-ppm','spec-offset'):
                dialog.value_list.setCurrentRow(row)
                dialog.value_expression.setPlainText(ppm if ident=='spec-ppm' else offset)
        dialog.save()
        # Same entry point as the automatic timer; no old manual Calculate button.
        w._check_modified()
        width=Decimal(w.variable_values['dVs']['values'][0]['half_width'])
        assert width==Decimal(expected),(width,expected)
        checks.append({'setting_V':setting,'setting_ppm':ppm,'offset_V':offset,'computed_half_width_V':str(width)})
    assert w.load_data(payload,show_message=False)
    dialog=ParameterFormulaDialog(w,'dVs')
    dialog.review();dialog.show();app.processEvents()
    dialog.grab().save(str(OUT/'S9_reference_preview.png'))
    dialog.reject()
    atomic_write_json(OUT/'S9_reference_checks.json',{'expression':payload['value_references']['rules']['dVs']['expression'],
        'input_method':'Vs central-value widget and reusable-values editor; no half-width entry or manual Calculate button',
        'cases':checks,'original_project_unchanged':True})
    print(json.dumps(checks,indent=2))
finally:
    w.hide();w.close()
