import pytest

try:
    from PySide6.QtWidgets import QApplication
    from src.utils.equation_formatter import EquationFormatter
    from src.tabs.report_tab import ReportTab
except ImportError:
    pytest.skip("PySide6 is not available", allow_module_level=True)


@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_equation_formatter_formats_subscript_and_superscript():
    formatter = EquationFormatter()
    html = formatter.format_equation("Y_1 = X_2^2 + A^(n+1)")

    assert "<sub>1</sub>" in html
    assert "<sub>2</sub>" in html
    assert "<sup>2</sup>" in html
    assert "<sup>(n+1)</sup>" in html


def test_equation_formatter_keeps_underscore_inside_single_subscript():
    formatter = EquationFormatter()
    html = formatter.format_equation("Y = V_ref_stability + X_a_b")

    assert "V</span><sub>ref_stability</sub>" in html
    assert "X</span><sub>a_b</sub>" in html


def test_report_tab_model_equation_keeps_subscript_and_superscript(qapp):
    class DummyParent:
        pass

    parent = DummyParent()
    parent.last_equation = "Y_1 = X_2^2"
    parent.document_info = {}
    parent.variables = []
    parent.result_variables = ["Y_1"]
    parent.variable_values = {}
    parent.value_names = []

    tab = ReportTab()
    tab.parent = parent
    tab.result_combo.addItem("Y_1")
    tab.result_combo.setCurrentIndex(0)

    html = tab.generate_report_html("Y_1 = X_2")

    assert "<sub>1</sub>" in html
    assert "<sub>2</sub>" in html
    assert "<sup>2</sup>" in html


def test_report_tab_variable_detail_layout_type_a_and_b(qapp):
    class DummyParent:
        pass

    parent = DummyParent()
    parent.last_equation = "Y=XA+XB"
    parent.document_info = {}
    parent.variables = ["Y", "XA", "XB"]
    parent.result_variables = ["Y"]
    parent.value_names = ["P1"]
    parent.variable_values = {
        "XA": {
            "unit": "V",
            "type": "A",
            "values": [
                {
                    "central_value": "10",
                    "standard_uncertainty": "0.2",
                    "degrees_of_freedom": "9",
                    "measurements": "9.8, 10.0, 10.2",
                    "description": "TypeA detail",
                }
            ],
        },
        "XB": {
            "unit": "V",
            "type": "B",
            "distribution": "rectangular",
            "values": [
                {
                    "central_value": "20",
                    "half_width": "0.5",
                    "divisor": "1.732",
                    "degrees_of_freedom": "50",
                    "description": "TypeB detail",
                }
            ],
        },
        "Y": {
            "unit": "V",
            "type": "result",
            "values": [{"central_value": "30"}],
        },
    }

    tab = ReportTab()
    tab.parent = parent
    tab.result_combo.addItem("Y")
    tab.result_combo.setCurrentIndex(0)

    html = tab.generate_report_html("Y=XA+XB")

    assert "REPORT_VARIABLE_DETAILS" not in html
    assert "DETAIL_DESCRIPTION" not in html
    assert "<strong>XA</strong>" in html
    assert "<strong>XB</strong>" in html
    assert "REPORT_CENTRAL_VALUE" in html
    assert "REPORT_STANDARD_UNCERTAINTY" in html
    assert "REPORT_DOF" in html
    assert "<td>10</td>" in html
    assert "<td>0.2</td>" in html
    assert "<td>9</td>" in html
    assert "9.8" in html and "10.0" in html and "10.2" in html
    assert "DIVISOR" in html
    assert "<td>1.732</td>" in html
    assert "<td>50</td>" in html
    assert "TypeA detail" in html
    assert "TypeB detail" in html


