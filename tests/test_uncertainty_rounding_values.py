from decimal import Decimal

import pytest
from src.utils import uncertainty_rounding as rounding
from src.utils import number_formatter as formatter


@pytest.mark.parametrize("value,mode,expected", [
    ("1.24", "round_up", "1.3"),
    ("1.28", "5_percent", "1.3"),
    ("1.24", "5_percent", "1.2"),
    ("0.0128", "5_percent", "0.013"),
    ("1280", "5_percent", "1300"),
    ("-1.28", "round_up", "-1.3"),
])
def test_rounding(monkeypatch, value, mode, expected):
    monkeypatch.setattr(rounding, "get_uncertainty_rounding_settings",
                        lambda: {"significant_digits": 2, "rounding_mode": mode})
    assert rounding.round_uncertainty(Decimal(value)) == Decimal(expected)


@pytest.mark.parametrize("value,expected", [
    ("120", "120 E0"), ("12", "12 E0"), ("1.2", "1.2 E0"),
    ("0.12", "120 E-3"), ("-1.2", "-1.2 E0"),
    ("999", "1.0 E3"),
])
def test_engineering_format(monkeypatch, value, expected):
    monkeypatch.setattr(rounding, "get_uncertainty_rounding_settings",
                        lambda: {"significant_digits": 2, "rounding_mode": "round_up"})
    monkeypatch.setattr(formatter, "_get_uncertainty_settings", lambda: (2, "round_up"))
    assert rounding.format_uncertainty(Decimal(value)) == expected
    assert formatter.format_expanded_uncertainty(Decimal(value)) == expected.removesuffix(" E0")
