"""Shared, restricted mathematical syntax for measurement models."""
import ast
import operator
import io
import keyword
import tokenize
import sympy as sp
from .equation_normalizer import normalize_equation_text

FUNCTIONS = {name: getattr(sp, name) for name in (
    'sin', 'cos', 'tan', 'asin', 'acos', 'atan', 'sinh', 'cosh', 'tanh',
    'exp', 'log', 'sqrt', 'atan2')}
FUNCTIONS.update(ln=sp.log, abs=sp.Abs, Abs=sp.Abs)
CONSTANTS = {'pi': sp.pi}
OPERATORS = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
             ast.Div: operator.truediv, ast.Pow: operator.pow}


def split_equations(text):
    parts = []
    start = depth = 0
    text = normalize_equation_text(text or '')
    for index, char in enumerate(text):
        if char == '(':
            depth += 1
        elif char == ')':
            depth -= 1
        elif char in ',;\r\n' and depth == 0:
            if text[start:index].strip():
                parts.append(text[start:index].strip())
            start = index + 1
    if text[start:].strip():
        parts.append(text[start:].strip())
    return parts


def parse_expression(text, symbols=None):
    text = normalize_equation_text(text or '').strip().replace('^', '**')
    try:
        # Python normalises identifiers with NFKC (e.g. ϑ→θ, ϕ→φ).
        # Alias tokens before AST parsing so distinct metrological quantities stay distinct.
        names = {}
        aliases = {}
        tokens = []
        for token in tokenize.generate_tokens(io.StringIO(text).readline):
            if token.type == tokenize.NAME and not keyword.iskeyword(token.string):
                alias = aliases.setdefault(token.string, f'_quantity_{len(aliases)}')
                names[alias] = token.string
                token = token._replace(string=alias)
            tokens.append(token)
        text = tokenize.untokenize(tokens)
        tree = ast.parse(text, mode='eval')
    except (SyntaxError, tokenize.TokenError) as error:
        raise ValueError('数式の構文を確認してください') from error
    symbols = dict(symbols or {})

    def convert(node):
        if isinstance(node, ast.Constant) and type(node.value) in (int, float):
            return sp.Float(ast.get_source_segment(text, node), 28)
        if isinstance(node, ast.Name):
            name = names.get(node.id,node.id)
            return symbols.get(name, CONSTANTS.get(name, sp.Symbol(name, real=True)))
        if isinstance(node, ast.BinOp) and type(node.op) in OPERATORS:
            return OPERATORS[type(node.op)](convert(node.left), convert(node.right))
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
            value = convert(node.operand)
            return -value if isinstance(node.op, ast.USub) else value
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and not node.keywords:
            name = names.get(node.func.id,node.func.id)
            if name not in FUNCTIONS:
                raise ValueError(f'未対応の数学関数です: {name}')
            try:
                return FUNCTIONS[name](*(convert(arg) for arg in node.args))
            except (TypeError, ValueError) as error:
                raise ValueError(f'{name}の引数を確認してください: {error}') from error
        raise ValueError('数式には数値・量名・四則演算・登録済み数学関数を使用してください')

    return convert(tree.body)


def variable_names(text):
    expression = parse_expression(text)
    return sorted(str(symbol) for symbol in expression.free_symbols)
