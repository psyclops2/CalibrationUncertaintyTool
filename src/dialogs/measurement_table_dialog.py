"""Optional paired-observation editor; row identity is preserved."""
from src.utils.ui_translation import tr_ui
import copy
import csv
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QDialog,QVBoxLayout,QHBoxLayout,QLabel,QLineEdit,QTableWidget,
    QTableWidgetItem,QPushButton,QDialogButtonBox,QMessageBox,QFileDialog,QHeaderView)
from src.utils.input_sources import evaluate_table, evaluate_table_rows


class MeasurementTableDialog(QDialog):
    def __init__(self, table=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr_ui('同時観測の測定表'))
        self.resize(850,680)
        self.result_table = None
        self.original = copy.deepcopy(table or {'name':tr_ui('測定表'),'columns':[{'id':'x','unit':'','expression':''}], 'rows':[]})
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(tr_ui('同じ行が同じ観測組です。欠測のある組は、行全体を除外してください。派生列は行ごとに計算します。')))
        self.name = QLineEdit(self.original.get('name',''))
        layout.addWidget(self.name)
        self.columns = QTableWidget(0,3)
        self.columns.setHorizontalHeaderLabels([tr_ui('列名（量名）'),tr_ui('単位'),tr_ui('派生列の式（元データ列は空欄）')])
        self.columns.setToolTip(tr_ui('列の式は同じ行の量名で記述します。数値の単位換算は自動ではありません。'))
        self.columns.setMaximumHeight(190)
        self.columns.horizontalHeader().setSectionResizeMode(2,QHeaderView.Stretch)
        layout.addWidget(self.columns)
        bar = QHBoxLayout()
        for title, action in ((tr_ui('列を追加'),self.add_column),(tr_ui('列を削除'),self.remove_column),(tr_ui('CSVを取り込む…'),self.import_csv)):
            button=QPushButton(title);button.setAutoDefault(False);button.clicked.connect(action);bar.addWidget(button)
        layout.addLayout(bar)
        self.rows = QTableWidget()
        self.rows.setSortingEnabled(False)
        self.rows.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        layout.addWidget(self.rows)
        bar = QHBoxLayout()
        for title,action in ((tr_ui('観測組を追加'),self.add_row),(tr_ui('観測組を削除'),self.remove_row),(tr_ui('評価を確認'),self.preview)):
            button=QPushButton(title);button.setAutoDefault(False);button.clicked.connect(action);bar.addWidget(button)
        layout.addLayout(bar)
        self.status=QLabel('');self.status.setWordWrap(True);layout.addWidget(self.status)
        buttons=QDialogButtonBox(QDialogButtonBox.Ok|QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept);buttons.rejected.connect(self.reject);layout.addWidget(buttons)
        self.load(self.original)
        self.columns.itemChanged.connect(self.sync_headers)

    def load(self, table):
        self.columns.blockSignals(True)
        self.columns.setRowCount(len(table['columns']))
        for i,column in enumerate(table['columns']):
            for j,key in enumerate(('id','unit','expression')):
                self.columns.setItem(i,j,QTableWidgetItem(column.get(key,'')))
        self.columns.blockSignals(False)
        self.sync_headers()
        self.rows.setRowCount(0)
        for data in table['rows']:
            self.add_row()
            i=self.rows.rowCount()-1
            self.rows.item(i,0).setCheckState(Qt.Checked if data.get('excluded',False) else Qt.Unchecked)
            for j,column in enumerate(table['columns'],1):
                self.rows.setItem(i,j,QTableWidgetItem(str(data.get(column['id'],''))))
        self.columns.resizeColumnsToContents()
        self.sync_headers()

    def text(self, table, row, column):
        item=table.item(row,column)
        return item.text().strip() if item else ''

    def sync_headers(self, *_):
        self.rows.setColumnCount(self.columns.rowCount()+1)
        self.rows.setHorizontalHeaderLabels([tr_ui('除外')]+[self.text(self.columns,i,0) for i in range(self.columns.rowCount())])
        for i in range(self.rows.rowCount()):
            for j in range(self.columns.rowCount()):
                item=self.rows.item(i,j+1)
                if item is None:
                    item=QTableWidgetItem('');self.rows.setItem(i,j+1,item)
                flags=Qt.ItemIsEnabled|Qt.ItemIsSelectable
                if not self.text(self.columns,j,2):flags|=Qt.ItemIsEditable
                item.setFlags(flags)

    def add_column(self):
        index=self.columns.rowCount();self.columns.insertRow(index)
        self.columns.setItem(index,0,QTableWidgetItem('column'+str(index+1)))
        self.sync_headers()

    def remove_column(self):
        index=self.columns.currentRow()
        if index>=0:
            self.rows.removeColumn(index+1);self.columns.removeRow(index);self.sync_headers()

    def add_row(self):
        index=self.rows.rowCount();self.rows.insertRow(index)
        item=QTableWidgetItem('')
        item.setFlags(Qt.ItemIsEnabled|Qt.ItemIsUserCheckable)
        item.setCheckState(Qt.Unchecked);self.rows.setItem(index,0,item)
        self.sync_headers()

    def remove_row(self):
        if self.rows.currentRow()>=0:self.rows.removeRow(self.rows.currentRow())

    def collect(self):
        columns=[dict(zip(('id','unit','expression'),[self.text(self.columns,i,j) for j in range(3)])) for i in range(self.columns.rowCount())]
        rows=[]
        for i in range(self.rows.rowCount()):
            row={column['id']:self.text(self.rows,i,j+1) for j,column in enumerate(columns) if not column['expression'].strip()}
            row['excluded']=self.rows.item(i,0).checkState()==Qt.Checked
            rows.append(row)
        return dict(name=self.name.text().strip(),columns=columns,rows=rows)

    def preview(self):
        try:
            ids,means,covariance,df=evaluate_table(self.collect())
            values=evaluate_table_rows(self.collect());used=0
            for i in range(self.rows.rowCount()):
                excluded=self.rows.item(i,0).checkState()==Qt.Checked
                for j in range(self.columns.rowCount()):
                    if self.text(self.columns,j,2):
                        self.rows.item(i,j+1).setText(tr_ui('除外') if excluded else f'{values[used,j]:.12g}')
                if not excluded:used+=1
            self.status.setText(tr_ui('使用した観測組 {0} / 自由度 {1}\n').format(df + 1,df)+'、'.join(
                tr_ui('{0}: 平均={1:.8g}, u={2:.6g}').format(name,means[i],max(0, covariance[i, i]) ** 0.5) for i,name in enumerate(ids)))
            return True
        except Exception as error:
            self.status.setText(str(error));return False

    def import_csv(self):
        path,_=QFileDialog.getOpenFileName(self,tr_ui('CSVを取り込む'),'','CSV (*.csv)')
        if not path:return
        try:
            with open(path,encoding='utf-8-sig',newline='') as stream:
                reader=csv.DictReader(stream); rows=list(reader); headers=reader.fieldnames or []
            if any(None in row for row in rows):
                raise ValueError(tr_ui('CSVの列数が見出しと一致していません'))
            if not headers or len(headers)!=len(set(headers)) or any(not name.isidentifier() for name in headers):
                raise ValueError(tr_ui('CSVの見出しには、重複しない量名を指定してください'))
            if self.rows.rowCount() and QMessageBox.question(self,tr_ui('表を置き換える'),
                tr_ui('編集中の測定表をCSVの内容で置き換えますか？'),QMessageBox.Yes|QMessageBox.No,QMessageBox.No)!=QMessageBox.Yes:return
            self.load(dict(columns=[dict(id=name,unit='',expression='') for name in headers],rows=rows))
            self.status.setText(tr_ui('取り込んだ列の単位と行の対応を確認してください。'))
        except Exception as error:QMessageBox.warning(self,tr_ui('CSVを確認してください'),str(error))

    def accept(self):
        if self.preview():
            self.result_table=self.collect();super().accept()
