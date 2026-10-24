@echo off
call "%~dp0analyze_changed_and_new_files.bat" --load-config
if errorlevel 1 exit /b 1
cd /d "%~dp0.."

"%CLI_ANALYZER_PATH%\venv\Scripts\python.exe" "%CLI_ANALYZER_PATH%\main.py" --language %LANGUAGE% --path "." --verbosity minimal --output "code_analysis_results" --maxamountoferrors 50 --rules "code_analysis_rules.json"
set "ANALYZER_RESULT=%ERRORLEVEL%"
if not "%ANALYZER_RESULT%"=="0" exit /b %ANALYZER_RESULT%
if exist "code_analysis_results\*.csv" (
    echo Analyzer found reported findings.
    exit /b 1
)
cd /d "%~dp0"
exit /b 0
