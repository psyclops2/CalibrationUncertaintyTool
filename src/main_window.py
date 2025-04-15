import traceback
from PySide6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QTabWidget, QMessageBox, QFileDialog, QMenuBar, QMenu
from PySide6.QtGui import QAction
from PySide6.QtCore import Qt
import json

from src.tabs.model_equation_tab import ModelEquationTab
from src.tabs.variables_tab import VariablesTab
from src.tabs.uncertainty_calculation_tab import UncertaintyCalculationTab
from src.tabs.report_tab import ReportTab
from src.tabs.partial_derivative_tab import PartialDerivativeTab
from src.dialogs.about_dialog import AboutDialog

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("不確かさ計算ツール")
        self.setGeometry(100, 100, 1200, 800)
        
        # アプリケーションの状態管理
        self.variables = []
        self.result_variables = []
        self.variable_values = {}
        self.last_equation = ""
        self.value_count = 1
        self.current_value_index = 0
        
        # UIの初期化
        self.setup_ui()
        self.create_menu_bar()
        
    def setup_ui(self):
        """UIの設定"""
        # メインウィジェットとレイアウトの設定
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)
        
        # タブウィジェットの作成
        self.tab_widget = QTabWidget()
        
        # 各タブの作成
        self.model_equation_tab = ModelEquationTab(self)
        self.variables_tab = VariablesTab(self)
        self.uncertainty_calculation_tab = UncertaintyCalculationTab(self)
        self.partial_derivative_tab = PartialDerivativeTab(self)
        self.report_tab = ReportTab(self)
        
        # タブの追加
        self.tab_widget.addTab(self.model_equation_tab, "モデル式")
        self.tab_widget.addTab(self.variables_tab, "変数管理/量の値管理")
        self.tab_widget.addTab(self.uncertainty_calculation_tab, "不確かさ計算")
        self.tab_widget.addTab(self.report_tab, "レポート")
        self.tab_widget.addTab(self.partial_derivative_tab, "偏微分")
        
        # タブ切り替え時のシグナル接続
        self.tab_widget.currentChanged.connect(self.on_tab_changed)
        
        layout.addWidget(self.tab_widget)
        
    def create_menu_bar(self):
        """メニューバーの作成"""
        menubar = self.menuBar()
        
        # ファイルメニュー
        file_menu = menubar.addMenu('ファイル')
        
        # 保存アクション
        save_action = QAction('名前を付けて保存...', self)
        save_action.triggered.connect(self.save_file)
        file_menu.addAction(save_action)
        
        # 開くアクション
        open_action = QAction('開く...', self)
        open_action.triggered.connect(self.open_file)
        file_menu.addAction(open_action)
        
        # 終了アクション
        exit_action = QAction('終了', self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # ヘルプメニュー
        help_menu = menubar.addMenu('ヘルプ')
        
        # Aboutアクション
        about_action = QAction('About', self)
        about_action.triggered.connect(self.show_about_dialog)
        help_menu.addAction(about_action)
        
    def get_save_data(self):
        """保存するデータを辞書にまとめる"""
        return {
            'variables': self.variables,
            'result_variables': self.result_variables,
            'variable_values': self.variable_values,
            'last_equation': self.last_equation,
            'value_count': self.value_count,
            'current_value_index': self.current_value_index
        }
        
    def load_data(self, data):
        """読み込んだデータでアプリケーションの状態を更新"""
        try:
            self.variables = data.get('variables', [])
            self.result_variables = data.get('result_variables', [])
            self.variable_values = data.get('variable_values', {})
            self.last_equation = data.get('last_equation', '')
            self.value_count = data.get('value_count', 1)
            self.current_value_index = data.get('current_value_index', 0)
            
            # UIの更新
            if hasattr(self, 'variables_tab'):
                self.variables_tab.update_variable_list(self.variables, self.result_variables)
            if hasattr(self, 'model_equation_tab'):
                self.model_equation_tab.set_equation(self.last_equation)
                
            QMessageBox.information(self, "成功", "ファイルを読み込みました。")
            
        except Exception as e:
            print(f"【エラー】データ読み込みエラー: {str(e)}")
            print(traceback.format_exc())
            QMessageBox.critical(self, "エラー", f"データの読み込みに失敗しました:\n{str(e)}")
            
    def save_file(self):
        """ファイルを保存"""
        try:
            options = QFileDialog.Options()
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "名前を付けて保存",
                "",
                "JSON Files (*.json);;All Files (*)",
                options=options
            )
            
            if file_path:
                save_data = self.get_save_data()
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(save_data, f, indent=4, ensure_ascii=False)
                QMessageBox.information(self, "成功", "ファイルを保存しました。")
                
        except Exception as e:
            print(f"【エラー】ファイル保存エラー: {str(e)}")
            print(traceback.format_exc())
            QMessageBox.critical(self, "エラー", f"ファイルの保存に失敗しました:\n{str(e)}")
            
    def open_file(self):
        """ファイルを開く"""
        try:
            options = QFileDialog.Options()
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                "開く",
                "",
                "JSON Files (*.json);;All Files (*)",
                options=options
            )
            
            if file_path:
                with open(file_path, 'r', encoding='utf-8') as f:
                    loaded_data = json.load(f)
                self.load_data(loaded_data)
                
        except FileNotFoundError:
            QMessageBox.critical(self, "エラー", "ファイルが見つかりません。")
        except json.JSONDecodeError:
            QMessageBox.critical(self, "エラー", "ファイル形式が正しくありません。JSONファイルを選択してください。")
        except Exception as e:
            print(f"【エラー】ファイル読み込みエラー: {str(e)}")
            print(traceback.format_exc())
            QMessageBox.critical(self, "エラー", f"ファイルの読み込みに失敗しました:\n{str(e)}")
            
    def on_tab_changed(self, index):
        """タブが切り替えられたときの処理"""
        if index == 2:  # 不確かさ計算タブ
            self.uncertainty_calculation_tab.update_result_combo()
            self.uncertainty_calculation_tab.update_value_combo()
        elif index == 3:  # レポートタブ
            self.report_tab.update_variable_list(self.variables, self.result_variables)
        elif index == 4:  # 偏微分タブ
            self.partial_derivative_tab.update_equation_display()
            
    def add_variable(self, var_name):
        """変数を追加"""
        if var_name not in self.variables:
            self.variables.append(var_name)
            self.variable_values[var_name] = {
                'values': [],
                'unit': '',
                'type': 'A',
                'measurements': '',
                'degrees_of_freedom': 0,
                'central_value': '',
                'standard_uncertainty': '',
                'distribution': 'normal',
                'divisor': '',
                'half_width': '',
                'fixed_value': ''
            }
            self.variables_tab.update_variable_list(self.variables, [])
            
    def remove_variable(self, var_name):
        """変数を削除"""
        if var_name in self.variables:
            self.variables.remove(var_name)
            if var_name in self.variable_values:
                del self.variable_values[var_name]
            self.variables_tab.update_variable_list(self.variables, [])
            
    def detect_variables(self):
        """変数の検出と変数タブの更新"""
        try:
            if hasattr(self, 'variables_tab'):
                self.variables_tab.update_variable_list(
                    self.variables,
                    self.result_variables
                )
            if hasattr(self, 'uncertainty_calculation_tab'):
                self.uncertainty_calculation_tab.update_result_combo()
            if hasattr(self, 'report_tab'):
                self.report_tab.update_variable_list(
                    self.variables,
                    self.result_variables
                )
        except Exception as e:
            print(f"【エラー】変数検出エラー: {str(e)}\n{traceback.format_exc()}")
            self.log_error(f"変数の検出エラー: {str(e)}", "変数検出エラー")
            
    def show_about_dialog(self):
        """Aboutダイアログを表示"""
        dialog = AboutDialog(self)
        dialog.exec_()
        
    def log_error(self, message, error_type="エラー"):
        """エラーログの記録"""
        print(f"{error_type}: {message}")

    def select_model_equation_tab(self):
        """モデル式タブを選択"""
        print("\n【デバッグ】モデル式タブを明示的に選択")
        self.tab_widget.setCurrentIndex(0)
        
    def select_variables_tab(self):
        """変数管理タブを選択"""
        print("\n【デバッグ】変数管理タブを明示的に選択")
        self.tab_widget.setCurrentIndex(1)
        
    def select_report_tab(self):
        """レポートタブを選択"""
        print("\n【デバッグ】レポートタブを明示的に選択")
        self.tab_widget.setCurrentIndex(4)

    # ... existing code ... 