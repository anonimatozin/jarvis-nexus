@echo off
chcp 65001 >nul
cd /d "%~dp0\.."
echo.
echo ============================================
echo   J.A.R.V.I.S. NEXUS - Auto-start Installer
echo ============================================
echo.
echo Opcoes:
echo   [1] Instalar auto-start
echo   [2] Remover auto-start
echo   [3] Verificar status
echo   [4] Sair
echo.
set /p choice="Escolha: "

if "%choice%"=="1" (
    venv\Scripts\python.exe boot\autostart.py enable
) else if "%choice%"=="2" (
    venv\Scripts\python.exe boot\autostart.py disable
) else if "%choice%"=="3" (
    venv\Scripts\python.exe boot\autostart.py status
)
pause