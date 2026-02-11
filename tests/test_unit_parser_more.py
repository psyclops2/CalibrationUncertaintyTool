import pytest

from src.utils.unit_parser import UnitParseError, format_dimension, parse_unit_expression


def test_parse_dimensionless_variants():
    assert parse_unit_expression("") == {}
    assert parse_unit_expression("1") == {}
    assert parse_unit_expression("-") == {}


def test_parse_simple_compound_units():
    dim = parse_unit_expression("m/s^2")
    assert dim["m"] == 1
    assert dim["s"] == -2


def test_parse_parentheses_and_power():
    dim = parse_unit_expression("(m/s)^2")
    assert dim["m"] == 2
    assert dim["s"] == -2


def test_parse_derived_units_expand():
    assert parse_unit_expression("Pa") == parse_unit_expression("N/m^2")
    assert parse_unit_expression("J") == parse_unit_expression("N*m")
    assert parse_unit_expression("W") == parse_unit_expression("J/s")
    assert parse_unit_expression("V") == parse_unit_expression("W/A")
    assert parse_unit_expression("ohm") == parse_unit_expression("V/A")
    assert parse_unit_expression("Ω") == parse_unit_expression("V/A")


def test_parse_celsius_aliases_as_kelvin():
    assert parse_unit_expression("degC") == parse_unit_expression("K")
    assert parse_unit_expression("digC") == parse_unit_expression("K")
    assert parse_unit_expression("℃") == parse_unit_expression("K")


def test_parse_unknown_unit_raises():
    with pytest.raises(UnitParseError):
        parse_unit_expression("foobar")


def test_parse_unsupported_character_raises():
    # Prefixes like "mm" are not supported in the current parser.
    with pytest.raises(UnitParseError):
        parse_unit_expression("mm")


def test_format_dimension_renders_dimensionless():
    assert format_dimension({}) == "1"
