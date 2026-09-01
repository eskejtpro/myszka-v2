@echo off
setlocal enabledelayedexpansion

echo =====================================================================
echo           MyszkaHUD - Skrypt Budowania EXE dla Windows 10 x64
echo =====================================================================
echo.

:: 1. Sprawdzenie obecności Pythona
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [BLAD] Python nie zostal znaleziony w sciezce PATH.
    echo Zainstaluj Pythona 3.10+ (64-bit) i zaznacz opcje "Add Python to PATH".
    exit /b 1
)

echo [1/5] Weryfikacja srodowiska Python...
python --version

:: 2. Ustawienie PYTHONPATH
set PYTHONPATH=src

:: 3. Uruchomienie pelnych testow jednostkowych przed kompilacja
echo.
echo [2/5] Uruchamianie testow jednostkowych i regresji...
python -m unittest discover -s tests -p "test_*.py"
if %errorlevel% neq 0 (
    echo.
    echo [BLAD] Testy jednostkowe nie powiodly sie! Przerywanie budowania EXE.
    exit /b %errorlevel%
)
echo [OK] Wszystkie testy przeszly pomyslnie!

:: 4. Sprawdzenie i instalacja PyInstaller
echo.
echo [3/5] Sprawdzanie instalacji PyInstaller...
pip show pyinstaller >nul 2>&1
if %errorlevel% neq 0 (
    echo Instalowanie pakietu pyinstaller...
    pip install pyinstaller
    if %errorlevel% neq 0 (
        echo [BLAD] Nie udalo sie zainstalowac PyInstaller.
        exit /b 1
    )
)

:: 5. Czyszczenie poprzednich plikow budowania
echo.
echo [4/5] Czyszczenie poprzednich artefaktow build i dist...
if exist "build" rmdir /s /q "build"
if exist "dist\MyszkaHUD.exe" del /f /q "dist\MyszkaHUD.exe"

:: 6. Budowanie aplikacji przez PyInstaller
echo.
echo [5/5] Kompilacja aplikacji MyszkaHUD.exe...

if "%1"=="debug" (
    echo [TRYB DEBUG] Budowanie z oknem konsoli (console=True)...
    pyinstaller --noconfirm --clean --console MyszkaHUD.spec
) else (
    echo [TRYB PRODUKCYJNY] Budowanie okienkowe GUI (console=False)...
    pyinstaller --noconfirm --clean MyszkaHUD.spec
)

if %errorlevel% neq 0 (
    echo.
    echo [BLAD] Kompilacja PyInstaller zakonczyla sie niepowodzeniem.
    exit /b %errorlevel%
)

echo.
echo =====================================================================
echo [SUKCES] Plik wykonywalny zostal poprawnie utworzony:
echo          dist\MyszkaHUD.exe
echo =====================================================================
echo.
echo Mozesz teraz uruchomic aplikacje:
echo   dist\MyszkaHUD.exe
echo.
exit /b 0
