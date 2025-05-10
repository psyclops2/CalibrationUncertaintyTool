@echo off
REM ディレクトリを移動
cd /d "%~dp0"

REM 仮想環境がなければ作成
if not exist venv (
    python -m venv venv
)

REM 仮想環境を有効化
call venv\Scripts\activate

REM 必要なパッケージをインストール
pip install --upgrade pip
pip install -r requirements.txt

echo.
echo ==============================
echo セットアップが完了しました！
echo run.batでアプリを起動してください。
echo ==============================
pause