# ライセンス・出典の整理

確認日：2026-11-21。既存の本体MITライセンスを維持し、第三者の権利と配布範囲を区別するための記録。

**対象読者：開発・配布管理者。配布先の利用者向け通知は `THIRD_PARTY_LICENSES.md` と `licenses/README.md`。** 本書は調査記録であり、About画面から案内する配布用通知とは分けて管理する。

## 本体と自作素材

`LICENSE`はMIT、著作権表示は既存の `Copyright (c) 2024 psyclops2` を維持した。根拠なく年や権利者を書き換えていない。

`img/logo.png`は利用者から自作と確認した。現行の本体MIT方針に含めて扱う。EURAMETサンプルの模式図は本プロジェクトの生成スクリプトで作図している。UIスクリーンショットは本アプリの表示を記録したもの。第三者の文書・ロゴ・図版を本体MITとして再許諾するものではない。

利用者の測定記録、証明書、説明文、添付画像の権利は別に扱う。生成レポートに含まれる外部素材の権利が消滅したり、本体のMITへ置き換わったりするものではない。

## 依存ライブラリ

[THIRD_PARTY_LICENSES.md](../THIRD_PARTY_LICENSES.md)を現状の環境に合わせて整理し、実物の原文を`licenses/`へ保存した。各ライブラリの著作権表示を、同じライセンス形式という理由で別の著作権者の表示へ代替しない。

直接依存のmpmath、PySide6に伴うShiboken・Qt関連パッケージ、開発用依存を記録した。pytestは実行用依存から外し、`requirements-dev.txt`で管理する。インストール済み環境の変更・依存のアップグレードは行っていない。

Qt関連のインストール済み配布物には、メタデータにOSSの選択肢がある一方、確認できた原文ファイルは商用条件への案内のみだった。Qtを含むEXE・venv・インストーラの配布については、全通知・対応ソース等の確認が未完了。現時点の記録を「バイナリ配布のライセンス対応完了」とは扱わない。

### 確認環境と原文収集

2026-11-21のローカル環境はPython 3.15.2、PySide6 / Essentials / Addons / shiboken6は6.12.0、PySide6_WebEngine / PySide6_Pdfは6.12.0.140、NumPyは2.5.5、SymPyは1.14.0、mpmathは1.3.0、Python-Markdownは3.11.3。依存バージョンの固定指定ではない。

詳細は `licenses/dependency-inventory.json` に、用途・メタデータ・原文ファイルのSHA-256とともに記録している。記録はPython配布物単位であり、wheel内のDLLや静的に組み込まれた全コンポーネントを網羅したSBOMではない。

Qt関連6パッケージで見つかった原文ファイルは `LicenseRef-Qt-Commercial.txt` のみ。これは商用ライセンス保有の証明ではない。`licenses/upstream/`にGNU公式の汎用原文を保存したが、Qtバイナリに対応する全通知・対応ソース等を収集できたとは扱わない。

配布内容を変更する際には、その環境から再収集する。

```powershell
.\venv\Scripts\python.exe scripts/collect_license_notices.py
```

スクリプトは原文を変更せずコピーし、利用者向けの原文一覧を生成する。以前のバージョンの原文は自動削除しない。公開する版の原文と実際の配布対象が一致するかを確認する。Gitでは原文の改行変換を無効にしている。

## 外部資料

| ローカルの資料 | 権利・確認内容 | 今回の扱い |
|---|---|---|
| `examples/ea402/sources/EA-4-02-M-2022.pdf` | EAが著作権を保有。本文に再販売目的のコピー禁止の表示 | 再配布条件を本体MITと混同しないため、原本PDFを配布対象から外す |
| `examples/gum/sources/JCGM_100_2008_E.pdf` | JCGMの著作物。複製・翻訳等の許可に関する条件を記載 | 公開コピーの許諾記録がないため原本PDFを配布対象から外す |
| `examples/euramet19/sources/euramet-cg19.pdf` | EURAMETの著作物。抜粋・改変版・翻訳等に条件を記載 | 原本PDFを配布対象から外す。サンプルの独自説明図と区別する |
| `docs/参考_GUM Workbench_User Manual.pdf` | © 2017 Metrodata GmbH。公開ダウンロードが存在しても、本プロジェクトからの再配布許諾とは別 | ローカル参照用。原本PDFを配布対象から外す |

ファイル自体は削除していない。外部資料を公開する許諾が既に存在する場合は、その記録と対象範囲を確認して扱いを見直せる。

`.gitignore`で未追跡のPDFの通常追加を防ぎ、`.gitattributes`の`export-ignore`で`git archive`の対象から外した。これらは手作業のZIP作成やPyInstaller等へ自動的には適用されない。今回確認した4つのPDFはGitの追跡対象に含まれていなかった。

## サンプルについて

数値事例に基づく計算モデル・説明と、原資料の本文・図版の転載は区別する。出典、採用条件、原文との差異を残す。許諾なく原資料の翻訳版や公式実装を名乗らない。サンプル中の説明・データをどこまで公開・商用再利用するかは、具体的な転載内容と出典条件に応じて確認する必要があり、今回の整理で全面的な許諾を確認したとは扱わない。

[examples/NOTICE.md](../examples/NOTICE.md)に共通の扱いを記載した。

## 公式の参照先

- [Qt Licensing](https://doc.qt.io/qt-6/licensing.html)
- [QtのLGPLに関する説明](https://www.qt.io/development/open-source-lgpl-obligations)
- [Qt for Pythonの第三者表示](https://doc.qt.io/qtforpython-6/licenses.html)
- [JCGMの著作権表示](https://www.iso.org/sites/JCGM/GUM/JCGM100/C045315e-html/C045315e_FILES/MAIN_C045315e/Copyright_e.html)
- [EURAMET cg-19](https://www.euramet.org/Media/docs/Publications/calguides/I-CAL-GUI-019_Calibration_Guide_No._19_web.pdf) 冒頭のCopyright／Conditions for the Use and Translation
- [Metrodata公式ダウンロード案内](https://metrodata.de/download_en.html)

## 今後、配布形態が決まった際の確認

- ソース配布に加え、EXE・Python・Qt DLL・ネイティブライブラリを同梱するか
- 配布物に実際に入るモジュールと、その版に対応する原文・通知・対応ソース
- 原資料の本文や図版を含むサンプルの具体的な公開範囲・許諾
- 新たに導入する素材・フォント・ライブラリの出典

本書は確認内容と未完了事項の記録であり、未確認の権利について許諾を与えるものではない。
