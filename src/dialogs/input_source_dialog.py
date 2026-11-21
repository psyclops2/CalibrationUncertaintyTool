"""Link a Type A quantity to a regression prediction or paired observation column."""
from src.utils.ui_translation import tr_ui
import copy
import uuid
from types import SimpleNamespace
from datetime import datetime, timezone
from PySide6.QtWidgets import (QDialog,QVBoxLayout,QFormLayout,QComboBox,QLineEdit,QLabel,
    QPushButton,QDialogButtonBox,QCheckBox)
from src.utils.input_sources import ensure_regression_ids, source_packet
from src.utils.value_references import enable_references
from src.utils.variable_utils import evaluate_type_a_value
from .measurement_table_dialog import MeasurementTableDialog


class InputSourceDialog(QDialog):
    def __init__(self, window, variable, point, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr_ui('評価値の入力元'))
        self.setMinimumWidth(620)
        self.variable=variable;self.point=point;self.result_value=None
        self.proxy=SimpleNamespace(variables=window.variables,value_names=window.value_names,
            variable_values=copy.deepcopy(window.variable_values),regressions=copy.deepcopy(window.regressions),
            measurement_tables=copy.deepcopy(getattr(window,'measurement_tables',{})),
            value_references=copy.deepcopy(window.value_references))
        ensure_regression_ids(self.proxy.regressions)
        self.original=copy.deepcopy(window.variable_values[variable]['values'][point])
        source=self.original.get('input_source',{})
        self.original_packet=None
        self.original_error=''
        if source:
            try:self.original_packet=source_packet(window,variable,point)
            except Exception as error:self.original_error=str(error)
        layout=QVBoxLayout(self)
        layout.addWidget(QLabel(tr_ui('量：{0} / 校正点：{1}\n適用範囲：この量の現在の校正点').format(variable,window.value_names[point])))
        self.form=QFormLayout();layout.addLayout(self.form)
        self.kind=QComboBox()
        for label,key in ((tr_ui('直接入力'),'direct'),(tr_ui('回帰の平均応答'),'regression'),(tr_ui('測定表の列の平均'),'table')):self.kind.addItem(label,key)
        self.kind.setCurrentIndex(max(0,self.kind.findData(source.get('kind','direct'))))
        self.form.addRow(tr_ui('入力元'),self.kind)
        self.regression=QComboBox()
        for name,model in self.proxy.regressions.items():self.regression.addItem(name,model['id'])
        if source.get('model_id'):self.regression.setCurrentIndex(self.regression.findData(source['model_id']))
        self.form.addRow(tr_ui('回帰モデル'),self.regression)
        self.navigate_model_id=None
        self.edit_regression=QPushButton(tr_ui('回帰タブでデータを編集…'))
        self.edit_regression.setAutoDefault(False)
        self.edit_regression.clicked.connect(self.navigate_to_regression)
        self.form.addRow(self.edit_regression)
        self.x_mode=QComboBox();self.x_mode.addItems([tr_ui('固定の数値・式'),tr_ui('固定量の現在点')])
        self.form.addRow(tr_ui('評価するxの入力'),self.x_mode)
        self.x_expression=QLineEdit(source.get('x_expression','0'))
        self.form.addRow(tr_ui('評価するx（回帰のxと同じ単位）'),self.x_expression)
        self.x_variable=QComboBox()
        for name,info in self.proxy.variable_values.items():
            if info.get('type')=='fixed':self.x_variable.addItem(name+' ['+info.get('unit','')+']',name)
        self.form.addRow(tr_ui('固定量'),self.x_variable)
        refs=self.proxy.value_references
        if refs:
            for i in range(self.x_variable.count()):
                name=self.x_variable.itemData(i);ident=refs['variables'].get(name)
                if source.get('x_expression')=='@{variable:'+str(ident)+':central_value:current}':
                    self.x_mode.setCurrentIndex(1);self.x_variable.setCurrentIndex(i)
        self.table=QComboBox();self.form.addRow(tr_ui('測定表'),self.table)
        self.column=QComboBox();self.form.addRow(tr_ui('使用する列'),self.column)
        self.add_table=QPushButton(tr_ui('測定表を作成…'));self.form.addRow(self.add_table)
        self.edit_table=QPushButton(tr_ui('選択した測定表を編集…'));self.form.addRow(self.edit_table)
        self.add_table.setAutoDefault(False);self.edit_table.setAutoDefault(False)
        self.add_table.clicked.connect(lambda:self.edit_measurement_table(True))
        self.edit_table.clicked.connect(lambda:self.edit_measurement_table(False))
        self.freeze=QCheckBox(tr_ui('接続中の評価値を統計量として固定し、根拠を残す'))
        self.freeze.setEnabled(self.original_packet is not None)
        self.freeze.setToolTip(self.original_error)
        self.form.addRow(self.freeze)
        self.preview_label=QLabel('');self.preview_label.setWordWrap(True);layout.addWidget(self.preview_label)
        self.preview_button=QPushButton(tr_ui('評価値を確認'));self.preview_button.clicked.connect(self.preview);layout.addWidget(self.preview_button)
        self.preview_button.setAutoDefault(False)
        self.buttons=QDialogButtonBox(QDialogButtonBox.Ok|QDialogButtonBox.Cancel)
        self.buttons.accepted.connect(self.accept);self.buttons.rejected.connect(self.reject);layout.addWidget(self.buttons)
        self.buttons.button(QDialogButtonBox.Ok).setDefault(True)
        self.table.currentIndexChanged.connect(self.update_columns)
        self.reload_tables(source.get('table_id'))
        if source.get('column'):self.column.setCurrentIndex(self.column.findData(source['column']))
        self.kind.currentIndexChanged.connect(self.update_fields);self.x_mode.currentIndexChanged.connect(self.update_fields)
        self.update_fields()

    def reload_tables(self, selected=None):
        self.table.blockSignals(True);self.table.clear()
        for ident,table in self.proxy.measurement_tables.items():self.table.addItem(table.get('name',tr_ui('測定表')),ident)
        if selected:self.table.setCurrentIndex(self.table.findData(selected))
        self.table.blockSignals(False);self.update_columns()

    def update_columns(self, *_):
        self.column.clear()
        table=self.proxy.measurement_tables.get(self.table.currentData(),{})
        for column in table.get('columns',[]):self.column.addItem(column['id'],column['id'])

    def update_fields(self, *_):
        kind=self.kind.currentData()
        for field in (self.regression,self.x_mode,self.edit_regression):self.form.setRowVisible(field,kind=='regression')
        self.form.setRowVisible(self.x_expression,kind=='regression' and self.x_mode.currentIndex()==0)
        self.form.setRowVisible(self.x_variable,kind=='regression' and self.x_mode.currentIndex()==1)
        for field in (self.table,self.column,self.add_table,self.edit_table):self.form.setRowVisible(field,kind=='table')
        self.form.setRowVisible(self.freeze,kind=='direct' and bool(self.original.get('input_source')))
        self.preview_label.clear()

    def navigate_to_regression(self):
        if not self.regression.currentData():
            self.preview_label.setText(tr_ui('回帰タブでモデルを登録してください。'));return
        self.navigate_model_id=self.regression.currentData()
        self.reject()

    def edit_measurement_table(self, new):
        ident=uuid.uuid4().hex if new else self.table.currentData()
        if not ident:return
        dialog=MeasurementTableDialog(None if new else self.proxy.measurement_tables[ident],self)
        if dialog.exec():
            self.proxy.measurement_tables[ident]=dialog.result_table;self.reload_tables(ident)

    def settings(self):
        if self.kind.currentData()=='regression':
            expression=self.x_expression.text().strip()
            if self.x_mode.currentIndex()==1:
                name=self.x_variable.currentData()
                if not name:raise ValueError(tr_ui('評価する固定量を選択してください'))
                refs=enable_references(self.proxy)
                expression='@{variable:'+refs['variables'][name]+':central_value:current}'
            if not self.regression.currentData():raise ValueError(tr_ui('回帰モデルを登録・選択してください'))
            return dict(kind='regression',model_id=self.regression.currentData(),x_expression=expression)
        if self.kind.currentData()=='table':
            if not self.table.currentData() or not self.column.currentData():raise ValueError(tr_ui('測定表と列を選択してください'))
            return dict(kind='table',table_id=self.table.currentData(),column=self.column.currentData())
        return None

    def preview(self):
        try:
            settings=self.settings()
            if settings is None:
                self.preview_label.setText(tr_ui('直接入力へ戻します。保存してある直接入力を復元します。') if not self.freeze.isChecked() else
                    tr_ui('現在の評価値を固定し、自動更新を解除します。'))
                return True
            self.proxy.variable_values[self.variable]['values'][self.point]['input_source']=settings
            packet=source_packet(self.proxy,self.variable,self.point)
            self.preview_label.setText(tr_ui('{0}\n中心値 {1:.12g} / u {2:.8g} / 自由度 {3}\n{4}\n単位：{5}（自動換算はしません）').format(packet['label'],packet['mean'],packet['u'],packet['df'],packet['note'],packet['unit']))
            return True
        except Exception as error:
            self.preview_label.setText(str(error));return False

    def accept(self):
        if not self.preview():return
        settings=self.settings()
        value=copy.deepcopy(self.original)
        if settings is None:
            if self.freeze.isChecked() and value.get('input_source'):
                packet=self.original_packet
                value=dict(evaluation_mode='summary',central_value=str(packet['mean']),standard_uncertainty=str(packet['u']),
                           degrees_of_freedom=str(packet['df']),measurements='',description=value.get('description',''),
                           evaluation_note=packet['label']+tr_ui(' / 固定した時点 ')+datetime.now(timezone.utc).isoformat())
            else:
                value=copy.deepcopy(value.get('direct_input',value))
                value.pop('input_source',None);value.pop('direct_input',None)
        else:
            if not value.get('input_source'):value['direct_input']=copy.deepcopy(value)
            value['input_source']=settings
        self.result_value=value
        super().accept()
