"""Verify every generated width formula through the current parameter editor."""
import os
import re
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from PySide6.QtWidgets import QApplication,QMessageBox
from src.main_window import MainWindow
from src.utils.project_io import read_project
from src.dialogs.parameter_formula_dialog import ParameterFormulaDialog
app=QApplication([]);MainWindow._offer_recovery=lambda self:None
QMessageBox.question=lambda *a:QMessageBox.Discard
window=MainWindow();window._change_timer.stop();window._recovery_timer.stop()
count=0
try:
 for area in ('ea402','gum','euramet19','voltage_comparison'):
  for path in sorted((ROOT/'examples'/area).rglob('*.cutp')):
   assert window.load_data(read_project(path),show_message=False)
   refs=window.value_references
   if not refs:continue
   names={ident:name for name,ident in refs['variables'].items()}
   for ident in list(refs['rules']):
    name=names[ident]
    before=[v['half_width'] for v in window.variable_values[name]['values']]
    dialog=ParameterFormulaDialog(window,name)
    assert dialog.pages.currentIndex()==2 and not dialog.failures,(path,name,dialog.error.text())
    assert not any(re.fullmatch(r'input_\d+', name) for name in dialog.bindings),(path,name)
    dialog.go(1);dialog.go(2);dialog.save()
    assert dialog.result()==dialog.DialogCode.Accepted,(path,name,dialog.error.text())
    after=[v['half_width'] for v in window.variable_values[name]['values']]
    assert before==after,(path,name,before,after)
    count+=1
 print('Verified',count,'formula editors without changing widths')
finally:window.hide();window.close()
