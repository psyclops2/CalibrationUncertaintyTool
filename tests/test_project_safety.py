import copy
import json

import numpy as np
import pytest
from PySide6.QtWidgets import QApplication, QMessageBox

from src.main_window import MainWindow
from src.utils.project_io import atomic_write_json, validate_project
from src.utils.correlation_utils import build_correlation_matrix
from src.utils.uncertainty_calculator import UncertaintyCalculator


@pytest.fixture
def window(tmp_path):
    app = QApplication.instance() or QApplication([])
    window = MainWindow()
    window._recovery_path = tmp_path / "recovery.json"
    yield window
    window.hide()
    window.close()


def test_atomic_save_preserves_existing_file_on_replace_failure(tmp_path, monkeypatch):
    path = tmp_path / "project.json"
    path.write_text('{"original": true}', encoding="utf-8")
    def fail(*args):
        raise OSError("disk error")
    monkeypatch.setattr("src.utils.project_io.os.replace", fail)
    with pytest.raises(OSError):
        atomic_write_json(path, {"new": 1})
    assert json.loads(path.read_text()) == {"original": True}
    assert list(tmp_path.iterdir()) == [path]


@pytest.mark.parametrize("data", [[], {"variables": "x"}, {"value_names": []},
    {"variable_values": {"x": {"values": [1]}}},
    {"correlation_coefficients": {"x": {"y": "nan"}}}])
def test_invalid_project_rejected(data):
    with pytest.raises(ValueError):
        validate_project(data)


def test_invalid_load_keeps_work_and_path(window, monkeypatch):
    window.last_equation = "Y = x"
    window.set_current_file_path("original.json")
    before = copy.deepcopy(window.get_save_data())
    monkeypatch.setattr(QMessageBox, "critical", lambda *args: None)
    assert window.load_data({"variables": "invalid"}, show_message=False) is False
    assert window.get_save_data() == before
    assert window.current_file_path == "original.json"


def test_apply_failure_rolls_back(window, monkeypatch):
    before = copy.deepcopy(window.get_save_data())
    original = window._apply_data
    def fail_once(data):
        if data.get("last_equation") == "FAIL":
            window.variables = ["changed"]
            raise ValueError("UI failure")
        original(data)
    monkeypatch.setattr(window, "_apply_data", fail_once)
    monkeypatch.setattr(QMessageBox, "critical", lambda *args: None)
    assert not window.load_data({"last_equation": "FAIL"}, show_message=False)
    assert window.get_save_data() == before


def test_cancel_and_failed_save_prevent_discard(window, monkeypatch):
    window.last_equation = "Y = x"
    monkeypatch.setattr(QMessageBox, "question", lambda *args: QMessageBox.Cancel)
    assert not window._confirm_unsaved()
    before = window.last_equation
    window.new_file()
    assert window.last_equation == before
    monkeypatch.setattr(QMessageBox, "question", lambda *args: QMessageBox.Save)
    monkeypatch.setattr(window, "save_file", lambda: False)
    assert not window._confirm_unsaved()


def test_dirty_recovery_and_successful_save(window, tmp_path):
    assert not window._check_modified()
    window.current_value_index = 3
    assert not window._check_modified()
    window.last_equation = "Y = x"
    window._autosave_recovery()
    assert "*" in window.windowTitle()
    assert json.loads(window._recovery_path.read_text(encoding="utf-8"))["last_equation"] == "Y = x"
    window._write_save_data_to_path(tmp_path / "saved.json")
    assert not window._check_modified()
    assert not window._recovery_path.exists()


def test_shared_correlation_validation_and_perfect_correlation(window):
    matrix = {"A": {"B": .9, "C": .9}, "B": {"C": -.9}}
    with pytest.raises(ValueError):
        build_correlation_matrix(["A", "B", "C"], matrix)
    with pytest.raises(ValueError):
        UncertaintyCalculator(None).calculate_combined_uncertainty_with_correlation([1, 1, 1], ["A", "B", "C"], matrix)
    window.correlation_coefficients = matrix
    with pytest.raises(ValueError):
        window.monte_carlo_tab._build_correlation_matrix(["A", "B", "C"])
    perfect = build_correlation_matrix(["A", "B"], {"A": {"B": 1}})
    samples = window.monte_carlo_tab._generate_correlated_normal_scores(perfect, 100)
    assert np.allclose(samples[:, 0], samples[:, 1])


