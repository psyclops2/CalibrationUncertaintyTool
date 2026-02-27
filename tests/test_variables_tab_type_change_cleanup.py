import pytest

try:
    from PySide6.QtWidgets import QMessageBox
    from src.tabs.variables_tab_handlers import VariablesTabHandlers
except ImportError:
    pytest.skip("PySide6 is not available", allow_module_level=True)


class _FakeRadio:
    def __init__(self, checked=False):
        self._checked = checked
        self._signals_blocked = False

    def isChecked(self):
        return self._checked

    def setChecked(self, checked):
        self._checked = checked

    def blockSignals(self, blocked):
        self._signals_blocked = blocked


class _FakeMainWindow:
    def __init__(self, variable_values):
        self.variable_values = variable_values


class _FakeTabParent:
    def __init__(self, variable_values, selected_type):
        self.parent = _FakeMainWindow(variable_values)
        self.type_a_radio = _FakeRadio(selected_type == "A")
        self.type_b_radio = _FakeRadio(selected_type == "B")
        self.type_fixed_radio = _FakeRadio(selected_type == "fixed")
        self.last_visible_type = None
        self.display_called = 0
        self.layout_called = 0

    def display_current_value(self):
        self.display_called += 1

    def update_form_layout(self):
        self.layout_called += 1

    def tr(self, text):
        return text


def _create_handler_with_data(var_info, selected_type):
    parent = _FakeTabParent({"x": var_info}, selected_type)
    handler = VariablesTabHandlers(parent)
    handler.current_variable = "x"
    handler.current_variable_is_result = False
    handler.update_widget_visibility = lambda uncertainty_type: setattr(parent, "last_visible_type", uncertainty_type)
    return handler, parent


def test_type_change_b_to_a_keeps_only_unit_definition_description(monkeypatch):
    var_info = {
        "type": "B",
        "unit": "V",
        "definition": "def",
        "distribution": "NORMAL_DISTRIBUTION",
        "divisor": "2",
        "values": [
            {
                "central_value": "49",
                "standard_uncertainty": "0.000625",
                "degrees_of_freedom": "inf",
                "half_width": "0.001250",
                "calculation_formula": "25E-6*50",
                "divisor": "2",
                "description": "d1",
            },
            {
                "central_value": "50",
                "degrees_of_freedom": "100",
                "description": "d2",
                "measurements": "1,2",
            }
        ],
    }
    handler, parent = _create_handler_with_data(var_info, selected_type="A")
    monkeypatch.setattr(QMessageBox, "question", lambda *args, **kwargs: QMessageBox.Yes)

    handler.on_type_changed(True)

    cleaned = parent.parent.variable_values["x"]
    assert cleaned["type"] == "A"
    assert cleaned["unit"] == "V"
    assert cleaned["definition"] == "def"
    assert "distribution" not in cleaned
    assert "divisor" not in cleaned
    assert cleaned["values"] == [{"description": "d1"}, {"description": "d2"}]


def test_type_change_cancel_keeps_previous_type_and_values(monkeypatch):
    var_info = {
        "type": "B",
        "distribution": "NORMAL_DISTRIBUTION",
        "divisor": "2",
        "values": [{"half_width": "0.001250", "calculation_formula": "x", "divisor": "2"}],
    }
    handler, parent = _create_handler_with_data(var_info, selected_type="A")
    monkeypatch.setattr(QMessageBox, "question", lambda *args, **kwargs: QMessageBox.No)

    handler.on_type_changed(True)

    current = parent.parent.variable_values["x"]
    assert current["type"] == "B"
    assert current["distribution"] == "NORMAL_DISTRIBUTION"
    assert current["divisor"] == "2"
    assert current["values"][0]["half_width"] == "0.001250"
    assert parent.type_b_radio.isChecked()
    assert not parent.type_a_radio.isChecked()


def test_type_change_to_b_resets_all_value_fields_except_description(monkeypatch):
    var_info = {
        "type": "A",
        "unit": "V",
        "definition": "def",
        "distribution": "NORMAL_DISTRIBUTION",
        "values": [
            {
                "measurements": "1,2,3",
                "degrees_of_freedom": "4",
                "central_value": "2",
                "standard_uncertainty": "0.1",
                "description": "memo",
                "half_width": "0.1",
            }
        ],
    }
    handler, parent = _create_handler_with_data(var_info, selected_type="B")
    monkeypatch.setattr(QMessageBox, "question", lambda *args, **kwargs: QMessageBox.Yes)

    handler.on_type_changed(True)

    current = parent.parent.variable_values["x"]
    assert current["type"] == "B"
    assert current["unit"] == "V"
    assert current["definition"] == "def"
    assert "measurements" not in current["values"][0]
    assert "degrees_of_freedom" not in current["values"][0]
    assert "central_value" not in current["values"][0]
    assert "distribution" not in current
    assert current["values"][0] == {"description": "memo"}
