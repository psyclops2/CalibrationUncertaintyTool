@echo off
REM 仮想環境を有効化
cd /d "%~dp0"
call venv\Scripts\activate

REM アプリを起動
python -m src

pause