def test_overview_reports_missing_and_restores_selection(window):
    data = {
        "last_equation": "Y = A + B", "variables": ["Y", "A", "B"], "result_variables": ["Y"],
        "value_names": ["P1", "P2"], "value_count": 2,
        "variable_values": {
            "Y": {"type": "result", "values": [{}, {}]},
            "A": {"type": "fixed", "values": [{"central_value": "1"}, {"central_value": "2"}]},
            "B": {"type": "fixed", "values": [{"central_value": "3"}, {"central_value": ""}]},
        },
    }
    assert window.load_data(data, show_message=False)
    tab = window.uncertainty_calculation_tab
    tab.result_combo.setCurrentText("Y")
    tab.value_combo.setCurrentIndex(0)
    original = tab.central_value_label.text()
    rows = tab.collect_point_overview()
    assert rows[0][-1] == "OK"
    assert "B" in rows[1][-1]
    assert tab.value_combo.currentIndex() == 0
    assert window.current_value_index == 0
    assert tab.value_handler.current_value_index == 0
    assert tab.central_value_label.text() == original


def test_recovery_restores_unsaved_work(window, monkeypatch):
    path = window._recovery_path.parent / "recovery-old.json"
    data = window.get_save_data()
    data["document_info"]["document_name"] = "Recovered work"
    atomic_write_json(path, data)
    monkeypatch.setattr(window, "isVisible", lambda: True)
    monkeypatch.setattr(QMessageBox, "question", lambda *args: QMessageBox.Yes)
    window._offer_recovery()
    assert window.get_save_data()["document_info"]["document_name"] == "Recovered work"
    assert window._check_modified()
    assert window.current_file_path is None
    assert window._recovery_path.exists()
    assert not path.exists()
    monkeypatch.setattr(window, "isVisible", lambda: False)


def test_open_cancel_keeps_project(window, monkeypatch, tmp_path):
    from PySide6.QtWidgets import QFileDialog
    path = tmp_path / "other.json"
    atomic_write_json(path, window.get_save_data())
    window.last_equation = "Y = x"
    before = copy.deepcopy(window.get_save_data())
    monkeypatch.setattr(QFileDialog, "getOpenFileName", lambda *args, **kwargs: (str(path), ""))
    monkeypatch.setattr(QMessageBox, "question", lambda *args: QMessageBox.Cancel)
    window.open_file()
    assert window.get_save_data() == before
    assert window.current_file_path is None


def test_invalid_correlation_clears_old_calculation(window):
    window.variables = ["Y", "A", "B", "C"]
    window.result_variables = ["Y"]
    window.last_equation = "Y = A + B + C"
    window.variable_values = {var: {"type": "B", "values": [{"central_value": "1", "standard_uncertainty": "1"}]}
                              for var in ["A", "B", "C"]}
    tab = window.uncertainty_calculation_tab
    tab.calculate_sensitivity_coefficients(window.last_equation)
    assert tab.central_value_label.text() != "--"
    window.correlation_coefficients = {"A": {"B": .9, "C": .9}, "B": {"C": -.9}}
    tab.calculate_sensitivity_coefficients(window.last_equation)
    assert tab.central_value_label.text() == "--"
    assert "相関" in tab.warning_label.text()


def test_recovery_only_writes_changed_content(window, monkeypatch):
    writes = []
    from src.utils.project_io import atomic_write_json as write
    def record(path, data):
        writes.append(copy.deepcopy(data))
        write(path, data)
    monkeypatch.setattr("src.main_window.atomic_write_json", record)
    window._autosave_recovery()
    assert not writes
    window.last_equation = "Y = x"
    window._autosave_recovery()
    window._autosave_recovery()
    window.current_value_index = 1
    window._autosave_recovery()
    assert len(writes) == 1
    window.last_equation = "Y = x + 1"
    window._autosave_recovery()
    assert len(writes) == 2
    window.last_equation = ""
    window._autosave_recovery()
    assert not window._recovery_path.exists()
    window.last_equation = "Y = x + 1"
    window._autosave_recovery()
    assert len(writes) == 3


def test_failed_recovery_write_is_retried(window, monkeypatch):
    from src.utils.project_io import atomic_write_json as write
    calls = []
    def fail_once(path, data):
        calls.append(1)
        if len(calls) == 1:
            raise OSError("temporary error")
        write(path, data)
    monkeypatch.setattr("src.main_window.atomic_write_json", fail_once)
    window.last_equation = "Y = x"
    window._autosave_recovery()
    window._autosave_recovery()
    assert len(calls) == 2
    assert window._recovery_path.exists()
