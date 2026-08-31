@echo off
setlocal
cd /d "%~dp0"
echo ===================================================
echo   Uruchamianie MyszkaHUD v0.1 (Windows 10 x64)
echo   Skrot aktywacji: Alt + Q
echo   Zamkniecie HUD:  Esc lub klikniecie poza oknem
echo   Zatrzymanie programu w CMD: Ctrl + C
echo ===================================================
set PYTHONPATH=%CD%\src;%PYTHONPATH%
python -m myszkahud
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [BLAD] Aplikacja zakonczyla sie z kodem: %ERRORLEVEL%
    pause
)
