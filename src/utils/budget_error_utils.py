from dataclasses import dataclass
from typing import Optional

import sympy as sp

from .equation_normalizer import normalize_equation_text


@dataclass
class BudgetCalculationIssue:
    field_name: str
    variable_name: str
    point_name: str
    reason: str
    value_repr: str
    hint: str = ""

    def to_display_line(self) -> str:
        line = (
            f"{self.field_name} [{self.variable_name}] @ {self.point_name}: "
            f"{self.reason} (value={self.value_repr})"
        )
        if self.hint:
            return f"{line} / {self.hint}"
        return line


def detect_zero_denominator_terms(expression: str, variables, value_handler):
    """
    Return [(var_name, raw_value)] where the variable appears in denominator and
    its central value is numerically zero at the current point.
    """
    try:
        symbols = {var: sp.Symbol(var) for var in variables}
        expr = sp.sympify(
            normalize_equation_text(expression).replace("^", "**"),
            locals=symbols,
        )
        denominator = sp.denom(sp.together(expr))
    except Exception:
        return []

    if denominator == 1:
        return []

    zero_terms = []
    for var in variables:
        symbol = symbols.get(var)
        if symbol is None or symbol not in denominator.free_symbols:
            continue
        raw_value = value_handler.get_central_value(var)
        try:
            if raw_value is not None and float(raw_value) == 0.0:
                zero_terms.append((var, raw_value))
        except (TypeError, ValueError):
            continue
    return zero_terms


def build_zero_denominator_hint(zero_terms) -> str:
    if not zero_terms:
        return ""
    joined = ", ".join(f"{var}={value}" for var, value in zero_terms)
    return f"0除算候補: {joined}"


def to_budget_float(
    value,
    *,
    field_name: str,
    variable_name: str,
    point_name: str,
    tiny_imag_threshold: float = 1e-12,
):
    """
    Convert numeric/sympy values into float for uncertainty-budget calculations.
    Returns (float_value, issue). When conversion fails, float_value is None.
    """
    if value is None or value == "":
        return None, BudgetCalculationIssue(
            field_name=field_name,
            variable_name=variable_name,
            point_name=point_name,
            reason="値が空です",
            value_repr=str(value),
        )

    if value is sp.zoo:
        return None, BudgetCalculationIssue(
            field_name=field_name,
            variable_name=variable_name,
            point_name=point_name,
            reason="複素無限大です（0除算の可能性）",
            value_repr="zoo",
        )

    if value in (sp.oo, -sp.oo):
        return None, BudgetCalculationIssue(
            field_name=field_name,
            variable_name=variable_name,
            point_name=point_name,
            reason="無限大です（0除算または発散の可能性）",
            value_repr=str(value),
        )

    if value is sp.nan:
        return None, BudgetCalculationIssue(
            field_name=field_name,
            variable_name=variable_name,
            point_name=point_name,
            reason="非数（NaN）です",
            value_repr="nan",
        )

    if isinstance(value, complex):
        if abs(value.imag) <= tiny_imag_threshold:
            return float(value.real), None
        return None, BudgetCalculationIssue(
            field_name=field_name,
            variable_name=variable_name,
            point_name=point_name,
            reason="複素数です",
            value_repr=str(value),
        )

    if isinstance(value, sp.Expr):
        if value.has(sp.zoo):
            return None, BudgetCalculationIssue(
                field_name=field_name,
                variable_name=variable_name,
                point_name=point_name,
                reason="複素無限大を含みます（0除算の可能性）",
                value_repr=str(value),
            )
        if value.has(sp.oo) or value.has(-sp.oo):
            return None, BudgetCalculationIssue(
                field_name=field_name,
                variable_name=variable_name,
                point_name=point_name,
                reason="無限大を含みます",
                value_repr=str(value),
            )
        if value.has(sp.nan):
            return None, BudgetCalculationIssue(
                field_name=field_name,
                variable_name=variable_name,
                point_name=point_name,
                reason="非数（NaN）を含みます",
                value_repr=str(value),
            )
        if value.is_real is False:
            return None, BudgetCalculationIssue(
                field_name=field_name,
                variable_name=variable_name,
                point_name=point_name,
                reason="複素数です",
                value_repr=str(value),
            )

        real_part, imag_part = value.as_real_imag()
        try:
            imag_float = float(imag_part.evalf())
        except Exception:
            imag_float = None
        if imag_float is not None and abs(imag_float) > tiny_imag_threshold:
            return None, BudgetCalculationIssue(
                field_name=field_name,
                variable_name=variable_name,
                point_name=point_name,
                reason="虚部が残っています",
                value_repr=str(value),
            )

        value = real_part

    try:
        return float(value), None
    except (TypeError, ValueError):
        return None, BudgetCalculationIssue(
            field_name=field_name,
            variable_name=variable_name,
            point_name=point_name,
            reason="float変換に失敗しました",
            value_repr=str(value),
        )


def summarize_budget_issues(issues, max_lines: int = 6) -> Optional[str]:
    if not issues:
        return None

    lines = [issue.to_display_line() for issue in issues[:max_lines]]
    if len(issues) > max_lines:
        lines.append(f"... and {len(issues) - max_lines} more issue(s)")

    return (
        "不確かさバジェット計算に失敗しました。\n"
        "原因となった値を確認してください（特に分母0、複素数、NaN、∞）。\n\n"
        + "\n".join(lines)
    )
