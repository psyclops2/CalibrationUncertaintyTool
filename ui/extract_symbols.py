import xml.etree.ElementTree as ET

xml_file_path = "symbols.xml"

# XMLのインデントを設定する関数
def indent(elem, level=0):
    i = "\n" + level * "  "
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "  "
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
        for elem in elem:
            indent(elem, level + 1)
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i


# 記号の整理
def update_xml(symbols_list, xml_file_path):
    try:
        # XMLファイルを解析し、ルート要素を取得
        tree = ET.parse(xml_file_path)
        root = tree.getroot()
        symbols_section = root.find("symbols")
        # symbolsセクションが存在しない場合、新たに作成
        if symbols_section is None:
            symbols_section = ET.SubElement(root, "symbols")
    except FileNotFoundError:
        # ファイルが存在しない場合、新たにデータとsymbolsセクションを作成
        root = ET.Element("data")
        tree = ET.ElementTree(root)
        symbols_section = ET.SubElement(root, "symbols")

    # 既存のシンボルを辞書に格納
    existing_symbols = {symbol.get("name"): symbol for symbol in symbols_section.findall("symbol")}
    
    # デバッグ出力：既存のシンボルリスト
    print("Existing symbols:", existing_symbols.keys())

    # デバッグ出力：新しいシンボルリスト
    print("New symbols list:", symbols_list)

    for symbol in symbols_list:
        symbol_name = str(symbol)
        if symbol_name not in existing_symbols:
            # 新しいシンボルを追加
            print(f"Adding new symbol: {symbol_name}")  # デバッグ出力
            symbol_element = ET.SubElement(symbols_section, "symbol", name=symbol_name)
            ET.SubElement(symbol_element, "unit").text = ""
            ET.SubElement(symbol_element, "definition").text = ""
            ET.SubElement(symbol_element, "derivative").text = ""
            #ET.SubElement(symbol_element, "type").text = ""
            #ET.SubElement(symbol_element, "distribution").text = ""
        else:
            # 既存のシンボルが存在する場合、内容を表示して何もしない
            symbol_element = existing_symbols[symbol_name]
            print(f"Symbol {symbol_name} already exists, no changes made.")  # デバッグ出力
            unit = symbol_element.find('unit').text if symbol_element.find('unit') is not None else ""
            definition = symbol_element.find('definition').text if symbol_element.find('definition') is not None else ""
            derivative = symbol_element.find('derivative').text if symbol_element.find('derivative') is not None else ""
            #_type = symbol_element.find('type').text if symbol_element.find('type') is not None else ""
            #distribution = symbol_element.find('distribution').text if symbol_element.find('distribution') is not None else ""
            #print(f"Existing symbol details: unit={unit}, definition={definition}, derivative={derivative}, type={_type}, distribution={distribution}")
            print(f"Existing symbol details: unit={unit}, definition={definition}, derivative={derivative}")

    # 新しいシンボルリストに含まれない既存のシンボルを削除
    existing_symbol_names = set(existing_symbols.keys())
    new_symbol_names = set(str(symbol) for symbol in symbols_list)

    for symbol_name in existing_symbol_names - new_symbol_names:
        symbol_element = existing_symbols[symbol_name]
        print(f"Removing symbol: {symbol_name}")  # デバッグ出力
        symbols_section.remove(symbol_element)

    # インデントを付けてXMLを書き込み
    indent(root)
    tree.write(xml_file_path, encoding='utf-8', xml_declaration=True)


# 記号をTreeViewに表示する関数
def extract_and_display_symbols(symbols_list, tree):
    tree.delete(*tree.get_children())
    for i, symbol in enumerate(symbols_list):
        sorting_no = i + 1
        tag = 'evenrow' if i % 2 == 0 else 'oddrow'
        tree.insert("", "end", text=str(sorting_no), values=(str(symbol), "", "", ""), tags=(tag,))

# TreeViewのデータを保存
def save_tree_to_xml(tree_widget, xml_file_path):
    try:
        tree = ET.parse(xml_file_path)
        root = tree.getroot()
        symbols = root.find("symbols")
        if symbols is None:
            symbols = ET.SubElement(root, "symbols")
    except FileNotFoundError:
        root = ET.Element("data")
        tree = ET.ElementTree(root)
        symbols = ET.SubElement(root, "symbols")

    existing_symbols = {symbol.get("name"): symbol for symbol in symbols.findall("symbol")}

    for item in tree_widget.get_children():
        values = tree_widget.item(item, "values")
        symbol_name = values[0]
        if symbol_name in existing_symbols:
            symbol_element = existing_symbols[symbol_name]
            symbol_element.find("unit").text = values[1] if values[1] else ""
            #symbol_element.find("definition").text = values[2] if values[2] else ""
            #symbol_element.find("derivative").text = values[3] if values[3] else ""
        else:
            symbol_element = ET.SubElement(symbols, "symbol", name=symbol_name)
            ET.SubElement(symbol_element, "unit").text = values[1] if values[1] else ""
            ET.SubElement(symbol_element, "definition").text = values[2] if values[2] else ""
            ET.SubElement(symbol_element, "derivative").text = values[3] if values[3] else ""
            #ET.SubElement(symbol_element, "type").text = ""
            #ET.SubElement(symbol_element, "distribution").text = ""

    indent(root)
    tree.write(xml_file_path, encoding='utf-8', xml_declaration=True)

# text_boxのデータを保存
def save_text_box_to_xml(text_box, tag):
    try:
        tree = ET.parse(xml_file_path)
        root = tree.getroot()
        equation = root.find("equation")
        if equation is None:
            equation = ET.SubElement(root, "equation")
    except FileNotFoundError:
        root = ET.Element("data")
        tree = ET.ElementTree(root)
        equation = ET.SubElement(root, "equation")

    element = equation.find(tag)
    if element is not None:
        element.text = text_box.get("1.0", "end-1c")
    else:
        text_box_element = ET.SubElement(equation, tag)
        text_box_element.text = text_box.get("1.0", "end-1c")

    indent(root)
    tree.write(xml_file_path, encoding='utf-8', xml_declaration=True)