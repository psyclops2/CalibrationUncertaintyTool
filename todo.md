# 多言語対応（国際化）実装計画

## 1. 基本方針
- Qt（PySide6）の標準的な国際化機能（QTranslator）を利用
- 設定ファイル（config.ini）で言語設定を保存
- 最初は日本語と英語の2言語対応
- アプリケーション起動時（QApplication作成直後）に翻訳を適用
- 定義済みキーを使用した翻訳管理（長期的な保守性向上）

## 2. フォルダ構成
```
Uncertainty cal tool/
├── src/
│   ├── i18n/                  # 国際化関連ファイル
│   │   ├── en.ts              # 英語翻訳ソース
│   │   ├── en.qm              # コンパイル済み英語翻訳
│   │   ├── ja.ts              # 日本語翻訳ソース
│   │   └── ja.qm              # コンパイル済み日本語翻訳
│   ├── utils/
│   │   ├── language_manager.py  # 言語管理クラス
│   │   └── ...
│   └── ...
└── config.ini                 # 設定ファイル（言語設定を追加）
```

## 3. 実装ステップ

### 3.1 設定ファイルの拡張
config.iniに言語設定セクションを追加：
```ini
[Language]
current = ja  # ja:日本語, en:英語
use_system_locale = false  # システムロケールを使用するかどうか
```

### 3.2 言語管理クラスの作成
`src/utils/language_manager.py`を作成：
- 現在の言語設定の読み込み
- 言語の切り替え機能
- 翻訳ファイルのロード

### 3.3 文字列の国際化
1. **ハードコードされた文字列を置き換え**
   - 現在のコードで直接記述されている日本語文字列を`tr()`関数で置き換え
   - 例：`self.label.setText("計算結果:")` → `self.label.setText(self.tr("CALCULATION_RESULT_LABEL"))`
   - 定義済みキーを使用することで、文字列変更による翻訳漏れを防止

2. **翻訳ファイルの作成**
   - `pylupdate6`ツールを使用して.tsファイルを生成（.pyファイルと.uiファイル両方を対象に）
   - Qt Linguistで翻訳を編集
   - `lrelease`ツールで.qmファイルにコンパイル
   - バージョン管理では.tsファイルのみを管理し、.qmファイルは除外

### 3.4 言語切り替え機能の実装
- メインウィンドウに言語切り替えメニューを追加
- 言語変更時の対応（2つの選択肢）：
  1. **再起動方式**（シンプルで確実）：言語設定を保存し、アプリの再起動を促す
  2. **動的切り替え方式**（高度）：`changeEvent`で`LanguageChange`イベントを検知し、`retranslateUi()`で全UIを更新

### 3.5 数値・日付のローカライズ
- `QLocale`を使用して数値表示をローカライズ（特に小数点、桁区切り）
- 科学表記の形式を言語に合わせて調整
- 日付・時刻表示も言語に応じたフォーマットに調整

## 4. コード例

### 4.1 言語管理クラス
```python
from PySide6.QtCore import QTranslator, QLocale, QCoreApplication
from .config_loader import ConfigLoader
import os

class LanguageManager:
    def __init__(self):
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
            return True
        return False
        
    def get_locale(self):
        """現在の言語のQLocaleを返す（数値フォーマット等に使用）"""
        return self.locale
        
    def change_language(self, language_code):
        """言語を変更して設定を保存"""
        if language_code in ['ja', 'en']:
            self.current_language = language_code
            
            # 設定ファイルに保存
            if not self.config.config.has_section('Language'):
                self.config.config.add_section('Language')
            self.config.config.set('Language', 'current', language_code)
            self.config.save_config()
            
            return True
        return False
```

