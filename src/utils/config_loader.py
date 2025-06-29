import configparser
import os

class ConfigLoader:
    def __init__(self, config_path: str = None):
        self.config = configparser.ConfigParser()
        if config_path is None:
            config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'config.ini')
        self.config_path = config_path  # 設定ファイルのパスを保存


        # UTF-8エンコーディングでファイルを読み込む
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config.read_file(f)


    def get_precision(self) -> int:
        """計算の精度を取得"""
        try:
            return int(self.config.get('Calculation', 'precision'))
        except configparser.NoSectionError:
            print("【警告】Calculationセクションが見つかりません。デフォルト値を使用します。")
            return 28

    def get_uncertainty_types(self) -> dict:
        """不確度の種類を取得"""
        return {
            'type_a': self.config.get('Uncertainty', 'type_a'),
            'type_b': self.config.get('Uncertainty', 'type_b'),
            'type_fixed': self.config.get('Uncertainty', 'type_fixed')
        }

    def get_fixed_value_uncertainty(self) -> float:
        """固定値の標準不確度を取得"""
        return float(self.config.get('Uncertainty', 'fixed_value_uncertainty'))

    def get_calibration_point_limits(self) -> dict:
        """校正点の制限値を取得"""
        try:
            return {
                'min_count': int(self.config.get('CalibrationPoints', 'min_count')),
                'max_count': int(self.config.get('CalibrationPoints', 'max_count'))
            }
        except configparser.NoSectionError:
            print("【警告】CalibrationPointsセクションが見つかりません。デフォルト値を使用します。")
            return {
                'min_count': 1,
                'max_count': 10
            }

    def get_rounding_settings(self) -> dict:
        """丸め設定を取得"""
        try:
            return {
                'decimal_places': int(self.config.get('Rounding', 'decimal_places'))
            }
        except configparser.NoSectionError:
            print("【警告】Roundingセクションが見つかりません。デフォルト値を使用します。")
            return {
                'decimal_places': 6
            }

    def get_defaults(self) -> dict:
        """デフォルト値を取得"""
        return {
            'value_count': int(self.config.get('Defaults', 'value_count')),
            'current_value_index': int(self.config.get('Defaults', 'current_value_index'))
        }

    def get_distribution_divisors(self) -> dict:
        """分布の除数を取得"""
        try:

            return {
                'normal': self.config.get('Distribution', 'normal_distribution'),
                'rectangular': self.config.get('Distribution', 'rectangular_distribution'),
                'triangular': self.config.get('Distribution', 'triangular_distribution'),
                'u': self.config.get('Distribution', 'u_distribution')
            }
        except configparser.NoSectionError:
            print("【警告】Distributionセクションが見つかりません。デフォルト値を使用します。")
            return {
                'normal': '',
                'rectangular': '1.732050808',
                'triangular': '2.449489743',
                'u': '1.414213562'
            }

    def get_t_values(self) -> dict:
        """t分布表を取得"""
        try:
            t_values = {}
            for key, value in self.config.items('TValues'):
                if key == 'infinity':
                    t_values[float('inf')] = float(value)
                else:
                    t_values[int(key)] = float(value)
            return t_values
        except configparser.NoSectionError:
            print("【警告】TValuesセクションが見つかりません。デフォルト値を使用します。")
            return {
                1: 12.706,
                2: 4.303,
                3: 3.182,
                4: 2.776,
                5: 2.571,
                6: 2.447,
                7: 2.365,
                8: 2.306,
                9: 2.262,
                10: 2.228,
                15: 2.131,
                20: 2.086,
                30: 2.042,
                40: 2.021,
                60: 2.000,
                120: 1.980,
                float('inf'): 1.960
            }

    def get_message(self, key: str) -> str:
        """メッセージを取得"""
        return self.config.get('Messages', key)

    def get_version(self) -> str:
        """バージョン情報を取得"""
        return self.config.get('Version', 'version')
        
    def save_config(self) -> bool:
        """設定ファイルに変更を保存する"""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                self.config.write(f)

            return True
        except Exception as e:
            print(f"【エラー】設定ファイルの保存に失敗しました: {str(e)}")
            return False
