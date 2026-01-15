import math
import traceback


def _parse_float(value):
    """Safely parse a float from various input types."""
    try:
        if value is None:
            return None
        if isinstance(value, (int, float)):
            return float(value)
        value_str = str(value).strip()
        if value_str == "":
            return None
        return float(value_str)
    except (TypeError, ValueError):
        return None


def _extract_xy_points(data):
    """Extract numeric x/y pairs from regression data."""
    if not isinstance(data, list):
        return [], []

    xs = []
    ys = []
    for row in data:
        if not isinstance(row, dict):
            continue
        x_val = _parse_float(row.get("x"))
        y_val = _parse_float(row.get("y"))
        if x_val is None or y_val is None:
            continue
        xs.append(x_val)
        ys.append(y_val)
    return xs, ys


def calculate_linear_regression_prediction(model_data, x_value):
    """
    Calculate linear regression prediction and its standard uncertainty.

    Returns tuple (prediction, standard_uncertainty, degrees_of_freedom).
    """
    try:
        xs, ys = _extract_xy_points(model_data.get("data", []))
        if len(xs) < 2:
            return None, None, None

        x_mean = sum(xs) / len(xs)
        y_mean = sum(ys) / len(ys)

        sxx = sum((x - x_mean) ** 2 for x in xs)
        if sxx == 0:
            return None, None, None

        slope = sum((x - x_mean) * (y - y_mean) for x, y in zip(xs, ys)) / sxx
        intercept = y_mean - slope * x_mean

        prediction = slope * x_value + intercept

        if len(xs) >= 3:
            residuals = [y - (slope * x + intercept) for x, y in zip(xs, ys)]
            variance = sum(r ** 2 for r in residuals) / (len(xs) - 2)
            standard_error = math.sqrt(variance)
            standard_uncertainty = standard_error * math.sqrt(
                (1 / len(xs)) + ((x_value - x_mean) ** 2 / sxx)
            )
            degrees_of_freedom = len(xs) - 2
        else:
            standard_uncertainty = 0.0
            degrees_of_freedom = "inf"

        return prediction, standard_uncertainty, degrees_of_freedom

    except Exception as e:
        print(f"【エラー】回帰モデル計算エラー: {str(e)}")
        print(traceback.format_exc())
        return None, None, None
