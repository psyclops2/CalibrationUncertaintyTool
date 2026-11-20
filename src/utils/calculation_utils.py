import ast
import operator
import math
import traceback
import decimal
from decimal import Decimal, getcontext
from .config_loader import ConfigLoader
from .app_logger import log_error


def evaluate_formula(formula, variables=None):
    """
    計算式を評価して結果を返す

    Args:
        formula (str): 評価する計算式
        variables (dict): 変数名と値の辞書

    Returns:
        Decimal | None: 計算結果
    """
    try:
        if not formula:
            return None

        if variables is None:
            variables = {}

        config = ConfigLoader()
        precision = config.get_precision()
        getcontext().prec = precision

        # ^ を Python のべき乗演算子へ変換
        formula = formula.replace('^', '**')

        tree = ast.parse(formula, mode="eval")
        binary_ops = {
            ast.Add: operator.add, ast.Sub: operator.sub,
            ast.Mult: operator.mul, ast.Div: operator.truediv,
            ast.Pow: operator.pow, ast.Mod: operator.mod,
            ast.FloorDiv: operator.floordiv,
        }
        functions = {
            name: getattr(math, name) for name in (
                "sin", "cos", "tan", "asin", "acos", "atan", "atan2",
                "sinh", "cosh", "tanh", "exp", "log", "log10", "log2",
                "sqrt", "fabs", "floor", "ceil", "degrees", "radians",
            )
        }

        def evaluate(node):
            if isinstance(node, ast.Constant) and type(node.value) in (int, float):
                return Decimal(ast.get_source_segment(formula, node).replace("_", ""))
            if isinstance(node, ast.Name) and node.id in variables:
                return Decimal(str(variables[node.id]))
            if isinstance(node, ast.BinOp) and type(node.op) in binary_ops:
                return binary_ops[type(node.op)](evaluate(node.left), evaluate(node.right))
            if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
                value = evaluate(node.operand)
                return -value if isinstance(node.op, ast.USub) else value
            if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name):
                if node.value.id == "math" and node.attr in ("pi", "e", "tau"):
                    return Decimal(str(getattr(math, node.attr)))
            if isinstance(node, ast.Call) and not node.keywords:
                func = node.func
                if (isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name)
                        and func.value.id == "math" and func.attr in functions):
                    args = [evaluate(arg) for arg in node.args]
                    # sqrt can preserve Decimal precision; other math functions use float.
                    if func.attr == "sqrt" and len(args) == 1:
                        return args[0].sqrt()
                    return Decimal(str(functions[func.attr](*args)))
            raise ValueError("Unsupported formula expression")

        return evaluate(tree.body)

    except Exception as e:
        log_error(f"計算式の評価エラー: {str(e)}", details=traceback.format_exc())
        return None
