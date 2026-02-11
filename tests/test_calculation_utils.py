from decimal import Decimal

from src.utils.calculation_utils import evaluate_formula


def test_evaluate_formula_plain_expression():
    result = evaluate_formula("1+2*3")
    assert result == Decimal("7")


def test_evaluate_formula_with_variables_and_literals():
    result = evaluate_formula("a*2+0.5", {"a": "1.5"})
    assert result == Decimal("3.5")


def test_evaluate_formula_with_power_operator_and_variables():
    result = evaluate_formula("x^2 + 1", {"x": "3"})
    assert result == Decimal("10")


def test_evaluate_formula_with_scientific_notation_lower_e():
    result = evaluate_formula("50e-6*50")
    assert result == Decimal("0.00250")


def test_evaluate_formula_with_scientific_notation_upper_e():
    result = evaluate_formula("2E3+1")
    assert result == Decimal("2001")
