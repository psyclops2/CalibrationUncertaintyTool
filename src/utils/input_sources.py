"""Linked statistical estimates and their common covariance / degrees of freedom."""
import math
import uuid
import json
from functools import lru_cache
import numpy as np
import sympy as sp
from .model_expression import parse_expression, variable_names
from .variable_utils import evaluate_type_a_value
from .value_references import ReferenceEvaluator, TOKEN
from .correlation_utils import build_correlation_matrix


def ensure_regression_ids(models):
    seen = set()
    for model in models.values():
        ident = model.get('id')
        if not ident:
            ident = uuid.uuid4().hex
            model['id'] = ident
        if ident in seen:
            raise ValueError('回帰モデルのIDが重複しています')
        seen.add(ident)


def number(raw):
    value = float(raw)
    if not math.isfinite(value):
        raise ValueError('有限の数値を入力してください')
    return value


class FixedReferences(ReferenceEvaluator):
    def resolve(self, address, point=None):
        if address.startswith('variable:'):
            name = self.names.get(address.split(':')[1])
            if self.variables.get(name, {}).get('type') != 'fixed':
                raise ValueError('評価するxには固定値を指定してください。不確かさを持つxの伝播は未対応です')
        return super().resolve(address, point)


def regression_packet(window, source, point):
    models = getattr(window, 'regressions', {})
    ensure_regression_ids(models)
    match = [(name, model) for name, model in models.items() if model['id'] == source['model_id']]
    if not match:
        raise ValueError('接続した回帰モデルが見つかりません')
    name, model = match[0]
    refs = getattr(window, 'value_references', None) or dict(variables={}, points=[], values={}, rules={})
    point_id = refs['points'][point] if point < len(refs['points']) else None
    evaluator=FixedReferences(refs,window.variable_values)
    text=TOKEN.sub(lambda match:'('+str(evaluator.resolve(match.group(1),point_id))+')',source.get('x_expression','0'))
    x_expr=parse_expression(text)
    if x_expr.free_symbols:
        raise ValueError('評価するxには固定の数値か、参照指定した固定量を使用してください')
    x = number(x_expr)
    expression=source.get('x_expression','').strip()
    if expression.startswith('@{variable:') and expression.endswith(':central_value:current}'):
        ident=expression[2:-1].split(':')[1]
        reference_name=next((name for name,value in refs['variables'].items() if value==ident),None)
        unit=window.variable_values.get(reference_name,{}).get('unit','').strip()
        if unit and model.get('x_unit','').strip() and unit!=model['x_unit'].strip():
            raise ValueError('固定量の単位と回帰のxの単位が一致しません。xの定義を確認してください')
    rows = model.get('data', [])
    if len(rows) < 3:
        raise ValueError('回帰には3組以上の有効なデータが必要です')
    if any(number(row.get('ux') or 0) != 0 for row in rows):
        raise ValueError('xに不確かさを持つ回帰は、この接続方法では未対応です')
    xs = np.array([number(row['x']) for row in rows])
    ys = np.array([number(row['y']) for row in rows])
    xm = float(np.mean(xs)); ym = float(np.mean(ys))
    sxx = float(np.sum((xs-xm)**2))
    if sxx <= 0:
        raise ValueError('回帰のxには異なる値が必要です')
    slope = float((xs-xm) @ (ys-ym) / sxx)
    intercept = ym-slope*xm
    df = len(xs)-2
    variance = float(np.sum((ys-(intercept+slope*xs))**2)/df)
    # Center the common parameter basis to avoid cancellation at large x offsets.
    covariance = variance*np.diag([1/len(xs),1/sxx])
    basis = np.array([1., x-xm])
    return dict(key=('regression', source['model_id']), mean=ym+slope*(x-xm), basis=basis,
                covariance=covariance, df=df, label=f'回帰「{name}」 / x={x:g} {model.get("x_unit", "")}',
                note='外挿です' if x < min(xs) or x > max(xs) else '', unit=model.get('y_unit',''))


def _evaluate_table_data(table):
    columns = table.get('columns', [])
    ids = [column['id'] for column in columns]
    if not ids or len(ids) != len(set(ids)) or any(not name.isidentifier() for name in ids):
        raise ValueError('測定表の列名は重複しない量名にしてください')
    definitions = {column['id']: column for column in columns}
    expressions = {name: parse_expression(column['expression']) for name,column in definitions.items() if column.get('expression','').strip()}
    values = []
    for index, row in enumerate(table.get('rows', [])):
        if type(row.get('excluded',False)) is not bool:
            raise ValueError('除外の指定は観測組ごとの真偽値にしてください')
        if row.get('excluded', False):
            continue
        cache = {}; active = set()
        def resolve(name):
            if name in cache:
                return cache[name]
            if name not in definitions:
                raise ValueError(f'派生列の参照先がありません: {name}')
            if name in active:
                raise ValueError('派生列の式が循環しています')
            active.add(name)
            if name in expressions:
                expr = expressions[name]
                result = number(expr.subs({symbol: resolve(str(symbol)) for symbol in expr.free_symbols}))
            else:
                try:
                    result = number(row.get(name, ''))
                except (TypeError, ValueError) as error:
                    raise ValueError(f'測定表 {index+1}行目 / {name}: 数値を入力するか観測組全体を除外してください') from error
            active.remove(name);cache[name] = result
            return result
        values.append([resolve(name) for name in ids])
    if len(values) < 2:
        raise ValueError('測定表には2組以上の有効な観測が必要です')
    data = np.array(values)
    covariance = np.atleast_2d(np.cov(data, rowvar=False, ddof=1))/len(data)
    return ids, np.mean(data,axis=0), covariance, len(data)-1, data


