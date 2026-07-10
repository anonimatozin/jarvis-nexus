@echo off
title J.A.R.V.I.S. Control Center
echo ========================================
echo   J.A.R.V.I.S. Control Center v2.0
echo   http://localhost:8080
echo ========================================
echo.
cd /d "%~dp0"
.\venv\Scripts\python dashboard\app.py
pause
