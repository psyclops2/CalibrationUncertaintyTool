"""Stable data addresses and point-aware numeric expressions, independent of Qt."""
import re
import uuid
from decimal import Decimal, localcontext
from .calculation_utils import evaluate_formula
from .config_loader import ConfigLoader

TOKEN = re.compile(r"@\{([^{}]+)\}")


def is_constant_reference(data, ident, active=None):
    """Classify global constants structurally; evaluation still validates numbers/cycles."""
    active = set() if active is None else active
    if ident in active: return True
    entry = data['values'].get(ident)
    if entry is None: return True  # Keep broken global expressions editable.
    if entry.get('parameter_owner') or entry.get('scope', 'common') != 'common': return False
    active = active | {ident}
    for match in TOKEN.finditer(entry.get('expression', '')):
        parts = match[1].split(':')
        if len(parts) != 2 or parts[0] != 'value' or not is_constant_reference(data, parts[1], active): return False
    return True


def new_id():
    return uuid.uuid4().hex


def enable_references(window):
    if window.value_references is None:
        window.value_references = {"version": 1, "variables": {}, "points": [], "values": {}, "rules": {}}
    data = window.value_references
    for name in window.variables:
        data["variables"].setdefault(name, new_id())
    while len(data["points"]) < len(window.value_names):
        data["points"].append(new_id())
    return data


def validate_references(data, point_count):
    if data is None:
        return
    if not isinstance(data, dict) or data.get("version") != 1:
        raise ValueError("Unsupported value reference version")
    for key in ("variables", "values", "rules"):
        if not isinstance(data.get(key), dict):
            raise ValueError(f"value_references.{key}: expected object")
    ids = list(data["variables"].values())
    points = data.get("points")
    if not isinstance(points, list) or len(points) != point_count:
        raise ValueError("Reference point IDs do not match calibration points")
    for group in (ids, points, list(data["values"])):
        if any(not isinstance(x, str) or not re.fullmatch(r"[A-Za-z0-9_-]+", x) for x in group) or len(set(group)) != len(group):
            raise ValueError("Invalid or duplicate reference IDs")
    for entry in data["values"].values():
        if not isinstance(entry, dict) or not isinstance(entry.get("name"), str) or not isinstance(entry.get("expression"), str):
            raise ValueError("Invalid reference value")
        if any(not isinstance(entry.get(field, ''), str) for field in ('unit', 'description')):
            raise ValueError("Invalid reference metadata")
        if entry.get("scope", "common") not in ("common", "point"):
            raise ValueError("Invalid reference scope")
        if not isinstance(entry.get("overrides", {}), dict) or any(not isinstance(v, str) for v in entry.get("overrides", {}).values()):
            raise ValueError("Invalid point override")
    for rule in data["rules"].values():
        if not isinstance(rule, dict) or not isinstance(rule.get("expression"), str):
            raise ValueError("Invalid half-width expression")
        if not isinstance(rule.get("overrides", {}), dict) or any(not isinstance(v, str) for v in rule.get("overrides", {}).values()):
            raise ValueError("Invalid half-width override")


class ReferenceEvaluator:
    def __init__(self, definitions, variables, window=None):
        self.window = window
        self.data = definitions
        self.variables = variables
        self.names = {ident: name for name, ident in definitions["variables"].items()}
        self.cache = {}
        self.active = set()

    def resolve(self, address, point=None):
        key = (address, point)
        if key in self.active:
            raise ValueError(f"循環参照: {address}")
        if key in self.cache:
            return self.cache[key]
        self.active.add(key)
        try:
            parts = address.split(":")
            if parts[0] == "value" and len(parts) in (2, 3):
                entry = self.data["values"].get(parts[1])
                if entry is None:
                    raise ValueError(f"参照先がありません: {address}")
                requested_point = parts[2] if len(parts) == 3 else point
                context = requested_point if entry.get("scope", "common") == "point" else None
                if entry.get("scope", "common") == "point" and context not in self.data['points']:
                    raise ValueError(f"校正点を指定してください: {address}")
                expression = entry.get("overrides", {}).get(context, entry["expression"])
                result = self.expression(expression, context)
            elif parts[0] == "variable" and len(parts) == 4 and parts[2] == "central_value":
                name = self.names.get(parts[1])
                if name not in self.variables or self.variables[name].get("type") == "result":
                    raise ValueError(f"入力変数の参照先がありません: {address}")
                target = point if parts[3] == "current" else parts[3]
                if target is None or target not in self.data["points"]:
                    raise ValueError(f"校正点を指定してください: {address}")
                index = self.data["points"].index(target)
                value = self.variables[name].get("values", [])[index]
                if value.get('input_source') and self.window is not None:
                    from .input_sources import source_packet
                    value = dict(central_value=source_packet(self.window,name,index)['mean'])
                elif self.variables[name].get('type') == 'A' and 'evaluation_mode' in value:
                    from .variable_utils import evaluate_type_a_value
                    value = evaluate_type_a_value(value)
                raw = value.get("central_value", "")
                result = self.number(raw)
            else:
                raise ValueError(f"未対応のアドレス: {address}")
            self.cache[key] = result
            return result
        finally:
            self.active.remove(key)

    @staticmethod
    def number(raw):
        if raw in (None, ""):
            raise ValueError("参照値が未入力です")
        value = Decimal(str(raw))
        if not value.is_finite():
            raise ValueError("参照値は有限な数値にしてください")
        return value

    def expression(self, expression, point=None):
        variables = {}
        def replace(match):
            key = f"ref_{len(variables)}"
            variables[key] = self.resolve(match.group(1), point)
            return key
        expanded = TOKEN.sub(replace, expression)
        result = evaluate_formula(expanded, variables)
        if result is None:
            raise ValueError("数式を評価できません。式と参照先を確認してください")
        return self.number(result)


def evaluate_half_widths(definitions, variables, window=None):
    evaluator = ReferenceEvaluator(definitions, variables, window)
    results = {}
    names = evaluator.names
    with localcontext() as context:
        context.prec = ConfigLoader().get_precision()
        for ident, rule in definitions["rules"].items():
            name = names.get(ident)
            for index, point in enumerate(definitions["points"]):
                try:
                    if name not in variables or variables[name].get("type") != "B":
                        raise ValueError("参照式の対象はType Bである必要があります")
                    expression = rule.get("overrides", {}).get(point, rule["expression"])
                    width = evaluator.expression(expression, point)
                    if width < 0:
                        raise ValueError("半値幅は0以上にしてください")
                    info = variables[name]
                    divisor = evaluator.number(info["values"][index].get("divisor") or info.get("divisor", ""))
                    if divisor <= 0:
                        raise ValueError("除数は0より大きくしてください")
                    results[(name, index)] = {"value": width, "uncertainty": width / divisor, "error": ""}
                except Exception as error:
                    results[(name or ident, index)] = {"value": None, "uncertainty": None, "error": str(error)}
    return results
