@echo off
REM Activate virtual environment
call venv\Scripts\activate

REM Generate and build translation files
echo Generating translation files...
pushd src
python -m i18n.generate_translations

REM Compile TS to QM
echo Compiling translation files...
pyside6-lrelease i18n/ja.ts
pyside6-lrelease i18n/en.ts
popd

REM Run the application
echo Starting the application...
python -m src
