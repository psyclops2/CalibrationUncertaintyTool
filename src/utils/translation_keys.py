"""
翻訳キー定義
多言語対応のための翻訳キーを定義
"""

# アプリケーション全般
APP_TITLE = "APP_TITLE"  # アプリケーションのタイトル

# メニューバー
FILE_MENU = 'file_menu'
OPEN_FILE = 'open_file'
SAVE = 'save'
SAVE_AS = 'save_as'
EXIT = 'exit'
EDIT_MENU = 'edit_menu'
SETTINGS_MENU = 'settings_menu'
HELP_MENU = 'help_menu'

# メニュー関連
MENU_FILE = "MENU_FILE"  # ファイルメニュー
MENU_EDIT = "MENU_EDIT"  # 編集メニュー
MENU_VIEW = "MENU_VIEW"  # 表示メニュー
MENU_LANGUAGE = "MENU_LANGUAGE"  # 言語メニュー
MENU_HELP = "MENU_HELP"  # ヘルプメニュー

# タブ
TAB_EQUATION = "TAB_EQUATION"  # モデル式
TAB_VARIABLES = "TAB_VARIABLES"  # 変数
TAB_CALCULATION = "TAB_CALCULATION"  # 計算
TAB_REPORT = "TAB_REPORT"  # レポート
PARTIAL_DERIVATIVE = "PARTIAL_DERIVATIVE"  # 偏微分タブ
POINT_SETTINGS_TAB = 'point_settings_tab'
POINT_SETTINGS_TAB_INFO = 'point_settings_tab_info'
INDEX = 'index'

# タブ名
POINT_NAME = 'point_name'
ADD_POINT = 'add_point'
REMOVE_POINT = 'remove_point'

# ファイルメニューアクション
FILE_SAVE_AS = "FILE_SAVE_AS"  # 名前を付けて保存...
FILE_OPEN = "FILE_OPEN"  # 開く...
FILE_EXIT = "FILE_EXIT"  # 終了

# 言語関連
LANGUAGE_JAPANESE = "LANGUAGE_JAPANESE"  # 日本語
LANGUAGE_ENGLISH = "LANGUAGE_ENGLISH"  # 英語
LANGUAGE_SETTINGS = "LANGUAGE_SETTINGS"  # 言語設定
LANGUAGE_CHANGED = "LANGUAGE_CHANGED"  # 言語が変更されました
USE_SYSTEM_LOCALE = "USE_SYSTEM_LOCALE"  # システムロケールを使用
RESTART_REQUIRED = "RESTART_REQUIRED"  # 再起動が必要です
LANGUAGE_CHANGED_RESTART_MESSAGE = "LANGUAGE_CHANGED_RESTART_MESSAGE"  # 言語設定を変更しました。変更を適用するにはアプリケーションを再起動してください。

# タブ名
TAB_EQUATION = "TAB_EQUATION"  # モデル式
TAB_VARIABLES = "TAB_VARIABLES"  # 変数
TAB_CALCULATION = "TAB_CALCULATION"  # 計算
TAB_REPORT = "TAB_REPORT"  # レポート
PARTIAL_DERIVATIVE = "PARTIAL_DERIVATIVE"  # 偏微分タブ

# ボタン
BUTTON_ADD = "BUTTON_ADD"  # 追加
BUTTON_EDIT = "BUTTON_EDIT"  # 編集
BUTTON_DELETE = "BUTTON_DELETE"  # 削除
BUTTON_SAVE = "BUTTON_SAVE"  # 保存
BUTTON_CANCEL = "BUTTON_CANCEL"  # キャンセル
BUTTON_CALCULATE = "BUTTON_CALCULATE"  # 計算
BUTTON_GENERATE_REPORT = "BUTTON_GENERATE_REPORT"  # レポート生成
BUTTON_SAVE_REPORT = "BUTTON_SAVE_REPORT"  # レポート保存