def test_report_tab_variable_detail_layout_fixed_uses_plain_description(qapp):
    class DummyParent:
        pass

    parent = DummyParent()
    parent.last_equation = "Y=XF"
    parent.document_info = {}
    parent.variables = ["Y", "XF"]
    parent.result_variables = ["Y"]
    parent.value_names = ["P1"]
    parent.variable_values = {
        "XF": {
            "unit": "V",
            "type": "fixed",
            "values": [
                {
                    "central_value": "5",
                    "description": "Fixed detail",
                }
            ],
        },
        "Y": {
            "unit": "V",
            "type": "result",
            "values": [{"central_value": "5"}],
        },
    }

    tab = ReportTab()
    tab.parent = parent
    tab.result_combo.addItem("Y")
    tab.result_combo.setCurrentIndex(0)

    html = tab.generate_report_html("Y=XF")

    assert "<strong>XF</strong>" in html
    assert "DETAIL_DESCRIPTION" not in html
    assert "Fixed detail" in html
    assert "<th>REPORT_CENTRAL_VALUE</th><th>REPORT_UNIT</th>" in html
    assert "<th>DETAIL_DESCRIPTION</th>" not in html


def test_report_tab_shows_correlation_matrix_when_non_default(qapp):
    class DummyParent:
        pass

    parent = DummyParent()
    parent.last_equation = "Y=X1+X2"
    parent.document_info = {}
    parent.variables = ["Y", "X1", "X2"]
    parent.result_variables = ["Y"]
    parent.variable_values = {}
    parent.value_names = []
    parent.correlation_coefficients = {
        "X1": {"X1": 1.0, "X2": 0.35},
        "X2": {"X1": 0.35, "X2": 1.0},
    }

    tab = ReportTab()
    tab.parent = parent
    tab.result_combo.addItem("Y")
    tab.result_combo.setCurrentIndex(0)

    html = tab.generate_report_html("Y=X1+X2")

    assert "CORRELATION_MATRIX_INPUT" in html
    assert "<th>X1</th>" in html
    assert "<th>X2</th>" in html
    assert "<td>0.35</td>" in html


def test_report_tab_hides_correlation_matrix_when_off_diagonal_is_all_zero(qapp):
    class DummyParent:
        pass

    parent = DummyParent()
    parent.last_equation = "Y=X1+X2"
    parent.document_info = {}
    parent.variables = ["Y", "X1", "X2"]
    parent.result_variables = ["Y"]
    parent.variable_values = {}
    parent.value_names = []
    parent.correlation_coefficients = {
        "X1": {"X1": 1.0, "X2": 0.0},
        "X2": {"X1": 0.0, "X2": 1.0},
    }

    tab = ReportTab()
    tab.parent = parent
    tab.result_combo.addItem("Y")
    tab.result_combo.setCurrentIndex(0)

    html = tab.generate_report_html("Y=X1+X2")

    assert "CORRELATION_MATRIX_INPUT" not in html


def test_report_tab_formats_variable_names_with_underscore_in_non_equation_sections(qapp):
    class DummyParent:
        pass

    parent = DummyParent()
    parent.last_equation = "Y=V_ref_stability+X_a_b"
    parent.document_info = {}
    parent.variables = ["Y", "V_ref_stability", "X_a_b"]
    parent.result_variables = ["Y"]
    parent.value_names = ["P1"]
    parent.correlation_coefficients = {
        "V_ref_stability": {"V_ref_stability": 1.0, "X_a_b": 0.2},
        "X_a_b": {"V_ref_stability": 0.2, "X_a_b": 1.0},
    }
    parent.variable_values = {
        "Y": {"unit": "V", "type": "result", "values": [{"central_value": "1"}]},
        "V_ref_stability": {
            "unit": "V",
            "definition": "",
            "type": "fixed",
            "values": [{"central_value": "1", "description": ""}],
        },
        "X_a_b": {
            "unit": "V",
            "definition": "",
            "type": "fixed",
            "values": [{"central_value": "1", "description": ""}],
        },
    }

    tab = ReportTab()
    tab.parent = parent
    tab.result_combo.addItem("Y")
    tab.result_combo.setCurrentIndex(0)

    html = tab.generate_report_html("Y=V_ref_stability+X_a_b")

    assert "<th>V<sub>ref_stability</sub></th>" in html
    assert "<th>X<sub>a_b</sub></th>" in html
    assert "<td>V<sub>ref_stability</sub></td>" in html
    assert "<td>X<sub>a_b</sub></td>" in html
    assert "<strong>V<sub>ref_stability</sub></strong>" in html
    assert "<strong>X<sub>a_b</sub></strong>" in html


