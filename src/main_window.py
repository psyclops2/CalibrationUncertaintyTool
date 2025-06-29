import traceback
from PySide6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QTabWidget, QMessageBox, QFileDialog, QMenuBar, QMenu
from PySide6.QtGui import QAction
from PySide6.QtCore import Qt, QEvent, Slot
import json

from src.tabs.model_equation_tab import ModelEquationTab
from src.tabs.variables_tab import VariablesTab
from src.tabs.uncertainty_calculation_tab import UncertaintyCalculationTab
from src.tabs.report_tab import ReportTab
from src.tabs.partial_derivative_tab import PartialDerivativeTab
from src.tabs.point_settings_tab import PointSettingsTab
from src.dialogs.about_dialog import AboutDialog
from src.utils.language_manager import LanguageManager
from src.i18n.translator import Translator
from src.utils.translation_keys import *

class MainWindow(QMainWindow):
    def __init__(self, language_manager=None):
        super().__init__()
        
        # 言語管理の初期化
        self.language_manager = language_manager or LanguageManager()
        self.translator = Translator(self.language_manager.current_language)
        
        # ウィンドウの設定
        self.setWindowTitle(self.tr(APP_TITLE))
        self.setGeometry(100, 100, 1200, 800)
        
        # アプリケーションの状態管理
        self.variables = []
        self.result_variables = []
        self.variable_values = {}
        self.last_equation = ""
        self.value_count = 1
        self.current_value_index = 0
        self.value_names = [f"校正点 {i+1}" for i in range(self.value_count)]
        
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
        self.point_settings_tab = PointSettingsTab(self)
        
        # タブの追加
        self.tab_widget.addTab(self.model_equation_tab, self.tr(TAB_EQUATION))
        self.tab_widget.addTab(self.variables_tab, self.tr(TAB_VARIABLES))
        self.tab_widget.addTab(self.uncertainty_calculation_tab, self.tr(TAB_CALCULATION))
        self.tab_widget.addTab(self.report_tab, self.tr(TAB_REPORT))
        self.tab_widget.addTab(self.partial_derivative_tab, self.tr(PARTIAL_DERIVATIVE))
        self.tab_widget.addTab(self.point_settings_tab, self.tr(POINT_SETTINGS_TAB))
        
        # タブ切り替え時のシグナル接続
        self.tab_widget.currentChanged.connect(self.on_tab_changed)
        
        # Connect signals
        self.point_settings_tab.points_changed.connect(self.on_points_changed)
        self.point_settings_tab.point_count_changed.connect(self.on_value_count_changed)
        
        layout.addWidget(self.tab_widget)

    @Slot()
    def on_points_changed(self):
        """
        Handles changes from PointSettingsTab (e.g., name edited).
        The `value_names` list in MainWindow is assumed to be updated by the tab.
        This method propagates the changes to other tabs.
        """
        self.variables_tab.update_value_combo()
        self.uncertainty_calculation_tab.update_value_combo()
        self.report_tab.update_report()

    @Slot(int)
    def on_value_count_changed(self, new_count):
        """
        Handles changes in the number of calibration points from the PointSettingsTab.
        """
        if self.value_count == new_count:
            return

        self.value_count = new_count
        
        # Adjust the length of the value_names list
        current_len = len(self.value_names)
        if new_count > current_len:
            # Add new default names for the new points
            for i in range(current_len, new_count):
                self.value_names.append(f"校正点 {i + 1}")
        else:
            # Truncate the list if points were removed
            self.value_names = self.value_names[:new_count]

        # Notify other tabs about the change
        self.variables_tab.on_parent_value_count_changed(new_count)
        self.uncertainty_calculation_tab.update_value_combo()
        self.report_tab.update_report()
        
    def create_menu_bar(self):
        """メニューバーの作成"""
        menubar = self.menuBar()
        
        # ファイルメニュー
        file_menu = menubar.addMenu(self.tr(MENU_FILE))
        
        # 保存アクション
        save_action = QAction(self.tr(FILE_SAVE_AS), self)
        save_action.triggered.connect(self.save_file)
        file_menu.addAction(save_action)
        
        # 開くアクション
        open_action = QAction(self.tr(FILE_OPEN), self)
        open_action.triggered.connect(self.open_file)
        file_menu.addAction(open_action)
        
        # 終了アクション
        exit_action = QAction(self.tr(FILE_EXIT), self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # 言語メニュー
        language_menu = menubar.addMenu(self.tr(MENU_LANGUAGE))
        
        # 日本語アクション
        ja_action = QAction(self.tr(LANGUAGE_JAPANESE), self)
        ja_action.triggered.connect(lambda: self.change_language('ja'))
        language_menu.addAction(ja_action)
        
        # 英語アクション
        en_action = QAction(self.tr(LANGUAGE_ENGLISH), self)
        en_action.triggered.connect(lambda: self.change_language('en'))
        language_menu.addAction(en_action)
        
        # システムロケール使用オプション
        system_locale_action = QAction(self.tr(USE_SYSTEM_LOCALE), self)
        system_locale_action.setCheckable(True)
        use_system = self.language_manager.config.config.getboolean('Language', 'use_system_locale', fallback=False)
        system_locale_action.setChecked(use_system)
        system_locale_action.triggered.connect(self.toggle_system_locale)
        language_menu.addAction(system_locale_action)
        
        # ヘルプメニュー
        help_menu = menubar.addMenu(self.tr(MENU_HELP))
        
        # Aboutアクション
        about_action = QAction(self.tr('About'), self)
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
            'current_value_index': self.current_value_index,
            'value_names': self.value_names
        }
        
    def load_data(self, data):
        """読み込んだデータでアプリケーションの状態を更新"""
        try:
            self.variables = data.get('variables', [])
            self.result_variables = data.get('result_variables', [])
            self.variable_values = data.get('variable_values', {})
            self.last_equation = data.get('last_equation', "")
            self.value_count = data.get('value_count', 1)
            self.current_value_index = data.get('current_value_index', 0)
            self.value_names = data.get('value_names', [f"校正点 {i+1}" for i in range(self.value_count)])
            
            # UIの更新
            if hasattr(self, 'variables_tab'):
                self.variables_tab.update_variable_list(self.variables, self.result_variables)
            if hasattr(self, 'model_equation_tab'):
                self.model_equation_tab.set_equation(self.last_equation)
                
            QMessageBox.information(self, self.tr("成功"), self.tr("ファイルを読み込みました。"))
            
        except Exception as e:
            print(f"【エラー】データ読み込みエラー: {str(e)}")
            print(traceback.format_exc())
            QMessageBox.critical(self, self.tr("エラー"), f"データの読み込みに失敗しました:\n{str(e)}")
            
    def save_file(self):
        """ファイルを保存"""
        try:
            options = QFileDialog.Options()
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                self.tr("名前を付けて保存"),
                "",
                "JSON Files (*.json);;All Files (*)",
                options=options
            )
            
            if file_path:
                save_data = self.get_save_data()
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(save_data, f, indent=4, ensure_ascii=False)
                QMessageBox.information(self, self.tr("成功"), self.tr("ファイルを保存しました。"))
                
        except Exception as e:
            print(f"【エラー】ファイル保存エラー: {str(e)}")
            print(traceback.format_exc())
            QMessageBox.critical(self, self.tr("エラー"), f"ファイルの保存に失敗しました:\n{str(e)}")
            
    def open_file(self):
        """ファイルを開く"""
        try:
            options = QFileDialog.Options()
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                self.tr("開く"),
                "",
                "JSON Files (*.json);;All Files (*)",
                options=options
            )
            
            if file_path:
                with open(file_path, 'r', encoding='utf-8') as f:
                    loaded_data = json.load(f)
                self.load_data(loaded_data)
                
        except FileNotFoundError:
            QMessageBox.critical(self, self.tr("エラー"), self.tr("ファイルが見つかりません。"))
        except json.JSONDecodeError:
            QMessageBox.critical(self, self.tr("エラー"), self.tr("ファイル形式が正しくありません。JSONファイルを選択してください。"))
        except Exception as e:
            print(f"【エラー】ファイル読み込みエラー: {str(e)}")
            print(traceback.format_exc())
            QMessageBox.critical(self, self.tr("エラー"), f"ファイルの読み込みに失敗しました:\n{str(e)}")
            
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
        
    def change_language(self, language_code):
        """言語を変更して再起動を促す"""
        if self.language_manager.change_language(language_code):
            QMessageBox.information(
                self,
                self.tr(LANGUAGE_SETTINGS),
                self.tr(LANGUAGE_CHANGED_RESTART_MESSAGE)
            )
    
    def toggle_system_locale(self, checked):
        """システムロケール使用の切り替え"""
        if not self.language_manager.config.config.has_section('Language'):
            self.language_manager.config.config.add_section('Language')
        self.language_manager.config.config.set('Language', 'use_system_locale', str(checked).lower())
        self.language_manager.config.save_config()
        
        QMessageBox.information(
            self,
            self.tr(LANGUAGE_SETTINGS),
            self.tr(RESTART_REQUIRED)
        )
    
    def tr(self, key):
        """翻訳キーに対応する文字列を取得"""
        return self.translator.translate(key, key)
    
    def changeEvent(self, event):
        """イベント処理（言語変更イベントを検知）"""
        if event.type() == QEvent.LanguageChange:
            self.retranslate_ui()
        super().changeEvent(event)
    
    def retranslate_ui(self):
        """UIのテキストを現在の言語で更新"""
        # ウィンドウタイトル
        self.setWindowTitle(self.tr(APP_TITLE))
        
        # タブのタイトル
        self.tab_widget.setTabText(0, self.tr(TAB_EQUATION))
        self.tab_widget.setTabText(1, self.tr(TAB_VARIABLES))
        self.tab_widget.setTabText(2, self.tr(TAB_CALCULATION))
        self.tab_widget.setTabText(3, self.tr(TAB_REPORT))
        self.tab_widget.setTabText(4, self.tr(PARTIAL_DERIVATIVE))
        
        # 各タブのUIテキストを更新
        if hasattr(self, 'model_equation_tab') and hasattr(self.model_equation_tab, 'retranslate_ui'):
            self.model_equation_tab.retranslate_ui()
            
        if hasattr(self, 'variables_tab') and hasattr(self.variables_tab, 'retranslate_ui'):
            self.variables_tab.retranslate_ui()
            
        if hasattr(self, 'uncertainty_calculation_tab') and hasattr(self.uncertainty_calculation_tab, 'retranslate_ui'):
            self.uncertainty_calculation_tab.retranslate_ui()
            
        if hasattr(self, 'partial_derivative_tab') and hasattr(self.partial_derivative_tab, 'retranslate_ui'):
            self.partial_derivative_tab.retranslate_ui()
            
        if hasattr(self, 'report_tab') and hasattr(self.report_tab, 'retranslate_ui'):
            self.report_tab.retranslate_ui()
        
        # メニューバーの更新
        self.create_menu_bar()

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