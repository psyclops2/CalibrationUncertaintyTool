# EA-4/02 Mのサンプル

出典と利用条件は [共通のNOTICE](../NOTICE.md)を参照。原本PDFはローカル参照用であり、公開・配布対象には含めない。

Toolの「ファイル → 開く」で[projects](projects/)の`.cutp`を読み込む。改良前のサンプルと生成物は削除し、現行機能で再計算した全11事例を保持している。段階別と包含方法の違いを含め14モデル。

最新版のToolでレポートと画面画像も再生成した。各モデルの中心値・不確かさ・有効自由度・包含係数が保存・再読込で変わらないことを確認した。

- [現行サンプルの結果一覧](reports/index.html)
- [採用条件と未対応事項](docs/improvements.md)
- [原典との不一致の調査・独立検算](../docs/numerical-discrepancies.md)
- [S9の参照式の説明](docs/s9.md)
- [回帰・測定表などの操作方法](../../docs/uncertainty-workflow-usage.md)

| フォルダ | 内容 |
|---|---|
| [projects](projects/) | Toolで読み込む現行モデル |
| [reports](reports/) | 現行モデルのレポート、検証記録、画面画像 |
| [scripts](scripts/) | 原文の入力値と現行モデルの生成・検証処理 |
| [docs](docs/) | 採用条件と未対応事項 |
| [sources](sources/) | 原文PDF |

出典：[EA-4/02 M:2022 rev03](https://www.accredia.it/wp-content/uploads/2013/09/EA-4-02_2022-incertezza-nelle-tarature.pdf)。二次項、原文の記載不整合、未提示の自由度などの制約を各モデルに残しており、すべてを完全再現したという意味ではない。

リポジトリ直下で再実行する。MCは自動実行しない。

```powershell
.\venv\Scripts\python.exe examples/ea402/scripts/verify_improvements.py
.\venv\Scripts\python.exe examples/ea402/scripts/verify_references.py
```

`S12_average.cutp`はEA表の掲載係数、`S12_probability.cutp`は包含確率からの数値t分位点を使う現行の別方式。S12の体積と単回誤差は`S12_staged.cutp`の複数式で扱う。
