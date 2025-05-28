"""
言語管理クラス
多言語対応のための翻訳管理と言語切り替え機能を提供
"""

from PySide6.QtCore import QTranslator, QLocale, QCoreApplication
import os
from .config_loader import ConfigLoader

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
            self.current_language = self.config.config.get('Language', 'current', fallback='ja')
        
        # 現在の言語に基づいてQLocaleを設定
        self.locale = QLocale(self.current_language)
        QLocale.setDefault(self.locale)
    
    def load_language(self):
        """現在の言語設定に基づいて翻訳をロード"""
        # 翻訳ファイルのパス（絶対パスで指定）
        app_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        translation_file = os.path.join(app_dir, f"i18n/{self.current_language}.qm")
        
        # 翻訳をロード
        if self.translator.load(translation_file):
            QCoreApplication.installTranslator(self.translator)
            print(f"【デバッグ】言語ファイルをロードしました: {translation_file}")
            return True
        else:
            print(f"【エラー】言語ファイルのロードに失敗しました: {translation_file}")
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
            
            self.config.config.set('Language', 'current', language_code)
            self.config.save_config()
            
            print(f"【デバッグ】言語を変更しました: {language_code}")
            return True
        
        print(f"【エラー】サポートされていない言語コード: {language_code}")
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
        
        print(f"【デバッグ】システムロケール使用設定を変更しました: {use_system}")
        return True
