"""Explicit coverage methods; EA values are from EA-4/02 M:2022, Table E.1."""
from functools import lru_cache
import math
from statistics import NormalDist
import mpmath as mp
from .ui_translation import tr_ui

METHODS = {
    'legacy': '従来互換（自由度10以上はk=2）',
    'table': 't分布（設定ファイルの表）',
    'ea': 'EA-4/02 表E.1（95.45%・自由度切捨て）',
    'manual': '包含係数を指定（根拠を記録）',
    'student': '包含確率から計算（t分布／正規分布近似）',
}
EA_TABLE = dict(enumerate((0, 13.97, 4.53, 3.31, 2.87, 2.65, 2.52, 2.43,
                          2.37, 2.32, 2.28, 2.25, 2.23, 2.21, 2.20, 2.18,
                          2.17, 2.16, 2.15, 2.14, 2.13)))
EA_TABLE.update({25: 2.11, 30: 2.09, 35: 2.07, 40: 2.06, 45: 2.06, 50: 2.05})


def validate_coverage(settings):
    if not isinstance(settings, dict) or settings.get('method') not in METHODS:
        raise ValueError('包含係数の評価方法が不正です')
    if not isinstance(settings.get('note', ''), str):
        raise ValueError('包含係数の根拠は文字列で入力してください')
    if settings['method'] == 'manual':
        k = float(settings.get('k', ''))
        if not math.isfinite(k) or k <= 0 or not settings.get('note', '').strip():
            raise ValueError('正の包含係数と採用根拠を入力してください')
    if settings['method'] == 'student':
        probability = float(settings.get('probability',0))
        if not math.isfinite(probability) or not 0 < probability < 1:
            raise ValueError('包含確率は0%より大きく100%未満にしてください')
        if type(settings.get('floor_df',False)) is not bool:
            raise ValueError('自由度の切捨て条件が不正です')


@lru_cache(maxsize=512)
def student_factor(df, probability, floor_df=False):
    if math.isnan(df) or df <= 0:
        raise ValueError('有効自由度は正の数にしてください')
    if not 0 < probability < 1:
        raise ValueError('包含確率は0から1の間にしてください')
    if floor_df and math.isfinite(df):
        df = math.floor(df)
        if df < 1:
            raise ValueError('切捨て後の自由度が1未満です')
    z = NormalDist().inv_cdf((1+probability)/2)
    if math.isinf(df) or df >= 1e100:
        return z
    if df >= 1e7:
        return z+(z**3+z)/(4*df)+(5*z**5+16*z**3+3*z)/(96*df**2)
    with mp.workdps(32):
        nu = mp.mpf(str(df)); target = mp.mpf(str(probability))
        def covered(t):
            return mp.betainc(mp.mpf('.5'),nu/2,0,t*t/(nu+t*t),regularized=True)
        low = mp.mpf(0); high = mp.mpf(max(2.,z))
        while covered(high) < target:
            high *= 2
            if high > mp.mpf('1e12'):
                raise ValueError('指定した包含条件の係数を数値評価できません')
        for _ in range(65):
            mid = (low+high)/2
            if covered(mid) < target:low = mid
            else:high = mid
        return float((low+high)/2)


@lru_cache(maxsize=256)
def ea_coverage_factor(df):
    if math.isnan(df) or df <= 0:
        raise ValueError('有効自由度は正の数にしてください')
    if not math.isfinite(df) or df >= 1e100:
        return 2.0
    if df < 1:
        raise ValueError('EA表による評価には有効自由度1以上が必要です')
    nu = math.floor(df)
    if nu in EA_TABLE:
        return EA_TABLE[nu]
    # For gaps in the printed table, choose the next lower *listed* df.
    # This is conservative, not an interpolated t quantile. Keep it visible in the UI.
    return EA_TABLE[max(key for key in EA_TABLE if 0 < key <= nu)]


def coverage_description(settings):
    method = settings.get('method', 'legacy')
    description = tr_ui(METHODS[method])
    if method == 'ea':
        description += tr_ui('／表にない自由度は下側の掲載値を使用（保守的）')
    if method == 'student':
        description = f'{float(settings["probability"])*100:g}% '+tr_ui('t分布')
        description += tr_ui('・自由度切捨て') if settings.get('floor_df',False) else tr_ui('・自由度をそのまま使用')
    note = settings.get('note', '').strip()
    return description + ('：' + note if note else '')
