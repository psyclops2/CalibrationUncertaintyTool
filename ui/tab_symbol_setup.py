import tkinter as tk
from tkinter import ttk, scrolledtext
import xml.etree.ElementTree as ET

def create_symbol_tab(tab, symbol_name, symbol_element, tree, xml_file_path):
    # タブの内容をクリア
    for widget in tab.winfo_children():
        widget.destroy()

    # Typeの値を事前に読み取る
    type_element = symbol_element.find("type")
    type_value = type_element.text if type_element is not None else "Type A"  # デフォルト値として'Type A'

    fields = [
        ("Type:", "type"),
        ("Number of Observations:", "number_of_observations"),
        ("Degrees of Freedom:", "degrees_of_freedom"),
        ("Distribution:", "distribution"),
        ("Value:", "value"),
        ("Expanded Uncertainty:", "expanded_uncertainty"),
        ("Coverage Factor:", "coverage_factor"),
    ]

    tab.grid_columnconfigure(0, weight=0)
    tab.grid_columnconfigure(1, weight=1)
    tab.grid_columnconfigure(2, weight=1)

    related_widgets = {}
    for i, (label_text, tag) in enumerate(fields):
        # Type Bの場合は特定のラベルを変更する
        if tag == "expanded_uncertainty" and type_value == "Type B":
            label_text = "Half Width Limit:"
        if tag == "number_of_observations" and type_value == "Type B":
            continue  # Type Bの場合はNumber of Observationsをスキップ
        # Calibration Valueの場合、Type以外は生成しない
        if type_value == "Calibration Value" and tag != "type":
            continue
        
        label = tk.Label(tab, text=label_text)
        label.grid(row=i, column=0, padx=5, pady=5, sticky="e")

        element = symbol_element.find(tag)
        value = element.text if element is not None and element.text is not None else ""

        if tag in ["type", "distribution"]:
            options = ["Calibration Value","Type A", "Type B"] if tag == "type" else ["Normal", "Rectangular", "Triangular", "U-shape"]
            combobox = ttk.Combobox(tab, values=options)
            combobox.grid(row=i, column=1, padx=(0, 5), pady=5, sticky="ew")
            if value:
                combobox.set(value)
            related_widgets[tag] = combobox
            combobox.bind("<<ComboboxSelected>>", lambda e, combobox=combobox, tag=tag: on_widget_change(combobox, tag, symbol_element, tree, xml_file_path, tab, symbol_name))
        else:
            entry = tk.Entry(tab)
            entry.grid(row=i, column=1, padx=(0, 5), pady=5, sticky="ew")
            entry.insert(0, value)
            related_widgets[tag] = entry
            entry.bind("<FocusOut>", lambda e, entry=entry, tag=tag: on_widget_change(entry, tag, symbol_element, tree, xml_file_path, tab, symbol_name))

        if tag in ["value", "expanded_uncertainty"]:
            unit = symbol_element.find("unit").text if symbol_element.find("unit") is not None else ""
            unit_label = tk.Label(tab, text=unit)
            unit_label.grid(row=i, column=2, padx=(5, 0), pady=5, sticky="w")

    desc_image_notebook = ttk.Notebook(tab)
    desc_image_notebook.grid(row=len(fields), column=0, columnspan=3, padx=5, pady=5, sticky="ew")
    description_tab = ttk.Frame(desc_image_notebook)
    desc_image_notebook.add(description_tab, text="Description")
    description_text = scrolledtext.ScrolledText(description_tab, wrap=tk.WORD)
    description_text.pack(expand=True, fill='both')
    description_text.insert(tk.END, symbol_element.find("description").text if symbol_element.find("description") is not None else "")

    picture_tab = ttk.Frame(desc_image_notebook)
    desc_image_notebook.add(picture_tab, text="Picture")
    picture_label = tk.Label(picture_tab, text="No picture available")
    picture_label.pack(padx=10, pady=10)

def on_widget_change(widget, tag, symbol_element, tree, xml_file_path, tab,symbol_name):
    new_value = widget.get()  # コンボボックスから新しい値を取得
    element = symbol_element.find(tag)
    if element is None:
        element = ET.SubElement(symbol_element, tag)
    element.text = new_value  # XML要素のテキストを更新

    # type が Type A に変更された場合、distribution を Normal に設定
    if tag == "type" and new_value == "Type A":
        distribution_element = symbol_element.find('distribution')
        if distribution_element is None:
            distribution_element = ET.SubElement(symbol_element, 'distribution')
        distribution_element.text = "Normal"  # distribution を Normal に設定
        tree.write(xml_file_path, encoding='utf-8', xml_declaration=True)  # XML ファイルに保存

    if tag == "type" and new_value == "Type B":
        degrees_of_freedom_element = symbol_element.find('degrees_of_freedom')
        if degrees_of_freedom_element is None:
            degrees_of_freedom_element = ET.SubElement(symbol_element, 'degrees_of_freedom')
        degrees_of_freedom_element.text = "inf"  # degrees_of_freedom を inf に設定
        tree.write(xml_file_path, encoding='utf-8', xml_declaration=True)  # XML ファイルに保存

    if tag == "distribution" and new_value == "Normal":
        coverage_factor_element = symbol_element.find('coverage_factor')
        if coverage_factor_element is None:
            coverage_factor_element = ET.SubElement(symbol_element, 'coverage_factor')
        coverage_factor_element.text = "1"  # coverage_factor を inf に設定
        tree.write(xml_file_path, encoding='utf-8', xml_declaration=True)  # XML ファイルに保存

    if tag == "distribution" and new_value == "Rectangular":
        coverage_factor_element = symbol_element.find('coverage_factor')
        if coverage_factor_element is None:
            coverage_factor_element = ET.SubElement(symbol_element, 'coverage_factor')
        coverage_factor_element.text = "sqrt(3)"  # coverage_factor を inf に設定
        tree.write(xml_file_path, encoding='utf-8', xml_declaration=True)  # XML ファイルに保存

    if tag == "distribution" and new_value == "Triangular":
        coverage_factor_element = symbol_element.find('coverage_factor')
        if coverage_factor_element is None:
            coverage_factor_element = ET.SubElement(symbol_element, 'coverage_factor')
        coverage_factor_element.text = "sqrt(6)"  # coverage_factor を inf に設定
        tree.write(xml_file_path, encoding='utf-8', xml_declaration=True)  # XML ファイルに保存

    if tag == "distribution" and new_value == "U-shape":
        coverage_factor_element = symbol_element.find('coverage_factor')
        if coverage_factor_element is None:
            coverage_factor_element = ET.SubElement(symbol_element, 'coverage_factor')
        coverage_factor_element.text = "sqrt(2)"  # coverage_factor を inf に設定
        tree.write(xml_file_path, encoding='utf-8', xml_declaration=True)  # XML ファイルに保存

    save_xml(tree, xml_file_path)  # すべての変更を保存
    reload_tab_content(tab, symbol_name, symbol_element, tree, xml_file_path)  # タブの内容を再読込

def reload_tab_content(tab, symbol_name, symbol_element, tree, xml_file_path):
    create_symbol_tab(tab, symbol_name, symbol_element, tree, xml_file_path)

def save_xml(tree, xml_file_path):
    root = tree.getroot()
    indent(root)
    tree.write(xml_file_path, encoding='utf-8', xml_declaration=True)
    print(f"XML saved to {xml_file_path}")

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