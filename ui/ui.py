import sys
import os

# 現在のディレクトリをモジュール検索パスに追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import tkinter as tk
from tkinter import ttk
from ui.process import on_tab_selected
from ui.tab0_setup import setup_tab0
from ui.tab1_setup import setup_tab1
from ui.tab2_setup import setup_tab2
from ui.tab3_setup import setup_tab3
from ui.tab4_setup import setup_tab4
from ui.process import on_entry_change,on_combobox_change

def main():
    root = tk.Tk()
    root.title("Uncertainty Tool Kit")
    root.geometry("700x500")

    notebook = ttk.Notebook(root)
    notebook.pack(fill='both', expand=True)

    # タブ0の作成
    tab0 = ttk.Frame(notebook)
    notebook.add(tab0, text='Measurement Procedure')
    setup_tab0(tab0)

    # タブ1の作成
    tab1 = ttk.Frame(notebook)
    notebook.add(tab1, text='Model Equation')
    setup_tab1(tab1)

    # タブ2の作成
    tab2 = ttk.Frame(notebook)
    notebook.add(tab2, text='Quantity Data')
    setup_tab2(tab2)

    # タブ3の作成
    tab3 = ttk.Frame(notebook)
    notebook.add(tab3, text='Observation Results')
    setup_tab3(tab3)

    # タブ4の作成
    tab4 = ttk.Frame(notebook)
    notebook.add(tab4, text='Uncertainty Budget')
    setup_tab4(tab4)

    notebook.bind("<<NotebookTabChanged>>", on_tab_selected)

    root.mainloop()

if __name__ == "__main__":
    main()