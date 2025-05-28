"""
トランスレータークラス
翻訳辞書を使って文字列の翻訳を行う
"""

from .translations_ja import translations as ja_translations
from .translations_en import translations as en_translations

class Translator:
    """トランスレータークラス"""
    
    def __init__(self, language='ja'):
        """
        初期化
        
        Args:
            language (str): 言語コード（'ja'または'en'）
        """
        self.language = language
        self.translations = {
            'ja': ja_translations,
            'en': en_translations
        }
    
    def set_language(self, language):
        """
        言語を設定
        
        Args:
            language (str): 言語コード（'ja'または'en'）
            
        Returns:
            bool: 設定が成功したかどうか
        """
        if language in self.translations:
            self.language = language
            return True
        return False
    
    def translate(self, key, default=None):
        """
        キーに対応する翻訳を取得
        
        Args:
            key (str): 翻訳キー
            default (str, optional): キーが見つからない場合のデフォルト値
            
        Returns:
            str: 翻訳された文字列
        """
        # 現在の言語の翻訳辞書を取得
        current_translations = self.translations.get(self.language, {})
        
        # キーに対応する翻訳を取得
        translation = current_translations.get(key)
        
        # 翻訳が見つからない場合
        if translation is None:
            # デフォルト値が指定されている場合はそれを返す
            if default is not None:
                return default
            
            # デフォルト値が指定されていない場合はキーをそのまま返す
            return key
        
        return translation
