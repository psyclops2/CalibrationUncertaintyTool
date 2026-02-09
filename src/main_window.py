import traceback
import copy
import os
from PySide6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QTabWidget, QMessageBox, QFileDialog, QMenuBar, QMenu
from PySide6.QtGui import QAction
from PySide6.QtCore import Qt, QEvent, Slot
import json
import decimal

from src.utils.app_logger import log_error as write_error_log

from src.tabs.document_info_tab import DocumentInfoTab
from src.tabs.model_equation_tab import ModelEquationTab
from src.tabs.variables_tab import VariablesTab
from src.tabs.regression_tab import RegressionTab
from src.tabs.uncertainty_calculation_tab import UncertaintyCalculationTab
from src.tabs.monte_carlo_tab import MonteCarloTab
from src.tabs.report_tab import ReportTab
from src.tabs.partial_derivative_tab import PartialDerivativeTab
from src.tabs.point_settings_tab import PointSettingsTab
from src.dialogs.about_dialog import AboutDialog
from src.utils.language_manager import LanguageManager

from src.utils.translation_keys import *
from src.utils.variable_utils import create_empty_value_dict, get_distribution_translation_key

class MainWindow(QMainWindow):
    def __init__(self, language_manager=None):
        super().__init__()
        
        # 言語管理の初期化
        self.language_manager = language_manager or LanguageManager()

        
        # ファイル状態
        self.current_file_path = None

        # ウィンドウの設定
        self.update_window_title()
        self.setGeometry(100, 100, 1200, 800)
        
        # アプリケーションの状態管理
        self.variables = []
        self.result_variables = []
        self.variable_values = {}
        self.last_equation = ""
        self.value_count = 1
        self.current_value_index = 0
        self.value_names = [f"{self.tr(CALIBRATION_POINT_NAME)} {i+1}" for i in range(self.value_count)]
        self.regressions = {}
        self.document_info = {
            'document_number': '',
            'document_name': '',
            'version_info': '',
            'description_markdown': '',
            'description_html': '',
            'revision_history': ''
        }
        
        # UIの初期化
        self.setup_ui()
        self.create_menu_bar()

    def set_current_file_path(self, file_path):
        """現在開いているファイルパスを設定して、タイトルを更新する"""
        self.current_file_path = file_path
        self.update_window_title()

    def update_window_title(self):
        """アプリ名の後に現在のファイル名を表示する"""
        base_title = self.tr(APP_TITLE)
        if self.current_file_path:
            self.setWindowTitle(f"{base_title} - {os.path.basename(self.current_file_path)}")
        else:
            self.setWindowTitle(base_title)
        
    def setup_ui(self):
        """UIの設定"""
        # メインウィジェットとレイアウトの設定
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)
        
        # タブウィジェットの作成
        self.tab_widget = QTabWidget()
        
        # 各タブの作成
        self.document_info_tab = DocumentInfoTab(self)
        self.model_equation_tab = ModelEquationTab(self)
        self.regression_tab = RegressionTab(self)
        self.point_settings_tab = PointSettingsTab(self)
        self.variables_tab = VariablesTab(self)
        self.uncertainty_calculation_tab = UncertaintyCalculationTab(self)
        self.monte_carlo_tab = MonteCarloTab(self)
        self.partial_derivative_tab = PartialDerivativeTab(self)
        self.report_tab = ReportTab(self)

        # タブの追加
        self.tab_widget.addTab(self.document_info_tab, self.tr(DOCUMENT_INFO_TAB))
        self.tab_widget.addTab(self.model_equation_tab, self.tr(TAB_EQUATION))
        self.tab_widget.addTab(self.regression_tab, self.tr(TAB_REGRESSION))
        self.tab_widget.addTab(self.point_settings_tab, self.tr(POINT_SETTINGS_TAB))
        self.tab_widget.addTab(self.variables_tab, self.tr(TAB_VARIABLES))
        self.tab_widget.addTab(self.uncertainty_calculation_tab, self.tr(TAB_CALCULATION))
        self.tab_widget.addTab(self.monte_carlo_tab, self.tr(TAB_MONTE_CARLO))
        self.tab_widget.addTab(self.report_tab, self.tr(TAB_REPORT))
        self.tab_widget.addTab(self.partial_derivative_tab, self.tr(PARTIAL_DERIVATIVE))
        
        # タブ切り替え時のシグナル接続
        self.tab_widget.currentChanged.connect(self.on_tab_changed)
        
        # Connect signals
        self.point_settings_tab.points_changed.connect(self.on_points_changed)
        self.document_info_tab.info_changed.connect(self.report_tab.update_report)

        layout.addWidget(self.tab_widget)

    @Slot()
    def on_points_changed(self):
        """
        Handles changes from PointSettingsTab (e.g., name edited, points added/removed).
        The `value_names` list in MainWindow is updated by the tab.
        This method propagates the changes to other tabs.
        """
        self.value_count = max(1, len(self.value_names))
        if self.current_value_index >= self.value_count:
            self.current_value_index = self.value_count - 1
        self.sync_variable_values_with_points()
        self.variables_tab.update_value_combo()
        self.uncertainty_calculation_tab.update_value_combo()
        if hasattr(self, 'monte_carlo_tab'):
            self.monte_carlo_tab.refresh_controls()
        self.report_tab.update_report()

    def update_menu_bar_text(self):
        """メニューバーのテキストを現在の言語で更新"""
        self.file_menu.setTitle(self.tr(MENU_FILE))
        self.save_action.setText(self.tr(FILE_SAVE))
        self.save_as_action.setText(self.tr(FILE_SAVE_AS))
        self.open_action.setText(self.tr(FILE_OPEN))
        self.exit_action.setText(self.tr(FILE_EXIT))
        self.language_menu.setTitle(self.tr(MENU_LANGUAGE))
        self.ja_action.setText(self.tr(LANGUAGE_JAPANESE))
        self.en_action.setText(self.tr(LANGUAGE_ENGLISH))
        self.system_locale_action.setText(self.tr(USE_SYSTEM_LOCALE))
        self.help_menu.setTitle(self.tr(MENU_HELP))
        self.about_action.setText(self.tr(ABOUT_APP))
        self.tab_widget.setTabText(0, self.tr(DOCUMENT_INFO_TAB))
        
    def create_menu_bar(self):
        """メニューバーの作成"""
        menubar = self.menuBar()
        self.file_menu = menubar.addMenu(self.tr(MENU_FILE))
        self.language_menu = menubar.addMenu(self.tr(MENU_LANGUAGE))
        self.help_menu = menubar.addMenu(self.tr(MENU_HELP))
        
        # ファイルメニュー
        self.save_action = QAction(self.tr(FILE_SAVE), self)
        self.save_action.triggered.connect(self.save_file)
        self.save_action.setShortcut("Ctrl+S")
        self.file_menu.addAction(self.save_action)

        self.save_as_action = QAction(self.tr(FILE_SAVE_AS), self)
        self.save_as_action.triggered.connect(self.save_file_as)
        self.save_as_action.setShortcut("Ctrl+Shift+S")
        self.file_menu.addAction(self.save_as_action)
        
        self.open_action = QAction(self.tr(FILE_OPEN), self)
        self.open_action.triggered.connect(self.open_file)
        self.open_action.setShortcut("Ctrl+O")
        self.file_menu.addAction(self.open_action)
        
        self.exit_action = QAction(self.tr(FILE_EXIT), self)
        self.exit_action.triggered.connect(self.close)
        self.file_menu.addAction(self.exit_action)
        
        # 言語メニュー
        self.ja_action = QAction(self.tr(LANGUAGE_JAPANESE), self)
        self.ja_action.triggered.connect(lambda: self.change_language('ja'))
        self.language_menu.addAction(self.ja_action)
        
        self.en_action = QAction(self.tr(LANGUAGE_ENGLISH), self)
        self.en_action.triggered.connect(lambda: self.change_language('en'))
        self.language_menu.addAction(self.en_action)
        
        self.system_locale_action = QAction(self.tr(USE_SYSTEM_LOCALE), self)
        self.system_locale_action.setCheckable(True)
        use_system = self.language_manager.config.config.getboolean('Language', 'use_system_locale', fallback=False)
        self.system_locale_action.setChecked(use_system)
        self.system_locale_action.triggered.connect(self.toggle_system_locale)
        self.language_menu.addAction(self.system_locale_action)
        
        # ヘルプメニュー
        self.about_action = QAction(self.tr(ABOUT_APP), self)
        self.about_action.triggered.connect(self.show_about_dialog)
        self.help_menu.addAction(self.about_action)
        
    def get_save_data(self):
        """保存するデータを辞書にまとめる"""
        # 変数タブの選択状態も保存
        last_selected_variable = None
        last_selected_value_index = 0
        if hasattr(self, 'variables_tab') and hasattr(self.variables_tab, 'handlers'):
            last_selected_variable = self.variables_tab.handlers.last_selected_variable
            last_selected_value_index = self.variables_tab.handlers.last_selected_value_index
        save_variable_values = {}
        ordered_variables = list(dict.fromkeys(self.result_variables + self.variables))
        for var_name in ordered_variables:
            var_info = self.variable_values.get(var_name)
            if not isinstance(var_info, dict):
                continue
            cleaned_info = copy.deepcopy(var_info)
            # 互換性を考慮しない方針のため、use_regression は保存しない
            cleaned_info.pop('use_regression', None)
            cleaned_info.pop('nominal_value', None)
            values = cleaned_info.get('values', [])
            if not isinstance(values, list):
                values = []
            if len(values) < self.value_count:
                values.extend(create_empty_value_dict() for _ in range(self.value_count - len(values)))
            else:
                values = values[:self.value_count]
            cleaned_info['values'] = values
            save_variable_values[var_name] = cleaned_info

        # JSON出力の順序は「データを使用するタブの並び順」に合わせる。
        # ※ JSON仕様上、objectの順序は保証されないが、保存ファイルの可読性/差分を安定させる目的で整列する。
        return {
            # DocumentInfoTab
            'document_info': self.document_info_tab.get_document_info()
            if hasattr(self, 'document_info_tab')
            else self.document_info,

            # ModelEquationTab
            'last_equation': self.last_equation,

            # RegressionTab
            'regressions': self.regressions,

            # PointSettingsTab / calibration points
            'value_count': self.value_count,
            'current_value_index': self.current_value_index,
            'value_names': self.value_names,

            # VariablesTab
            'variables': self.variables,
            'result_variables': self.result_variables,
            'variable_values': save_variable_values,
            'last_selected_variable': last_selected_variable,
            'last_selected_value_index': last_selected_value_index,
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
            self.value_names = data.get('value_names', [f"{self.tr(CALIBRATION_POINT_NAME)} {i+1}" for i in range(self.value_count)])
            self.value_count = max(1, len(self.value_names))
            self.regressions = data.get('regressions', {})
            if self.current_value_index >= self.value_count:
                self.current_value_index = self.value_count - 1
            self.document_info = data.get('document_info', self.document_info)
            if hasattr(self, 'document_info_tab'):
                self.document_info_tab.set_document_info(self.document_info)
            self.prune_variable_values()
            self.sync_variable_values_with_points()
            # 変数タブの選択状態も復元（古いデータとの互換性あり）
            last_selected_variable = data.get('last_selected_variable', None)
            last_selected_value_index = data.get('last_selected_value_index', 0)
            if hasattr(self, 'variables_tab') and hasattr(self.variables_tab, 'handlers'):
                self.variables_tab.handlers.last_selected_variable = last_selected_variable
                self.variables_tab.handlers.last_selected_value_index = last_selected_value_index
            # UIの更新
            if hasattr(self, 'variables_tab'):
                self.variables_tab.update_variable_list(self.variables, self.result_variables)
                self.variables_tab.restore_selection_state()  # 選択状態と詳細表示をリフレッシュ
            if hasattr(self, 'model_equation_tab'):
                self.model_equation_tab.set_equation(self.last_equation)
            if hasattr(self, 'regression_tab'):
                self.regression_tab.refresh_model_list()

            # 結果変数を含め、すべての変数に必須フィールドを補完
            for var in self.result_variables:
                self.ensure_variable_initialized(var, is_result=True)
            for var in self.variables:
                if var not in self.result_variables:
                    self.ensure_variable_initialized(var)
            # 分布データを翻訳キーに正規化
            # 既存のJSONファイルとの互換性のため、sourceフィールドを補完
            for var_name, var_data in self.variable_values.items():
                if not isinstance(var_data, dict):
                    continue
                distribution = var_data.get('distribution')
                if distribution:
                    normalized = get_distribution_translation_key(distribution)
                    if normalized:
                        var_data['distribution'] = normalized
                
                # sourceフィールドの補完（既存データとの互換性）
                values = var_data.get('values', [])
                if isinstance(values, list):
                    for value_info in values:
                        if not isinstance(value_info, dict):
                            continue
                        # sourceフィールドが存在しない場合は補完
                        if 'source' not in value_info:
                            value_info['source'] = 'manual'
                        # regression_idが存在しない場合はregression_modelから補完
                        if 'regression_id' not in value_info and 'regression_model' in value_info:
                            value_info['regression_id'] = value_info['regression_model']
                        # regression_x_modeが存在しない場合は'fixed'をデフォルト
                        if 'regression_x_mode' not in value_info:
                            value_info['regression_x_mode'] = 'fixed'
                        # regression_x_valueが存在しない場合はregression_xから補完
                        if 'regression_x_value' not in value_info and 'regression_x' in value_info:
                            value_info['regression_x_value'] = value_info['regression_x']
            # 不確かさ計算タブの計算・テーブル再構築
            if hasattr(self, 'uncertainty_calculation_tab'):
                self.uncertainty_calculation_tab.update_result_combo()
                self.uncertainty_calculation_tab.update_value_combo()
                # 選択状態を復元し、計算を実行
                if self.uncertainty_calculation_tab.result_combo.count() > 0:
                    self.uncertainty_calculation_tab.result_combo.setCurrentIndex(0)
                    self.uncertainty_calculation_tab.on_result_changed(self.uncertainty_calculation_tab.result_combo.currentText())
                if self.uncertainty_calculation_tab.value_combo.count() > 0:
                    self.uncertainty_calculation_tab.value_combo.setCurrentIndex(0)
                    self.uncertainty_calculation_tab.on_value_changed(0)
            if hasattr(self, 'monte_carlo_tab'):
                self.monte_carlo_tab.refresh_controls()
            # レポートタブも必ずリフレッシュ
            if hasattr(self, 'report_tab'):
                self.report_tab.update_variable_list(self.variables, self.result_variables)
                self.report_tab.update_report()
            QMessageBox.information(self, self.tr(MESSAGE_SUCCESS), self.tr(FILE_LOADED))
            
        except Exception as e:
            self.log_error(f"データ読み込みエラー: {str(e)}", "データ読み込みエラー", details=traceback.format_exc())
            QMessageBox.critical(self, self.tr(MESSAGE_ERROR), f"データの読み込みに失敗しました:\n{str(e)}")

    def _write_save_data_to_path(self, file_path):
        save_data = self.get_save_data()

        # Decimal型のみstrに変換するカスタムエンコーダ
        def decimal_default(obj):
            if isinstance(obj, decimal.Decimal):
                return str(obj)
            raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")

        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(save_data, f, indent=4, ensure_ascii=False, default=decimal_default)

    def save_file(self):
        """上書き保存（保存先が未設定の場合は「名前を付けて保存」）"""
        if not self.current_file_path:
            return self.save_file_as()

        try:
            self._write_save_data_to_path(self.current_file_path)
            QMessageBox.information(self, self.tr(MESSAGE_SUCCESS), self.tr(FILE_SAVED))
        except Exception as e:
            self.log_error(f"ファイル保存エラー: {str(e)}", "ファイル保存エラー", details=traceback.format_exc())
            QMessageBox.critical(self, self.tr(MESSAGE_ERROR), self.tr(FILE_SAVE_ERROR) + f"\n{str(e)}")

    def save_file_as(self):
        """名前を付けて保存"""
        try:
            options = QFileDialog.Options()
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                self.tr(SAVE_DIALOG_TITLE),
                "",
                "JSON Files (*.json);;All Files (*)",
                options=options
            )

            if not file_path:
                return

            self._write_save_data_to_path(file_path)
            self.set_current_file_path(file_path)
            QMessageBox.information(self, self.tr(MESSAGE_SUCCESS), self.tr(FILE_SAVED))

        except Exception as e:
            self.log_error(f"ファイル保存エラー: {str(e)}", "ファイル保存エラー", details=traceback.format_exc())
            QMessageBox.critical(self, self.tr(MESSAGE_ERROR), self.tr(FILE_SAVE_ERROR) + f"\n{str(e)}")
            
    def open_file(self):
        """ファイルを開く"""
        try:
            options = QFileDialog.Options()
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                self.tr(OPEN_DIALOG_TITLE),
                "",
                "JSON Files (*.json);;All Files (*)",
                options=options
            )
            
            if file_path:
                with open(file_path, 'r', encoding='utf-8') as f:
                    loaded_data = json.load(f)
                self.load_data(loaded_data)
                self.set_current_file_path(file_path)
                
        except FileNotFoundError:
            QMessageBox.critical(self, self.tr(MESSAGE_ERROR), self.tr(FILE_NOT_FOUND))
        except json.JSONDecodeError:
            QMessageBox.critical(self, self.tr(MESSAGE_ERROR), self.tr(INVALID_FILE_FORMAT))
        except Exception as e:
            self.log_error(f"ファイル読み込みエラー: {str(e)}", "ファイル読み込みエラー", details=traceback.format_exc())
            QMessageBox.critical(self, self.tr(MESSAGE_ERROR), self.tr(FILE_LOAD_ERROR) + f"\n{str(e)}")
            
    def on_tab_changed(self, index):
        """タブが切り替えられたときの処理"""
        if index == 5:  # 不確かさ計算タブ
            self.uncertainty_calculation_tab.update_result_combo()
            self.uncertainty_calculation_tab.update_value_combo()
        elif index == 6:
            if hasattr(self, 'monte_carlo_tab'):
                self.monte_carlo_tab.refresh_controls()
        elif index == 7:
            if hasattr(self, 'report_tab'):
                self.report_tab.update_variable_list(self.variables, self.result_variables)
                self.report_tab.update_report()
        elif index == 8:
            self.partial_derivative_tab.update_equation_display()
        elif index == 6:  # レポートタブ
            if hasattr(self, 'report_tab'):
                self.report_tab.update_variable_list(self.variables, self.result_variables)
                self.report_tab.update_report()
        elif index == 7:  # 偏微分タブ
            self.partial_derivative_tab.update_equation_display()
        elif index == 4:  # 変数タブ（indexはタブ順に応じて調整）
            if hasattr(self, 'variables_tab'):
                self.variables_tab.restore_selection_state()
            
    def add_variable(self, var_name):
        """変数を追加"""
        if var_name not in self.variables:
            self.variables.append(var_name)
            self.ensure_variable_initialized(var_name)
            self.variables_tab.update_variable_list(self.variables, [])
            
    def remove_variable(self, var_name):
        """変数を削除"""
        if var_name in self.variables:
            self.variables.remove(var_name)
            if var_name in self.variable_values:
                del self.variable_values[var_name]
            self.variables_tab.update_variable_list(self.variables, [])

    def ensure_variable_initialized(self, var_name, is_result=False):
        """変数用の辞書を初期化（単位を含む）"""
        if var_name not in self.variable_values or not isinstance(self.variable_values[var_name], dict):
            self.variable_values[var_name] = {}

        var_info = self.variable_values[var_name]

        # 基本フィールドの初期化
        var_info.setdefault('unit', '')
        var_info.setdefault('definition', '')

        # 既存のタイプを尊重しつつ、結果変数であれば'result'を設定
        if is_result:
            var_info['type'] = 'result'
        else:
            var_info.setdefault('type', 'A')

        # values リストを校正点数に合わせて初期化
        values = var_info.get('values', [])
        if not isinstance(values, list):
            values = []
        required_values = max(1, getattr(self, 'value_count', 1))
        if len(values) < required_values:
            values.extend(create_empty_value_dict() for _ in range(required_values - len(values)))
        var_info['values'] = values

        self.variable_values[var_name] = var_info
        return var_info

    def sync_variable_values_with_points(self):
        """校正点数に合わせて変数の値リストを整合させる"""
        required_values = max(1, getattr(self, 'value_count', 1))
        for var_name, var_info in self.variable_values.items():
            if not isinstance(var_info, dict):
                continue
            values = var_info.get('values', [])
            if not isinstance(values, list):
                values = []
            if len(values) < required_values:
                values.extend(create_empty_value_dict() for _ in range(required_values - len(values)))
            elif len(values) > required_values:
                values = values[:required_values]
            var_info['values'] = values

    def prune_variable_values(self):
        """現在の変数リストにない値データを削除する"""
        active_variables = set(self.variables) | set(self.result_variables)
        stale_keys = [key for key in self.variable_values.keys() if key not in active_variables]
        for key in stale_keys:
            del self.variable_values[key]
            
    def detect_variables(self):
        """変数の検出と変数タブの更新"""
        try:
            self.prune_variable_values()
            if hasattr(self, 'variables_tab'):
                self.variables_tab.update_variable_list(
                    self.variables,
                    self.result_variables
                )
            if hasattr(self, 'uncertainty_calculation_tab'):
                self.uncertainty_calculation_tab.update_result_combo()
            if hasattr(self, 'monte_carlo_tab'):
                self.monte_carlo_tab.refresh_controls()
            if hasattr(self, 'report_tab'):
                self.report_tab.update_variable_list(
                    self.variables,
                    self.result_variables
                )
        except Exception as e:
            self.log_error(f"変数の検出エラー: {str(e)}", "変数検出エラー", details=traceback.format_exc())
             
    def show_about_dialog(self):
        """Aboutダイアログを表示"""
        dialog = AboutDialog(self)
        dialog.exec_()
        
    def log_error(self, message, error_type="エラー", details=None):
        """エラーログの記録"""
        write_error_log(message, error_type, details=details)
        
    def change_language(self, language_code):
        """言語を動的に変更する"""
        # システムロケールの使用をオフにする
        self.language_manager.toggle_system_locale(False)
        self.system_locale_action.setChecked(False)
        
        if self.language_manager.change_language(language_code):
            # 新しい言語をロード
            self.language_manager.load_language()
            # UIを再翻訳
            self.retranslate_ui()
    
    def toggle_system_locale(self, checked):
        """システムロケール使用の切り替え"""
        self.language_manager.toggle_system_locale(checked)
        # 新しい設定で言語をロード
        self.language_manager.load_language()
        # UIを再翻訳
        self.retranslate_ui()
    

    
    def changeEvent(self, event):
        """イベント処理（言語変更イベントを検知）"""
        if event.type() == QEvent.LanguageChange:
            self.retranslate_ui()
        super().changeEvent(event)
    
    def retranslate_ui(self):
        """UIのテキストを現在の言語で更新"""
        # ウィンドウタイトル
        self.update_window_title()
        
        # タブのタイトル
        self.tab_widget.setTabText(0, self.tr(DOCUMENT_INFO_TAB))
        self.tab_widget.setTabText(1, self.tr(TAB_EQUATION))
        self.tab_widget.setTabText(2, self.tr(TAB_REGRESSION))
        self.tab_widget.setTabText(3, self.tr(POINT_SETTINGS_TAB))
        self.tab_widget.setTabText(4, self.tr(TAB_VARIABLES))
        self.tab_widget.setTabText(5, self.tr(TAB_CALCULATION))
        self.tab_widget.setTabText(6, self.tr(TAB_MONTE_CARLO))
        self.tab_widget.setTabText(7, self.tr(TAB_REPORT))
        self.tab_widget.setTabText(8, self.tr(PARTIAL_DERIVATIVE))

        # 各タブのUIテキストを更新
        if hasattr(self, 'document_info_tab') and hasattr(self.document_info_tab, 'retranslate_ui'):
            self.document_info_tab.retranslate_ui()

        if hasattr(self, 'model_equation_tab') and hasattr(self.model_equation_tab, 'retranslate_ui'):
            self.model_equation_tab.retranslate_ui()
            
        if hasattr(self, 'variables_tab') and hasattr(self.variables_tab, 'retranslate_ui'):
            self.variables_tab.retranslate_ui()

        if hasattr(self, 'regression_tab') and hasattr(self.regression_tab, 'retranslate_ui'):
            self.regression_tab.retranslate_ui()
            
        if hasattr(self, 'uncertainty_calculation_tab') and hasattr(self.uncertainty_calculation_tab, 'retranslate_ui'):
            self.uncertainty_calculation_tab.retranslate_ui()

        if hasattr(self, 'monte_carlo_tab') and hasattr(self.monte_carlo_tab, 'retranslate_ui'):
            self.monte_carlo_tab.retranslate_ui()
            
        if hasattr(self, 'partial_derivative_tab') and hasattr(self.partial_derivative_tab, 'retranslate_ui'):
            self.partial_derivative_tab.retranslate_ui()
            
        if hasattr(self, 'report_tab') and hasattr(self.report_tab, 'retranslate_ui'):
            self.report_tab.retranslate_ui()

        if hasattr(self, 'point_settings_tab') and hasattr(self.point_settings_tab, 'retranslate_ui'):
            self.point_settings_tab.retranslate_ui()
        
        # メニューバーの更新
        self.update_menu_bar_text()

    def select_model_equation_tab(self):
        """モデル式タブを選択"""

        self.tab_widget.setCurrentIndex(1)
        
    def select_variables_tab(self):
        """変数管理タブを選択"""
        self.tab_widget.setCurrentIndex(4)
        
    def select_report_tab(self):
        """レポートタブを選択"""
        self.tab_widget.setCurrentIndex(7)

    # ... existing code ... 
