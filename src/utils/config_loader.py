import configparser
import os

from .app_logger import log_error, log_warning

class ConfigLoader:
    def __init__(self, config_path: str = None):
        # Support inline comments like: key = value  # comment
        # This avoids accidentally treating commented values as literals.
        self.config = configparser.ConfigParser(inline_comment_prefixes=("#", ";"))
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
            log_warning("Calculationセクションが見つかりません。デフォルト値を使用します。")
            return 28

    def get_calibration_point_limits(self) -> dict:
        """校正点の制限値を取得"""
        try:
            return {
                'min_count': int(self.config.get('CalibrationPoints', 'min_count')),
                'max_count': int(self.config.get('CalibrationPoints', 'max_count'))
            }
        except configparser.NoSectionError:
            log_warning("CalibrationPointsセクションが見つかりません。デフォルト値を使用します。")
            return {
                'min_count': 1,
                'max_count': 10
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
            log_warning("Distributionセクションが見つかりません。デフォルト値を使用します。")
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
            log_warning("TValuesセクションが見つかりません。デフォルト値を使用します。")
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
            log_error(f"設定ファイルの保存に失敗しました: {str(e)}")
            return False
