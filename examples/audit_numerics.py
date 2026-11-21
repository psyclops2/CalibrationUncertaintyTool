"""Independent first-order audit of saved samples (no application calculation imports).

Uses mpmath at 60 digits, a separate AST evaluator, numerical derivatives,
and statistics recomputed from source observations. This checks the supplied
models; agreement does not establish that a model reproduces its publication.
"""
import ast
import configparser
import json
from pathlib import Path
import re
import zipfile

import mpmath as mp

BASE = Path(__file__).resolve().parent
mp.mp.dps = 60
TOKEN = re.compile(r'@\{([^{}]+)\}')


def expression(text, resolve):
    text = str(text).replace('^', '**').replace('math.', '')
    tree = ast.parse(text, mode='eval')
    def visit(node):
        if isinstance(node, ast.Constant):
            return mp.mpf(ast.get_source_segment(text, node))
        if isinstance(node, ast.Name):
            return resolve(node.id)
        if isinstance(node, ast.UnaryOp):
            x = visit(node.operand)
            return -x if isinstance(node.op, ast.USub) else x
        if isinstance(node, ast.BinOp):
            a, b = visit(node.left), visit(node.right)
            operations = {ast.Add: lambda: a+b, ast.Sub: lambda: a-b,
                          ast.Mult: lambda: a*b, ast.Div: lambda: a/b,
                          ast.Pow: lambda: a**b}
            return operations[type(node.op)]()
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            functions = dict(sin=mp.sin, cos=mp.cos, exp=mp.exp, sqrt=mp.sqrt, abs=abs)
            return functions[node.func.id](*(visit(arg) for arg in node.args))
        raise ValueError(ast.dump(node))
    return visit(tree.body)


def mean(values):
    return mp.fsum(values)/len(values)


def sample_covariance(rows):
    n = len(rows)
    means = [mean(list(col)) for col in zip(*rows)]
    covariance = mp.matrix(len(means))
    for i in range(len(means)):
        for j in range(len(means)):
            covariance[i, j] = mp.fsum((row[i]-means[i])*(row[j]-means[j]) for row in rows)/(n*(n-1))
    return means, covariance


def load(path):
    with zipfile.ZipFile(path) as archive:
        return json.loads(archive.read('project.json'))