# ラベル
LABEL_EQUATION = "LABEL_EQUATION"  # 式
LABEL_VARIABLE = "LABEL_VARIABLE"  # 変数
LABEL_VALUE = "LABEL_VALUE"  # 値
LABEL_NOMINAL_VALUE = "LABEL_NOMINAL_VALUE"  # 呼び値
LABEL_UNIT = "LABEL_UNIT"  # 単位
LABEL_DEFINITION = "LABEL_DEFINITION"  # 定義
LABEL_UNCERTAINTY = "LABEL_UNCERTAINTY"  # 不確かさ
LABEL_UNCERTAINTY_TYPE = "LABEL_UNCERTAINTY_TYPE"  # 不確かさの種類
LABEL_DISTRIBUTION = "LABEL_DISTRIBUTION"  # 分布
LABEL_DEGREES_OF_FREEDOM = "LABEL_DEGREES_OF_FREEDOM"  # 自由度
LABEL_COVERAGE_FACTOR = "LABEL_COVERAGE_FACTOR"  # 包含係数
LABEL_EXPANDED_UNCERTAINTY = "LABEL_EXPANDED_UNCERTAINTY"  # 拡張不確かさ
LABEL_RESULT = "LABEL_RESULT"  # 結果
LABEL_CALCULATION_RESULT = "LABEL_CALCULATION_RESULT"  # 計算結果

# 不確かさの種類
UNCERTAINTY_TYPE_A = "UNCERTAINTY_TYPE_A"  # タイプA
UNCERTAINTY_TYPE_B = "UNCERTAINTY_TYPE_B"  # タイプB
UNCERTAINTY_TYPE_FIXED = "UNCERTAINTY_TYPE_FIXED"  # 固定値
UNCERTAINTY_TYPE_RESULT = "UNCERTAINTY_TYPE_RESULT"  # 計算結果

# 分布の種類
DISTRIBUTION_NORMAL = "DISTRIBUTION_NORMAL"  # 正規分布
DISTRIBUTION_RECTANGULAR = "DISTRIBUTION_RECTANGULAR"  # 一様分布
DISTRIBUTION_TRIANGULAR = "DISTRIBUTION_TRIANGULAR"  # 三角分布
DISTRIBUTION_U_SHAPED = "DISTRIBUTION_U_SHAPED"  # U字型分布

# メッセージ
MESSAGE_ERROR = "MESSAGE_ERROR"  # エラー
MESSAGE_WARNING = "MESSAGE_WARNING"  # 警告
MESSAGE_INFO = "MESSAGE_INFO"  # 情報
MESSAGE_CONFIRM = "MESSAGE_CONFIRM"  # 確認
MESSAGE_SUCCESS = "MESSAGE_SUCCESS"  # 成功
MESSAGE_EQUATION_CHANGE = "MESSAGE_EQUATION_CHANGE"  # モデル式の変更により、以下の変数の変更が必要です

# モデル式タブ関連
MODEL_EQUATION_INPUT = "MODEL_EQUATION_INPUT"  # モデル方程式の入力
EQUATION_PLACEHOLDER = "EQUATION_PLACEHOLDER"  # 例: y = a * x + b, z = x^2 + y
VARIABLE_LIST_DRAG_DROP = "VARIABLE_LIST_DRAG_DROP"  # 変数リスト（ドラッグ＆ドロップで並び順を変更できます）
HTML_DISPLAY = "HTML_DISPLAY"  # HTML表示
VARIABLE_ORDER_UPDATE_FAILED = "VARIABLE_ORDER_UPDATE_FAILED"  # 変数の並び順の更新に失敗しました
VARIABLE_ORDER_SAVE_FAILED = "VARIABLE_ORDER_SAVE_FAILED"  # 変数の並び順の保存に失敗しました
VARIABLE_ORDER_LOAD_FAILED = "VARIABLE_ORDER_LOAD_FAILED"  # 変数の並び順の読み込みに失敗しました
FILE_LOADED = "FILE_LOADED"  # ファイルを読み込みました

