"""
日本語翻訳ファイル
"""

from ..utils.translation_keys import *

# 翻訳辞書
translations = {
    "MainWindow": {
        # アプリケーション全般
        APP_TITLE: "校正の不確かさ計算ツール",
        
        # メニュー関連
        MENU_FILE: "ファイル",
        MENU_EDIT: "編集",
        MENU_VIEW: "表示",
        MENU_LANGUAGE: "言語",
        MENU_HELP: "ヘルプ",
        ABOUT_APP: "アプリについて",

        # ファイルメニューアクション
        FILE_OPEN: "開く...",
        FILE_SAVE_AS: "名前を付けて保存...",
        FILE_EXIT: "終了",
        
        # ダイアログ
        SAVE_DIALOG_TITLE: "名前を付けて保存",
        OPEN_DIALOG_TITLE: "ファイルを開く",
        
        # 言語関連
        LANGUAGE_JAPANESE: "日本語",
        LANGUAGE_ENGLISH: "英語",
        LANGUAGE_SETTINGS: "言語設定",
        LANGUAGE_CHANGED: "言語が変更されました",
        USE_SYSTEM_LOCALE: "システムの言語を使用",
        RESTART_REQUIRED: "再起動が必要です",
        LANGUAGE_CHANGED_RESTART_MESSAGE: "言語設定を変更しました。\n変更を適用するにはアプリケーションを再起動してください。",
        
        # タブ名 (MainWindowで設定)
        TAB_EQUATION: "モデル式",
        TAB_VARIABLES: "変数管理",
        TAB_CALCULATION: "不確かさ計算",
        TAB_REPORT: "レポート",
        PARTIAL_DERIVATIVE: "偏微分",
        POINT_SETTINGS_TAB: "校正点設定",
        DOCUMENT_INFO_TAB: "文書情報",

        # 一般的なボタン
        BUTTON_SAVE: "保存",
        BUTTON_CANCEL: "キャンセル",

        # メッセージ
        MESSAGE_SUCCESS: "成功",
        FILE_LOADED: "ファイルを読み込みました。",
        FILE_SAVED: "ファイルを保存しました。",
        FILE_LOAD_ERROR: "ファイルの読み込みに失敗しました。",
        FILE_NOT_FOUND: "ファイルが見つかりません。",
        INVALID_FILE_FORMAT: "無効なファイル形式です。",
        ERROR_OCCURRED: "エラーが発生しました。",
        
        # 校正点名
        CALIBRATION_POINT_NAME: "校正点",
    },
    "ModelEquationTab": {
        MODEL_EQUATION_INPUT: "数式モデル入力",
        EQUATION_PLACEHOLDER: "例: y = a * x + b",
        VARIABLE_LIST_DRAG_DROP: "変数リスト（ドラッグドロップで順序変更）",
        HTML_DISPLAY: "HTML表示",
        VARIABLE_ORDER_UPDATE_FAILED: "変数の並び順の更新に失敗しました。",
        VARIABLE_ORDER_SAVE_FAILED: "変数の並び順の保存に失敗しました。",
        VARIABLE_ORDER_LOAD_FAILED: "変数の並び順の読み込みに失敗しました。",
    },
    "DocumentInfoTab": {
        DOCUMENT_NUMBER: "文書番号",
        DOCUMENT_NAME: "文書名",
        VERSION_INFO: "バージョン情報",
        DESCRIPTION_LABEL: "説明文 (Markdownのみ)",
        REVISION_HISTORY: "改訂履歴",
        REVISION_HISTORY_PLACEHOLDER: "v1,説明文,作成者,照査者,承認者,2024-01-01",
        REVISION_HISTORY_INSTRUCTION: "各行を「ver,説明文,作成者,照査者,承認者,改定日」の形式で入力してください。",
    },
    "VariablesTab": {
        CALIBRATION_POINT_SETTINGS: "校正点設定",
        CALIBRATION_POINT_COUNT: "校正点数",
        CALIBRATION_POINT_SELECTION: "校正点の選択",
        VARIABLE_LIST_AND_VALUES: "変数リスト/量の値",
        VARIABLE_MODE: "変数モード",
        NOT_SELECTED: "未選択",
        VARIABLE_DETAIL_SETTINGS: "変数の詳細設定",
        UNIT: "単位",
        DEFINITION: "定義",
        UNCERTAINTY_TYPE: "不確かさのタイプ",
        TYPE_A: "タイプA",
        TYPE_B: "タイプB",
        FIXED_VALUE: "固定値",
        MEASUREMENT_VALUES: "測定値",
        MEASUREMENT_VALUES_PLACEHOLDER: "カンマ区切りで値を入力 (例: 1.2, 1.3, 1.4)",
        DEGREES_OF_FREEDOM: "自由度",
        CENTRAL_VALUE: "中央値",
        STANDARD_UNCERTAINTY: "標準不確かさ",
        DETAIL_DESCRIPTION: "詳細説明",
        DISTRIBUTION: "分布",
        NORMAL_DISTRIBUTION: "Normal Distribution",
        RECTANGULAR_DISTRIBUTION: "Rectangular Distribution",
        TRIANGULAR_DISTRIBUTION: "Triangular Distribution",
        U_DISTRIBUTION: "U-shaped Distribution",
        DIVISOR: "除数",
        HALF_WIDTH: "半値幅",
        CALCULATION_FORMULA: "計算式",
        CALCULATE: "計算",
        BUTTON_ADD: "追加",
        BUTTON_EDIT: "編集",
        BUTTON_DELETE: "削除",
        LABEL_UNIT: "単位",
    },
    "PointSettingsTab": {
        POINT_SETTINGS_TAB_INFO: "各校正点の名称を設定します。校正点の追加・削除も可能です。",
        INDEX: "インデックス",
        POINT_NAME: "校正点名",
        ADD_POINT: "点を追加",
        REMOVE_POINT: "点を削除",
    },
    "UncertaintyCalculationTab": {
        RESULT_SELECTION: "計算結果選択",
        RESULT_VARIABLE: "計算対象の変数",
        CALIBRATION_POINT: "校正点",
        CALIBRATION_VALUE: "校正値",
        VARIABLE: "変数",
        CENTRAL_VALUE: "中央値",
        STANDARD_UNCERTAINTY: "標準不確かさ",
        DEGREES_OF_FREEDOM: "自由度",
        DISTRIBUTION: "分布",
        SENSITIVITY_COEFFICIENT: "感度係数",
        CONTRIBUTION_UNCERTAINTY: "寄与不確かさ",
        CONTRIBUTION_RATE: "寄与率",
        CALCULATION_RESULT: "計算結果",
        COMBINED_STANDARD_UNCERTAINTY: "合成標準不確かさ",
        EFFECTIVE_DEGREES_OF_FREEDOM: "有効自由度",
        COVERAGE_FACTOR: "包含係数",
        EXPANDED_UNCERTAINTY: "拡張不確かさ",
    },
    "ReportTab": {
        # UI elements
        RESULT_VARIABLE: "計算対象の変数",
        GENERATE_REPORT: "レポート生成",
        SAVE_REPORT: "レポート保存",
        
        # save_report dialog
        SAVE_REPORT_DIALOG_TITLE: "レポートを保存",
        HTML_FILE: "HTMLファイル",
        SAVE_CANCELLED: "保存がキャンセルされました。",
        SAVE_SUCCESS: "成功",
        REPORT_SAVED: "レポートを保存しました。",
        SAVE_ERROR: "保存エラー",
        REPORT_SAVE_ERROR: "レポートの保存中にエラーが発生しました。",
        FILE_SAVE_ERROR: "ファイルの保存中にエラーが発生しました。",

        # HTML Report Title
        REPORT_TITLE_HTML: "校正不確かさ計算レポート",
        REPORT_DOCUMENT_INFO: "文書情報",

        # HTML Section Titles
        REPORT_MODEL_EQUATION: "数式モデル",
        REPORT_VARIABLE_LIST: "変数一覧",
        REPORT_VARIABLE_DETAILS: "各変数の詳細",
        REPORT_MEASUREMENT_VALUES: "測定値",
        REPORT_UNCERTAINTY_BUDGET: "不確かさのバジェット",
        REPORT_CALCULATION_RESULT: "計算結果",
        REPORT_REVISION_HISTORY: "改訂履歴",

        # HTML Table Headers
        REPORT_QUANTITY: "量",
        REPORT_UNIT: "単位",
        REPORT_DEFINITION: "定義",
        REPORT_UNCERTAINTY_TYPE: "不確かさの種類",
        REPORT_MEASUREMENT_NUMBER: "測定回数",
        REPORT_VALUE: "値",
        REPORT_FACTOR: "要因",
        REPORT_CENTRAL_VALUE: "中央値",
        REPORT_STANDARD_UNCERTAINTY: "標準不確かさ",
        REPORT_DOF: "自由度",
        REPORT_DISTRIBUTION: "分布",
        REPORT_SENSITIVITY: "感度係数",
        REPORT_CONTRIBUTION: "寄与(不確かさ)",
        REPORT_CONTRIBUTION_RATE: "寄与率(%)",
        REPORT_ITEM: "項目",
        DOCUMENT_NUMBER: "文書番号",
        DOCUMENT_NAME: "文書名",
        VERSION_INFO: "バージョン情報",
        DESCRIPTION_LABEL: "説明",
        REVISION_VERSION: "版",
        REVISION_DESCRIPTION: "説明",
        REVISION_AUTHOR: "作成者",
        REVISION_CHECKER: "照査者",
        REVISION_APPROVER: "承認者",
        REVISION_DATE: "改定日",

        # Variable details
        DETAIL_DESCRIPTION: "詳細説明",
        HALF_WIDTH: "半値幅",
        DISTRIBUTION: "分布",
        FIXED_VALUE: "固定値",
        NORMAL_DISTRIBUTION: "Normal Distribution",
        RECTANGULAR_DISTRIBUTION: "Rectangular Distribution",
        TRIANGULAR_DISTRIBUTION: "Triangular Distribution",
        U_DISTRIBUTION: "U-shaped Distribution",

        # HTML Calculation Result Items
        REPORT_CALIBRATION_POINT: "校正点",
        REPORT_EQUATION: "計算式",
        REPORT_COMBINED_UNCERTAINTY: "合成標準不確かさ",
        REPORT_EFFECTIVE_DOF: "有効自由度",
        REPORT_COVERAGE_FACTOR: "包含係数 k",
        REPORT_EXPANDED_UNCERTAINTY: "拡張不確かさ U",

        # get_uncertainty_type_display
        CALCULATION_RESULT_DISPLAY: "計算結果",
        TYPE_A_DISPLAY: "タイプA",
        TYPE_B_DISPLAY: "タイプB",
        FIXED_VALUE_DISPLAY: "固定値",
        UNKNOWN_TYPE: "不明",

        # Error messages
        HTML_GENERATION_ERROR: "レポート生成中にエラーが発生しました",
    },
    "PartialDerivativeTab": {
        PARTIAL_DERIVATIVE_TITLE: "偏微分",
        LABEL_EQUATION: "数式",
        DERIVATIVE_VARIABLE: "微分する変数",
        DERIVATIVE_RESULT: "微分結果",
        CALCULATE_DERIVATIVE: "微分を計算",
        DERIVATIVE_CALCULATION_ERROR: "微分計算エラー",
        DERIVATIVE_CALCULATION_SUCCESS: "微分計算成功",
        DERIVATIVE_EXPRESSION: "微分表現",
    },
}