def audit(project, recorded):
    infos = project['variable_values']
    names = [name for name, info in infos.items() if info['type'] != 'result']
    centers, uncertainties, dfs, groups = {}, {}, {}, {}
    tables = {}
    for ident, table in project.get('measurement_tables', {}).items():
        definitions = {c['id']: c for c in table['columns']}
        rows = []
        for row in table['rows']:
            if row.get('excluded'): continue
            def resolve(name):
                col = definitions[name]
                return expression(col['expression'], resolve) if col.get('expression') else mp.mpf(str(row[name]))
            rows.append([resolve(name) for name in definitions])
        means, cov = sample_covariance(rows)
        tables[ident] = list(definitions), means, cov, len(rows)-1

    for name in names:
        info = infos[name]; value = info['values'][0]
        source = value.get('input_source')
        groups[name] = ('direct', name)
        if source and source['kind'] == 'table':
            columns, means, covariance, df = tables[source['table_id']]
            index = columns.index(source['column'])
            centers[name] = means[index]
            uncertainties[name] = mp.sqrt(covariance[index, index])
            dfs[name] = mp.mpf(df); groups[name] = ('table', source['table_id'])
        elif source and source['kind'] == 'regression':
            model = next(m for m in project['regressions'].values() if m['id'] == source['model_id'])
            xs = [mp.mpf(row['x']) for row in model['data']]
            ys = [mp.mpf(row['y']) for row in model['data']]
            xm, ym = mean(xs), mean(ys)
            sxx = mp.fsum((x-xm)**2 for x in xs)
            slope = mp.fsum((x-xm)*(y-ym) for x,y in zip(xs,ys))/sxx
            residual = mp.fsum((y-ym-slope*(x-xm))**2 for x,y in zip(xs,ys))/(len(xs)-2)
            target = mp.mpf(source['x_expression'])
            centers[name] = ym+slope*(target-xm)
            uncertainties[name] = mp.sqrt(residual*(mp.mpf(1)/len(xs)+(target-xm)**2/sxx))
            dfs[name] = mp.mpf(len(xs)-2)
        elif info['type'] == 'A' and value.get('evaluation_mode', 'sample') in ('sample', 'pooled'):
            observations = [mp.mpf(x) for x in re.split(r'[,;\s]+', value['measurements'].strip()) if x]
            centers[name] = mean(observations)
            if value.get('evaluation_mode') == 'pooled':
                uncertainties[name] = mp.mpf(value['pooled_standard_deviation'])/mp.sqrt(len(observations))
                dfs[name] = mp.mpf(value['pooled_degrees_of_freedom'])
            else:
                uncertainties[name] = mp.sqrt(mp.fsum((x-centers[name])**2 for x in observations)/(len(observations)*(len(observations)-1)))
                dfs[name] = mp.mpf(len(observations)-1)
        else:
            centers[name] = mp.mpf(value['central_value'])
            uncertainties[name] = mp.mpf(value.get('standard_uncertainty', 0)) if info['type'] != 'fixed' else mp.mpf(0)
            dfs[name] = mp.mpf(value.get('degrees_of_freedom', 'inf'))

    refs = project.get('value_references') or {}
    def reference(address):
        parts = address.split(':')
        if parts[0] == 'value':
            return referenced_expression(refs['values'][parts[1]]['expression'])
        assert parts[0] == 'variable' and parts[2:] == ['central_value', 'current']
        return centers[next(name for name, ident in refs['variables'].items() if ident == parts[1])]
    def referenced_expression(text):
        substitutions = {}
        def replace(match):
            key = f'ref{len(substitutions)}'; substitutions[key] = reference(match[1]); return key
        return expression(TOKEN.sub(replace, text), substitutions.__getitem__)
    for name in names:
        if infos[name]['type'] == 'B':
            value = infos[name]['values'][0]
            ident = refs.get('variables', {}).get(name)
            rule = refs.get('rules', {}).get(ident)
            width = referenced_expression(rule['expression']) if rule else mp.mpf(value['half_width'])
            uncertainties[name] = width/mp.mpf(value.get('divisor', infos[name]['divisor']))

    cov = mp.matrix(len(names))
    for i, a in enumerate(names):
        for j, b in enumerate(names):
            rho = 1 if i == j else project.get('correlation_coefficients', {}).get(a, {}).get(b,
                project.get('correlation_coefficients', {}).get(b, {}).get(a, 0))
            cov[i,j] = uncertainties[a]*uncertainties[b]*mp.mpf(str(rho))
            if groups[a] == groups[b] and groups[a][0] == 'table':
                columns, _, table_cov, _ = tables[groups[a][1]]
                ca = infos[a]['values'][0]['input_source']['column']
                cb = infos[b]['values'][0]['input_source']['column']
                cov[i,j] = table_cov[columns.index(ca), columns.index(cb)]
    equations = dict(line.split('=',1) for line in project['last_equation'].splitlines() if line.strip())
    equations = {key.strip(): value.strip() for key, value in equations.items()}
    def result_value(result, inputs):
        def resolve(name):
            return inputs[name] if name in inputs else expression(equations[name], resolve)
        return resolve(result)
    results = {}
    for result, actual in recorded.items():
        gradient = []
        for name in names:
            def evaluate(x):
                return result_value(result, dict(centers, **{name:x}))
            gradient.append(mp.diff(evaluate, centers[name]))
        g = mp.matrix(gradient)
        variance = (g.T*cov*g)[0]
        # This auditor deliberately rejects df cases requiring a separate
        # cross-group covariance estimator; the current samples have none.
        for i, a in enumerate(names):
            for j, b in enumerate(names):
                if groups[a] != groups[b] and gradient[i]*gradient[j]*cov[i,j] != 0:
                    assert mp.isinf(dfs[a]) and mp.isinf(dfs[b]), 'cross-group finite-df correlation needs its own oracle'
        denominator = mp.mpf(0)
        for group in set(groups.values()):
            indices = [i for i,name in enumerate(names) if groups[name] == group]
            component = mp.fsum(g[i]*cov[i,j]*g[j] for i in indices for j in indices)
            denominator += component**2/dfs[names[indices[0]]]
        df = variance**2/denominator if denominator else mp.inf
        expected = dict(result_central_value=result_value(result, centers),
                        result_standard_uncertainty=mp.sqrt(variance), effective_df=df)
        settings = infos[result]['values'][0].get('coverage', {'method':'legacy'})
        method = settings['method']; k = mp.mpf(str(actual['coverage_factor']))
        if method == 'student':
            nu = mp.floor(df) if settings.get('floor_df') else df
            # Integrate the density directly, independently of the Tool's
            # incomplete-beta inverse implementation.
            density = lambda x: mp.gamma((nu+1)/2)/(mp.sqrt(nu*mp.pi)*mp.gamma(nu/2))*(1+x*x/nu)**(-(nu+1)/2)
            probability = mp.quad(density, [-k, 0, k])
            assert abs(probability-mp.mpf(str(settings['probability']))) < mp.mpf('1e-12')
        elif method == 'manual':
            assert k == mp.mpf(settings['k'])
        elif method == 'ea':
            assert mp.floor(df) == 10 and k == mp.mpf('2.28'), 'add an independent printed EA row if new samples are added'
        elif method == 'legacy':
            if df >= 10:
                assert k == 2
            else:
                config = configparser.ConfigParser(); config.read(BASE.parent/'config.ini', encoding='utf-8')
                integer_df = int(mp.nint(df))
                assert abs(df-integer_df) < mp.mpf('1e-50'), 'add independent interpolation if needed'
                assert k == mp.mpf(config['TValues'][str(integer_df)])
        else:
            raise ValueError(f'Coverage method needs an independent oracle: {method}')
        expected['expanded_uncertainty'] = mp.sqrt(variance)*k
        for key, value in expected.items():
            tool = actual[key]
            if key == 'effective_df' and mp.isinf(value):
                assert tool >= 1e99, (result, key, tool)
            else:
                assert tool is not None and abs(mp.mpf(str(tool))-value) <= max(mp.mpf('1e-25'),abs(value)*mp.mpf('2e-10')), (result, key, tool, str(value))
        results[result] = {key: str(value) for key,value in expected.items()}
        results[result]['coverage_factor'] = str(k)
    return results


def main():
    records = []
    for area in ('ea402', 'gum', 'euramet19'):
        verification = json.loads((BASE/area/'reports/verification.json').read_text(encoding='utf-8'))
        for record in verification:
            key = record.get('key', record.get('case'))
            project = load(BASE/area/'projects'/f'{key}.cutp')
            results = record.get('results') or {'V20': record['tool']}
            independent = audit(project, results)
            records.append(dict(area=area, model=key, independent=independent))
            print(area, key, 'OK', flush=True)
    (BASE/'numerical-audit.json').write_text(json.dumps(records, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')


if __name__ == '__main__':
    main()