# 変数タブ関連
CALIBRATION_POINT_SETTINGS = "CALIBRATION_POINT_SETTINGS"  # 校正点の数設定
CALIBRATION_POINT_COUNT = "CALIBRATION_POINT_COUNT"  # 校正点の数
CALIBRATION_POINT_SELECTION = "CALIBRATION_POINT_SELECTION"  # 校正点の選択
VARIABLE_LIST_AND_VALUES = "VARIABLE_LIST_AND_VALUES"  # 量一覧/量の値の一覧
VARIABLE_MODE = "VARIABLE_MODE"  # 量モード
NOT_SELECTED = "NOT_SELECTED"  # 未選択
VARIABLE_DETAIL_SETTINGS = "VARIABLE_DETAIL_SETTINGS"  # 量詳細設定/量の値詳細設定
UNIT = "UNIT"  # 単位
DEFINITION = "DEFINITION"  # 定義
UNCERTAINTY_TYPE = "UNCERTAINTY_TYPE"  # 不確かさ種類
TYPE_A = "TYPE_A"  # TypeA
TYPE_B = "TYPE_B"  # TypeB
FIXED_VALUE = "FIXED_VALUE"  # 固定値
MEASUREMENT_VALUES = "MEASUREMENT_VALUES"  # 測定値
MEASUREMENT_VALUES_PLACEHOLDER = "MEASUREMENT_VALUES_PLACEHOLDER"  # カンマ区切りで入力（例：1.2, 1.3, 1.4）
DEGREES_OF_FREEDOM = "DEGREES_OF_FREEDOM"  # 自由度
CENTRAL_VALUE = "CENTRAL_VALUE"  # 中央値
STANDARD_UNCERTAINTY = "STANDARD_UNCERTAINTY"  # 標準不確かさ
DETAIL_DESCRIPTION = "DETAIL_DESCRIPTION"  # 詳細説明
DISTRIBUTION = "DISTRIBUTION"  # 分布
NORMAL_DISTRIBUTION = "NORMAL_DISTRIBUTION"  # 正規分布
RECTANGULAR_DISTRIBUTION = "RECTANGULAR_DISTRIBUTION"  # 矩形分布
TRIANGULAR_DISTRIBUTION = "TRIANGULAR_DISTRIBUTION"  # 三角分布
U_DISTRIBUTION = "U_DISTRIBUTION"  # U分布
DIVISOR = "DIVISOR"  # 除数
HALF_WIDTH = "HALF_WIDTH"  # 半値幅
CALCULATION_FORMULA = "CALCULATION_FORMULA"  # 計算式
CALCULATE = "CALCULATE"  # 計算

# 計算タブ関連
RESULT_SELECTION = "RESULT_SELECTION"  # 計算結果の選択
RESULT_VARIABLE = "RESULT_VARIABLE"  # 計算結果
CALIBRATION_POINT = "CALIBRATION_POINT"  # 校正点
CALIBRATION_VALUE = "CALIBRATION_VALUE"  # 校正値
VARIABLE = "VARIABLE"  # 量
SENSITIVITY_COEFFICIENT = "SENSITIVITY_COEFFICIENT"  # 感度係数
CONTRIBUTION_UNCERTAINTY = "CONTRIBUTION_UNCERTAINTY"  # 寄与不確かさ
CONTRIBUTION_RATE = "CONTRIBUTION_RATE"  # 寄与率
CALCULATION_RESULT = "CALCULATION_RESULT"  # 計算結果
COMBINED_STANDARD_UNCERTAINTY = "COMBINED_STANDARD_UNCERTAINTY"  # 合成標準不確かさ
EFFECTIVE_DEGREES_OF_FREEDOM = "EFFECTIVE_DEGREES_OF_FREEDOM"  # 有効自由度
COVERAGE_FACTOR = "COVERAGE_FACTOR"  # 包含係数
EXPANDED_UNCERTAINTY = "EXPANDED_UNCERTAINTY"  # 拡張不確かさ

# レポートタブ関連
GENERATE_REPORT = "GENERATE_REPORT"  # レポート生成
SAVE_REPORT = "SAVE_REPORT"  # レポート保存
SAVE_REPORT_DIALOG_TITLE = "SAVE_REPORT_DIALOG_TITLE"  # レポートの保存
HTML_FILE = "HTML_FILE"  # HTMLファイル
SAVE_CANCELLED = "SAVE_CANCELLED"  # 保存がキャンセルされました
SAVE_SUCCESS = "SAVE_SUCCESS"  # 成功
REPORT_SAVED = "REPORT_SAVED"  # レポートを保存しました
SAVE_ERROR = "SAVE_ERROR"  # エラー
REPORT_SAVE_ERROR = "REPORT_SAVE_ERROR"  # レポートの保存中にエラーが発生しました
FILE_SAVE_ERROR = "FILE_SAVE_ERROR"  # ファイルの保存中にエラーが発生しました
ERROR_OCCURRED = "ERROR_OCCURRED"  # エラーが発生しました

# ダイアログタイトル
SAVE_DIALOG_TITLE = "SAVE_DIALOG_TITLE"
OPEN_DIALOG_TITLE = "OPEN_DIALOG_TITLE"

# メニューアクション
ABOUT_APP = "ABOUT_APP"

