import pytest

from src.utils.unit_validator import STATUS_ERROR, STATUS_OK, STATUS_WARN, render_dimension, validate_unit_consistency


def test_validate_no_equation_warn():
    report = validate_unit_consistency("", {"x": "m"})
    assert report.warn_count >= 1
    assert any(item.status == STATUS_WARN for item in report.equation_items)


def test_validate_lhs_unit_unresolved_warn():
    report = validate_unit_consistency("y = x", {"y": "", "x": "m"})
    assert any(item.status == STATUS_WARN for item in report.equation_items)


def test_validate_rhs_symbol_missing_is_error():
    report = validate_unit_consistency("y = x + z", {"y": "m", "x": "m"})
    assert any(item.status == STATUS_ERROR for item in report.equation_items)


def test_validate_trig_requires_dimensionless():
    report = validate_unit_consistency("y = sin(x)", {"y": "1", "x": "m"})
    assert any(item.status == STATUS_ERROR for item in report.equation_items)


def test_validate_power_exponent_must_be_numeric():
    report = validate_unit_consistency("y = x^a", {"y": "1", "x": "m", "a": "1"})
    assert any(item.status == STATUS_ERROR for item in report.equation_items)


def test_validate_abs_preserves_dimension():
    report = validate_unit_consistency("y = Abs(x)", {"y": "m", "x": "m"})
    assert any(item.status == STATUS_OK for item in report.equation_items)


def test_validate_sqrt_via_pow_rational_exponent():
    report = validate_unit_consistency("y = sqrt(x)", {"y": "m", "x": "m^2"})
    assert any(item.status == STATUS_OK for item in report.equation_items)


def test_render_dimension_fractional_exponent():
    report = validate_unit_consistency("y = sqrt(x)", {"y": "m", "x": "m^2"})
    item = report.equation_items[0]
    assert render_dimension(item.lhs_dimension) == "m"
    assert render_dimension(item.rhs_dimension) == "m"

