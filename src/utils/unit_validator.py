from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import Dict, List, Optional, Tuple

import sympy as sp

from src.utils.equation_normalizer import normalize_equation_text, normalize_variable_name
from src.utils.unit_parser import Dimension, UnitParseError, format_dimension, parse_unit_expression


STATUS_OK = "OK"
STATUS_WARN = "WARN"
STATUS_ERROR = "ERROR"

DIMENSIONLESS_FUNCTIONS = {
    "sin",
    "cos",
    "tan",
    "asin",
    "acos",
    "atan",
    "sinh",
    "cosh",
    "tanh",
    "exp",
    "log",
    "ln",
}


@dataclass
class UnitValidationItem:
    name: str
    unit: str
    status: str
    message: str
    dimension: Optional[Dimension]


@dataclass
class EquationValidationItem:
    equation: str
    lhs_dimension: Optional[Dimension]
    rhs_dimension: Optional[Dimension]
    status: str
    message: str


@dataclass
class UnitValidationReport:
    variable_items: List[UnitValidationItem]
    equation_items: List[EquationValidationItem]
    ok_count: int
    warn_count: int
    error_count: int


class DimensionEvaluationError(ValueError):
    pass


def validate_main_window_units(main_window) -> UnitValidationReport:
    ordered_variables = list(dict.fromkeys(getattr(main_window, "result_variables", []) + getattr(main_window, "variables", [])))
    variable_values = getattr(main_window, "variable_values", {})
    variable_units: Dict[str, str] = {}
    for name in ordered_variables:
        value = variable_values.get(name, {})
        unit_text = ""
        if isinstance(value, dict):
            unit_text = str(value.get("unit", "")).strip()
        variable_units[normalize_variable_name(name)] = unit_text

    equation_text = getattr(main_window, "last_equation", "")
    if not equation_text and hasattr(main_window, "model_equation_tab"):
        equation_text = main_window.model_equation_tab.equation_input.toPlainText().strip()

    return validate_unit_consistency(equation_text, variable_units)


def validate_unit_consistency(equation_text: str, variable_units: Dict[str, str]) -> UnitValidationReport:
    variable_items: List[UnitValidationItem] = []
    resolved_dimensions: Dict[str, Optional[Dimension]] = {}

    for name, unit_text in variable_units.items():
        if not unit_text:
            variable_items.append(
                UnitValidationItem(
                    name=name,
                    unit="",
                    status=STATUS_WARN,
                    message="Unit is not set.",
                    dimension=None,
                )
            )
            resolved_dimensions[name] = None
            continue
        try:
            dimension = parse_unit_expression(unit_text)
            variable_items.append(
                UnitValidationItem(
                    name=name,
                    unit=unit_text,
                    status=STATUS_OK,
                    message="Parsed successfully.",
                    dimension=dimension,
                )
            )
            resolved_dimensions[name] = dimension
        except UnitParseError as error:
            variable_items.append(
                UnitValidationItem(
                    name=name,
                    unit=unit_text,
                    status=STATUS_ERROR,
                    message=str(error),
                    dimension=None,
                )
            )
            resolved_dimensions[name] = None

    equation_items = _validate_equations(equation_text, resolved_dimensions)

    ok_count = sum(1 for item in variable_items if item.status == STATUS_OK) + sum(
        1 for item in equation_items if item.status == STATUS_OK
    )
    warn_count = sum(1 for item in variable_items if item.status == STATUS_WARN) + sum(
        1 for item in equation_items if item.status == STATUS_WARN
    )
    error_count = sum(1 for item in variable_items if item.status == STATUS_ERROR) + sum(
        1 for item in equation_items if item.status == STATUS_ERROR
    )

    return UnitValidationReport(
        variable_items=variable_items,
        equation_items=equation_items,
        ok_count=ok_count,
        warn_count=warn_count,
        error_count=error_count,
    )


