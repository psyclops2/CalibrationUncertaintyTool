from __future__ import annotations

from fractions import Fraction
from typing import Dict, List, Optional, Tuple


Dimension = Dict[str, Fraction]

BASE_UNITS = ("m", "kg", "s", "A", "K", "mol", "cd")

DERIVED_UNIT_EXPRESSIONS = {
    "N": "kg*m/s^2",
    "Pa": "N/m^2",
    "J": "N*m",
    "W": "J/s",
    "Hz": "1/s",
    "C": "A*s",
    "V": "W/A",
    "ohm": "V/A",
    "Ω": "V/A",
    "S": "A/V",
    "F": "C/V",
    "H": "V*s/A",
    "T": "Wb/m^2",
    "Wb": "V*s",
    "lx": "lm/m^2",
    "lm": "cd",
}

DIMENSIONLESS_SYMBOLS = {"", "1", "-", "—"}


class UnitParseError(ValueError):
    pass


def parse_unit_expression(unit_text: str) -> Dimension:
    text = (unit_text or "").strip()
    if text in DIMENSIONLESS_SYMBOLS:
        return {}
    parser = _UnitExpressionParser(text)
    return parser.parse()


def format_dimension(dimension: Optional[Dimension]) -> str:
    if dimension is None:
        return "--"
    if not dimension:
        return "1"

    positive_terms: List[str] = []
    negative_terms: List[str] = []
    for base in BASE_UNITS:
        exponent = dimension.get(base)
        if not exponent:
            continue
        rendered = _format_term(base, abs(exponent))
        if exponent > 0:
            positive_terms.append(rendered)
        else:
            negative_terms.append(rendered)

    if not positive_terms and not negative_terms:
        return "1"
    if not negative_terms:
        return "*".join(positive_terms) if positive_terms else "1"
    numerator = "*".join(positive_terms) if positive_terms else "1"
    denominator = "*".join(negative_terms)
    return f"{numerator}/{denominator}"


def _format_term(base: str, exponent: Fraction) -> str:
    if exponent == 1:
        return base
    if exponent.denominator == 1:
        return f"{base}^{exponent.numerator}"
    return f"{base}^{exponent.numerator}/{exponent.denominator}"


def _add_dimensions(left: Dimension, right: Dimension, sign: int = 1) -> Dimension:
    merged = dict(left)
    for base, exponent in right.items():
        merged[base] = merged.get(base, Fraction(0)) + Fraction(sign) * exponent
        if merged[base] == 0:
            del merged[base]
    return merged


class _UnitExpressionParser:
    def __init__(self, text: str):
        self.original_text = text
        normalized = text.replace("·", "*").replace("⋅", "*").replace(" ", "")
        self.tokens = self._tokenize(normalized)
        self.index = 0

    def parse(self) -> Dimension:
        result = self._parse_expression()
        if self._peek() is not None:
            raise UnitParseError(
                f"Unexpected token '{self._peek()}' in unit expression '{self.original_text}'."
            )
        return result

    def _tokenize(self, text: str) -> List[str]:
        tokens: List[str] = []
        current = []
        for char in text:
            if char.isalnum() or char in {"_", "μ", "µ", "Ω"}:
                current.append(char)
                continue
            if current:
                tokens.append("".join(current))
                current = []
            if char in {"*", "/", "^", "(", ")"}:
                tokens.append(char)
                continue
            raise UnitParseError(f"Unsupported character '{char}' in unit expression '{self.original_text}'.")
        if current:
            tokens.append("".join(current))
        return tokens

    def _parse_expression(self) -> Dimension:
        result = self._parse_term()
        while self._peek() in {"*", "/"}:
            operator = self._next()
            rhs = self._parse_term()
            if operator == "*":
                result = _add_dimensions(result, rhs, sign=1)
            else:
                result = _add_dimensions(result, rhs, sign=-1)
        return result

    def _parse_term(self) -> Dimension:
        result = self._parse_factor()
        if self._peek() == "^":
            self._next()
            exponent_token = self._next()
            exponent = self._parse_exponent(exponent_token)
            powered: Dimension = {}
            for base, base_power in result.items():
                powered[base] = base_power * exponent
            return {key: value for key, value in powered.items() if value != 0}
        return result

    def _parse_factor(self) -> Dimension:
        token = self._peek()
        if token is None:
            raise UnitParseError(f"Unexpected end of unit expression '{self.original_text}'.")
        if token == "(":
            self._next()
            inner = self._parse_expression()
            if self._next() != ")":
                raise UnitParseError(f"Missing ')' in unit expression '{self.original_text}'.")
            return inner

        token = self._next()
        if token.isdigit():
            return {}

        if token in BASE_UNITS:
            return {token: Fraction(1)}

        derived = DERIVED_UNIT_EXPRESSIONS.get(token)
        if derived is not None:
            return parse_unit_expression(derived)

        raise UnitParseError(f"Unknown unit '{token}' in unit expression '{self.original_text}'.")

    def _parse_exponent(self, token: Optional[str]) -> Fraction:
        if token is None:
            raise UnitParseError(f"Missing exponent in unit expression '{self.original_text}'.")
        if "/" in token:
            try:
                numerator, denominator = token.split("/", 1)
                return Fraction(int(numerator), int(denominator))
            except (ValueError, ZeroDivisionError):
                raise UnitParseError(
                    f"Invalid fractional exponent '{token}' in unit expression '{self.original_text}'."
                )
        try:
            return Fraction(token)
        except ValueError:
            raise UnitParseError(f"Invalid exponent '{token}' in unit expression '{self.original_text}'.")

    def _peek(self) -> Optional[str]:
        if self.index >= len(self.tokens):
            return None
        return self.tokens[self.index]

    def _next(self) -> Optional[str]:
        token = self._peek()
        if token is None:
            return None
        self.index += 1
        return token