### 4.2 メインウィンドウでの使用例
```python
from PySide6.QtWidgets import QMainWindow, QMenu, QAction, QMessageBox
from PySide6.QtCore import QEvent
from .utils.language_manager import LanguageManager

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # 言語マネージャーの初期化
        self.language_manager = LanguageManager()
        self.language_manager.load_language()
        
        # UIの構築
        self.setup_ui()
        
        # メニューバーの設定
        self.setup_menu()
        
        # 翻訳テキストの適用
        self.retranslate_ui()
        
    def setup_ui(self):
        """UIコンポーネントの構築"""
        # ここにUIコンポーネントの構築コードを記述
        pass
        
    def retranslate_ui(self):
        """UIコンポーネントのテキストを現在の言語で更新"""
        # ここに翻訳テキストの適用コードを記述
        # 例: self.label.setText(self.tr("CALCULATION_RESULT_LABEL"))
        pass
        
    def setup_menu(self):
        menubar = self.menuBar()
        
        # 言語メニュー
        language_menu = QMenu(self.tr("LANGUAGE_MENU"), self)
        
        # 日本語アクション
        ja_action = QAction(self.tr("JAPANESE"), self)
        ja_action.triggered.connect(lambda: self.change_language('ja'))
        language_menu.addAction(ja_action)
        
        # 英語アクション
        en_action = QAction(self.tr("ENGLISH"), self)
        en_action.triggered.connect(lambda: self.change_language('en'))
        language_menu.addAction(en_action)
        
        # システムロケール使用オプション
        system_locale_action = QAction(self.tr("USE_SYSTEM_LOCALE"), self)
        system_locale_action.setCheckable(True)
        use_system = self.language_manager.config.config.getboolean('Language', 'use_system_locale', fallback=False)
        system_locale_action.setChecked(use_system)
        system_locale_action.triggered.connect(self.toggle_system_locale)
        language_menu.addAction(system_locale_action)
        
        menubar.addMenu(language_menu)
    
    def toggle_system_locale(self, checked):
        """システムロケール使用の切り替え"""
        if not self.language_manager.config.config.has_section('Language'):
            self.language_manager.config.config.add_section('Language')
        self.language_manager.config.config.set('Language', 'use_system_locale', str(checked).lower())
        self.language_manager.config.save_config()
        
        QMessageBox.information(
            self,
            self.tr("SETTINGS_CHANGED"),
            self.tr("RESTART_REQUIRED_MESSAGE")
        )
        
    def change_language(self, language_code):
        """言語を変更して再起動を促す"""
        if self.language_manager.change_language(language_code):
            QMessageBox.information(
                self,
                self.tr("LANGUAGE_SETTINGS"),
                self.tr("LANGUAGE_CHANGED_RESTART_MESSAGE")
            )
    
    def changeEvent(self, event):
        """イベント処理（言語変更イベントを検知）"""
        if event.type() == QEvent.LanguageChange:
            # 言語が変更された場合、UIテキストを更新
            self.retranslate_ui()
        super().changeEvent(event)
```

## 5. 翻訳ファイル作成手順

### 5.1 翻訳ソースファイル（.ts）の生成
1. プロジェクトルートで以下のコマンドを実行（.pyファイルと.uiファイル両方を対象に）：
```
pylupdate6 src/*.py src/*/*.py src/ui/*.ui -ts src/i18n/en.ts src/i18n/ja.ts
```

### 5.2 翻訳の編集
1. Qt Linguistをインストール
2. Qt Linguistで.tsファイルを開いて翻訳を編集
3. 各言語の翻訳を保存

### 5.3 翻訳ファイル（.qm）のコンパイル
1. 以下のコマンドを実行：
```
lrelease src/i18n/*.ts
```

## 6. 注意点
- 動的に言語を切り替える場合は、すべてのUIコンポーネントを再構築する必要がある
- 再起動を促す方法が最もシンプル
- 日付や数値のフォーマットも言語によって変更する必要がある（QLocaleを使用）
- 翻訳キーには定義済みの識別子を使用し、直接の文字列を避ける
- QTranslatorの適用はアプリケーション起動時（QApplication作成直後）に行う

## 7. 追加の考慮点

### 7.1 テスト方法の確立
- 各言語での表示確認方法
- 自動テストでの多言語対応確認
- 翻訳漏れの検出方法

### 7.2 フォントの考慮
- 日本語と英語では最適なフォントが異なる場合がある
- 特殊文字（単位記号など）の表示確認
- フォントサイズの言語ごとの調整

### 7.3 レイアウトの調整
- 英語は日本語より文字列が長くなることが多い
- 動的なレイアウト調整が必要な場合がある
- ラベルの幅や配置の自動調整

## 8. 今後の拡張
- 他の言語のサポート追加（中国語、韓国語など）
- 言語自動検出機能（システム言語に合わせる）
- 言語リソースの外部ファイル化（JSON/YAMLなど）
- 翻訳管理ツールの導入（大規模化した場合）


## 新しい項目の追加時にやったこと。
翻訳キーの追加：
LABEL_NOMINAL_VALUEをtranslation_keys.pyに追加
日本語翻訳「呼び値」をtranslations_ja.pyに追加
英語翻訳「Nominal Value」をtranslations_en.pyに追加
UI要素の追加：
変数タブの詳細設定に「呼び値」入力フィールドを追加（単位の上に配置）
入力値の変更を処理するハンドラーメソッドon_nominal_value_changedを追加
データ処理の更新：
変数の共通設定表示時に「呼び値」の値を表示するようdisplay_common_settingsメソッドを更新
JSONファイルの読み込み・保存は既存のコードで対応可能（variable_values辞書に含まれる）