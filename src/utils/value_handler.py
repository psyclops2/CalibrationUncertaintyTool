import traceback

class ValueHandler:
    def __init__(self, main_window, current_value_index=0):
        self.main_window = main_window
        self.current_value_index = current_value_index

    def get_central_value(self, var):
        """変数の中央値を取得"""
        try:

            if var in self.main_window.variable_values:
                var_data = self.main_window.variable_values[var]

                
                if self.current_value_index < 0 or self.current_value_index >= len(var_data.get('values', [])):

                    return ''
                    
                value_data = var_data['values'][self.current_value_index]

                
                if var_data.get('type') == 'A':
                    value = value_data.get('central_value', '')

                elif var_data.get('type') == 'B':
                    value = value_data.get('central_value', '')

                else:  # fixed
                    value = value_data.get('fixed_value', '')

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

                
                if var_data.get('type') == 'A':
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

                
                if var_data.get('type') == 'B':
                    distribution = var_data.get('distribution', '')

                    return distribution
                else:

                    return ''

            return ''
            
        except Exception as e:
            print(f"【エラー】分布取得エラー: {str(e)}")
            print(traceback.format_exc())
            return '' 