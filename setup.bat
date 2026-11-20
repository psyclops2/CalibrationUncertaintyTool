@echo off
setlocal
cd /d "%~dp0"

REM Prefer the project-local Python; otherwise require Python 3.15 on PATH.
set "BASE_PYTHON=python"
if exist ".python\3.15.2\python.exe" set "BASE_PYTHON=%CD%\.python\3.15.2\python.exe"
"%BASE_PYTHON%" -c "import sys; sys.exit(0 if sys.version_info[:2] == (3, 15) else 1)"
if errorlevel 1 (
    echo Python 3.15 is required. Install the latest stable Python 3.15 release first.
    exit /b 1
)

set "VENV_DIR=venv"
set "VENV_PYTHON=%VENV_DIR%\Scripts\python.exe"

REM Check the interpreter itself: python.exe may exist with a missing base Python.
if exist "%VENV_PYTHON%" (
    "%VENV_PYTHON%" -c "import sys; sys.exit(0 if sys.version_info[:2] == (3, 15) else 1)" >nul 2>&1
    if errorlevel 1 (
        echo The virtual environment is broken. Recreating it...
        "%BASE_PYTHON%" -m venv --clear "%VENV_DIR%"
        if errorlevel 1 exit /b 1
    )
) else (
    echo Creating virtual environment...
    "%BASE_PYTHON%" -m venv "%VENV_DIR%"
    if errorlevel 1 exit /b 1
)

"%VENV_PYTHON%" --version
if errorlevel 1 exit /b 1

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
