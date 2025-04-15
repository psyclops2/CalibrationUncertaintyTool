import traceback

class ValueHandler:
    def __init__(self, main_window, current_value_index=0):
        self.main_window = main_window
        self.current_value_index = current_value_index

    def get_central_value(self, var):
        """変数の中央値を取得"""
        try:
            print(f"【デバッグ】中央値取得開始: {var}")
            if var in self.main_window.variable_values:
                var_data = self.main_window.variable_values[var]
                print(f"【デバッグ】変数データ: {var_data}")
                
                if self.current_value_index < 0 or self.current_value_index >= len(var_data.get('values', [])):
                    print(f"【デバッグ】無効な値のインデックス: {self.current_value_index}")
                    return ''
                    
                value_data = var_data['values'][self.current_value_index]
                print(f"【デバッグ】選択された値のデータ: {value_data}")
                
                if var_data.get('type') == 'A':
                    value = value_data.get('central_value', '')
                    print(f"【デバッグ】TypeA中央値: {value}")
                elif var_data.get('type') == 'B':
                    value = value_data.get('central_value', '')
                    print(f"【デバッグ】TypeB中央値: {value}")
                else:  # fixed
                    value = value_data.get('fixed_value', '')
                    print(f"【デバッグ】固定値: {value}")
                return value
            print(f"【デバッグ】変数が見つかりません: {var}")
            return ''
            
        except Exception as e:
            print(f"【エラー】中央値取得エラー: {str(e)}")
            print(traceback.format_exc())
            return ''

    def get_standard_uncertainty(self, var):
        """変数の標準不確かさを取得"""
        try:
            print(f"【デバッグ】標準不確かさ取得開始: {var}")
            if var in self.main_window.variable_values:
                var_data = self.main_window.variable_values[var]
                print(f"【デバッグ】変数データ: {var_data}")
                
                if self.current_value_index < 0 or self.current_value_index >= len(var_data.get('values', [])):
                    print(f"【デバッグ】無効な値のインデックス: {self.current_value_index}")
                    return ''
                    
                value_data = var_data['values'][self.current_value_index]
                print(f"【デバッグ】選択された値のデータ: {value_data}")
                
                if var_data.get('type') == 'A':
                    value = value_data.get('standard_uncertainty', '')
                    print(f"【デバッグ】TypeA標準不確かさ: {value}")
                elif var_data.get('type') == 'B':
                    value = value_data.get('standard_uncertainty', '')
                    print(f"【デバッグ】TypeB標準不確かさ: {value}")
                else:  # fixed
                    value = '0'  # 固定値の標準不確かさは0
                    print(f"【デバッグ】固定値の標準不確かさ: {value}")
                return value
            print(f"【デバッグ】変数が見つかりません: {var}")
            return ''
            
        except Exception as e:
            print(f"【エラー】標準不確かさ取得エラー: {str(e)}")
            print(traceback.format_exc())
            return ''

    def get_degrees_of_freedom(self, var):
        """変数の自由度を取得"""
        try:
            print(f"【デバッグ】自由度取得開始: {var}")
            if var in self.main_window.variable_values:
                var_data = self.main_window.variable_values[var]
                print(f"【デバッグ】変数データ: {var_data}")
                
                if self.current_value_index < 0 or self.current_value_index >= len(var_data.get('values', [])):
                    print(f"【デバッグ】無効な値のインデックス: {self.current_value_index}")
                    return ''
                    
                value_data = var_data['values'][self.current_value_index]
                print(f"【デバッグ】選択された値のデータ: {value_data}")
                
                degrees_of_freedom = value_data.get('degrees_of_freedom', '')
                print(f"【デバッグ】自由度: {degrees_of_freedom}")
                return degrees_of_freedom
            print(f"【デバッグ】変数が見つかりません: {var}")
            return ''
            
        except Exception as e:
            print(f"【エラー】自由度取得エラー: {str(e)}")
            print(traceback.format_exc())
            return ''

    def get_distribution(self, var):
        """変数の分布を取得"""
        try:
            print(f"【デバッグ】分布取得開始: {var}")
            if var in self.main_window.variable_values:
                var_data = self.main_window.variable_values[var]
                print(f"【デバッグ】変数データ: {var_data}")
                
                if var_data.get('type') == 'B':
                    distribution = var_data.get('distribution', '')
                    print(f"【デバッグ】分布: {distribution}")
                    return distribution
                else:
                    print("【デバッグ】TypeB以外の変数")
                    return ''
            print(f"【デバッグ】変数が見つかりません: {var}")
            return ''
            
        except Exception as e:
            print(f"【エラー】分布取得エラー: {str(e)}")
            print(traceback.format_exc())
            return '' 