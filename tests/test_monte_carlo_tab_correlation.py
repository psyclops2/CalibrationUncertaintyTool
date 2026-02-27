import numpy as np
import pytest

try:
    from PySide6.QtWidgets import QApplication, QWidget
    from src.tabs.monte_carlo_tab import MonteCarloTab
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
        self.value_names = ["P1"]
        self.current_value_index = 0
        self.variables = ["Y", "A", "B"]
        self.result_variables = ["Y"]
        self.last_equation = "Y = A - B"
        self.correlation_coefficients = {
            "A": {"A": 1.0, "B": 0.0},
            "B": {"A": 0.0, "B": 1.0},
        }
        self.variable_values = {
            "Y": {"type": "result", "values": [{}]},
            "A": {
                "type": "B",
                "distribution": "Normal Distribution",
                "values": [{"central_value": "0", "standard_uncertainty": "1"}],
            },
            "B": {
                "type": "B",
                "distribution": "Normal Distribution",
                "values": [{"central_value": "0", "standard_uncertainty": "1"}],
            },
        }


def test_monte_carlo_uses_correlation_coefficients_for_joint_sampling(qapp):
    parent = _DummyParent()
    tab = MonteCarloTab(parent)

    sample_count = 40000

    np.random.seed(1234)
    parent.correlation_coefficients["A"]["B"] = 0.0
    parent.correlation_coefficients["B"]["A"] = 0.0
    samples_uncorrelated = tab._evaluate_result_samples("Y", sample_count)

    np.random.seed(1234)
    parent.correlation_coefficients["A"]["B"] = 0.9
    parent.correlation_coefficients["B"]["A"] = 0.9
    samples_correlated = tab._evaluate_result_samples("Y", sample_count)

    std_uncorrelated = float(np.std(samples_uncorrelated, ddof=1))
    std_correlated = float(np.std(samples_correlated, ddof=1))

    assert abs(std_uncorrelated - np.sqrt(2.0)) < 0.08
    assert abs(std_correlated - np.sqrt(0.2)) < 0.05
    assert std_correlated < std_uncorrelated * 0.5
