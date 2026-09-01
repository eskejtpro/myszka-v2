@echo off
setlocal enabledelayedexpansion

echo =====================================================================
echo       MyszkaHUD v1.0.0 - Kompletny Skrypt Wydania (Release Windows x64)
echo =====================================================================
echo.

:: 1. Sprawdzenie Pythona
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [BLAD] Python nie zostal odnaleziony w sciezce PATH.
    exit /b 1
)

set PYTHONPATH=src

:: 2. Weryfikacja skladniowa
echo [KROK 1/6] Walidacja skladniowa (compileall)...
python -m compileall -q src tests
if %errorlevel% neq 0 (
    echo [BLAD] Wykryto bledy skladniowe!
    exit /b 1
)
echo [OK] Skladnia prawidlowa.

:: 3. Testy jednostkowe i regresyjne
echo.
echo [KROK 2/6] Uruchamianie pelnego zestawu testow automatycznych...
python -m unittest discover -s tests -p "test_*.py"
if %errorlevel% neq 0 (
    echo [BLAD] Testy jednostkowe zakonczone niepowodzeniem!
    exit /b %errorlevel%
)
echo [OK] Wszystkie testy zaliczone w 100%%.

:: 4. Przygotowanie srodowiska kompilacji
echo.
echo [KROK 3/6] Sprawdzanie pakietu PyInstaller...
pip show pyinstaller >nul 2>&1
if %errorlevel% neq 0 (
    echo Instalowanie PyInstaller...
    pip install pyinstaller
    if %errorlevel% neq 0 (
        echo [BLAD] Nie udalo sie zainstalowac PyInstaller.
        exit /b 1
    )
)

:: 5. Czyszczenie starych artefaktow
echo.
echo [KROK 4/6] Czyszczenie katalogow build i dist...
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"
mkdir "dist"

:: 6. Kompilacja MyszkaHUD.exe
echo.
echo [KROK 5/6] Kompilacja produkcyjnego pliku MyszkaHUD.exe...
pyinstaller --noconfirm --clean MyszkaHUD.spec
if %errorlevel% neq 0 (
    echo [BLAD] Kompilacja PyInstaller nie powiodla sie!
    exit /b %errorlevel%
)

if not exist "dist\MyszkaHUD.exe" (
    echo [BLAD] Plik dist\MyszkaHUD.exe nie zostal wygenerowany!
    exit /b 1
)

:: 7. Generowanie sumy kontrolnej SHA256 i archiwum ZIP
echo.
echo [KROK 6/6] Obliczanie sumy SHA256 i tworzenie archiwum ZIP...
powershell -Command "Get-FileHash -Algorithm SHA256 dist\MyszkaHUD.exe | Format-List" > "dist\SHA256_MyszkaHUD.txt"
type "dist\SHA256_MyszkaHUD.txt"

powershell -Command "Compress-Archive -Path dist\MyszkaHUD.exe, README.md -DestinationPath dist\MyszkaHUD-v1.0.0-windows-x64.zip -Force"
if exist "dist\MyszkaHUD-v1.0.0-windows-x64.zip" (
    echo [OK] Utworzono archiwum: dist\MyszkaHUD-v1.0.0-windows-x64.zip
)

echo.
echo =====================================================================
echo [SUKCES] Wydanie produkcyjne MyszkaHUD v1.0.0 gotowe!
echo          Plik wykonywalny: dist\MyszkaHUD.exe
echo          Paczka wydania:   dist\MyszkaHUD-v1.0.0-windows-x64.zip
echo          Suma kontrolna:   dist\SHA256_MyszkaHUD.txt
echo =====================================================================
echo.
exit /b 0
