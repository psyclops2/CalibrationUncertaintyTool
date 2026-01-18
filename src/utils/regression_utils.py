import math
import traceback

import sympy as sp


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


def _extract_xy_points(data, x_key="x", y_key="y"):
    """Extract numeric x/y pairs from regression data."""
    if not isinstance(data, list):
        return [], []

    xs = []
    ys = []
    for row in data:
        if not isinstance(row, dict):
            continue
        x_val = _parse_float(row.get(x_key))
        y_val = _parse_float(row.get(y_key))
        if x_val is None or y_val is None:
            continue
        xs.append(x_val)
        ys.append(y_val)
    return xs, ys


def _extract_xyw_points(data, x_key="x", y_key="y", weight_key="ux", use_weights=False):
    """Extract numeric x/y pairs and optional weights from regression data."""
    if not isinstance(data, list):
        return [], [], []

    xs = []
    ys = []
    ws = []
    for row in data:
        if not isinstance(row, dict):
            continue
        x_val = _parse_float(row.get(x_key))
        y_val = _parse_float(row.get(y_key))
        if x_val is None or y_val is None:
            continue
        xs.append(x_val)
        ys.append(y_val)
        if use_weights:
            weight_base = _parse_float(row.get(weight_key))
            if weight_base is not None and weight_base > 0:
                ws.append(1.0 / (weight_base ** 2))
            else:
                ws.append(1.0)
    return xs, ys, ws


def _resolve_use_weights(model_data, use_weights):
    if use_weights is None:
        return bool(model_data.get("use_weights", False))
    return bool(use_weights)


def calculate_xy_averages(model_data, x_key="x", y_key="y", weight_key="ux", use_weights=None):
    """Calculate average x and y values used for regression."""
    try:
        use_weights = _resolve_use_weights(model_data, use_weights)
        if use_weights:
            xs, ys, ws = _extract_xyw_points(
                model_data.get("data", []),
                x_key=x_key,
                y_key=y_key,
                weight_key=weight_key,
                use_weights=True,
            )
            if not xs:
                return None, None
            weight_sum = sum(ws)
            if weight_sum == 0:
                return None, None
            x_mean = sum(w * x for w, x in zip(ws, xs)) / weight_sum
            y_mean = sum(w * y for w, y in zip(ws, ys)) / weight_sum
        else:
            xs, ys = _extract_xy_points(model_data.get("data", []), x_key=x_key, y_key=y_key)
            if not xs:
                return None, None
            x_mean = sum(xs) / len(xs)
            y_mean = sum(ys) / len(ys)
        return x_mean, y_mean
    except Exception as e:
        print(f"【エラー】平均値計算エラー: {str(e)}")
        print(traceback.format_exc())
        return None, None


def calculate_value_average(model_data, value_key):
    """Calculate average of a numeric column in regression data."""
    try:
        values = []
        for row in model_data.get("data", []):
            if not isinstance(row, dict):
                continue
            value = _parse_float(row.get(value_key))
            if value is None:
                continue
            values.append(value)
        if not values:
            return None
        return sum(values) / len(values)
    except Exception as e:
        print(f"【エラー】平均値計算エラー: {str(e)}")
        print(traceback.format_exc())
        return None


def calculate_regression_sxx(model_data, weight_key="ux", use_weights=None):
    """Calculate Sxx and mean of x values used for regression."""
    try:
        use_weights = _resolve_use_weights(model_data, use_weights)
        xs, ys, ws = _extract_xyw_points(
            model_data.get("data", []),
            x_key="x",
            y_key="y",
            weight_key=weight_key,
            use_weights=use_weights,
        )
        if len(xs) < 2:
            return None, None, 0
        if use_weights:
            weight_sum = sum(ws)
            if weight_sum == 0:
                return None, None, 0
            x_mean = sum(w * x for w, x in zip(ws, xs)) / weight_sum
            sxx = sum(w * (x - x_mean) ** 2 for w, x in zip(ws, xs))
        else:
            x_mean = sum(xs) / len(xs)
            sxx = sum((x - x_mean) ** 2 for x in xs)
        return sxx, x_mean, len(xs)
    except Exception as e:
        print(f"【エラー】Sxx計算エラー: {str(e)}")
        print(traceback.format_exc())
        return None, None, 0


def calculate_linear_regression_parameters(model_data, x_key="x", y_key="y", weight_key="ux", use_weights=None):
    """
    Calculate linear regression parameters (slope, intercept, residual standard deviation, degrees of freedom).
    
    Returns tuple (slope, intercept, residual_std, degrees_of_freedom, data_count) or None if error.
    """
    try:
        use_weights = _resolve_use_weights(model_data, use_weights)
        xs, ys, ws = _extract_xyw_points(
            model_data.get("data", []),
            x_key=x_key,
            y_key=y_key,
            weight_key=weight_key,
            use_weights=use_weights,
        )
        if len(xs) < 2:
            return None

        if use_weights:
            weight_sum = sum(ws)
            if weight_sum == 0:
                return None
            x_mean = sum(w * x for w, x in zip(ws, xs)) / weight_sum
            y_mean = sum(w * y for w, y in zip(ws, ys)) / weight_sum
            sxx = sum(w * (x - x_mean) ** 2 for w, x in zip(ws, xs))
        else:
            x_mean = sum(xs) / len(xs)
            y_mean = sum(ys) / len(ys)
            sxx = sum((x - x_mean) ** 2 for x in xs)
        if sxx == 0:
            return None

        if use_weights:
            slope = sum(
                w * (x - x_mean) * (y - y_mean) for w, x, y in zip(ws, xs, ys)
            ) / sxx
        else:
            slope = sum((x - x_mean) * (y - y_mean) for x, y in zip(xs, ys)) / sxx
        intercept = y_mean - slope * x_mean

        if len(xs) >= 3:
            residuals = [y - (slope * x + intercept) for x, y in zip(xs, ys)]
            if use_weights:
                variance = sum(w * (r ** 2) for w, r in zip(ws, residuals)) / (len(xs) - 2)
            else:
                variance = sum(r ** 2 for r in residuals) / (len(xs) - 2)
            residual_std = math.sqrt(variance)
            degrees_of_freedom = len(xs) - 2
        else:
            residual_std = 0.0
            degrees_of_freedom = "inf"

        return (slope, intercept, residual_std, degrees_of_freedom, len(xs))

    except Exception as e:
        print(f"【エラー】回帰パラメータ計算エラー: {str(e)}")
        print(traceback.format_exc())
        return None