# メッセージ
FILE_SAVED = "FILE_SAVED"
FILE_LOAD_ERROR = "FILE_LOAD_ERROR"
FILE_NOT_FOUND = "FILE_NOT_FOUND"
INVALID_FILE_FORMAT = "INVALID_FILE_FORMAT"

# その他
CALIBRATION_POINT_NAME = "CALIBRATION_POINT_NAME"

# レポートHTML内のテキスト
REPORT_TITLE_HTML = "REPORT_TITLE_HTML"  # 校正不確かさ計算レポート
MODEL_EQUATION_HTML = "MODEL_EQUATION_HTML"  # モデル式
VARIABLE_LIST_HTML = "VARIABLE_LIST_HTML"  # 量のリスト
QUANTITY_HTML = "QUANTITY_HTML"  # 量
UNIT_HTML = "UNIT_HTML"  # 単位
DEFINITION_HTML = "DEFINITION_HTML"  # 定義
UNCERTAINTY_TYPE_HTML = "UNCERTAINTY_TYPE_HTML"  # 不確かさの種類
VARIABLE_DETAILS_HTML = "VARIABLE_DETAILS_HTML"  # 各量の値の詳細説明
MEASUREMENT_VALUES_HTML = "MEASUREMENT_VALUES_HTML"  # 測定値

# レポートタブのUI要素とHTMLレポート内のテキスト
REPORT_MODEL_EQUATION = "REPORT_MODEL_EQUATION"
REPORT_VARIABLE_LIST = "REPORT_VARIABLE_LIST"
REPORT_VARIABLE_DETAILS = "REPORT_VARIABLE_DETAILS"
REPORT_MEASUREMENT_VALUES = "REPORT_MEASUREMENT_VALUES"
REPORT_UNCERTAINTY_BUDGET = "REPORT_UNCERTAINTY_BUDGET"
REPORT_QUANTITY = "REPORT_QUANTITY"
REPORT_UNIT = "REPORT_UNIT"
REPORT_DEFINITION = "REPORT_DEFINITION"
REPORT_UNCERTAINTY_TYPE = "REPORT_UNCERTAINTY_TYPE"
REPORT_MEASUREMENT_NUMBER = "REPORT_MEASUREMENT_NUMBER"
REPORT_VALUE = "REPORT_VALUE"
REPORT_FACTOR = "REPORT_FACTOR"
REPORT_CENTRAL_VALUE = "REPORT_CENTRAL_VALUE"
REPORT_STANDARD_UNCERTAINTY = "REPORT_STANDARD_UNCERTAINTY"
REPORT_DOF = "REPORT_DOF"
REPORT_DISTRIBUTION = "REPORT_DISTRIBUTION"
REPORT_SENSITIVITY = "REPORT_SENSITIVITY"
REPORT_CONTRIBUTION = "REPORT_CONTRIBUTION"
REPORT_CONTRIBUTION_RATE = "REPORT_CONTRIBUTION_RATE"
REPORT_ITEM = "REPORT_ITEM"
REPORT_CALIBRATION_POINT = "REPORT_CALIBRATION_POINT"
REPORT_EQUATION = "REPORT_EQUATION"
REPORT_COMBINED_UNCERTAINTY = "REPORT_COMBINED_UNCERTAINTY"
REPORT_EFFECTIVE_DOF = "REPORT_EFFECTIVE_DOF"
REPORT_COVERAGE_FACTOR = "REPORT_COVERAGE_FACTOR"
REPORT_EXPANDED_UNCERTAINTY = "REPORT_EXPANDED_UNCERTAINTY"
CALCULATION_RESULT_DISPLAY = "CALCULATION_RESULT_DISPLAY"
TYPE_A_DISPLAY = "TYPE_A_DISPLAY"
TYPE_B_DISPLAY = "TYPE_B_DISPLAY"
FIXED_VALUE_DISPLAY = "FIXED_VALUE_DISPLAY"
UNKNOWN_TYPE = "UNKNOWN_TYPE"
HTML_GENERATION_ERROR = "HTML_GENERATION_ERROR"

