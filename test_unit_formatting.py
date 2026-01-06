import pytest

try:
    from src.tabs.uncertainty_calculation_tab import UncertaintyCalculationTab
except ImportError:
    pytest.skip("PySide6 is not available", allow_module_level=True)


def test_format_with_unit_placeholder():
    # 値が存在する場合、単位が空ならプレースホルダーを付与する
    assert UncertaintyCalculationTab._format_with_unit("1.0", "") == f"1.0 {UncertaintyCalculationTab.UNIT_PLACEHOLDER}"
    assert UncertaintyCalculationTab._format_with_unit("2.5", "m") == "2.5 m"

    # 値が空やプレースホルダーの場合はそのまま返す
    assert UncertaintyCalculationTab._format_with_unit("", "m") == ""
    assert UncertaintyCalculationTab._format_with_unit("--", "") == "--"
