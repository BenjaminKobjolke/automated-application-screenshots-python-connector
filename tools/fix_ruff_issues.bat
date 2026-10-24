@echo off
call "%~dp0analyze_changed_and_new_files.bat" --load-config
if errorlevel 1 exit /b 1
cd /d "%~dp0.."

"%CLI_ANALYZER_PATH%\venv\Scripts\python.exe" "%CLI_ANALYZER_PATH%\ruff_fixer.py" --path "." --rules "code_analysis_rules.json"
set "FIXER_RESULT=%ERRORLEVEL%"
cd /d "%~dp0"
exit /b %FIXER_RESULT%
