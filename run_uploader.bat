@echo off
cd /d "%~dp0"
title GitHub Auto Uploader
echo [System] Starting GitHub Auto Uploader...
python upload_to_github.py
pause
