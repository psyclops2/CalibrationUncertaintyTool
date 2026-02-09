import configparser
import os
import re

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
            self._save_config_preserving_format()
            return True
        except Exception as e:
            log_error(f"設定ファイルの保存に失敗しました: {str(e)}")
            return False

    @staticmethod
    def _parse_section_header(line: str):
        match = re.match(r"^\s*\[([^\]]+)\]\s*(?:[;#].*)?(?:\r?\n)?$", line)
        if not match:
            return None
        return match.group(1).strip()

    @staticmethod
    def _parse_option_line(line: str):
        match = re.match(
            r"^([ \t]*)([^=;#\s][^=]*?)([ \t]*=[ \t]*)(.*?)([ \t]*(?:[#;].*)?)?(\r?\n)?$",
            line,
        )
        if not match:
            return None

        key = match.group(2).strip()
        return {
            "indent": match.group(1) or "",
            "key_raw": match.group(2),
            "key_normalized": key.lower(),
            "separator": match.group(3) or " = ",
            "comment": match.group(5) or "",
            "newline": match.group(6) or "\n",
        }

    def _get_section_ranges(self, lines):
        ranges = {}
        headers = []
        for index, line in enumerate(lines):
            section_name = self._parse_section_header(line)
            if section_name is not None:
                headers.append((section_name, index))

        for index, (section_name, start) in enumerate(headers):
            end = headers[index + 1][1] if index + 1 < len(headers) else len(lines)
            ranges[section_name] = (start, end)
        return ranges

    def _save_config_preserving_format(self):
        with open(self.config_path, 'r', encoding='utf-8') as config_file:
            lines = config_file.readlines()

        for section in self.config.sections():
            section_ranges = self._get_section_ranges(lines)
            section_items = list(self.config.items(section))

            if section in section_ranges:
                section_start, section_end = section_ranges[section]
                option_line_indices = {}

                for line_index in range(section_start + 1, section_end):
                    parsed = self._parse_option_line(lines[line_index])
                    if parsed is None:
                        continue
                    option_line_indices[parsed["key_normalized"]] = (line_index, parsed)

                missing_lines = []
                for option_name, option_value in section_items:
                    normalized_name = option_name.lower()
                    value_text = str(option_value)
                    if normalized_name in option_line_indices:
                        line_index, parsed = option_line_indices[normalized_name]
                        lines[line_index] = (
                            f"{parsed['indent']}{parsed['key_raw']}{parsed['separator']}"
                            f"{value_text}{parsed['comment']}{parsed['newline']}"
                        )
                    else:
                        missing_lines.append(f"{option_name} = {value_text}\n")

                if missing_lines:
                    insertion_index = section_end
                    lines[insertion_index:insertion_index] = missing_lines
            else:
                if lines and not lines[-1].endswith("\n"):
                    lines[-1] += "\n"
                if lines and lines[-1].strip():
                    lines.append("\n")
                lines.append(f"[{section}]\n")
                for option_name, option_value in section_items:
                    lines.append(f"{option_name} = {option_value}\n")

        with open(self.config_path, 'w', encoding='utf-8') as config_file:
            config_file.writelines(lines)
