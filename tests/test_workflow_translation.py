import ast
from pathlib import Path
from string import Formatter
import xml.etree.ElementTree as ET

import pytest
from PySide6.QtCore import QCoreApplication, QTranslator, Qt
from src.dialogs.coverage_dialog import CoverageDialog
from src.dialogs.type_a_evaluation_dialog import TypeAEvaluationDialog
from src.dialogs.measurement_table_dialog import MeasurementTableDialog
from src.dialogs.input_source_dialog import InputSourceDialog
from src.tabs.model_equation_tab import FUNCTION_INSERTIONS
from src.utils.coverage import METHODS
from src.utils.variable_utils import TYPE_A_MODES
from src.i18n.translations_en import translations as EN
from src.i18n.translations_ja import translations as JA
from src.i18n.generate_translations import generate_ts_file, compile_ts_to_qm
from tests.test_project_safety import window

ROOT = Path(__file__).resolve().parents[1]


def workflow_messages(language):
    return (EN if language=='en' else JA)['WorkflowUI']


@pytest.fixture(scope='module')
def compiled_catalogs(tmp_path_factory):
    directory=tmp_path_factory.mktemp('translation-regeneration')
    for language,dictionary in (('en',EN),('ja',JA)):
        ts=directory/f'{language}.ts';qm=directory/f'{language}.qm'
        generate_ts_file(language,dictionary,str(ts))
        compile_ts_to_qm(str(ts),str(qm))
        root=ET.parse(ts)
        context=next(c for c in root.findall('context') if c.findtext('name')=='WorkflowUI')
        rebuilt={m.findtext('source'):m.findtext('translation') for m in context.findall('message')}
        assert rebuilt==dictionary['WorkflowUI']
    return directory


def test_all_shared_ui_sources_have_ja_en_translations_and_matching_placeholders():
    used = {description for _,description in FUNCTION_INSERTIONS.values()}
    used.update(METHODS.values()); used.update(TYPE_A_MODES.values())
    for path in (ROOT/'src').rglob('*.py'):
        tree = ast.parse(path.read_text(encoding='utf-8-sig'))
        for node in ast.walk(tree):
            if isinstance(node,ast.Call) and isinstance(node.func,ast.Name) and node.func.id=='tr_ui':
                if node.args and isinstance(node.args[0],ast.Constant):
                    used.add(node.args[0].value)
    japanese=workflow_messages('ja');english=workflow_messages('en')
    for source in used:
        assert source in japanese and japanese[source],source
        assert source in english and english[source],source
        def fields(text):return sorted((field,spec,conversion) for _,field,spec,conversion in Formatter().parse(text) if field is not None)
        assert fields(source)==fields(english[source]),source


def test_reference_editor_and_picker_use_compiled_language(window,compiled_catalogs):
    from src.dialogs.value_references_dialog import ValueReferencesDialog,ReferencePicker
    data={'last_equation':'Y=x','variables':['Y','x'],'result_variables':['Y'],'value_names':['P1'],
          'variable_values':{'Y':{'type':'result','values':[{}]},'x':{'type':'B','unit':'V',
          'distribution':'RECTANGULAR_DISTRIBUTION','divisor':'2','values':[{'central_value':'0','half_width':'1','standard_uncertainty':'.5','divisor':'2'}]}}}
    assert window.load_data(data,show_message=False)
    before=window.get_save_data();app=QCoreApplication.instance()
    for language in ('en','ja'):
        translator=QTranslator();assert translator.load(str(compiled_catalogs/f'{language}.qm'))
        app.installTranslator(translator)
        try:
            dialog=ValueReferencesDialog(window);picker=ReferencePicker(dialog)
            if language=='en':
                assert dialog.windowTitle()=='Reference value'
                assert picker.insert_button.text()=='Insert into formula'
            else:
                assert dialog.windowTitle()=='参照値'
                assert picker.insert_button.text()=='式に挿入'
            picker.reject();dialog.reject()
            assert window.get_save_data()==before
        finally:app.removeTranslator(translator)


