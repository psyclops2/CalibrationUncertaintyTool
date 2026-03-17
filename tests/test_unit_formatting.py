import pytest

try:
    from src.tabs.uncertainty_calculation_tab import UncertaintyCalculationTab
    from src.tabs.model_equation_tab import ModelEquationTab
    from src.tabs.partial_derivative_tab import PartialDerivativeTab
except ImportError:
    pytest.skip("PySide6 is not available", allow_module_level=True)


def test_format_with_unit_placeholder():
    # 蛟､縺悟ｭ伜惠縺吶ｋ蝣ｴ蜷医∝腰菴阪′遨ｺ縺ｪ繧峨・繝ｬ繝ｼ繧ｹ繝帙Ν繝繝ｼ繧剃ｻ倅ｸ弱☆繧・
    assert UncertaintyCalculationTab._format_with_unit("1.0", "") == f"1.0 {UncertaintyCalculationTab.UNIT_PLACEHOLDER}"
    assert UncertaintyCalculationTab._format_with_unit("2.5", "m") == "2.5 m"

    # 蛟､縺檎ｩｺ繧・・繝ｬ繝ｼ繧ｹ繝帙Ν繝繝ｼ縺ｮ蝣ｴ蜷医・縺昴・縺ｾ縺ｾ霑斐☆
    assert UncertaintyCalculationTab._format_with_unit("", "m") == ""
    assert UncertaintyCalculationTab._format_with_unit("--", "") == "--"


def test_model_equation_tab_formats_multiple_subscripts():
    formatted = ModelEquationTab._format_subscripts("Y = V_ref_stability + X_a_b")
    assert "V<sub>ref_stability</sub>" in formatted
    assert "X<sub>a_b</sub>" in formatted


def test_partial_derivative_tab_formats_multiple_subscripts():
    formatted = PartialDerivativeTab._format_subscripts("dY/dV_ref_stability = A_ref_stability")
    assert "V<sub>ref_stability</sub>" in formatted
    assert "A<sub>ref_stability</sub>" in formatted
