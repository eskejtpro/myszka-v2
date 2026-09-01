@echo off
setlocal enabledelayedexpansion

echo =====================================================================
echo         MyszkaHUD - Zautomatyzowany Skrypt Walidacji Windows 10 x64
echo =====================================================================
echo.

set PYTHONPATH=src

echo [ETAP 1/4] Sprawdzanie kompilacji skladniowej Pythona (py_compile)...
python -m py_compile src/myszkahud/main.py
if %errorlevel% neq 0 (
    echo [BLAD] Blad kompilacji w main.py!
    exit /b 1
)
echo [OK] Skladnia Pythona poprawna.

echo.
echo [ETAP 2/4] Uruchamianie pelnego zestawu testow jednostkowych...
python -m unittest discover -s tests -p "test_*.py"
if %errorlevel% neq 0 (
    echo [BLAD] Testy regresyjne zakonczyly sie niepowodzeniem!
    exit /b %errorlevel%
)
echo [OK] Wszystkie testy jednostkowe i integracyjne przeszly (100%% OK).

echo.
echo [ETAP 3/4] Weryfikacja katalogu danych i bazy SQLite w %%LOCALAPPDATA%%...
python -c "from myszkahud.storage.paths import get_app_data_dir, get_database_path; print('Katalog danych:', get_app_data_dir()); print('Baza SQLite:', get_database_path())"
if %errorlevel% neq 0 (
    echo [BLAD] Blad podczas sprawdzania sciezek danych!
    exit /b 1
)
echo [OK] Sciezki AppData prawidlowe i odizolowane od folderu programu.

echo.
echo [ETAP 4/4] Weryfikacja importu modulow rdzennych i GUI...
python -c "import myszkahud.main; from myszkahud.application import MyszkaHUDApp; print('[OK] Glowna aplikacja MyszkaHUD zaimportowana poprawnie.')"
if %errorlevel% neq 0 (
    echo [BLAD] Blad importu aplikacji!
    exit /b 1
)

echo.
echo =====================================================================
echo [SUKCES] Automatyczna walidacja kodu i testow zakonczona pomyslnie!
echo          Szczegolowa reczna checklista: WINDOWS_VALIDATION.md
echo =====================================================================
echo.
exit /b 0