def calculate_significance_f(model_data, slope=None, intercept=None, x_key="x", y_key="y", weight_key="ux", use_weights=None):
    """
    Calculate Significance F (p-value) for linear regression.

    Returns p-value (float) or None if it cannot be computed.
    """
    try:
        use_weights = _resolve_use_weights(model_data, use_weights)
        xs, ys, ws = _extract_xyw_points(
            model_data.get("data", []),
            x_key=x_key,
            y_key=y_key,
            weight_key=weight_key,
            use_weights=use_weights,
        )
        data_count = len(xs)
        if data_count < 3:
            return None

        if use_weights:
            weight_sum = sum(ws)
            if weight_sum == 0:
                return None
            x_mean = sum(w * x for w, x in zip(ws, xs)) / weight_sum
            y_mean = sum(w * y for w, y in zip(ws, ys)) / weight_sum
            sxx = sum(w * (x - x_mean) ** 2 for w, x in zip(ws, xs))
        else:
            x_mean = sum(xs) / data_count
            y_mean = sum(ys) / data_count
            sxx = sum((x - x_mean) ** 2 for x in xs)
        if sxx == 0:
            return None

        if slope is None or intercept is None:
            if use_weights:
                slope = sum(
                    w * (x - x_mean) * (y - y_mean) for w, x, y in zip(ws, xs, ys)
                ) / sxx
            else:
                slope = sum((x - x_mean) * (y - y_mean) for x, y in zip(xs, ys)) / sxx
            intercept = y_mean - slope * x_mean

        y_hat = [slope * x + intercept for x in xs]
        if use_weights:
            ssr = sum(w * ((yh - y_mean) ** 2) for w, yh in zip(ws, y_hat))
            sse = sum(w * ((y - yh) ** 2) for w, y, yh in zip(ws, ys, y_hat))
        else:
            ssr = sum((yh - y_mean) ** 2 for yh in y_hat)
            sse = sum((y - yh) ** 2 for y, yh in zip(ys, y_hat))

        df1 = 1
        df2 = data_count - 2
        if sse == 0 or df2 <= 0:
            return 0.0

        mse = sse / df2
        if mse == 0:
            return 0.0

        f_stat = ssr / mse
        if f_stat < 0:
            return None

        x = (df1 * f_stat) / (df1 * f_stat + df2)
        a = df1 / 2
        b = df2 / 2
        incomplete = sp.betainc(a, b, 0, x)
        regularized = incomplete / sp.beta(a, b)
        p_value = 1 - float(sp.N(regularized))
        if math.isnan(p_value):
            return None
        return max(0.0, min(1.0, p_value))

    except Exception as e:
        print(f"【エラー】有意F計算エラー: {str(e)}")
        print(traceback.format_exc())
        return None


def calculate_linear_regression_prediction(model_data, x_value, weight_key="ux", use_weights=None):
    """
    Calculate linear regression prediction and its standard uncertainty.

    Returns tuple (prediction, standard_uncertainty, degrees_of_freedom).
    """
    try:
        use_weights = _resolve_use_weights(model_data, use_weights)
        xs, ys, ws = _extract_xyw_points(
            model_data.get("data", []),
            x_key="x",
            y_key="y",
            weight_key=weight_key,
            use_weights=use_weights,
        )
        if len(xs) < 2:
            return None, None, None

        if use_weights:
            weight_sum = sum(ws)
            if weight_sum == 0:
                return None, None, None
            x_mean = sum(w * x for w, x in zip(ws, xs)) / weight_sum
            y_mean = sum(w * y for w, y in zip(ws, ys)) / weight_sum
            sxx = sum(w * (x - x_mean) ** 2 for w, x in zip(ws, xs))
        else:
            x_mean = sum(xs) / len(xs)
            y_mean = sum(ys) / len(ys)
            sxx = sum((x - x_mean) ** 2 for x in xs)
        if sxx == 0:
            return None, None, None

        if use_weights:
            slope = sum(
                w * (x - x_mean) * (y - y_mean) for w, x, y in zip(ws, xs, ys)
            ) / sxx
        else:
            slope = sum((x - x_mean) * (y - y_mean) for x, y in zip(xs, ys)) / sxx
        intercept = y_mean - slope * x_mean

        prediction = slope * x_value + intercept

        if len(xs) >= 3:
            residuals = [y - (slope * x + intercept) for x, y in zip(xs, ys)]
            if use_weights:
                variance = sum(w * (r ** 2) for w, r in zip(ws, residuals)) / (len(xs) - 2)
            else:
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