def test_report_tab_syncs_calculation_tab_selection_when_result_changes(qapp):
    class _FakeCombo:
        def __init__(self, items):
            self._items = list(items)
            self._index = 0 if self._items else -1

        def findText(self, text):
            try:
                return self._items.index(text)
            except ValueError:
                return -1

        def setCurrentIndex(self, index):
            self._index = index

        def currentText(self):
            if 0 <= self._index < len(self._items):
                return self._items[self._index]
            return ""

    class _FakeItem:
        def __init__(self, text):
            self._text = text

        def text(self):
            return self._text

    class _FakeTable:
        def __init__(self):
            self._rows = []

        def set_rows(self, rows):
            self._rows = rows

        def rowCount(self):
            return len(self._rows)

        def item(self, row, col):
            try:
                return _FakeItem(self._rows[row][col])
            except Exception:
                return None

    class _FakeLabel:
        def __init__(self):
            self._text = "-"

        def setText(self, text):
            self._text = text

        def text(self):
            return self._text

    class _FakeCalcTab:
        def __init__(self):
            self.result_combo = _FakeCombo(["Y1", "Y2"])
            self.value_combo = _FakeCombo(["P1"])
            self.calibration_table = _FakeTable()
            self.central_value_label = _FakeLabel()
            self.standard_uncertainty_label = _FakeLabel()
            self.effective_degrees_of_freedom_label = _FakeLabel()
            self.coverage_factor_label = _FakeLabel()
            self.expanded_uncertainty_label = _FakeLabel()
            self._update()

        def _update(self):
            result = self.result_combo.currentText()
            self.calibration_table.set_rows(
                [[f"factor_{result}", "1", "0.1", "10", "normal", "1", "0.1", "100%"]]
            )
            self.central_value_label.setText(f"CV_{result}")
            self.standard_uncertainty_label.setText(f"SU_{result}")
            self.effective_degrees_of_freedom_label.setText(f"DOF_{result}")
            self.coverage_factor_label.setText(f"K_{result}")
            self.expanded_uncertainty_label.setText(f"EU_{result}")

        def on_result_changed(self, _):
            self._update()

        def on_value_changed(self, _):
            self._update()

    class DummyParent:
        pass

    parent = DummyParent()
    parent.last_equation = "Y1=A,Y2=B"
    parent.document_info = {}
    parent.variables = ["Y1", "Y2", "A", "B"]
    parent.result_variables = ["Y1", "Y2"]
    parent.value_names = ["P1"]
    parent.variable_values = {
        "Y1": {"unit": "V", "type": "result", "values": [{"central_value": "1"}]},
        "Y2": {"unit": "V", "type": "result", "values": [{"central_value": "2"}]},
        "A": {"unit": "V", "type": "fixed", "values": [{"central_value": "1"}]},
        "B": {"unit": "V", "type": "fixed", "values": [{"central_value": "2"}]},
    }
    parent.correlation_coefficients = {}
    parent.uncertainty_calculation_tab = _FakeCalcTab()

    tab = ReportTab()
    tab.parent = parent
    tab.result_combo.addItem("Y1")
    tab.result_combo.addItem("Y2")
    tab.result_combo.setCurrentText("Y1")
    html_y1 = tab.generate_report_html("Y1=A")
    assert "CV_Y1" in html_y1
    assert "factor<sub>Y1</sub>" in html_y1

    tab.result_combo.setCurrentText("Y2")
    html_y2 = tab.generate_report_html("Y2=B")
    assert "CV_Y2" in html_y2
    assert "factor<sub>Y2</sub>" in html_y2
