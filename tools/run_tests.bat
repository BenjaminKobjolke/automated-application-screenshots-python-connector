@echo off
echo ========================================
echo  automated-screenshot-connector - Tests
echo ========================================
echo.
cd /d "%~dp0.."
uv run pytest tests -v
if %errorlevel% neq 0 (
    echo.
    echo Tests FAILED
    exit /b 1
)
echo.
echo All tests passed!
exit /b 0