def _validate_equations(equation_text: str, dimensions: Dict[str, Optional[Dimension]]) -> List[EquationValidationItem]:
    normalized_text = normalize_equation_text(equation_text or "")
    equations = [part.strip() for part in normalized_text.split(",") if part.strip()]
    if not equations:
        return [
            EquationValidationItem(
                equation="",
                lhs_dimension=None,
                rhs_dimension=None,
                status=STATUS_WARN,
                message="No equation found.",
            )
        ]

    symbols = {name: sp.Symbol(name) for name in dimensions.keys()}
    items: List[EquationValidationItem] = []

    for equation in equations:
        if "=" not in equation:
            items.append(
                EquationValidationItem(
                    equation=equation,
                    lhs_dimension=None,
                    rhs_dimension=None,
                    status=STATUS_WARN,
                    message="Equation is ignored because '=' is not found.",
                )
            )
            continue

        lhs_text, rhs_text = equation.split("=", 1)
        lhs_name = normalize_variable_name(lhs_text.strip())
        rhs_expr = rhs_text.strip()
        lhs_dimension = dimensions.get(lhs_name)

        if lhs_name not in dimensions:
            items.append(
                EquationValidationItem(
                    equation=equation,
                    lhs_dimension=None,
                    rhs_dimension=None,
                    status=STATUS_WARN,
                    message=f"LHS variable '{lhs_name}' is not registered.",
                )
            )
            continue
        if lhs_dimension is None:
            items.append(
                EquationValidationItem(
                    equation=equation,
                    lhs_dimension=None,
                    rhs_dimension=None,
                    status=STATUS_WARN,
                    message=f"LHS variable '{lhs_name}' unit is unresolved.",
                )
            )
            continue

        try:
            sympy_expr = sp.sympify(rhs_expr.replace("^", "**"), locals=symbols)
            rhs_dimension = _evaluate_dimension(sympy_expr, dimensions)
        except Exception as error:
            items.append(
                EquationValidationItem(
                    equation=equation,
                    lhs_dimension=lhs_dimension,
                    rhs_dimension=None,
                    status=STATUS_ERROR,
                    message=str(error),
                )
            )
            continue

        if _is_same_dimension(lhs_dimension, rhs_dimension):
            items.append(
                EquationValidationItem(
                    equation=equation,
                    lhs_dimension=lhs_dimension,
                    rhs_dimension=rhs_dimension,
                    status=STATUS_OK,
                    message="LHS and RHS dimensions are consistent.",
                )
            )
        else:
            items.append(
                EquationValidationItem(
                    equation=equation,
                    lhs_dimension=lhs_dimension,
                    rhs_dimension=rhs_dimension,
                    status=STATUS_ERROR,
                    message="LHS and RHS dimensions do not match.",
                )
            )
    return items


def _evaluate_dimension(expression, dimensions: Dict[str, Optional[Dimension]]) -> Dimension:
    if expression is None:
        return {}
    if expression.is_Number:
        return {}
    if expression.is_Symbol:
        symbol_name = str(expression)
        symbol_dimension = dimensions.get(symbol_name)
        if symbol_dimension is None:
            raise DimensionEvaluationError(f"Unit for variable '{symbol_name}' is unresolved.")
        return symbol_dimension
    if expression.is_Add:
        arg_dimensions = [_evaluate_dimension(arg, dimensions) for arg in expression.args]
        first = arg_dimensions[0]
        for current in arg_dimensions[1:]:
            if not _is_same_dimension(first, current):
                raise DimensionEvaluationError("Addition/subtraction requires same dimensions for all terms.")
        return first
    if expression.is_Mul:
        result: Dimension = {}
        for arg in expression.args:
            result = _merge_dimension(result, _evaluate_dimension(arg, dimensions), sign=1)
        return result
    if expression.is_Pow:
        base, exponent = expression.args
        base_dimension = _evaluate_dimension(base, dimensions)
        exponent_dimension = _evaluate_dimension(exponent, dimensions)
        if exponent_dimension:
            raise DimensionEvaluationError("Exponent must be dimensionless.")
        if getattr(exponent, "free_symbols", None):
            raise DimensionEvaluationError("Exponent must be numeric.")
        exponent_fraction = _to_fraction(exponent.evalf())
        powered: Dimension = {}
        for key, value in base_dimension.items():
            powered[key] = value * exponent_fraction
            if powered[key] == 0:
                del powered[key]
        return powered
    if expression.is_Function:
        func_name = expression.func.__name__
        if func_name in DIMENSIONLESS_FUNCTIONS:
            for arg in expression.args:
                arg_dimension = _evaluate_dimension(arg, dimensions)
                if arg_dimension:
                    raise DimensionEvaluationError(f"Function '{func_name}' requires dimensionless arguments.")
            return {}
        if func_name == "Abs":
            if len(expression.args) != 1:
                raise DimensionEvaluationError("Abs function expects a single argument.")
            return _evaluate_dimension(expression.args[0], dimensions)
        raise DimensionEvaluationError(f"Unsupported function '{func_name}' in equation.")
    raise DimensionEvaluationError(f"Unsupported expression '{expression}'.")


def _to_fraction(number) -> Fraction:
    if isinstance(number, Fraction):
        return number
    if isinstance(number, int):
        return Fraction(number, 1)
    if isinstance(number, float):
        return Fraction(str(number))
    if isinstance(number, sp.Rational):
        return Fraction(int(number.p), int(number.q))
    try:
        return Fraction(str(number))
    except ValueError:
        raise DimensionEvaluationError(f"Invalid exponent '{number}'.")


def _merge_dimension(left: Dimension, right: Dimension, sign: int = 1) -> Dimension:
    merged = dict(left)
    for key, value in right.items():
        merged[key] = merged.get(key, Fraction(0)) + Fraction(sign) * value
        if merged[key] == 0:
            del merged[key]
    return merged


def _is_same_dimension(left: Optional[Dimension], right: Optional[Dimension]) -> bool:
    if left is None or right is None:
        return False
    keys = set(left.keys()) | set(right.keys())
    for key in keys:
        if left.get(key, Fraction(0)) != right.get(key, Fraction(0)):
            return False
    return True


def render_dimension(dimension: Optional[Dimension]) -> str:
    return format_dimension(dimension)
