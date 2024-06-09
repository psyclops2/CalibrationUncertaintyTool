import xml.etree.ElementTree as ET
import math
from tkinter import ttk, scrolledtext
import tkinter as tk

xml_file_path = "symbols.xml"

def on_tab_selected(event):
    selected_tab = event.widget.tab('current')['text']
    if selected_tab == 'Quantity Data':
        tab = event.widget.nametowidget(event.widget.select())
        for child in tab.winfo_children():
            child.destroy()
        from .tab2_setup import setup_tab2
        setup_tab2(tab)