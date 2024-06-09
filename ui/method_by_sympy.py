from sympy import symbols, Eq, solve, sympify, diff
import xml.etree.ElementTree as ET

def indent(elem, level=0):
    i = "\n" + level * "  "
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "  "
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
        for child in elem:
            indent(child, level + 1)
        if not child.tail or not child.tail.strip():
            child.tail = i
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i

# 1. 方程式を統合
def integrate_equations(input_text):
    equations = []
    for line in input_text.strip().split('\n'):
        lhs, rhs = line.split('=')
        eq = Eq(sympify(lhs.strip()), sympify(rhs.strip()))
        equations.append(eq)
    
    def unify_equations(eqs):
        if len(eqs) == 1:
            return eqs[0]
        eq1 = eqs.pop(0)
        eq2 = eqs.pop(0)
        unified_eq = eq1.subs(eq2.lhs, solve(eq2, eq2.lhs)[0])
        eqs.insert(0, unified_eq)
        return unify_equations(eqs)
    
    unified_eq = unify_equations(equations)
    return unified_eq

# 2. 記号を抽出
def extract_symbols(text):
    symbols_list = []
    processed_symbols = set()

    try:
        for line in text.strip().split('\n'):
            if '=' not in line:  # '='が含まれていない行をスキップ
                continue
            lhs, rhs = line.split('=')
            lhs_expr = sympify(lhs.strip())
            if lhs_expr.is_Symbol and lhs_expr not in processed_symbols:
                processed_symbols.add(lhs_expr)
                symbols_list.append(lhs_expr)

            rhs_expr = sympify(rhs.strip())
            for symbol in sorted(rhs_expr.free_symbols, key=lambda x: str(x)):
                if symbol not in processed_symbols:
                    processed_symbols.add(symbol)
                    symbols_list.append(symbol)
    except Exception as e:
        print(f"Error processing the expression: {e}")

    return symbols_list

# 3. 偏微分を計算し更新
def calculate_and_update_derivatives(tree, unified_eq, xml_file_path):
    lhs, rhs = unified_eq.lhs, unified_eq.rhs
    symbols = rhs.free_symbols

    try:
        tree_xml = ET.parse(xml_file_path)
        root = tree_xml.getroot()
    except ET.ParseError:
        print("XML parsing error.")
        return
    except FileNotFoundError:
        print("XML file not found.")
        return

    for child in tree.get_children():
        current_values = list(tree.item(child, 'values'))
        symbol_name = current_values[0] if len(current_values) > 0 else None
        try:
            symbol_obj = symbols.intersection({sympify(symbol_name)}).pop() if sympify(symbol_name) in symbols else None
        except (SyntaxError, ValueError):
            print(f"Error processing symbol: {symbol_name}")
            continue
        
        if symbol_obj:
            derivative = diff(rhs, symbol_obj)
            # Update TreeView
            while len(current_values) < 4:
                current_values.append('')
            current_values[3] = str(derivative)
            tree.item(child, values=current_values)
            
            # Update XML file
            for symbol_element in root.findall(f".//symbol[@name='{symbol_name}']"):
                derivative_elem = symbol_element.find('derivative')
                if derivative_elem is None:
                    derivative_elem = ET.SubElement(symbol_element, 'derivative')
                derivative_elem.text = str(derivative)
    
    # Format and save XML
    indent(root)
    tree_xml.write(xml_file_path, encoding='utf-8', xml_declaration=True)
