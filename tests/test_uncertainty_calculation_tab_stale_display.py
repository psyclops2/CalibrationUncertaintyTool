import pytest

try:
    from PySide6.QtWidgets import QApplication, QWidget
    from src.tabs.uncertainty_calculation_tab import UncertaintyCalculationTab
except ImportError:
    pytest.skip("PySide6 is not available", allow_module_level=True)


@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


class _DummyParent(QWidget):
    def __init__(self):
        super().__init__()
        self.variables = ["Y", "A", "B"]
        self.result_variables = ["Y"]
        self.value_names = ["P1", "P2"]
        self.correlation_coefficients = {}
        self.variable_values = {
            "Y": {
                "type": "result",
                "unit": "",
                "values": [{}, {}],
            },
            "A": {
                "type": "A",
                "unit": "",
                "values": [
                    {
                        "central_value": "2",
                        "standard_uncertainty": "0.1",
                        "degrees_of_freedom": "10",
                    },
                    {
                        "central_value": "3",
                        "standard_uncertainty": "0.1",
                        "degrees_of_freedom": "10",
                    },
                ],
            },
            "B": {
                "type": "A",
                "unit": "",
                "values": [
                    {
                        "central_value": "5",
                        "standard_uncertainty": "0.2",
                        "degrees_of_freedom": "10",
                    },
                    {
                        # P2 intentionally invalid/missing central_value
                        "central_value": "",
                        "standard_uncertainty": "0.2",
                        "degrees_of_freedom": "10",
                    },
                ],
            },
        }


def test_uncertainty_tab_clears_previous_result_on_calculation_error(qapp):
    parent = _DummyParent()
    tab = UncertaintyCalculationTab(parent)

    # 1) Successful calculation at P1
    tab.value_handler.current_value_index = 0
    tab.calculate_sensitivity_coefficients("Y = A*B")
    assert tab.central_value_label.text() != "--"
    assert tab.calibration_table.rowCount() > 0

    # 2) Failing calculation at P2 must not keep old display
    tab.value_handler.current_value_index = 1
    tab.calculate_sensitivity_coefficients("Y = A*B")

    assert tab.calibration_table.rowCount() == 0
    assert tab.central_value_label.text() == "--"
    assert tab.standard_uncertainty_label.text() == "--"
    assert tab.effective_degrees_of_freedom_label.text() == "--"
    assert tab.coverage_factor_label.text() == "--"
    assert tab.expanded_uncertainty_label.text() == "--"
