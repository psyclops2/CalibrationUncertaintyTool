from PySide6.QtCore import QItemSelectionModel
from PySide6.QtWidgets import QTableWidgetItem

from src.utils.model_expression import FUNCTIONS, parse_expression
from src.utils.project_io import read_project
from tests.test_project_safety import window


def test_revision_table_roundtrip_commas_quotes_and_newlines(window,tmp_path):
    tab = window.document_info_tab
    assert tab.revision_table.rowCount() >= 1
    cells = ['1.2','補正式, "係数"を修正\n根拠を追加','作成者','照査者','承認者','2026-11-21']
    for column,value in enumerate(cells):
        tab.revision_table.setItem(0,column,QTableWidgetItem(value))
    assert list(tab.parse_revision_history()[0].values()) == cells
    destination = tmp_path/'revision.cutp'
    window._write_save_data_to_path(destination)
    assert window.load_data(read_project(destination),show_message=False)
    assert list(tab.parse_revision_history()[0].values()) == cells
    tab.add_revision_button.click()
    row = tab.revision_table.currentRow()
    tab.revision_table.setItem(row,0,QTableWidgetItem('2.0'))
    tab.revision_table.selectRow(row)
    tab.remove_revision_button.click()
    assert len(tab.parse_revision_history()) == 1


def test_old_csv_revisions_load_into_table(window):
    tab = window.document_info_tab
    tab.set_document_info({'revision_history':'1.0,"初版, 公開",A,B,C,2026-01-01\n1.1,改訂,D,E,F,2026-02-01'})
    assert tab.revision_table.item(0,1).text() == '初版, 公開'
    assert tab.revision_table.item(1,0).text() == '1.1'
    assert len(tab.parse_revision_history()) == 2


def test_function_menu_lists_all_supported_functions_and_inserts_editable_arguments(window):
    tab = window.model_equation_tab
    assert set(tab.function_actions) == set(FUNCTIONS)
    assert tab.insert_greek_button.menu() is not None
    assert tab.insert_function_button.menu() is not None
    assert not hasattr(tab,'greek_combo')
    assert tab.equation_input.placeholderText() == ''
    assert not hasattr(tab,'notation_combo')
    assert not hasattr(tab,'notation_help')
    tab.equation_input.setPlainText('Y = ')
    cursor = tab.equation_input.textCursor()
    cursor.movePosition(cursor.MoveOperation.End)
    tab.equation_input.setTextCursor(cursor)
    tab.function_actions['atan2'].trigger()
    assert tab.equation_input.toPlainText() == 'Y = atan2(y, x)'
    assert tab.equation_input.textCursor().selectedText() == 'y, x'
    tab.equation_input.insertPlainText('1, 1')
    assert abs(float(parse_expression(tab.equation_input.toPlainText().split('=',1)[1]))-.7853981633974483)<1e-12
    assert window.uncertainty_calculation_tab.approximation_button.text() == '一次近似を点検'
