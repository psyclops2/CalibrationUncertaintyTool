@echo off
REM Activate virtual environment
call venv\Scripts\activate

REM Build translation files
echo Building translation files...
pushd src
if not exist i18n\translations mkdir i18n\translations
pyside6-lupdate -extensions py,ui -ts i18n/translations/translations_ja.ts i18n/translations/translations_en.ts
pyside6-lrelease i18n/translations/*.ts
popd

REM Run the application
echo Starting the application...
python -m src

pause
