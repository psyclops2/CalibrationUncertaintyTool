# 不確かさ計算支援ソフト

## 概要
このソフトは、測定値の不確かさを計算するためのGUIアプリケーションです。

JCGM 100（Guide to the Expression of Uncertainty in Measurement, GUM）の考え方に基づいて、
モデル式から不確かさバジェットを作成し、合成標準不確かさ・有効自由度・包含係数・拡張不確かさを計算します。

同一モデル式に従う複数の校正点を扱え、回帰、モンテカルロ、レポート出力にも対応しています。

## 主な機能
1. モデル方程式の入力と量の管理
2. 校正点ごとの値・不確かさ情報（A/B/固定値）の管理
3. 感度係数の自動計算
4. 相関係数行列を考慮した不確かさ伝播計算
5. 不確かさバジェット表示とレポート（HTML）出力
6. 回帰分析（モデル管理、CSV取込、逆推定）
7. モンテカルロシミュレーション（分布可視化、95%区間比較）
8. 単位整合チェック（変数単位・式次元）
9. 一括入力ダイアログ（Bタイプ/固定値の複数校正点一括更新）

## システム要件
- Python 3.8以上
- PySide6
- NumPy
- SymPy
- Markdown（Python-Markdown）

## インストール方法
1. 依存パッケージをインストール
```bash
pip install -r requirements.txt
```

