@echo off
cd /d "%~dp0"
title NPA Monitor Dashboard
echo [System] Starting NPA Monitor Dashboard...
python -m streamlit run dashboard.py
if %ERRORLEVEL% neq 0 (
    echo [Error] Failed to start Streamlit. Please make sure Streamlit is installed.
    pause
)