def test_runtime_language_switch_updates_added_controls_without_changing_model(window,compiled_catalogs):
    data={'last_equation':'Y=x','variables':['Y','x'],'result_variables':['Y'],'value_names':['利用者の点名'],
        'variable_values':{'Y':{'type':'result','values':[{}]},'x':{'type':'A','values':[{
        'evaluation_mode':'summary','central_value':'1','standard_uncertainty':'.1','degrees_of_freedom':'9',
        'description':'利用者が記入した説明'}]}}}
    assert window.load_data(data,show_message=False)
    window.document_info_tab.description_edit.setPlainText('利用者の説明：日本語を保持')
    before=window.get_save_data()
    app=QCoreApplication.instance()
    translators=[]
    try:
        for language in ('en','ja','en'):
            if translators:app.removeTranslator(translators[-1])
            translator=QTranslator();assert translator.load(str(compiled_catalogs/f'{language}.qm'))
            translators.append(translator);app.installTranslator(translator)
            app.processEvents();window.retranslate_ui()
            model=window.model_equation_tab
            if language=='en':
                assert model.insert_greek_button.text()=='Insert character'
                assert model.insert_function_button.text()=='Insert function'
                assert model.letter_menus['lower'].title()=='Lowercase'
                assert model.function_actions['sin'].text()=='sin(x) — Sine'
                assert window.document_info_tab.add_revision_button.text()=='Add row'
                assert window.document_info_tab.revision_table.horizontalHeaderItem(1).text()=='Changes'
                assert window.variables_tab.definition_input.insert_image_button.text()=='Insert image…'
                assert window.uncertainty_calculation_tab.approximation_button.text()=='Check first-order approximation'
                assert window.monte_carlo_tab.save_trial_button.text()=='Save trial results…'
                assert window.references_action.text()=='Reference value'
                coverage=CoverageDialog({'method':'student','probability':.95},window)
                assert coverage.windowTitle()=='Coverage method (current result and calibration point)'
                assert coverage.method.currentText().startswith('Calculate from coverage probability')
                evaluation=TypeAEvaluationDialog(data['variable_values']['x']['values'][0],window)
                assert evaluation.mode.currentText()=='Enter evaluated statistics'
                table=MeasurementTableDialog(parent=window)
                assert table.columns.horizontalHeaderItem(0).text()=='Column name (quantity)'
                source=InputSourceDialog(window,'x',0,window.variables_tab)
                assert source.windowTitle()=='Source of evaluated values'
                for dialog in (coverage,evaluation,table,source):dialog.close()
            else:
                assert model.insert_greek_button.text()=='文字を挿入'
                assert window.document_info_tab.add_revision_button.text()=='行を追加'
                assert window.variables_tab.definition_input.insert_image_button.text()=='画像を挿入…'
            assert window.get_save_data()==before
    finally:
        for translator in translators:app.removeTranslator(translator)
        app.processEvents()


def test_quantity_mode_translates_on_language_change_and_deselection(window,compiled_catalogs):
    assert window.load_data({'variables':['Y','x'],'result_variables':['Y'],'last_equation':'Y=x',
        'variable_values':{'Y':{'type':'result','values':[{}]},'x':{'type':'fixed','values':[{'central_value':'1'}]}}},
        show_message=False)
    app=QCoreApplication.instance()
    tab=window.variables_tab
    translator=None
    try:
        for language in ('en','ja','en'):
            if translator:app.removeTranslator(translator)
            translator=QTranslator();assert translator.load(str(compiled_catalogs/f'{language}.qm'))
            app.installTranslator(translator);app.processEvents();window.retranslate_ui()
            tab.variable_list.setCurrentRow(0)
            assert tab.mode_display.text()==('Result quantity' if language=='en' else '計算結果')
            tab.variable_list.setCurrentRow(1)
            assert tab.mode_display.text()==('Input quantity' if language=='en' else '入力量')
            tab.variable_list.setCurrentRow(-1)
            assert tab.handlers.current_variable is None
            assert tab.mode_display.text()==('Not Selected' if language=='en' else '未選択')
            assert not tab.settings_group.isEnabled()
            assert tab.variable_list.item(1).data(Qt.UserRole)=='x'
    finally:
        if translator:app.removeTranslator(translator)
        app.processEvents()
