import math

import pytest

from src.utils.uncertainty_calculator import UncertaintyCalculator


@pytest.mark.parametrize("contributions", [[1, 1], [1, -1], [-1, 1], [-1, -1]])
def test_equal_contributions_have_same_df_regardless_of_sign(contributions):
    calculator = UncertaintyCalculator(None)
    result = calculator.calculate_effective_degrees_of_freedom(
        math.sqrt(2), contributions, [5, 5]
    )
    assert result == pytest.approx(10)


def test_unequal_signed_contributions_match_welch_satterthwaite_formula():
    calculator = UncertaintyCalculator(None)
    # uc² = 2² + (-3)² = 13; denominator = 2⁴/4 + (-3)⁴/9 = 13.
    result = calculator.calculate_effective_degrees_of_freedom(
        math.sqrt(13), [2, -3], [4, 9]
    )
    assert result == pytest.approx(13)


def test_zero_contribution_does_not_affect_effective_df():
    calculator = UncertaintyCalculator(None)
    result = calculator.calculate_effective_degrees_of_freedom(
        2, [0, -2], [0, 7]
    )
    assert result == pytest.approx(7)


@pytest.mark.parametrize("infinite_df", ["inf", "infinity", "∞", float("inf")])
def test_infinite_df_component_with_negative_finite_df_component(infinite_df):
    calculator = UncertaintyCalculator(None)
    result = calculator.calculate_effective_degrees_of_freedom(
        math.sqrt(2), [1, -1], [infinite_df, 5]
    )
    assert result == pytest.approx(20)
