@echo off
REM Create virtual environment if it doesn't exist
if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
call venv\Scripts\activate

REM Install required packages
echo Installing dependencies from requirements.txt...
pip install --upgrade pip
pip install -r requirements.txt

echo.
echo ==============================
echo Setup complete!
echo You can now run the application using run.bat
echo ==============================
pause