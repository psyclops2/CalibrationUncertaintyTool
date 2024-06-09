# ファイル概要タブのUI

import tkinter as tk
from tkinter import scrolledtext
import xml.etree.ElementTree as ET

xml_file_path = "symbols.xml"

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

def setup_tab0(tab):
    xml_file_path = "symbols.xml"
    
    # グリッド構造の設定
    tab.grid_columnconfigure(0, weight=0)
    tab.grid_columnconfigure(1, weight=0)
    tab.grid_columnconfigure(2, weight=0)
    tab.grid_columnconfigure(3, weight=0)
    tab.grid_columnconfigure(4, weight=1)
    tab.grid_rowconfigure(6, weight=1)

    label_title = tk.Label(tab, text="Title:")
    label_title.grid(row=0, column=0, sticky="e", padx=5, pady=5)
    entry_title = tk.Entry(tab)
    entry_title.grid(row=0, column=1, columnspan=5, sticky="ew", padx=5, pady=5)
    entry_title.bind("<FocusOut>", lambda event: on_entry_change(event, entry_title, "title", xml_file_path))

    label_reference = tk.Label(tab, text="Reference:")
    label_reference.grid(row=1, column=0, sticky="e", padx=5, pady=5)
    entry_reference = tk.Entry(tab)
    entry_reference.grid(row=1, column=1, sticky="ew", padx=5, pady=5)
    entry_reference.bind("<FocusOut>", lambda event: on_entry_change(event, entry_reference, "reference", xml_file_path))

    label_revision = tk.Label(tab, text="Revision:")
    label_revision.grid(row=1, column=2, sticky="e", padx=5, pady=5)
    entry_revision = tk.Entry(tab)
    entry_revision.grid(row=1, column=3, sticky="ew", padx=5, pady=5)
    entry_revision.bind("<FocusOut>", lambda event: on_entry_change(event, entry_revision, "revision", xml_file_path))

    label_date = tk.Label(tab, text="Date:")
    label_date.grid(row=1, column=4, sticky="e", padx=5, pady=5)
    entry_date = tk.Entry(tab)
    entry_date.grid(row=1, column=5, sticky="ew", padx=5, pady=5)
    entry_date.bind("<FocusOut>", lambda event: on_entry_change(event, entry_date, "date", xml_file_path))

    label_author = tk.Label(tab, text="Author:")
    label_author.grid(row=2, column=0, sticky="e", padx=5, pady=5)
    entry_author = tk.Entry(tab)
    entry_author.grid(row=2, column=1, sticky="ew", padx=5, pady=5)
    entry_author.bind("<FocusOut>", lambda event: on_entry_change(event, entry_author, "author", xml_file_path))

    label_checker = tk.Label(tab, text="Checker:")
    label_checker.grid(row=2, column=2, sticky="e", padx=5, pady=5)
    entry_checker = tk.Entry(tab)
    entry_checker.grid(row=2, column=3, sticky="ew", padx=5, pady=5)
    entry_checker.bind("<FocusOut>", lambda event: on_entry_change(event, entry_checker, "checker", xml_file_path))

    label_approver = tk.Label(tab, text="Approver:")
    label_approver.grid(row=2, column=4, sticky="e", padx=5, pady=5)
    entry_approver = tk.Entry(tab)
    entry_approver.grid(row=2, column=5, sticky="ew", padx=5, pady=5)
    entry_approver.bind("<FocusOut>", lambda event: on_entry_change(event, entry_approver, "approver", xml_file_path))

    label_procedure_description = tk.Label(tab, text="Procedure Description:")
    label_procedure_description.grid(row=3, column=0, columnspan=3, sticky="w", padx=5, pady=5)
    text_procedure_description = scrolledtext.ScrolledText(tab, wrap=tk.WORD, height=20)
    text_procedure_description.grid(row=4, column=0, columnspan=6, sticky="nsew", padx=5, pady=5)
    text_procedure_description.bind("<FocusOut>", lambda event: on_text_change(event, text_procedure_description, "procedure_description", xml_file_path))

    for i in range(6):
        tab.grid_columnconfigure(i, weight=1)
    tab.grid_rowconfigure(4, weight=1)

    # XMLの値をフォームに読み込む
    load_xml_to_form(xml_file_path, entry_title, entry_reference, entry_revision, entry_date, entry_author, entry_checker, entry_approver, text_procedure_description)

def load_xml_to_form(xml_file_path, entry_title, entry_reference, entry_revision, entry_date, entry_author, entry_checker, entry_approver, text_procedure_description):
    try:
        tree = ET.parse(xml_file_path)
        root = tree.getroot()
    except FileNotFoundError:
        print("XML file not found. Loading default values...")
        root = ET.Element("data")
        tree = ET.ElementTree(root)
        procedure = ET.SubElement(root, "procedure")
    else:
        procedure = root.find("procedure") or ET.SubElement(root, "procedure")

    if procedure.find("title") is not None and procedure.find("title").text is not None:
        entry_title.insert(0, procedure.find("title").text)
    if procedure.find("reference") is not None and procedure.find("reference").text is not None:
        entry_reference.insert(0, procedure.find("reference").text)
    if procedure.find("revision") is not None and procedure.find("revision").text is not None:
        entry_revision.insert(0, procedure.find("revision").text)
    if procedure.find("date") is not None and procedure.find("date").text is not None:
        entry_date.insert(0, procedure.find("date").text)
    if procedure.find("author") is not None and procedure.find("author").text is not None:
        entry_author.insert(0, procedure.find("author").text)
    if procedure.find("checker") is not None and procedure.find("checker").text is not None:
        entry_checker.insert(0, procedure.find("checker").text)
    if procedure.find("approver") is not None and procedure.find("approver").text is not None:
        entry_approver.insert(0, procedure.find("approver").text)
    if procedure.find("procedure_description") is not None and procedure.find("procedure_description").text is not None:
        text_procedure_description.insert(tk.END, procedure.find("procedure_description").text)

    # Save the default empty XML structure if necessary
    if not ET.iselement(root.find("procedure")):
        tree.write(xml_file_path, encoding='utf-8', xml_declaration=True)

def on_entry_change(event, entry, tag, xml_file_path):
    try:
        tree = ET.parse(xml_file_path)
        root = tree.getroot()
        procedure = root.find("procedure")
        if procedure is None:
            procedure = ET.SubElement(root, "procedure")
    except FileNotFoundError:
        root = ET.Element("data")
        tree = ET.ElementTree(root)
        procedure = ET.SubElement(root, "procedure")

    value = entry.get()
    element = procedure.find(tag)
    if element is not None:
        element.text = value
    else:
        element = ET.SubElement(procedure, tag)
        element.text = value

    indent(root)
    tree.write(xml_file_path, encoding='utf-8', xml_declaration=True)

def on_text_change(event, text_widget, tag, xml_file_path):
    try:
        tree = ET.parse(xml_file_path)
        root = tree.getroot()
        procedure = root.find("procedure")
        if procedure is None:
            procedure = ET.SubElement(root, "procedure")
    except FileNotFoundError:
        root = ET.Element("data")
        tree = ET.ElementTree(root)
        procedure = ET.SubElement(root, "procedure")

    value = text_widget.get("1.0", tk.END).strip()
    element = procedure.find(tag)
    if element is not None:
        element.text = value
    else:
        element = ET.SubElement(procedure, tag)
        element.text = value

    indent(root)
    tree.write(xml_file_path, encoding='utf-8', xml_declaration=True)