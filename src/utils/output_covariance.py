"""Joint first-order output covariance at a single calibration point."""
import numpy as np
import sympy as sp
from .equation_handler import EquationHandler
from .model_expression import parse_expression, variable_names
from .value_handler import ValueHandler
from .input_sources import statistical_state


def evaluate_outputs(window, point, results=None):
    results = list(results or window.result_variables)
    equations = EquationHandler(window)
    expressions = []
    names = set()
    for result in results:
        equation = equations.get_target_equation(result)
        if not equation:
            raise ValueError(f'結果の式がありません: {result}')
        rhs = equation.split('=',1)[1]
        names.update(variable_names(rhs))
        expressions.append(parse_expression(rhs))
    names = sorted(names)
    handler = ValueHandler(window,point)
    values = {sp.Symbol(name, real=True): float(handler.get_central_value(name)) for name in names}
    jacobian = np.array([[float(sp.diff(expr,sp.Symbol(name, real=True)).subs(values)) for name in names] for expr in expressions])
    if not np.isfinite(jacobian).all():
        raise ValueError('有限の感度係数を評価できません')
    covariance, _, _ = statistical_state(window,names,point,handler)
    output = jacobian @ covariance @ jacobian.T
    sd = np.sqrt(np.maximum(0,np.diag(output)))
    denominator = np.outer(sd,sd)
    correlation = np.divide(output,denominator,out=np.full_like(output,np.nan),where=denominator!=0)
    return results, output, correlation
