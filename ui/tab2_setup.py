# 量の入力タブのUI
import tkinter as tk
from tkinter import ttk
import xml.etree.ElementTree as ET
from ui.tab_symbol_setup import create_symbol_tab

xml_file_path = "symbols.xml"

def setup_tab2(tab):
    # スタイルを設定
    style = ttk.Style(tab)
    style.configure('lefttab_custom.TNotebook', tabposition='wn')
    style.configure('lefttab_custom.TNotebook.Tab', padding=[5, 1], width=15)  # タブの幅を指定

    # 左側のノートブックを作成
    notebook_left = ttk.Notebook(tab, style='lefttab_custom.TNotebook')
    notebook_left.pack(side='left', fill='y')

    # XMLを読み込む
    try:
        tree = ET.parse(xml_file_path)
        root = tree.getroot()
        symbols_section = root.find("symbols")
        if symbols_section is None:
            symbols_section = ET.SubElement(root, "symbols")
    except FileNotFoundError:
        print("Warning: XML file not found. Creating a new default XML structure.")
        root = ET.Element("data")
        tree = ET.ElementTree(root)
        symbols_section = ET.SubElement(root, "symbols")

    # XMLにある記号のタブを作成
    symbols = symbols_section.findall("symbol")
    if symbols:
        for symbol in symbols:
            symbol_name = symbol.get("name")
            new_tab = ttk.Frame(notebook_left)
            notebook_left.add(new_tab, text=symbol_name)  # カスタムスタイルを適用
            create_symbol_tab(new_tab, symbol_name, symbol, tree, xml_file_path)  # 正しい引数リスト
    else:
        # XMLが空の場合は、デフォルトのタブを1つ表示する
        new_tab = ttk.Frame(notebook_left)
        notebook_left.add(new_tab, text="No Items")  # カスタムスタイルを適用
        label = tk.Label(new_tab, text="No content available")
        label.pack(padx=10, pady=10)

    # 右側に内容を表示する部分
    content_frame = ttk.Frame(tab)
    content_frame.pack(side="right", fill="both", expand=True)

