"""Normalize generated samples to named formula arguments and constant references."""
import keyword
import re
from src.utils.value_references import TOKEN, is_constant_reference
from src.utils.parameter_formula import compile_formula, FUNCTIONS


def current_format(project):
    refs = project.get('value_references')
    if not refs:
        return project
    names = {ident: name for name, ident in refs['variables'].items()}
    for rule in refs['rules'].values():
        if rule.get('parameter_setup'):
            setup = rule['parameter_setup']
            compiled = compile_formula(setup['formula'], setup['bindings'])
            assert compiled == rule['expression'].replace('^', '**')
            rule['expression'] = compiled
            continue
        bindings = {}
        addresses = {}
        def replace(match):
            address = match[1]
            if address not in addresses:
                parts = address.split(':')
                base = names.get(parts[1], parts[1])
                base = re.sub(r'\W', '_', base)
                if not base.isidentifier() or keyword.iskeyword(base) or base in FUNCTIONS or base == 'math':
                    base = 'value_' + base
                name = base; index = 2
                while name in bindings:
                    name = base + '_' + str(index); index += 1
                addresses[address] = name
                bindings[name] = dict(kind='variable' if parts[0] == 'variable' and parts[-1] == 'current' else 'reference', address=address)
            return addresses[address]
        formula = TOKEN.sub(replace, rule['expression'])
        assert compile_formula(formula, bindings) == rule['expression'].replace('^', '**')
        rule['expression'] = compile_formula(formula, bindings)
        rule['parameter_setup'] = dict(formula=formula, bindings=bindings)
    # Sample generators own this catalogue. Remove declarations no longer used by
    # any expression, following transitive dependencies rather than list order.
    def dependencies(value):
        if isinstance(value, str):
            return {m[1].split(':')[1] for m in TOKEN.finditer(value) if m[1].startswith('value:')}
        if isinstance(value, dict): return set().union(*(dependencies(v) for v in value.values()))
        if isinstance(value, list): return set().union(*(dependencies(v) for v in value))
        return set()
    live = dependencies(refs['rules']) | dependencies(project.get('regressions', {})) | dependencies(project.get('measurement_tables', {}))
    pending = list(live)
    while pending:
        entry = refs['values'].get(pending.pop(), {})
        extra = dependencies(entry) - live
        live.update(extra); pending.extend(extra)
    refs['values'] = {ident: entry for ident, entry in refs['values'].items() if ident in live}
    assert all(entry.get('parameter_owner') or is_constant_reference(refs, ident) for ident, entry in refs['values'].items())
    for info in project['variable_values'].values():
        for value in info['values']:
            if not value.get('calculation_formula'): value.pop('calculation_formula', None)
    return project
