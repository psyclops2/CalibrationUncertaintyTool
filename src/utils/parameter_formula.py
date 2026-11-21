"""Named arguments compiled to the existing stable reference expression format."""
import ast
import re
from .value_references import TOKEN


FUNCTIONS = set('abs sin cos tan asin acos atan atan2 sinh cosh tanh exp log log10 log2 sqrt fabs floor ceil degrees radians'.split())


def mark_parameter_values(data):
    """Recognize private inputs saved before ownership was explicitly recorded."""
    for owner, rule in data['rules'].items():
        overrides = rule.get('override_setups', {})
        setups = [rule.get('parameter_setup', {})] + (list(overrides.values()) if isinstance(overrides, dict) else [])
        for setup in setups:
            if not isinstance(setup, dict) or not isinstance(setup.get('bindings', {}), dict): continue
            for binding in setup.get('bindings', {}).values():
                if not isinstance(binding, dict): continue
                ident = binding.get('manual_id')
                if ident in data['values'] and binding.get('address') == 'value:' + ident:
                    data['values'][ident].setdefault('parameter_owner', owner)


def prune_parameter_values(data, external=()):
    """Remove unreachable private inputs; intentionally registered values are roots."""
    mark_parameter_values(data)
    active_points = set(data['points'])
    for entry in list(data['values'].values()) + list(data['rules'].values()):
        for key in ('overrides', 'override_setups'):
            if isinstance(entry.get(key), dict):
                entry[key] = {p: value for p, value in entry[key].items() if p in active_points}
    def addresses(value):
        if isinstance(value, str):
            return {m[1].split(':')[1] for m in TOKEN.finditer(value) if m[1].startswith('value:')}
        if isinstance(value, dict):
            return set().union(*(addresses(v) for k, v in value.items() if k not in ('parameter_setup', 'override_setups')))
        if isinstance(value, (list, tuple)):
            return set().union(*(addresses(v) for v in value))
        return set()
    live = addresses(data['rules']) | addresses(external)
    live.update(ident for ident, entry in data['values'].items() if not entry.get('parameter_owner'))
    pending = list(live)
    while pending:
        entry = data['values'].get(pending.pop(), {})
        dependencies = addresses([entry.get('expression', ''), entry.get('overrides', {})]) - live
        live.update(dependencies); pending.extend(dependencies)
    removed = set(data['values']) - live
    for ident in removed: data['values'].pop(ident)
    return removed


def normalize_formula(text):
    return re.sub(r'(?<![\w.])(' + '|'.join(FUNCTIONS - {'abs'}) + r')\s*(?=\()', r'math.\1', text.strip()).replace('^', '**')


def argument_names(text):
    tree = ast.parse(normalize_formula(text), mode='eval')
    calls = {id(node.func) for node in ast.walk(tree) if isinstance(node, ast.Call)}
    names = {node.id for node in ast.walk(tree) if isinstance(node, ast.Name) and id(node) not in calls and node.id != 'math'}
    return sorted(names)


def compile_formula(text, bindings):
    names = argument_names(text)
    missing = set(names) - bindings.keys()
    if missing:
        raise ValueError(', '.join(sorted(missing)))
    # Protect generated addresses: replace original names in a single pass.
    return re.sub(r'\b[^\W\d]\w*\b', lambda m: '@{' + bindings[m[0]]['address'] + '}' if m[0] in names else m[0], normalize_formula(text))


def unpack_rule(rule):
    setup = rule.get('parameter_setup')
    if isinstance(setup, dict):
        try:
            bindings = setup['bindings']
            if (isinstance(bindings, dict) and all(isinstance(v, dict) and isinstance(v.get('address'), str) for v in bindings.values())
                    and compile_formula(setup['formula'], bindings) == rule['expression']):
                return setup['formula'], setup['bindings']
        except (KeyError, ValueError, SyntaxError, TypeError):
            pass
    bindings = {}
    addresses = {}
    def substitute(match):
        address = match[1]
        if address not in addresses:
            name = 'input_' + str(len(addresses) + 1)
            addresses[address] = name
            kind = 'variable' if address.startswith('variable:') and address.endswith(':central_value:current') else 'reference'
            bindings[name] = {'kind': kind, 'address': address}
        return addresses[address]
    return TOKEN.sub(substitute, rule.get('expression', '')), bindings
