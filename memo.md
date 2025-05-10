## 詳細な依存関係
1) MainWindow
各タブの管理
アプリケーションの状態管理
メニューバーの管理
2) ModelEquationTab
方程式の解析
変数の検出
偏微分の計算
依存関係：
calculation_utils.py：式の評価
variable_utils.py：変数の処理
3) VariablesTab
変数の管理
測定値の入力
不確度の計算
依存関係：
variable_utils.py：変数の処理
equation_formatter.py：方程式の表示
4) UncertaintyCalculationTab
不確度の計算
合成不確度の計算
依存関係：
calculation_utils.py：式の評価
variable_utils.py：変数の処理
uncertainty_calculator.py：不確度の計算
5) ReportTab
レポートの生成
結果の表示
依存関係：
variable_utils.py：変数の処理
number_formatter.py：数値の表示
6) PartialDerivativeTab
偏微分の計算
依存関係：
calculation_utils.py：式の評価
variable_utils.py：変数の処理
7) Utils
calculation_utils.py：式の評価
variable_utils.py：変数の処理
equation_formatter.py：方程式の表示
uncertainty_calculator.py：不確度の計算
number_formatter.py：数値の表示
## 主要なデータフロー
# 変数管理
MainWindow → VariablesTab → variable_utils.py
# 方程式の処理
MainWindow → ModelEquationTab → calculation_utils.py
# 不確度の計算
MainWindow → UncertaintyCalculationTab → uncertainty_calculator.py
# レポート生成
MainWindow → ReportTab → number_formatter.py