import traceback
from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QTabWidget, QMessageBox
from PyQt5.QtCore import Qt
from src.tabs.model_equation_tab import ModelEquationTab
from src.tabs.variables_tab import VariablesTab
from src.tabs.report_tab import ReportTab

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        print("\n=== MainWindow初期化 ===")
        self.variables = []  # 全ての変数のリスト（入力変数と計算結果変数の両方を含む）
        self.result_variables = []  # 計算結果の変数のリスト
        self.variable_values = {}  # 変数の値を保持する辞書
        self.last_equation = ""  # 最後に入力された方程式
        print("変数リストを初期化")
        self.setup_ui()
        
        # タブ切り替えのデバッグ用
        print("\n【デバッグ】初期タブ選択: モデル式タブ")
        self.tab_widget.setCurrentIndex(0)  # 初期状態ではモデル式タブを選択
        
    def setup_ui(self):
        """UIの設定"""
        # メインウィジェットとレイアウトの設定
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)
        
        # タブウィジェットの作成
        self.tab_widget = QTabWidget()  # タブウィジェットを保存
        
        # 各タブの作成
        self.model_equation_tab = ModelEquationTab(self)
        self.variables_tab = VariablesTab(self)  # VariablesTabを使用
        self.report_tab = ReportTab(self)  # レポートタブを追加
        
        # タブの追加
        self.tab_widget.addTab(self.model_equation_tab, "モデル式")
        self.tab_widget.addTab(self.variables_tab, "変数管理/量の値管理")  # VariablesTabを使用
        self.tab_widget.addTab(self.report_tab, "レポート")  # レポートタブを追加
        
        # タブ切り替えシグナルの接続
        print("\n【重要】タブ切り替えシグナルを接続します")
        self.tab_widget.currentChanged.disconnect() if self.tab_widget.receivers(self.tab_widget.currentChanged) > 0 else None
        self.tab_widget.currentChanged.connect(self.on_tab_changed)
        print(f"【重要】currentChangedシグナルの接続数: {self.tab_widget.receivers(self.tab_widget.currentChanged)}")
        
        layout.addWidget(self.tab_widget)
        
        # ウィンドウの設定
        self.setWindowTitle("不確かさ計算ツール")
        self.setGeometry(100, 100, 1200, 800)
        
    def on_tab_changed(self, index):
        """タブが変更された時の処理"""
        try:
            tab_name = self.tab_widget.tabText(index)
            print(f"\n【タブ切り替え】インデックス {index} : '{tab_name}' タブ")
            
            # 簡易デバッグ出力（常に表示）
            print(f"【デバッグ】MainWindowクラスの変数状態:")
            print(f"  - 変数リスト: {self.variables}")
            print(f"  - 計算結果変数: {self.result_variables}")
            print(f"  - 変数値の数: {len(self.variable_values)}")
            
            # 変数管理タブが選択された場合
            if tab_name == "変数管理/量の値管理" and hasattr(self, 'variables_tab'):
                print(f"\n【デバッグ】変数管理/量の値管理タブ選択検出")
                
                # 簡易デバッグ - 変数値の内容を表示
                for var_name in sorted(self.variables):
                    is_result = var_name in self.result_variables
                    mode = "計算結果" if is_result else "入力変数"
                    value = self.variable_values.get(var_name, {}).get('value', '未設定')
                    print(f"  - 変数: {var_name}, モード: {mode}, 値: {value}")
                
                # 変数リストを必ず更新
                if hasattr(self.variables_tab, 'update_variable_list'):
                    print("\n【デバッグ】変数リストを強制的に更新します")
                    self.variables_tab.update_variable_list(
                        self.variables,
                        self.result_variables
                    )
                    print("【デバッグ】変数リスト更新完了")
                else:
                    print("【エラー】variables_tabオブジェクトにupdate_variable_listメソッドが見つかりません")
            
            # レポートタブが選択された場合
            elif tab_name == "レポート" and hasattr(self, 'report_tab'):
                print(f"\n【デバッグ】レポートタブ選択検出")
                if hasattr(self.report_tab, 'update_variable_list'):
                    print("\n【デバッグ】レポートタブの変数リストを更新します")
                    self.report_tab.update_variable_list(
                        self.variables,
                        self.result_variables
                    )
                    print("【デバッグ】レポートタブの変数リスト更新完了")
                else:
                    print("【エラー】report_tabオブジェクトにupdate_variable_listメソッドが見つかりません")
            
        except Exception as e:
            print(f"【エラー】タブ切り替えエラー: {str(e)}")
            print(traceback.format_exc())
            self.log_error(f"タブ切り替えエラー: {str(e)}", "タブ切り替えエラー")
            
    def log_error(self, message, title="エラー"):
        """エラーメッセージを表示"""
        print(f"【エラーログ】{title}: {message}")
        QMessageBox.critical(self, title, message)
        
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
        self.tab_widget.setCurrentIndex(2)

    # ... existing code ... 