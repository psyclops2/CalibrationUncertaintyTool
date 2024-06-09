import tkinter as tk
import xml.etree.ElementTree as ET

xml_file_path = "symbols.xml"

current_entry = None

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

def on_cell_double_click(event, tree):
    global current_entry
    if current_entry is not None:
        current_entry.destroy()
        current_entry = None

    item = tree.selection()[0]
    column = tree.identify_column(event.x)
    column_index = int(column.strip('#'))  # TreeViewの列番号を取得

    if column_index <= 0:
        return

    row_id = tree.identify_row(event.y)
    x, y, width, height = tree.bbox(row_id, column)

    current_values = list(tree.item(item, 'values'))
    while len(current_values) < column_index:
        current_values.append('')

    entry = tk.Entry(tree)
    entry.insert(0, current_values[column_index - 1])  # 正しいインデックスにアクセス
    entry.place(x=x, y=y, width=width, height=height)

    def on_entry_confirm(event):
        current_values[column_index - 1] = entry.get()  # 正しいインデックスに更新
        tree.item(item, values=current_values)
        symbol_name = current_values[0]  # シンボル名はTreeViewの1番目のカラムに設定されていると仮定
        update_xml_entry(symbol_name, current_values)
        entry.destroy()

    entry.bind('<Return>', on_entry_confirm)
    entry.bind('<FocusOut>', on_entry_confirm)
    entry.focus()
    current_entry = entry

def update_xml_entry(symbol_name, values):
    try:
        tree_xml = ET.parse(xml_file_path)
        root = tree_xml.getroot()

        symbol_found = False
        for symbol_element in root.findall(".//symbol[@name='" + symbol_name + "']"):
            symbol_found = True
            tags = ["unit", "definition", "type", "distribution", "derivative"]
            for i, tag in enumerate(tags, start=1):  # start from 1 to skip the symbol name
                element = symbol_element.find(tag)
                if element is not None:
                    element.text = values[i] if len(values) > i else ""
                else:
                    # If element is not found, create it
                    new_elem = ET.SubElement(symbol_element, tag)
                    new_elem.text = values[i] if len(values) > i else ""

        if not symbol_found:
            print(f"Symbol '{symbol_name}' not found in XML. No updates made.")
            return

        indent(root)  # インデント関数を呼び出してXMLを整形
        tree_xml.write(xml_file_path, encoding='utf-8', xml_declaration=True)
        print("XML file updated successfully.")
    except Exception as e:
        print("Failed to update XML file:")
