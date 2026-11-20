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


def test_math_functions_mix_with_decimal():
    assert evaluate_formula("math.sin(x)+0.5", {"x": "0"}) == Decimal("0.5")
    assert evaluate_formula("math.sqrt(2)^2") is not None


def test_unsafe_expressions_are_rejected():
    for formula in ('__import__("os")', '(1).__class__', 'math.__dict__',
                    '[x for x in ()]', 'open("test.json")'):
        assert evaluate_formula(formula) is None
    assert evaluate_formula("x+1", {"x": '1") or __import__("os")'}) is None


def test_variable_names_with_digits():
    assert evaluate_formula("x1+1e-3", {"x1": "2"}) == Decimal("2.001")
