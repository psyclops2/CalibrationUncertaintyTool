"""
言語管理クラス
多言語対応のための翻訳管理と言語切り替え機能を提供
"""

from PySide6.QtCore import QTranslator, QLocale, QCoreApplication
import os
from .config_loader import ConfigLoader
from .app_logger import log_debug, log_error

class LanguageManager:
    """言語管理クラス"""
    
    def __init__(self):
        """初期化"""
        self.config = ConfigLoader()
        self.translator = QTranslator()
        
        # システムロケールを使用するかどうか
        use_system_locale = self.config.config.getboolean('Language', 'use_system_locale', fallback=False)
        
        if use_system_locale:
            # システムロケールから言語を取得
            system_locale = QLocale.system().name()[:2]  # 'ja_JP' → 'ja'
            self.current_language = system_locale if system_locale in ['ja', 'en'] else 'en'
        else:
            # 設定ファイルから言語を取得
            self.current_language = self.config.config.get('Language', 'current', fallback='ja').strip().lower()
        
        # 現在の言語に基づいてQLocaleを設定
        self.locale = QLocale(self.current_language)
        QLocale.setDefault(self.locale)
    
    def load_language(self):
        """現在の言語設定に基づいて翻訳をロード"""
        log_debug(f"[DEBUG] load_language called for language: {self.current_language}")
        
        # 翻訳ファイルのパス（絶対パスで指定）
        app_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        translation_file = os.path.join(app_dir, "i18n", f"{self.current_language}.qm")
        log_debug(f"[DEBUG] Attempting to load translation file: {translation_file}")
        
        # 翻訳をロード
        if not os.path.exists(translation_file):
            log_error(f"Translation file not found: {translation_file}", error_type="DEBUG_ERROR")
            return False

        # 既存のTranslatorを一旦削除してから新しいものをロードする
        QCoreApplication.removeTranslator(self.translator)
        self.translator = QTranslator()

        if self.translator.load(translation_file):
            log_debug(f"[DEBUG] Successfully loaded translation file: {translation_file}")
            if QCoreApplication.installTranslator(self.translator):
                log_debug("[DEBUG] Translator installed successfully.")
            else:
                log_error("Failed to install translator.", error_type="DEBUG_ERROR")
            return True
        else:
            log_error(
                f"Failed to load language file (file exists but content may be invalid or unreadable): {translation_file}",
                error_type="DEBUG_ERROR",
            )
            return False
    
    def get_locale(self):
        """現在の言語のQLocaleを返す（数値フォーマット等に使用）"""
        return self.locale
    
    def change_language(self, language_code):
        """
        言語を変更して設定を保存
        
        Args:
            language_code (str): 言語コード（'ja'または'en'）
            
        Returns:
            bool: 変更が成功したかどうか
        """
        if language_code in ['ja', 'en']:
            self.current_language = language_code
            
            # 設定ファイルに保存
            if not self.config.config.has_section('Language'):
                self.config.config.add_section('Language')
            
            self.config.config.set('Language', 'current', language_code.strip())
            self.config.save_config()
            

            return True
        
        log_error(f"サポートされていない言語コード: {language_code}")
        return False
    
    def toggle_system_locale(self, use_system):
        """
        システムロケール使用の切り替え
        
        Args:
            use_system (bool): システムロケールを使用するかどうか
            
        Returns:
            bool: 変更が成功したかどうか
        """
        if not self.config.config.has_section('Language'):
            self.config.config.add_section('Language')
        
        self.config.config.set('Language', 'use_system_locale', str(use_system).lower())
        self.config.save_config()
        

        return True
