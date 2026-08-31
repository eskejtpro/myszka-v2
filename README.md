# MyszkaHUD

MyszkaHUD to szybki, lekki i nowoczesny radialny HUD narzędziowy pod kursorem myszy przeznaczony dla systemu **Windows 10 64-bit**.

Domyślny skrót otwierający HUD: **Alt + Q**

## Wymagania
- Windows 10 64-bit (22H2 / build 19045+)
- Python 3.10+ (w tym Python 3.14)
- PySide6

## Uruchomienie lokalne

### Krok 1. Instalacja zależności
```cmd
pip install -r requirements.txt
```
lub
```cmd
pip install PySide6 psutil google-genai pytest
```

### Krok 2. Uruchomienie aplikacji
```cmd
run.bat
```
lub
```cmd
python -m src.myszkahud
```

### Krok 3. Użycie
1. Wciśnij **Alt + Q** w dowolnym miejscu systemu Windows.
2. Radialny HUD pojawi się przy aktualnej pozycji kursora myszy.
3. Naciśnij **Esc** lub kliknij poza HUD, aby go zamknąć.
