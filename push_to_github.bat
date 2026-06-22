@echo off
cd /d "%~dp0"
echo ===================================================
echo     AMC NPA GitHub Uploader Launcher (BAM Style)
echo ===================================================
echo.
echo Starting GitHub Push...
echo.

if exist ".venv\Scripts\python.exe" (
    echo [System] Running via virtual environment...
    ".venv\Scripts\python.exe" github_push.py
) else (
    echo [System] Running via system Python...
    python github_push.py
)

echo.
echo ===================================================
echo Git push finished.
echo ===================================================
pause