# 偏微分タブ
PARTIAL_DERIVATIVE_TITLE = "PARTIAL_DERIVATIVE_TITLE"
DERIVATIVE_VARIABLE = "DERIVATIVE_VARIABLE"
DERIVATIVE_RESULT = "DERIVATIVE_RESULT"
CALCULATE_DERIVATIVE = "CALCULATE_DERIVATIVE"
DERIVATIVE_CALCULATION_ERROR = "DERIVATIVE_CALCULATION_ERROR"
DERIVATIVE_CALCULATION_SUCCESS = "DERIVATIVE_CALCULATION_SUCCESS"
DERIVATIVE_EXPRESSION = "DERIVATIVE_EXPRESSION"
MEASUREMENT_NUMBER_HTML = "MEASUREMENT_NUMBER_HTML"  # n回目
UNCERTAINTY_BUDGET_HTML = "UNCERTAINTY_BUDGET_HTML"  # 不確かさバジェット
VALUE_HTML = "VALUE_HTML"  # 値
EQUATION_HTML = "EQUATION_HTML"  # 計算式

# 不確かさの種類
TYPE_A_DISPLAY = "TYPE_A_DISPLAY"  # Type A
TYPE_B_DISPLAY = "TYPE_B_DISPLAY"  # Type B
FIXED_VALUE_DISPLAY = "FIXED_VALUE_DISPLAY"  # 固定値
CALCULATION_RESULT_DISPLAY = "CALCULATION_RESULT_DISPLAY"  # 計算結果
UNKNOWN_TYPE = "UNKNOWN_TYPE"  # 未知

# 部分導関数タブ関連
PARTIAL_DERIVATIVE_TITLE = "PARTIAL_DERIVATIVE_TITLE"  # 部分導関数
DERIVATIVE_VARIABLE = "DERIVATIVE_VARIABLE"  # 微分対象変数
DERIVATIVE_RESULT = "DERIVATIVE_RESULT"  # 導関数結果
CALCULATE_DERIVATIVE = "CALCULATE_DERIVATIVE"  # 導関数計算
DERIVATIVE_CALCULATION_ERROR = "DERIVATIVE_CALCULATION_ERROR"  # 導関数計算エラー
DERIVATIVE_CALCULATION_SUCCESS = "DERIVATIVE_CALCULATION_SUCCESS"  # 導関数計算成功
DERIVATIVE_EXPRESSION = "DERIVATIVE_EXPRESSION"  # 導関数式

# レポート関連
REPORT_TITLE = "REPORT_TITLE"  # レポートタイトル
REPORT_MODEL_EQUATION = "REPORT_MODEL_EQUATION"  # モデル式
REPORT_VARIABLE_LIST = "REPORT_VARIABLE_LIST"  # 量のリスト
REPORT_QUANTITY = "REPORT_QUANTITY"  # 量
REPORT_UNIT = "REPORT_UNIT"  # 単位
REPORT_DEFINITION = "REPORT_DEFINITION"  # 定義
REPORT_UNCERTAINTY_TYPE = "REPORT_UNCERTAINTY_TYPE"  # 不確かさの種類
REPORT_CALIBRATION_POINT = "REPORT_CALIBRATION_POINT"  # 校正点
REPORT_CALCULATION_RESULT = "REPORT_CALCULATION_RESULT"  # 計算結果
REPORT_VARIABLE_DETAILS = "REPORT_VARIABLE_DETAILS"  # 各量の値の詳細説明
REPORT_MEASUREMENT_VALUES = "REPORT_MEASUREMENT_VALUES"  # 測定値
REPORT_MEASUREMENT_NUMBER = "REPORT_MEASUREMENT_NUMBER"  # n回目
REPORT_UNCERTAINTY_BUDGET = "REPORT_UNCERTAINTY_BUDGET"  # 不確かさバジェット
REPORT_CENTRAL_VALUE = "REPORT_CENTRAL_VALUE"  # 中央値
REPORT_STANDARD_UNCERTAINTY = "REPORT_STANDARD_UNCERTAINTY"  # 標準不確かさ
REPORT_SENSITIVITY = "REPORT_SENSITIVITY"  # 感度係数
REPORT_CONTRIBUTION = "REPORT_CONTRIBUTION"  # 寄与不確かさ
REPORT_CONTRIBUTION_RATE = "REPORT_CONTRIBUTION_RATE"  # 寄与率
REPORT_COMBINED_UNCERTAINTY = "REPORT_COMBINED_UNCERTAINTY"  # 合成標準不確かさ
REPORT_EFFECTIVE_DOF = "REPORT_EFFECTIVE_DOF"  # 有効自由度
REPORT_EXPANDED_UNCERTAINTY = "REPORT_EXPANDED_UNCERTAINTY"  # 拡張不確かさ
