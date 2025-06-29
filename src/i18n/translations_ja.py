"""
日本語翻訳ファイル
"""

from ..utils.translation_keys import *

# 翻訳辞書
translations = {
    # アプリケーション全般
    APP_TITLE: "校正の不確かさ計算ツール",
    
    # メニュー関連
    MENU_FILE: "ファイル",
    MENU_EDIT: "編集",
    MENU_VIEW: "表示",
    MENU_LANGUAGE: "言語",
    MENU_HELP: "ヘルプ",
    
    # ファイルメニューアクション
    FILE_SAVE_AS: "名前を付けて保存...",
    FILE_OPEN: "開く...",
    FILE_EXIT: "終了",
    
    # 言語関連
    LANGUAGE_JAPANESE: "日本語",
    LANGUAGE_ENGLISH: "英語",
    LANGUAGE_SETTINGS: "言語設定",
    LANGUAGE_CHANGED: "言語が変更されました",
    USE_SYSTEM_LOCALE: "システムの言語を使用",
    RESTART_REQUIRED: "再起動が必要です",
    LANGUAGE_CHANGED_RESTART_MESSAGE: "言語設定を変更しました。\n変更を適用するにはアプリケーションを再起動してください。",
    
    # タブ名
    TAB_EQUATION: "モデル式",
    TAB_VARIABLES: "変数管理/量の値管理",
    TAB_CALCULATION: "計算",
    TAB_REPORT: "レポート",
    PARTIAL_DERIVATIVE: "偏微分",
    
    # ボタン
    BUTTON_ADD: "追加",
    BUTTON_EDIT: "編集",
    BUTTON_DELETE: "削除",
    BUTTON_SAVE: "保存",
    BUTTON_CANCEL: "キャンセル",
    BUTTON_CALCULATE: "計算",
    BUTTON_GENERATE_REPORT: "レポート生成",
    BUTTON_SAVE_REPORT: "レポート保存",
    
    # ラベル
    LABEL_EQUATION: "式",
    LABEL_VARIABLE: "変数",
    LABEL_VALUE: "値",
    LABEL_NOMINAL_VALUE: "呼び値",
    LABEL_UNIT: "単位",
    LABEL_DEFINITION: "定義",
    LABEL_UNCERTAINTY: "不確かさ",
    LABEL_UNCERTAINTY_TYPE: "不確かさの種類",
    LABEL_DISTRIBUTION: "分布",
    LABEL_DEGREES_OF_FREEDOM: "自由度",
    LABEL_COVERAGE_FACTOR: "包含係数",
    LABEL_EXPANDED_UNCERTAINTY: "拡張不確かさ",
    LABEL_RESULT: "結果",
    LABEL_CALCULATION_RESULT: "計算結果",
    
    # 不確かさの種類
    UNCERTAINTY_TYPE_A: "タイプA",
    UNCERTAINTY_TYPE_B: "タイプB",
    UNCERTAINTY_TYPE_FIXED: "固定値",
    UNCERTAINTY_TYPE_RESULT: "計算結果",
    
    # 分布の種類
    DISTRIBUTION_NORMAL: "正規分布",
    DISTRIBUTION_RECTANGULAR: "一様分布",
    DISTRIBUTION_TRIANGULAR: "三角分布",
    DISTRIBUTION_U_SHAPED: "U字型分布",
    
    # メッセージ
    MESSAGE_ERROR: "エラー",
    MESSAGE_WARNING: "警告",
    MESSAGE_INFO: "情報",
    MESSAGE_CONFIRM: "確認",
    MESSAGE_SUCCESS: "成功",
    MESSAGE_EQUATION_CHANGE: "モデル式の変更により、以下の変数の変更が必要です",
    
    # モデル式タブ関連
    MODEL_EQUATION_INPUT: "モデル方程式の入力",
    EQUATION_PLACEHOLDER: "例: y = a * x + b, z = x^2 + y",
    VARIABLE_LIST_DRAG_DROP: "変数リスト（ドラッグ＆ドロップで並び順を変更できます）",
    HTML_DISPLAY: "HTML表示",
    VARIABLE_ORDER_UPDATE_FAILED: "変数の並び順の更新に失敗しました",
    VARIABLE_ORDER_SAVE_FAILED: "変数の並び順の保存に失敗しました",
    VARIABLE_ORDER_LOAD_FAILED: "変数の並び順の読み込みに失敗しました",
    FILE_LOADED: "ファイルを読み込みました",
    
    # 変数タブ関連
    CALIBRATION_POINT_SETTINGS: "校正点の数設定",
    CALIBRATION_POINT_COUNT: "校正点の数",
    CALIBRATION_POINT_SELECTION: "校正点の選択",
    VARIABLE_LIST_AND_VALUES: "量一覧/量の値の一覧",
    VARIABLE_MODE: "量モード",
    NOT_SELECTED: "未選択",
    VARIABLE_DETAIL_SETTINGS: "量詳細設定/量の値詳細設定",
    UNIT: "単位",
    DEFINITION: "定義",
    UNCERTAINTY_TYPE: "不確かさ種類",
    TYPE_A: "TypeA",
    TYPE_B: "TypeB",
    FIXED_VALUE: "固定値",
    MEASUREMENT_VALUES: "測定値",
    MEASUREMENT_VALUES_PLACEHOLDER: "カンマ区切りで入力（例：1.2, 1.3, 1.4）",
    DEGREES_OF_FREEDOM: "自由度",
    CENTRAL_VALUE: "中央値",
    STANDARD_UNCERTAINTY: "標準不確かさ",
    DETAIL_DESCRIPTION: "詳細説明",
    DISTRIBUTION: "分布",
    NORMAL_DISTRIBUTION: "正規分布",
    RECTANGULAR_DISTRIBUTION: "矩形分布",
    TRIANGULAR_DISTRIBUTION: "三角分布",
    U_DISTRIBUTION: "U分布",
    DIVISOR: "除数",
    HALF_WIDTH: "半値幅",
    CALCULATION_FORMULA: "計算式",
    CALCULATE: "計算",
    
    # 計算タブ関連
    RESULT_SELECTION: "計算結果の選択",
    RESULT_VARIABLE: "計算結果",
    CALIBRATION_POINT: "校正点",
    CALIBRATION_VALUE: "校正値",
    VARIABLE: "量",
    SENSITIVITY_COEFFICIENT: "感度係数",
    CONTRIBUTION_UNCERTAINTY: "寄与不確かさ",
    CONTRIBUTION_RATE: "寄与率",
    CALCULATION_RESULT: "計算結果",
    COMBINED_STANDARD_UNCERTAINTY: "合成標準不確かさ",
    EFFECTIVE_DEGREES_OF_FREEDOM: "有効自由度",
    COVERAGE_FACTOR: "包含係数",
    EXPANDED_UNCERTAINTY: "拡張不確かさ",
    
    # レポートタブ関連
    GENERATE_REPORT: "レポート生成",
    SAVE_REPORT: "レポート保存",
    SAVE_REPORT_DIALOG_TITLE: "レポートの保存",
    HTML_FILE: "HTMLファイル",
    SAVE_CANCELLED: "保存がキャンセルされました",
    SAVE_SUCCESS: "成功",
    REPORT_SAVED: "レポートを保存しました",
    SAVE_ERROR: "エラー",
    REPORT_SAVE_ERROR: "レポートの保存中にエラーが発生しました",
    FILE_SAVE_ERROR: "ファイルの保存中にエラーが発生しました",
    ERROR_OCCURRED: "エラーが発生しました",
    
    # レポートHTML内のテキスト
    REPORT_TITLE_HTML: "校正不確かさ計算レポート",
    MODEL_EQUATION_HTML: "モデル式",
    VARIABLE_LIST_HTML: "量のリスト",
    QUANTITY_HTML: "量",
    UNIT_HTML: "単位",
    DEFINITION_HTML: "定義",
    UNCERTAINTY_TYPE_HTML: "不確かさの種類",
    VARIABLE_DETAILS_HTML: "各量の値の詳細説明",
    MEASUREMENT_VALUES_HTML: "測定値",
    MEASUREMENT_NUMBER_HTML: "n回目",
    UNCERTAINTY_BUDGET_HTML: "不確かさバジェット",
    VALUE_HTML: "値",
    EQUATION_HTML: "計算式",
    
    # 不確かさの種類
    TYPE_A_DISPLAY: "Type A",
    TYPE_B_DISPLAY: "Type B",
    FIXED_VALUE_DISPLAY: "固定値",
    CALCULATION_RESULT_DISPLAY: "計算結果",
    UNKNOWN_TYPE: "未知",
    
    # 部分導関数タブ関連
    PARTIAL_DERIVATIVE_TITLE: "部分導関数",
    DERIVATIVE_VARIABLE: "微分対象変数",
    DERIVATIVE_RESULT: "導関数結果",
    CALCULATE_DERIVATIVE: "導関数計算",
    DERIVATIVE_CALCULATION_ERROR: "導関数計算エラー",
    DERIVATIVE_CALCULATION_SUCCESS: "導関数計算成功",
    DERIVATIVE_EXPRESSION: "導関数式",
    
    # レポート関連
    REPORT_TITLE: "校正不確かさ計算レポート",
    REPORT_MODEL_EQUATION: "モデル式",
    REPORT_VARIABLE_LIST: "量のリスト",
    REPORT_QUANTITY: "量",
    REPORT_UNIT: "単位",
    REPORT_DEFINITION: "定義",
    REPORT_UNCERTAINTY_TYPE: "不確かさの種類",
    REPORT_CALIBRATION_POINT: "校正点",
    REPORT_CALCULATION_RESULT: "計算結果",
    REPORT_VARIABLE_DETAILS: "各量の値の詳細説明",
    REPORT_MEASUREMENT_VALUES: "測定値",
    REPORT_MEASUREMENT_NUMBER: "n回目",
    REPORT_UNCERTAINTY_BUDGET: "不確かさバジェット",
    REPORT_CENTRAL_VALUE: "中央値",
    REPORT_STANDARD_UNCERTAINTY: "標準不確かさ",
    REPORT_SENSITIVITY: "感度係数",
    REPORT_CONTRIBUTION: "寄与不確かさ",
    REPORT_CONTRIBUTION_RATE: "寄与率",
    REPORT_COMBINED_UNCERTAINTY: "合成標準不確かさ",
    REPORT_EFFECTIVE_DOF: "有効自由度",
    REPORT_EXPANDED_UNCERTAINTY: "拡張不確かさ",
}
