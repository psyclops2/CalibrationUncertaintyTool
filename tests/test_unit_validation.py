from fractions import Fraction

from src.utils.unit_parser import parse_unit_expression
from src.utils.unit_validator import STATUS_ERROR, STATUS_OK, validate_unit_consistency


def test_parse_unit_expression_with_derived_units():
    dimension = parse_unit_expression("N")
    assert dimension["kg"] == Fraction(1)
    assert dimension["m"] == Fraction(1)
    assert dimension["s"] == Fraction(-2)


def test_validate_unit_consistency_ok_case():
    report = validate_unit_consistency(
        "F = m * a",
        {
            "F": "N",
            "m": "kg",
            "a": "m/s^2",
        },
    )
    assert report.error_count == 0
    assert any(item.status == STATUS_OK for item in report.equation_items)


def test_validate_unit_consistency_mismatch_case():
    report = validate_unit_consistency(
        "x = t + y",
        {
            "x": "m",
            "t": "s",
            "y": "m",
        },
    )
    assert any(item.status == STATUS_ERROR for item in report.equation_items)


def test_validate_unit_consistency_celsius_alias_ok_case():
    report = validate_unit_consistency(
        "T = dT",
        {
            "T": "K",
            "dT": "℃",
        },
    )
    assert report.error_count == 0
    assert any(item.status == STATUS_OK for item in report.equation_items)
