import tkinter as tk
import xml.etree.ElementTree as ET
from tkinter import ttk, scrolledtext
from ui.replace_tree import on_cell_double_click
from ui.extract_symbols import save_text_box_to_xml,update_xml
from ui.method_by_sympy import integrate_equations, extract_symbols, calculate_and_update_derivatives

def load_xml_to_form0(text_box1, text_box2, tree, xml_file_path):
    try:
        # XMLファイルを読み込みます
        tree_xml = ET.parse(xml_file_path)
        root = tree_xml.getroot()
    except FileNotFoundError:
        print("Warning: XML file not found. Loading with default values.")
        # デフォルトのテキストを設定
        text_box1.insert('end', "No equation available")
        text_box2.insert('end', "No integrated equation available")
        return  # ここで処理を終了し、ファイルがない場合には何も表示しない

    # Model Equationsをテキストボックスに表示
    model_equations = root.find('.//model_equations').text
    integrated_equation = root.find('.//integrated_equation').text
    text_box1.delete('1.0', 'end')  # 既存のテキストをクリア
    text_box1.insert('end', model_equations)
    text_box2.delete('1.0', 'end')  # 既存のテキストをクリア
    text_box2.insert('end', integrated_equation)

    # ツリービューにシンボルのデータを表示
    tree.delete(*tree.get_children())  # 既存のアイテムをクリア
    symbols = root.findall('.//symbol')
    for idx, symbol in enumerate(symbols):
        symbol_name = symbol.get('name')
        unit = symbol.find('unit').text or ""
        definition = symbol.find('definition').text or ""
        derivative = symbol.find('derivative').text or ""
        tree.insert("", "end", iid=idx, text=str(idx + 1), values=(symbol_name, unit, definition, derivative), tags=('oddrow' if idx % 2 == 0 else 'evenrow'))

def setup_tab1(tab):
    xml_file_path = "symbols.xml"
    
    label = tk.Label(tab, text="Model Equations", font=("", 10, "bold"))
    label.grid(row=0, column=0, padx=5, pady=0, sticky="w")
    
    text_box1 = scrolledtext.ScrolledText(tab, width=40, height=3)
    text_box1.grid(row=1, column=0, padx=5, pady=5, sticky="ew")
    
    text_box2 = scrolledtext.ScrolledText(tab, width=40, height=2)
    text_box2.grid(row=3, column=0, padx=5, pady=5, sticky="ew")
    
    tree = ttk.Treeview(tab, columns=("Symbol", "Unit", "Definition", "Derivative"))
    tree.heading("#0", text="Sorting No", anchor=tk.W)
    tree.heading("Symbol", text="Symbol", anchor=tk.W)
    tree.heading("Unit", text="Unit", anchor=tk.W)
    tree.heading("Definition", text="Definition", anchor=tk.W)
    tree.heading("Derivative", text="derivative", anchor=tk.W)
    tree.column("#0", width=70, stretch=tk.NO)
    tree.column("Symbol", width=70, stretch=tk.NO)
    tree.column("Unit", width=50, stretch=tk.NO)
    tree.column("Definition", width=350, stretch=tk.NO)
    tree.column("Derivative", width=150, stretch=tk.NO)
    tree.grid(row=5, column=0, padx=5, pady=5, sticky="ew")
    tree.tag_configure('oddrow', background='white')
    tree.tag_configure('evenrow', background='#DFDFDF')
    tree.bind("<Double-1>", lambda event, tree=tree: on_cell_double_click(event, tree))
    vsb = ttk.Scrollbar(tab, orient="vertical", command=tree.yview)
    vsb.grid(row=5, column=1, sticky="ns")
    tree.configure(yscrollcommand=vsb.set)
    
    # XMLデータをフォームにロード
    load_xml_to_form0(text_box1, text_box2, tree, xml_file_path)
    
    button = tk.Button(tab, text="Solve Model Equations", command=lambda: on_button_click(tab,text_box1, text_box2, tree, xml_file_path))
    button.grid(row=2, column=0, padx=5, pady=5, sticky="ew")
    label2 = tk.Label(tab, text="List of Quantity", font=("", 10, "bold"))
    label2.grid(row=4, column=0, padx=5, pady=0, sticky="w")
    
    return text_box1, text_box2, tree

# ボタンクリック時の処理
def on_button_click(tab,text_box1, text_box2, tree, xml_file_path):
    input_text = text_box1.get("1.0", "end-1c")
    unified_eq = integrate_equations(input_text)
    result_text = str(unified_eq)
    text_box2.delete("1.0", tk.END)
    text_box2.insert("1.0", result_text)
    symbols_list = extract_symbols(input_text)
    save_text_box_to_xml(text_box1, "model_equations")
    save_text_box_to_xml(text_box2, "integrated_equation")
    update_xml(symbols_list, xml_file_path)
    #extract_and_display_symbols(symbols_list, tree)
    calculate_and_update_derivatives(tree, unified_eq, xml_file_path)
    # save_tree_to_xml(tree, xml_file_path)
    setup_tab1(tab)