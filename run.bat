@echo off
REM Activate virtual environment
call venv\Scripts\activate

REM Generate and build translation files
echo Generating translation files...
pushd src
python -m i18n.generate_translations

REM Update TS files with new strings from source code
echo Updating translation files from source...
if not exist i18n\translations mkdir i18n\translations
pyside6-lupdate -extensions py,ui -ts i18n/translations/translations_ja.ts i18n/translations/translations_en.ts

REM Compile TS to QM
echo Compiling translation files...
pyside6-lrelease i18n/translations/*.ts
popd

REM Run the application
echo Starting the application...
python -m src

pause
