import traceback

from .app_logger import log_error
from .variable_utils import get_distribution_translation_key


class ValueHandler:
    def __init__(self, main_window, current_value_index=0):
        self.main_window = main_window
        self.current_value_index = current_value_index

    def _get_current_value_data(self, var):
        if var not in self.main_window.variable_values:
            return None, None
        var_data = self.main_window.variable_values.get(var)
        if not isinstance(var_data, dict):
            return None, None

        values = var_data.get("values", [])
        if not isinstance(values, list):
            return None, None
        if self.current_value_index < 0 or self.current_value_index >= len(values):
            return None, None

        value_data = values[self.current_value_index]
        if not isinstance(value_data, dict):
            return None, None
        return var_data, value_data

    def get_central_value(self, var):
        """Get the central value for the current calibration point."""
        try:
            _, value_data = self._get_current_value_data(var)
            if not value_data:
                return ""
            return value_data.get("central_value", "")
        except Exception as e:
            log_error(f"中央値取得エラー: {str(e)}", details=traceback.format_exc())
            return ""

    def get_standard_uncertainty(self, var):
        """Get the standard uncertainty for the current calibration point."""
        try:
            var_data, value_data = self._get_current_value_data(var)
            if not var_data or not value_data:
                return ""

            value_type = var_data.get("type")
            if value_type == "fixed":
                return "0"

            return value_data.get("standard_uncertainty", "")
        except Exception as e:
            log_error(f"標準不確かさ取得エラー: {str(e)}", details=traceback.format_exc())
            return ""

    def get_degrees_of_freedom(self, var):
        """Get degrees of freedom for the current calibration point."""
        try:
            _, value_data = self._get_current_value_data(var)
            if not value_data:
                return ""
            return value_data.get("degrees_of_freedom", "")
        except Exception as e:
            log_error(f"自由度取得エラー: {str(e)}", details=traceback.format_exc())
            return ""

    def get_distribution(self, var):
        """Get distribution (Type B only)."""
        try:
            var_data, _ = self._get_current_value_data(var)
            if not var_data:
                return ""
            if var_data.get("type") != "B":
                return ""
            distribution = var_data.get("distribution", "")
            return get_distribution_translation_key(distribution) or distribution
        except Exception as e:
            log_error(f"分布取得エラー: {str(e)}", details=traceback.format_exc())
            return ""

    def update_variable_value(self, var, field, value):
        """Update a specific field of a variable's value."""
        try:
            if var not in self.main_window.variable_values:
                return False

            var_data = self.main_window.variable_values[var]

            if "values" not in var_data:
                var_data["values"] = [{}]

            while len(var_data["values"]) <= self.current_value_index:
                var_data["values"].append({})

            if self.current_value_index >= 0:
                if field == "distribution":
                    value = get_distribution_translation_key(value) or value
                var_data["values"][self.current_value_index][field] = value
                return True

            return False

        except Exception as e:
            log_error(f"値更新エラー: {str(e)}", details=traceback.format_exc())
            return False
