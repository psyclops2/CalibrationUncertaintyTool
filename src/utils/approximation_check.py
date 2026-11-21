"""Opt-in diagnostic of terms hidden by zero first derivatives; no sampling."""
import sympy as sp
from .model_expression import parse_expression


def find_zero_sensitivity_products(expression, central_values, uncertainties):
    symbols = {name: sp.Symbol(name, real=True) for name in central_values}
    expr = parse_expression(expression, symbols)
    substitutions = {symbols[name]: sp.Float(str(value), 28) for name, value in central_values.items()}
    active = [name for name in symbols if float(uncertainties.get(name, 0)) > 0]
    derivatives = {name: sp.diff(expr, symbols[name]) for name in active}
    zero = [name for name in active if derivatives[name].subs(substitutions) == 0]
    pairs = set()
    for name in zero:
        for other in active:
            second = sp.diff(derivatives[name], symbols[other]).subs(substitutions)
            if second.is_finite is False:
                raise ValueError('二次微分が有限ではありません')
            if second != 0:
                pairs.add(tuple(sorted((name, other))))
    return sorted(pairs)