@lru_cache(maxsize=32)
def _cached_table(serialized):
    return _evaluate_table_data(json.loads(serialized))


def evaluate_table(table):
    ids,means,covariance,df,_ = _cached_table(json.dumps(table,sort_keys=True,default=str))
    return ids[:], means.copy(), covariance.copy(), df


def evaluate_table_rows(table):
    return _cached_table(json.dumps(table,sort_keys=True,default=str))[4].copy()


def source_packet(window, variable, point):
    info = window.variable_values[variable]
    value = info['values'][point]
    source = value.get('input_source')
    if not source:
        return None
    if info.get('type') != 'A':
        raise ValueError('統計的な入力元への接続はType Aの量で設定してください')
    if source['kind'] == 'regression':
        packet = regression_packet(window, source, point)
    elif source['kind'] == 'table':
        table = getattr(window, 'measurement_tables', {}).get(source['table_id'])
        if table is None:
            raise ValueError('接続した測定表が見つかりません')
        ids, means, covariance, df = evaluate_table(table)
        if source['column'] not in ids:
            raise ValueError('接続した測定表の列が見つかりません')
        index = ids.index(source['column'])
        packet = dict(key=('table',source['table_id']), mean=float(means[index]),
            basis=np.eye(len(ids))[index], covariance=covariance, df=df,
            label=f'測定表「{table.get("name", "")}」 / {source["column"]}の平均 / {df+1}組', note='',
            unit=table['columns'][index].get('unit',''))
    else:
        raise ValueError('未対応の入力元です')
    unit = info.get('unit','').strip()
    if unit and packet['unit'].strip() and unit != packet['unit'].strip():
        raise ValueError(f'入力元の単位 {packet["unit"]} と量の単位 {unit} が一致しません。数値は自動換算しません')
    packet['u'] = math.sqrt(max(0,float(packet['basis'] @ packet['covariance'] @ packet['basis'])))
    return packet


def statistical_state(window, names, point, handler):
    us = np.array([number(handler.get_standard_uncertainty(name) or 0) for name in names])
    correlation = build_correlation_matrix(names,getattr(window,'correlation_coefficients',{}))
    covariance = np.outer(us,us)*correlation
    packets = [source_packet(window,name,point) for name in names]
    group_ids = [packet['key'] if packet else ('direct',name) for name,packet in zip(names,packets)]
    for i, first in enumerate(packets):
        if first is None:continue
        for j, second in enumerate(packets):
            if second is not None and first['key']==second['key']:
                estimate = float(first['basis'] @ first['covariance'] @ second['basis'])
                if i!=j and correlation[i,j]!=0 and not math.isclose(covariance[i,j],estimate,abs_tol=1e-300,rel_tol=1e-8):
                    raise ValueError('入力元から計算した相関と手入力の相関が競合しています')
                covariance[i,j] = estimate
    if len(names) and np.min(np.linalg.eigvalsh(covariance / max(1e-300,float(np.max(np.diag(covariance)))))) < -1e-10:
        raise ValueError('入力元と手入力を合わせた共分散行列が半正定値ではありません')
    dfs = [packet['df'] if packet else handler.get_degrees_of_freedom(name) for name,packet in zip(names,packets)]
    return covariance, group_ids, dfs


def effective_df(covariance, gradient, groups, dfs):
    gradient = np.array(gradient,dtype=float)
    variance = float(gradient @ covariance @ gradient)
    if variance <= 0:return 1e100
    def normalize_df(value):
        if str(value).strip().lower() in ('inf','infinity','∞'):return math.inf
        try:return float(value)
        except (TypeError,ValueError):return math.nan
    dfs = [normalize_df(value) for value in dfs]
    active = [i for i,g in enumerate(gradient) if g!=0 and covariance[i,i]>0]
    # Cross-correlation of separately estimated blocks has no general WS df.
    for i in active:
        for j in active:
            if i!=j and groups[i]!=groups[j] and covariance[i,j]!=0 and (math.isfinite(dfs[i]) or math.isfinite(dfs[j])):
                return None
    denominator = 0.
    for group in set(groups):
        indices = [i for i in active if groups[i]==group]
        if not indices:continue
        df = dfs[indices[0]]
        if math.isnan(df) or df<=0:return None
        vec = gradient[indices]
        component = max(0.,float(vec @ covariance[np.ix_(indices,indices)] @ vec))
        denominator += component**2/df
    return variance**2/denominator if denominator>0 else 1e100
