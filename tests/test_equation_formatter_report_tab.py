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
    assert "DETAIL_DESCRIPTION" in html
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
