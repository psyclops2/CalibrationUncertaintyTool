"""Project validation and atomic JSON persistence."""
import json
import os
import tempfile
import math
from decimal import Decimal


def atomic_write_json(path, data):
    text = json.dumps(data, indent=4, ensure_ascii=False,
                      default=lambda value: str(value) if isinstance(value, Decimal) else _unsupported(value),
                      allow_nan=False)
    directory = os.path.dirname(os.path.abspath(path))
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=directory,
                                         prefix=".project-", suffix=".tmp", delete=False) as stream:
            temporary = stream.name
            stream.write(text)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if temporary and os.path.exists(temporary):
            os.unlink(temporary)


def _unsupported(value):
    raise TypeError(f"Cannot serialize {type(value).__name__}")


def validate_project(data):
    if not isinstance(data, dict):
        raise ValueError("Project must be a JSON object")
    for key in ("variables", "result_variables", "value_names"):
        if key in data and (not isinstance(data[key], list) or
                            any(not isinstance(v, str) or not v.strip() for v in data[key])):
            raise ValueError(f"{key}: expected a list of nonempty names")
        if key in data and len(data[key]) != len(set(data[key])):
            raise ValueError(f"{key}: duplicate names")
    for key in ("document_info", "variable_values", "correlation_coefficients", "regressions"):
        if key in data and not isinstance(data[key], dict):
            raise ValueError(f"{key}: expected an object")
    for key in ("value_count", "current_value_index"):
        if key in data and (type(data[key]) is not int or data[key] < (1 if key == "value_count" else 0)):
            raise ValueError(f"{key}: invalid index/count")
    if "value_names" in data and not data["value_names"]:
        raise ValueError("value_names: at least one point is required")
    if not isinstance(data.get("last_equation", ""), str):
        raise ValueError("last_equation: expected text")
    for name, info in data.get("variable_values", {}).items():
        if not isinstance(info, dict):
            raise ValueError(f"variable_values.{name}: expected an object")
        if info.get("type", "A") not in ("A", "B", "fixed", "result"):
            raise ValueError(f"variable_values.{name}.type: unknown type")
        values = info.get("values", [])
        if not isinstance(values, list) or any(not isinstance(v, dict) for v in values):
            raise ValueError(f"variable_values.{name}.values: expected objects")
        for field in ("unit", "definition", "distribution"):
            if field in info and not isinstance(info[field], str):
                raise ValueError(f"variable_values.{name}.{field}: expected text")
    for name, model in data.get("regressions", {}).items():
        if not isinstance(model, dict):
            raise ValueError(f"regressions.{name}: expected an object")

    for key, value in data.get("document_info", {}).items():
        if not isinstance(value, str):
            raise ValueError(f"document_info.{key}: expected text")
    coefficients = data.get("correlation_coefficients", {})
    for name, row in coefficients.items():
        if not isinstance(row, dict):
            raise ValueError(f"correlation_coefficients.{name}: expected an object")
        for other, value in row.items():
            try:
                number = float(value)
            except (ValueError, TypeError):
                raise ValueError(f"correlation_coefficients.{name}.{other}: invalid coefficient")
            if not math.isfinite(number) or abs(number) > 1:
                raise ValueError(f"correlation_coefficients.{name}.{other}: coefficient out of range")
    declared = set(data.get("variables", [])) | set(data.get("result_variables", []))
    if any(name not in declared for name in data.get("variable_values", {})):
        raise ValueError("variable_values: undeclared variable")
