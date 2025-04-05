import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QTabWidget, QWidget, QVBoxLayout,
                           QMessageBox, QFileDialog, QAction)
from PyQt5.QtCore import Qt
import json
import traceback

from src.tabs.model_equation_tab import ModelEquationTab
from src.tabs.variables_tab import VariablesTab
from src.tabs.uncertainty_calculation_tab import UncertaintyCalculationTab
from src.tabs.report_tab import ReportTab
from src.tabs.partial_derivative_tab import PartialDerivativeTab
from src.dialogs.about_dialog import AboutDialog

class UncertaintyCalculator(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("不確かさ計算ツール")
        self.setGeometry(100, 100, 1200, 800)
        
        # 変数とその値を保持する辞書
        self.variables = []
        self.result_variables = []  # 計算結果の変数のリスト
        self.variable_values = {}
        self.last_equation = ""  # 最後に入力された方程式
        self.value_count = 1  # デフォルトの値の数
        self.current_value_index = 0  # 現在選択されている値のインデックス
        
        print("【デバッグ】UncertaintyCalculator初期化")
        print(f"【デバッグ】result_variables: {self.result_variables}")
        print(f"【デバッグ】value_count: {self.value_count}")
        
        self.setup_ui()
        self.create_menu_bar()
        
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
            'result_variables': self.result_variables,  # 計算結果変数も保存
            'variable_values': self.variable_values,
            'last_equation': self.last_equation,
            'value_count': self.value_count,
            'current_value_index': self.current_value_index
        }

    def load_data(self, data):
        """読み込んだデータでアプリケーションの状態を更新"""
        try:
            self.variables = data.get('variables', [])
            self.result_variables = data.get('result_variables', [])  # 計算結果変数を読み込み
            self.variable_values = data.get('variable_values', {})
            self.last_equation = data.get('last_equation', '')
            self.value_count = data.get('value_count', 1)
            self.current_value_index = data.get('current_value_index', 0)
            
            # UIの更新
            if hasattr(self, 'variables_tab'):
                self.variables_tab.update_variable_list(self.variables, self.result_variables)  # 計算結果変数も渡す
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

    def setup_ui(self):
        """UIの設定"""
        print("【デバッグ】setup_ui開始")
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
        self.tab_widget.addTab(self.partial_derivative_tab, "偏微分")
        self.tab_widget.addTab(self.report_tab, "レポート")
        
        # タブ切り替え時のシグナル接続
        self.tab_widget.currentChanged.connect(self.on_tab_changed)
        
        # レポートタブの初期化
        self.report_tab.update_variable_list(self.variables, self.result_variables)
        
        layout.addWidget(self.tab_widget)
        print("【デバッグ】setup_ui完了")
        
    def on_tab_changed(self, index):
        """タブが切り替えられたときの処理"""
        print(f"【デバッグ】タブ切り替え: {index}")
        if index == 2:  # 不確かさ計算タブが選択された場合
            print("【デバッグ】不確かさ計算タブが選択されました")
            print(f"【デバッグ】現在のresult_variables: {self.result_variables}")
            print(f"【デバッグ】現在のvalue_count: {self.value_count}")
            self.uncertainty_calculation_tab.update_result_combo()
            self.uncertainty_calculation_tab.update_value_combo()
        elif index == 3:  # 偏微分タブが選択された場合
            print("【デバッグ】偏微分タブが選択されました")
            self.partial_derivative_tab.update_equation_display()
        elif index == 4:  # レポートタブが選択された場合
            print("【デバッグ】レポートタブが選択されました")
            print(f"【デバッグ】現在のresult_variables: {self.result_variables}")
            self.report_tab.update_variable_list(self.variables, self.result_variables)
        
    def add_variable(self, var_name):
        """変数を追加"""
        if var_name not in self.variables:
            self.variables.append(var_name)
            # 変数値辞書の初期化
            self.variable_values[var_name] = {
                'values': [],  # 複数の値のリスト
                'unit': '',    # 単位
                'type': 'A',   # 不確かさの種類（'A', 'B', 'fixed'）
                # TypeA用のフィールド
                'measurements': '',  # カンマ区切りの測定値
                'degrees_of_freedom': 0,  # 自由度
                'central_value': '',  # 中央値（平均値）
                'standard_uncertainty': '',  # 標準不確かさ
                # TypeB用のフィールド
                'distribution': 'normal',  # 分布の種類（'normal', 'rectangular', 'triangular', 'u'）
                'divisor': '',  # 除数
                'half_width': '',  # 半値幅
                # 固定値用のフィールド
                'fixed_value': ''  # 固定値
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
            print("\n=== 変数検出開始 ===")
            print(f"現在の変数リスト: {self.variables}")
            print(f"現在の計算結果変数: {self.result_variables}")
            
            # デバッグ用に現在のタブウィジェットの情報を出力
            print(f"\nタブウィジェット情報:")
            print(f"  タブの数: {self.tab_widget.count()}")
            for i in range(self.tab_widget.count()):
                print(f"  タブ{i}: {self.tab_widget.tabText(i)}")
            
            # 変数タブの更新
            if hasattr(self, 'variables_tab'):
                print("\n変数タブの更新を実行")
                print(f"更新する変数リスト: {self.variables}")
                print(f"更新する計算結果変数: {self.result_variables}")
                
                # 変数タブの更新（全ての変数を渡す）
                self.variables_tab.update_variable_list(
                    self.variables,  # 全ての変数
                    self.result_variables  # 計算結果の変数
                )
                print("変数タブの更新完了")
            else:
                print("【警告】変数タブが見つかりません")
                
            # 不確かさ計算タブの更新
            if hasattr(self, 'uncertainty_calculation_tab'):
                print("\n不確かさ計算タブの更新を実行")
                self.uncertainty_calculation_tab.update_result_combo()
                print("不確かさ計算タブの更新完了")
            else:
                print("【警告】不確かさ計算タブが見つかりません")
                
            # レポートタブの更新
            if hasattr(self, 'report_tab'):
                print("\nレポートタブの更新を実行")
                self.report_tab.update_variable_list(
                    self.variables,
                    self.result_variables
                )
                print("レポートタブの更新完了")
            else:
                print("【警告】レポートタブが見つかりません")
                
            print("\n=== 変数検出完了 ===")
            
        except Exception as e:
            print(f"【エラー】変数検出エラー: {str(e)}\n{traceback.format_exc()}")
            self.log_error(f"変数の検出エラー: {str(e)}", "変数検出エラー")
        
    def calculate_partial_derivatives(self):
        """偏微分の計算"""
        pass  # 今後実装予定
        
    def log_error(self, message, error_type="エラー"):
        """エラーログの記録"""
        print(f"{error_type}: {message}")  # 今後、より適切なログ機構に変更予定
        
    def show_about_dialog(self):
        """Aboutダイアログを表示"""
        dialog = AboutDialog(self)
        dialog.exec_()

def main():
    app = QApplication(sys.argv)
    window = UncertaintyCalculator()
    window.show()
    sys.exit(app.exec_())
    
if __name__ == "__main__":
    main() 