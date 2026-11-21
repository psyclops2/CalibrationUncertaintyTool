import math
from decimal import Decimal
from types import SimpleNamespace

import pytest

from src.utils.approximation_check import find_zero_sensitivity_products
from src.utils.equation_handler import EquationHandler
from src.utils.uncertainty_calculator import UncertaintyCalculator
from src.utils.value_handler import ValueHandler
from src.utils.variable_utils import evaluate_type_a_value


def test_pooled_s2_retains_external_standard_deviation_when_observations_change():
    value = dict(evaluation_mode='pooled', measurements='10,30,20',
                 pooled_standard_deviation='25', pooled_degrees_of_freedom='40')
    first = evaluate_type_a_value(value)
    assert Decimal(first['standard_uncertainty']) == Decimal(25)/Decimal(3).sqrt()
    value.update(measurements='10,20,30,40')
    after = evaluate_type_a_value(value)
    assert after['central_value'] == '25'
    assert after['standard_uncertainty'] == '12.5'
    assert after['degrees_of_freedom'] == '40'


def test_summary_is_not_replaced_by_unrelated_observations():
    value = dict(evaluation_mode='summary', measurements='1,2,3', central_value='1000.5',
                 standard_uncertainty='.1', degrees_of_freedom='inf')
    result = evaluate_type_a_value(value)
    assert result['central_value'] == '1000.5'
    assert result['standard_uncertainty'] == '0.1'
    assert result['degrees_of_freedom'] == 'inf'


@pytest.mark.parametrize('updates', [dict(pooled_standard_deviation='-1'),
    dict(pooled_standard_deviation='NaN'), dict(pooled_degrees_of_freedom='0'),
    dict(measurements='1,Infinity')])
def test_pooled_rejects_invalid_inputs(updates):
    value = dict(evaluation_mode='pooled', measurements='1,2',
                 pooled_standard_deviation='1', pooled_degrees_of_freedom='inf')
    value.update(updates)
    with pytest.raises(ValueError):
        evaluate_type_a_value(value)


def test_value_handler_recomputes_pooled_inputs_before_consumption():
    value = dict(evaluation_mode='pooled', measurements='2,4,6,8',
                 pooled_standard_deviation='10', pooled_degrees_of_freedom='12')
    window = SimpleNamespace(variable_values={'x': {'type': 'A', 'values': [value]}})
    handler = ValueHandler(window)
    assert handler.get_central_value('x') == '5'
    assert handler.get_standard_uncertainty('x') == '5'
    assert handler.get_degrees_of_freedom('x') == '12'


def test_ea_s12_coverage_does_not_collapse_to_two_at_df_ten():
    calculator = UncertaintyCalculator(None)
    assert calculator.get_coverage_factor(10.329971955, {'method': 'ea'}) == 2.28
    assert calculator.get_coverage_factor(10.329971955, {'method': 'legacy'}) == 2
    assert calculator.get_coverage_factor(10, {'method': 'table'}) == 2.228
    assert calculator.get_coverage_factor(math.inf, {'method': 'ea'}) == 2


def test_table_interpolation_above_last_finite_df_approaches_limit():
    calculator = UncertaintyCalculator(None)
    assert calculator.get_coverage_factor(240, {'method': 'table'}) == pytest.approx(1.97)


def test_manual_factor_requires_evidence():
    calculator = UncertaintyCalculator(None)
    with pytest.raises(ValueError):
        calculator.get_coverage_factor(100, {'method': 'manual', 'k': 1.65})
    assert calculator.get_coverage_factor(100, {'method': 'manual', 'k': 1.65,
                                               'note': 'S9 dominant rectangular approximation'}) == 1.65


def test_s4_product_is_detected_without_running_mc():
    assert find_zero_sensitivity_products('ls-L*(alpha*dt+da*t)',
        dict(ls=.05, L=.05, alpha=11.5e-6, dt=0, da=0, t=0),
        dict(ls=15e-9, L=0, alpha=1e-6, dt=.03, da=1e-6, t=.3)) == [('alpha', 'dt'), ('da', 't')]
    assert find_zero_sensitivity_products('x+y', dict(x=0, y=0), dict(x=1, y=1)) == []


def test_stage_expansion_preserves_shared_input_cancellation():
    handler = EquationHandler(None)
    equation = handler.resolve_equation('y', ['stage = x+e', 'y = stage-x'])
    values = SimpleNamespace(get_central_value=lambda name: {'x': '10', 'e': '0'}[name])
    assert handler.calculate_sensitivity(equation, 'x', ['x', 'e'], values) == 0
    assert handler.calculate_sensitivity(equation, 'e', ['x', 'e'], values) == 1


def test_stage_expansion_rejects_cycles_and_preserves_numeric_exponents():
    handler = EquationHandler(None)
    with pytest.raises(ValueError, match='循環'):
        handler.resolve_equation('y', ['y=z', 'z=y'])
    equation = handler.resolve_equation('y', ['e=x', 'y=1e-6+e'])
    assert '1e-6' in equation and '(x)' in equation


def test_reference_reads_evaluated_type_a_mean_without_stale_cache():
    from src.utils.value_references import ReferenceEvaluator
    value = dict(evaluation_mode='pooled', measurements='2,4,6,8', central_value='999',
                 pooled_standard_deviation='10', pooled_degrees_of_freedom='12')
    definitions = dict(variables={'x': 'id-x'}, points=['p1'], values={}, rules={})
    evaluator = ReferenceEvaluator(definitions, {'x': {'type': 'A', 'values': [value]}})
    assert evaluator.resolve('variable:id-x:central_value:current', 'p1') == Decimal(5)
