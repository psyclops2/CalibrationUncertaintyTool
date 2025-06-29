import os
import sys
import subprocess
from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom.minidom import parseString

# プロジェクトのルートディレクトリをsys.pathに追加
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src.i18n.translations_ja import translations as ja_translations
from src.i18n.translations_en import translations as en_translations

TS_FILE_TEMPLATE = '''<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE TS>
<TS version="2.1" language="{language_code}">
{contexts}
</TS>'''

CONTEXT_TEMPLATE = '''<context>
    <name>{context_name}</name>
{messages}
</context>'''

MESSAGE_TEMPLATE = '''    <message>
        <source>{source}</source>
        <translation>{translation}</translation>
    </message>'''

def generate_ts_file(language_code, translations, output_path):
    contexts = []
    for context_name, trans_dict in translations.items():
        messages = []
        for key, value in trans_dict.items():
            messages.append(MESSAGE_TEMPLATE.format(source=key, translation=value))
        
        context_content = CONTEXT_TEMPLATE.format(context_name=context_name, messages='\n'.join(messages))
        contexts.append(context_content)
    
    ts_content = TS_FILE_TEMPLATE.format(language_code=language_code, contexts='\n'.join(contexts))
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(ts_content)
    print(f"Generated TS file: {output_path}")

def compile_ts_to_qm(ts_file, qm_file):
    command = ['pyside6-lrelease', ts_file, '-qm', qm_file]
    try:
        result = subprocess.run(command, check=True, capture_output=True, text=True, encoding='utf-8')
        print(f"Updating '{qm_file}'...")
        # lrelease prints its output to stdout, so we print it
        print(result.stdout.strip())
    except FileNotFoundError:
        print("Error: 'pyside6-lrelease' command not found.")
        print("Please ensure PySide6 is installed and its tools are in your system's PATH.")
    except subprocess.CalledProcessError as e:
        print(f"Error compiling {ts_file}: {e}")
        print(f"lrelease stderr:\n{e.stderr}")

def main():
    i18n_dir = os.path.dirname(os.path.abspath(__file__))
    
    # JA
    ja_ts_file = os.path.join(i18n_dir, 'ja.ts')
    ja_qm_file = os.path.join(i18n_dir, 'ja.qm')
    generate_ts_file('ja_JP', ja_translations, ja_ts_file)
    compile_ts_to_qm(ja_ts_file, ja_qm_file)
    
    # EN
    en_ts_file = os.path.join(i18n_dir, 'en.ts')
    en_qm_file = os.path.join(i18n_dir, 'en.qm')
    generate_ts_file('en_US', en_translations, en_ts_file)
    compile_ts_to_qm(en_ts_file, en_qm_file)

if __name__ == '__main__':
    main()
