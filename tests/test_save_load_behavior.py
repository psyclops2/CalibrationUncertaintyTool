import pytest

try:
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import QApplication

    from src.main_window import MainWindow
    from src.utils.language_manager import LanguageManager
except ImportError:
    pytest.skip("PySide6 is not available", allow_module_level=True)


@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


@pytest.fixture
def main_window(qapp):
    window = MainWindow(LanguageManager())
    try:
        yield window
    finally:
        window.close()


def test_get_save_data_omits_last_selected_fields_and_normalizes_variable_values(main_window):
    main_window.variables = ["input_a", "input_b", "fixed_c"]
    main_window.result_variables = ["result_x"]
    main_window.value_count = 2
    main_window.value_names = ["50 V", "10 V"]
    main_window.current_value_index = 1
    main_window.variable_values = {
        "result_x": {
            "type": "result",
            "unit": "V",
            "values": [
                {"central_value": "", "regression_x_mode": "fixed"},
                {"central_value": "", "regression_x_mode": "fixed"},
            ],
        },
        "input_a": {
            "type": "A",
            "unit": "V",
            "definition": "type A input",
            "distribution": "NORMAL_DISTRIBUTION",
            "values": [
                {
                    "measurements": "1,2,3",
                    "degrees_of_freedom": "2",
                    "central_value": "2",
                    "standard_uncertainty": "0.1",
                    "description": "memo",
                    "half_width": "999",
                    "source": "ui-cache",
                },
                {"description": ""},
            ],
        },
        "input_b": {
            "type": "B",
            "unit": "V",
            "definition": "type B input",
            "distribution": "RECTANGULAR_DISTRIBUTION",
            "divisor": "1.732050808",
            "values": [
                {
                    "central_value": "10",
                    "half_width": "0.2",
                    "standard_uncertainty": "0.1",
                    "degrees_of_freedom": "inf",
                    "description": "memo",
                    "calculation_formula": "10/50",
                    "divisor": "1.732050808",
                    "measurements": "should be removed",
                },
                {},
            ],
        },
        "fixed_c": {
            "type": "fixed",
            "unit": "V",
            "definition": "fixed input",
            "distribution": "NORMAL_DISTRIBUTION",
            "values": [
                {
                    "central_value": "5",
                    "description": "fixed memo",
                    "standard_uncertainty": "should be removed",
                },
                {},
            ],
        },
    }
    main_window.variables_tab.handlers.last_selected_variable = "input_b"
    main_window.variables_tab.handlers.last_selected_value_index = 1

    save_data = main_window.get_save_data()

    assert "last_selected_variable" not in save_data
    assert "last_selected_value_index" not in save_data

    saved_a = save_data["variable_values"]["input_a"]
    assert tuple(saved_a.keys()) == ("unit", "definition", "type", "values")
    assert saved_a["values"][0] == {
        "measurements": "1,2,3",
        "degrees_of_freedom": "2",
        "central_value": "2",
        "standard_uncertainty": "0.1",
        "description": "memo",
    }

    saved_b = save_data["variable_values"]["input_b"]
    assert tuple(saved_b.keys()) == ("unit", "definition", "type", "distribution", "divisor", "values")
    assert saved_b["values"][0] == {
        "degrees_of_freedom": "inf",
        "central_value": "10",
        "standard_uncertainty": "0.1",
        "half_width": "0.2",
        "description": "memo",
        "calculation_formula": "10/50",
        "divisor": "1.732050808",
    }

    saved_fixed = save_data["variable_values"]["fixed_c"]
    assert tuple(saved_fixed.keys()) == ("unit", "definition", "type", "values")
    assert saved_fixed["values"][0] == {
        "central_value": "5",
        "description": "fixed memo",
    }

    saved_result = save_data["variable_values"]["result_x"]
    assert saved_result["values"][0]["regression_x_mode"] == "fixed"


def test_load_data_ignores_legacy_last_selected_fields_and_restores_first_variable(main_window):
    data = {
        "document_info": {
            "document_number": "",
            "document_name": "",
            "version_info": "",
            "description_markdown": "",
            "description_html": "",
            "revision_history": "",
        },
        "last_equation": "result_x = input_a + input_b",
        "value_count": 2,
        "current_value_index": 1,
        "value_names": ["50 V", "10 V"],
        "variables": ["result_x", "input_a", "input_b"],
        "result_variables": ["result_x"],
        "correlation_coefficients": {},
        "variable_values": {
            "result_x": {"type": "result", "unit": "V", "values": [{}, {}]},
            "input_a": {
                "type": "A",
                "unit": "V",
                "definition": "input A",
                "values": [
                    {"measurements": "1,2,3", "description": ""},
                    {"measurements": "4,5,6", "description": ""},
                ],
            },
            "input_b": {
                "type": "fixed",
                "unit": "V",
                "definition": "input B",
                "values": [
                    {"central_value": "50", "description": ""},
                    {"central_value": "10", "description": ""},
                ],
            },
        },
        "last_selected_variable": "input_b",
        "last_selected_value_index": 0,
        "regressions": {},
    }

    main_window.load_data(data, show_message=False)

    current_item = main_window.variables_tab.variable_list.currentItem()
    assert current_item is not None
    assert current_item.data(Qt.UserRole) == "result_x"
    assert main_window.variables_tab.handlers.last_selected_variable == "result_x"
    assert main_window.variables_tab.value_combo.currentIndex() == 1
