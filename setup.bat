@echo off
setlocal

set "VENV_DIR=venv"
set "VENV_PYTHON=%VENV_DIR%\Scripts\python.exe"

REM Create virtual environment if it doesn't exist
if not exist "%VENV_PYTHON%" (
    echo Creating virtual environment...
    python -m venv "%VENV_DIR%"
)

if not exist "%VENV_PYTHON%" (
    echo Failed to create virtual environment.
    exit /b 1
)

REM Install required packages
echo Installing dependencies from requirements.txt...
"%VENV_PYTHON%" -m pip install --upgrade pip
if errorlevel 1 exit /b 1
"%VENV_PYTHON%" -m pip install -r requirements.txt
if errorlevel 1 exit /b 1

echo.
echo ==============================
echo Setup complete!
echo You can now run the application using run.bat
echo ==============================
pause
endlocal
