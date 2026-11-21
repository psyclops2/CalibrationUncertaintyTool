# GUM附属書Hのサンプル

出典と利用条件は [共通のNOTICE](../NOTICE.md)を参照。原本PDFはローカル参照用であり、公開・配布対象には含めない。

[JCGM 100:2008の附属書H](https://www.bipm.org/en/doi/10.59161/jcgm100-2008e)の全6事例を、現行の回帰・測定表の接続機能で試算した。手法の違いを含め8モデル。改良前のモデルと生成物は削除済み。

最新版のToolで再生成し、`.cutp`形式で保存している。各モデルの中心値・不確かさ・有効自由度・包含係数が保存・再読込で変わらないことを確認した。

- [現行の計算結果一覧](reports/index.html)
- [確認内容と未対応事項](docs/workflow-results.md)
- [原典との不一致の調査・独立検算](../docs/numerical-discrepancies.md)
- [入力元接続の操作方法](../../docs/uncertainty-workflow-usage.md)

| フォルダ | 内容 |
|---|---|
| [projects](projects/) | Toolの「ファイル → 開く」で読み込む現行モデル |
| [reports](reports/) | レポート、共分散、保存・再読込の検証記録、画面画像 |
| [scripts](scripts/) | 原文の数値と、現行モデルの生成・検証処理 |
| [sources](sources/) | 原文PDF・出典情報 |
| [docs](docs/) | 採用条件と残る改良課題 |

H.2のR・X・Zは三角関数を含む原式で計算可能。H.3は回帰予測を接続して自由度9を保持する。H.1の二次伝播、H.5のANOVA、未提示の自由度の評価は未対応として残す。

```powershell
.\venv\Scripts\python.exe examples/gum/scripts/verify_workflow.py
```

出力先はprojectsとreports。MCは自動実行しない。
