from src.utils.ui_translation import tr_ui
import math
from PySide6.QtWidgets import (QDialog,QVBoxLayout,QLabel,QTabWidget,QTableWidget,
                               QTableWidgetItem,QDialogButtonBox,QCheckBox,QAbstractItemView)
from src.utils.output_covariance import evaluate_outputs


class OutputCovarianceDialog(QDialog):
    def __init__(self, window, point, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr_ui('結果どうしの共分散・相関'))
        self.resize(650,430)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(tr_ui('校正点：')+window.value_names[point]+tr_ui(' / 一次伝播')))
        names,covariance,correlation = evaluate_outputs(window,point)
        tabs = QTabWidget()
        for title, matrix in ((tr_ui('共分散（行の単位 × 列の単位）'),covariance),(tr_ui('相関係数'),correlation)):
            table = QTableWidget(len(names),len(names))
            labels = [name+' ['+window.variable_values[name].get('unit','')+']' for name in names]
            table.setHorizontalHeaderLabels(labels);table.setVerticalHeaderLabels(labels)
            table.setEditTriggers(QAbstractItemView.NoEditTriggers)
            for i in range(len(names)):
                for j in range(len(names)):
                    value = float(matrix[i,j])
                    table.setItem(i,j,QTableWidgetItem(f'{value:.7g}' if math.isfinite(value) else tr_ui('未定義（u=0）')))
            table.resizeColumnsToContents();tabs.addTab(table,title)
        layout.addWidget(tabs)
        self.include = QCheckBox(tr_ui('この校正点のレポートに出力間の共分散・相関を含める'))
        result = parent.result_combo.currentText()
        value = window.variable_values[result]['values'][point]
        self.include.setChecked(value.get('include_output_covariance',False))
        layout.addWidget(self.include)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok|QDialogButtonBox.Cancel)
        buttons.accepted.connect(lambda: (value.update(include_output_covariance=self.include.isChecked()),self.accept()))
        buttons.rejected.connect(self.reject);layout.addWidget(buttons)
