"""Show named references while retaining stable addresses for persistence."""
import re
from PySide6.QtWidgets import QPlainTextEdit
from src.utils.ui_translation import tr_ui
from src.utils.value_references import TOKEN

FUNCTIONS='sin cos tan asin acos atan atan2 sinh cosh tanh exp log log10 log2 sqrt fabs floor ceil degrees radians'.split()


def address_label(address,data,points):
    parts=address.split(':')
    if parts[0]=='value' and len(parts) in (2,3) and parts[1] in data['values']:
        label=data['values'][parts[1]]['name']
        if len(parts)==3:label+=' / '+points.get(parts[2],tr_ui('削除された校正点'))
        return label
    if parts[0]=='variable' and len(parts)==4:
        name=next((n for n,i in data['variables'].items() if i==parts[1]),None)
        if name:
            point=tr_ui('計算する校正点') if parts[3]=='current' else points.get(parts[3],tr_ui('削除された校正点'))
            return tr_ui('{0}の中心値 / {1}').format(name,point)
    return tr_ui('参照先が見つかりません')


class ReferenceExpressionEdit(QPlainTextEdit):
    def __init__(self,parent=None):
        super().__init__(parent);self.bindings={}
        self.setMinimumHeight(90);self.setMaximumHeight(130);self.setTabChangesFocus(True)

    def label_for(self,address,data,points):
        for label,value in self.bindings.items():
            if value==address:return label
        base=address_label(address,data,points).replace('【','(').replace('】',')').replace('\n',' ')
        label='【'+base+'】';index=2
        while label in self.bindings:label='【'+base+f' ({index})】';index+=1
        self.bindings[label]=address;return label

    def set_expression(self,raw,data,points):
        self.bindings={}
        text=re.sub(r'\bmath\.('+'|'.join(FUNCTIONS)+r')\b',r'\1',raw)
        text=TOKEN.sub(lambda m:self.label_for(m[1],data,points),text)
        self.setPlainText(text)

    def expression(self):
        text=self.toPlainText().strip()
        for label,address in self.bindings.items():text=text.replace(label,'@{'+address+'}')
        tokens={}
        def protect(match):
            key=f'__saved_reference_{len(tokens)}__';tokens[key]=match[0];return key
        text=TOKEN.sub(protect,text)
        text=re.sub(r'(?<![\w.])('+'|'.join(FUNCTIONS)+r')\s*(?=\()',r'math.\1',text)
        for key,value in tokens.items():text=text.replace(key,value)
        return text

    def insert_reference(self,address,data,points):
        self.insertPlainText(self.label_for(address,data,points));self.setFocus()
