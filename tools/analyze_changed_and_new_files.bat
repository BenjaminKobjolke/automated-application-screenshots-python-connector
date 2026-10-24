@echo off
if /i "%~1"=="--load-config" goto load_config_mode
call :load_config
if errorlevel 1 exit /b 1
cd /d "%~dp0.."
"%CLI_ANALYZER_PATH%\venv\Scripts\python.exe" "%CLI_ANALYZER_PATH%\main.py" --language %LANGUAGE% --path "." --only-changed --verbosity minimal --output "code_analysis_results" --rules "code_analysis_rules.json"
set "ANALYZER_RESULT=%ERRORLEVEL%"
if not "%ANALYZER_RESULT%"=="0" exit /b %ANALYZER_RESULT%
if exist "code_analysis_results\*.csv" (
    echo Analyzer found reported findings.
    exit /b 1
)
exit /b 0

:load_config_mode
call :load_config
exit /b %ERRORLEVEL%

:load_config
if not exist "%~dp0analyze_code_config.bat" (
    echo ERROR: analyze_code_config.bat not found.
    echo Copy analyze_code_config.example.bat to analyze_code_config.bat and set CLI_ANALYZER_PATH and LANGUAGE.
    exit /b 1
)
call "%~dp0analyze_code_config.bat"
if not defined CLI_ANALYZER_PATH (
    echo ERROR: CLI_ANALYZER_PATH is not set.
    exit /b 1
)
if not defined LANGUAGE (
    echo ERROR: LANGUAGE is not set.
    exit /b 1
)
exit /b 0