2. 必要に応じて仮想環境を作成
```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

3. 起動
```bash
python -m src
```

補助スクリプト:
- `setup.bat`: 仮想環境作成 + 依存インストール
- `run.bat`: 翻訳更新（ts/qm）後に起動

## 設定ファイル（config.ini）
アプリ設定はリポジトリ直下の [`config.ini`](./config.ini) に保存されます。

- `[Calculation]`
  - `precision`: Decimal計算精度
- `[Defaults]`
  - `value_count`: 初期校正点数
  - `current_value_index`: 初期選択インデックス
- `[CalibrationPoints]`
  - `min_count`, `max_count`: 校正点数の許容範囲
- `[UncertaintyRounding]`
  - `significant_digits`: 表示有効数字
  - `rounding_mode`: `round_up` または `5_percent`
- `[Language]`
  - `current`: `ja` / `en`
  - `use_system_locale`: システムロケール優先可否
- `[Distribution]`
  - `normal_distribution`, `rectangular_distribution`, `triangular_distribution`, `u_distribution`
  - Bタイプ換算で使う除数
- `[TValues]`
  - 自由度に対する包含係数テーブル（無限大は `infinity`）

## タブ・機能仕様

### 1. モデル式入力タブ
- 例: `W = V * I / R`
- `^` はべき、`_` は添字表記に対応
- 左辺は結果変数として扱い、直接値入力しない
- カンマ区切りで複数式入力可
- 変数リストはドラッグ&ドロップで表示順変更可

### 2. 校正点設定タブ
- 校正点名の変更
- 追加・削除・並び替え
- 校正点変更は他タブ（量設定、計算、レポート等）へ反映

### 3. 量設定タブ
- 量ごとに単位・定義を設定
- 不確かさタイプ
  - Aタイプ: 繰返し測定列から平均・標準不確かさ・自由度を算出
  - Bタイプ: 中心値、半値幅、分布、除数、自由度、説明
  - 固定値: 中心値のみ

### 4. 相関係数タブ（編集制約）
- 対象は入力変数のみ（結果変数は除外）
- 対角要素は常に `1.0` 固定（編集不可）
- 編集可能なのは上三角セルのみ
- 下三角セルは上三角のミラー（編集不可）
- 非対角の初期値は `0.0`（独立）
- `1` を超える値は警告して元値に戻す

### 5. 不確かさ計算タブ
- 校正点と結果変数を選択してバジェット生成
- 表示項目: 中心値、標準不確かさ、自由度、分布、感度係数、寄与不確かさ、寄与率
- 結果項目: 合成標準不確かさ、有効自由度、包含係数、拡張不確かさ
- 相関係数行列を考慮した合成計算に対応

### 6. モンテカルロタブ
- 分布（正規/矩形/三角/U字）に応じてサンプリング
- ヒストグラム表示
- 1σ、理論95%区間、経験的95%区間、中央値、正規曲線重ね描画

### 7. 回帰タブ（詳細）
- 複数モデル管理（追加・複製・削除）
- モデル属性: 説明、`x`単位、`y`単位
- データ表: `x`, `u(x)`, `y`
- CSV貼り付け取込: `x, u(x), y` または `x, y`（2点以上必須）
- 列ヘッダクリックでソート（昇順/降順トグル）
- 主な計算結果:
  - 切片、傾き、Significance F、残差標準偏差
  - `u(beta)`
  - `x`平均、`y`平均、`u(x)`平均、`u(y)`
- 逆推定:
  - 入力列 `y0`
  - 自動計算列 `x0`, `u(x0)`

### 8. 偏微分タブ
- モデル式から偏微分式を記号計算で表示

### 9. 単位検証タブ
- 変数単位から次元を解析
- 式の左辺次元と右辺次元の整合を判定
- `OK/WARN/ERROR` で表示

### 10. 文書情報タブ
- 文書番号、文書名、版数
- 説明文（Markdown）
- 改訂履歴（CSV: 版数, 内容, 作成, 確認, 承認, 日付）

### 11. レポートタブ
- 全校正点のバジェット・計算結果をHTML化
- CSSカスタマイズ
  - `css/default.css`（ベース）
  - `css/custom.css`（上書き）

### 12. 一括入力ダイアログ（詳細）
- メニュー: ツール -> 一括入力
- 対象行
  - Bタイプ: `central_value`, `half_width`, `distribution`
  - 固定値: `central_value`
  - Aタイプ/結果変数は対象外
- 空セルは未変更（既存値保持）
- 数値は `Decimal` で検証し、不正値があると適用しない
- Bタイプの自動処理
  - `distribution` を変更したとき
    - `degrees_of_freedom = "inf"` を自動設定
    - `divisor` を自動設定
      - 正規分布: `"2"`
      - それ以外: 分布設定に対応する除数
  - `central_value` / `half_width` を変更したとき
    - `degrees_of_freedom = "inf"` を自動設定
    - `divisor` を分布に応じて自動設定
    - `half_width` と `divisor` が有効で `divisor != 0` の場合
      - `standard_uncertainty = half_width / divisor` を自動再計算

## 計算の背景と根拠

### 1. 不確かさの伝播則
相関込みで次を用います。

`u(x_i, x_j) = u(x_i) u(x_j) r(x_i, x_j)`

ここで `r(x_i, x_j)` は、「4. 相関係数タブ（編集制約）」で入力した相関係数です。
相関係数タブの値が、下式第2項（共分散項）にそのまま反映されます。

`u^2(y) = Σ_i (∂f/∂x_i)^2 u^2(x_i) + 2Σ_{i<j} (∂f/∂x_i)(∂f/∂x_j) u(x_i)u(x_j) r(x_i, x_j)`

同値な表現として、

`u^2(y) = Σ_i (∂f/∂x_i)^2 u^2(x_i) + 2Σ_{i<j} (∂f/∂x_i)(∂f/∂x_j) u(x_i, x_j)`

### 2. 感度係数
`∂f/∂x_i` を式から計算します（偏微分）。

### 3. A/Bタイプ不確かさ
- Aタイプ（反復測定）
  - `u = sqrt((1/(n(n-1))) Σ(x_i - x̄)^2)`
  - `ν = n - 1`
- Bタイプ（仕様書・証明書等）
  - 矩形: `u = a / sqrt(3)`
  - 三角: `u = a / sqrt(6)`
  - 正規: `u = a / k`

### 4. 有効自由度
Welch-Satterthwaite 近似を使用します。

### 5. 拡張不確かさ
`U = k * u(y)`

`k` は自由度に応じた `config.ini` の `TValues` を参照します。

## 保存データ
プロジェクトはJSONで保存され、次を含みます。
- 文書情報
- モデル式
- 校正点情報（名称・選択インデックス）
- 変数情報（入力/結果）
- 相関係数
- 変数値
- 回帰モデル

## プロジェクト構造
```text
src/
├── __main__.py
├── main.py
├── main_window.py
├── dialogs/
├── tabs/
├── utils/
└── i18n/
css/
├── default.css
└── custom.css
tests/
```

## テスト
```bash
pytest
```

## ライセンス
このソフトウェアは **MIT License** の下で公開されています。

詳細は [`LICENSE`](./LICENSE) を参照してください。
依存ライブラリのライセンスは [`THIRD_PARTY_LICENSES.md`](./THIRD_PARTY_LICENSES.md) に記載しています。
