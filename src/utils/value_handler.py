import traceback
from .variable_utils import get_distribution_translation_key
from .calculation_utils import evaluate_formula
from .regression_utils import calculate_linear_regression_prediction

class ValueHandler:
    def __init__(self, main_window, current_value_index=0):
        self.main_window = main_window
        self.current_value_index = current_value_index

    def _parse_regression_x(self, x_input):
        try:
            if x_input is None:
                return None
            if isinstance(x_input, (int, float)):
                return float(x_input)
            x_str = str(x_input).strip()
            if x_str == "":
                return None
            try:
                return float(x_str)
            except ValueError:
                value = evaluate_formula(x_str)
                if value is None:
                    return None
                return float(value)
        except Exception:
            return None

    def _get_regression_result(self, var):
        try:
            if var not in self.main_window.variable_values:
                return None, None, None
            var_data = self.main_window.variable_values[var]
            values = var_data.get('values', [])
            if not isinstance(values, list):
                return None, None, None
            if self.current_value_index < 0 or self.current_value_index >= len(values):
                return None, None, None
            value_data = values[self.current_value_index]
            
            # sourceフィールドを確認
            source = value_data.get('source', 'manual')
            if source != 'regression':
                # 後方互換性のため、use_regressionやtypeも確認
                if not (var_data.get('type') == 'regression' or var_data.get('use_regression')):
                    return None, None, None
            else:
                # sourceが'regression'の場合は、必ず回帰式から取得
                pass
            
            # 回帰モデルIDを取得（regression_idを優先、なければregression_model）
            model_name = value_data.get('regression_id', '') or value_data.get('regression_model', '')
            if not model_name:
                return None, None, None
            regression_model = getattr(self.main_window, 'regressions', {}).get(model_name)
            if not isinstance(regression_model, dict):
                return None, None, None
            
            # xの値を決定
            x_mode = value_data.get('regression_x_mode', 'fixed')
            if x_mode == 'point_name':
                # 校正点名を数値として使う
                point_names = getattr(self.main_window, 'value_names', [])
                if 0 <= self.current_value_index < len(point_names):
                    point_name = point_names[self.current_value_index]
                    try:
                        x_value = float(point_name)
                    except ValueError:
                        return None, None, None
                else:
                    return None, None, None
            elif x_mode == 'fixed':
                # 固定値を指定する
                x_value = self._parse_regression_x(value_data.get('regression_x_value', '') or value_data.get('regression_x', ''))
                if x_value is None:
                    return None, None, None
            else:
                # 将来拡張用（別の量の値を使う）
                return None, None, None
            
            return calculate_linear_regression_prediction(regression_model, x_value)
        except Exception as e:
            print(f"【エラー】回帰値取得エラー: {str(e)}")
            print(traceback.format_exc())
            return None, None, None

    def get_central_value(self, var):
        """変数の中央値を取得"""
        try:

            if var in self.main_window.variable_values:
                var_data = self.main_window.variable_values[var]

                
                if self.current_value_index < 0 or self.current_value_index >= len(var_data.get('values', [])):

                    return ''
                    
                value_data = var_data['values'][self.current_value_index]

                # sourceフィールドを確認
                source = value_data.get('source', 'manual')
                if source == 'regression' or var_data.get('type') == 'regression' or var_data.get('use_regression'):
                    value, _, _ = self._get_regression_result(var)
                    if value is None:
                        value = ''

                elif var_data.get('type') == 'A':
                    value = value_data.get('central_value', '')

                elif var_data.get('type') == 'B':
                    value = value_data.get('central_value', '')

                else:  # fixed
                    value = value_data.get('central_value', '')

                return value

            return ''
            
        except Exception as e:
            print(f"【エラー】中央値取得エラー: {str(e)}")
            print(traceback.format_exc())
            return ''

    def get_standard_uncertainty(self, var):
        """変数の標準不確かさを取得"""
        try:

            if var in self.main_window.variable_values:
                var_data = self.main_window.variable_values[var]

                
                if self.current_value_index < 0 or self.current_value_index >= len(var_data.get('values', [])):

                    return ''
                    
                value_data = var_data['values'][self.current_value_index]

                # sourceフィールドを確認
                source = value_data.get('source', 'manual')
                if source == 'regression' or var_data.get('type') == 'regression' or var_data.get('use_regression'):
                    _, value, _ = self._get_regression_result(var)
                    if value is None:
                        value = ''

                elif var_data.get('type') == 'A':
                    value = value_data.get('standard_uncertainty', '')

                elif var_data.get('type') == 'B':
                    value = value_data.get('standard_uncertainty', '')

                else:  # fixed
                    value = '0'  # 固定値の標準不確かさは0

                return value

            return ''
            
        except Exception as e:
            print(f"【エラー】標準不確かさ取得エラー: {str(e)}")
            print(traceback.format_exc())
            return ''

    def get_degrees_of_freedom(self, var):
        """変数の自由度を取得"""
        try:

            if var in self.main_window.variable_values:
                var_data = self.main_window.variable_values[var]

                
                if self.current_value_index < 0 or self.current_value_index >= len(var_data.get('values', [])):

                    return ''
                    
                value_data = var_data['values'][self.current_value_index]

                # sourceフィールドを確認
                source = value_data.get('source', 'manual')
                if source == 'regression' or var_data.get('type') == 'regression' or var_data.get('use_regression'):
                    _, _, degrees_of_freedom = self._get_regression_result(var)
                    if degrees_of_freedom is None:
                        degrees_of_freedom = ''
                else:
                    degrees_of_freedom = value_data.get('degrees_of_freedom', '')

                return degrees_of_freedom

            return ''
            
        except Exception as e:
            print(f"【エラー】自由度取得エラー: {str(e)}")
            print(traceback.format_exc())
            return ''

    def get_distribution(self, var):
        """変数の分布を取得"""
        try:
            if var in self.main_window.variable_values:
                var_data = self.main_window.variable_values[var]
                values = var_data.get('values', [])
                if isinstance(values, list) and 0 <= self.current_value_index < len(values):
                    value_data = values[self.current_value_index]
                    source = value_data.get('source', 'manual')
                    if source == 'regression' or var_data.get('type') == 'regression' or var_data.get('use_regression'):
                        return get_distribution_translation_key('Normal Distribution')
                if var_data.get('type') == 'B':
                    distribution = var_data.get('distribution', '')
                    return get_distribution_translation_key(distribution) or distribution
                else:
                    return ''
            return ''
            
        except Exception as e:
            print(f"【エラー】分布取得エラー: {str(e)}")
            print(traceback.format_exc())
            return ''
            
    def update_variable_value(self, var, field, value):
        """Update a specific field of a variable's value"""
        try:
            if var not in self.main_window.variable_values:
                return False
                
            var_data = self.main_window.variable_values[var]
            
            # Ensure we have a values list
            if 'values' not in var_data:
                var_data['values'] = [{}]
                
            # Ensure we have the current index
            while len(var_data['values']) <= self.current_value_index:
                var_data['values'].append({})
                
            # Update the value
            if self.current_value_index >= 0:
                if field == 'distribution':
                    value = get_distribution_translation_key(value) or value
                var_data['values'][self.current_value_index][field] = value
                return True
                
            return False
            
        except Exception as e:
            print(f"【エラー】変数値更新エラー: {str(e)}")
            print(traceback.format_exc())
            return False
