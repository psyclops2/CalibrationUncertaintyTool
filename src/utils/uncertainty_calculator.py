import traceback
import numpy as np
from .config_loader import ConfigLoader
from .app_logger import log_error

class UncertaintyCalculator:
    def __init__(self, main_window):
        self.main_window = main_window
        self._inf_replacement = 1e100

    def _normalize_degrees_of_freedom(self, df):
        """自由度を数値として正規化（infは大きな値に置換）"""
        if df is None:
            return None
        if isinstance(df, str):
            df_str = df.strip().lower()
            if df_str in {"inf", "infinity", "∞"}:
                return self._inf_replacement
            if df_str == "":
                return None
        try:
            df_value = float(df)
        except (TypeError, ValueError):
            return None
        if df_value == float('inf'):
            return self._inf_replacement
        return df_value

    def calculate_combined_uncertainty(self, contributions):
        """合成標準不確かさを計算"""
        try:
            total_contribution = sum(c ** 2 for c in contributions if c)
            return (total_contribution ** 0.5) if total_contribution > 0 else 0
        except Exception as e:
            log_error(f"合成標準不確かさ計算エラー: {str(e)}", details=traceback.format_exc())
            return 0

    def calculate_effective_degrees_of_freedom(self, result_standard_uncertainty, contributions, degrees_of_freedom_list):
        """有効自由度を計算（Welch-Satterthwaiteの式）"""
        try:
            if result_standard_uncertainty <= 0:
                return self._inf_replacement

            denominator = 0
            for contribution, df in zip(contributions, degrees_of_freedom_list):
                if contribution > 0:
                    df_value = self._normalize_degrees_of_freedom(df)
                    if df_value and df_value > 0:
                        denominator += (contribution ** 4) / df_value

            if denominator > 0:
                return (result_standard_uncertainty ** 4) / denominator
            return self._inf_replacement

        except Exception as e:
            log_error(f"有効自由度計算エラー: {str(e)}", details=traceback.format_exc())
            return self._inf_replacement

    def get_coverage_factor(self, effective_df):
        """包含係数を取得"""
        try:
            if effective_df >= 10:
                return 2.0
            return self.get_t_value(effective_df)
        except Exception as e:
            log_error(f"包含係数取得エラー: {str(e)}", details=traceback.format_exc())
            return 2.0

    def get_t_value(self, degrees_of_freedom):
        """t分布表から95%信頼区間のt値を取得"""
        # t分布表を設定ファイルから取得
        config = ConfigLoader()
        t_table = config.get_t_values()
        
        try:
            df = float(degrees_of_freedom)
            # 完全一致する自由度がある場合
            if df in t_table:
                return t_table[df]
            
            # 最も近い値を探す
            keys = sorted(t_table.keys())
            for i in range(len(keys) - 1):
                if keys[i] <= df < keys[i + 1]:
                    # 線形補間
                    x1, x2 = keys[i], keys[i + 1]
                    y1, y2 = t_table[x1], t_table[x2]
                    return y1 + (y2 - y1) * (df - x1) / (x2 - x1)
            
            # 範囲外の場合は無限大の値を使用
            return t_table.get(float('inf'), 1.960)
            
        except Exception as e:
            log_error(f"t値取得エラー: {str(e)}", details=traceback.format_exc())
            return 2.0  # エラー時はデフォルト値として2.0を返す

    def calculate_contribution_rates(self, contributions):
        """寄与率を計算"""
        try:
            total_contribution = sum(c ** 2 for c in contributions if c)
            if total_contribution <= 0:
                return [0] * len(contributions)

            return [(c ** 2 / total_contribution) * 100 if c else 0 for c in contributions]

        except Exception as e:
            log_error(f"寄与率計算エラー: {str(e)}", details=traceback.format_exc())
            return [0] * len(contributions) 
