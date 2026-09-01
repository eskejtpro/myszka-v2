# MyszkaHUD — Raport i Checklista Walidacji Windows 10 (64-bit)

Data utworzenia: 2026-09-01  
Wersja aplikacji: **MyszkaHUD v0.14 (Validation Suite)**  
Docelowe środowisko produkcyjne: **Windows 10 64-bit (wersje 20H2 lub nowsze), Python 3.10–3.14 x64**

---

## 1. Status Walidacji Środowiska

| Środowisko | Status | Uwagi |
| :--- | :--- | :--- |
| **AI Studio Container (Linux)** | **100% OK (144 testy)** | Syntaktyka, logika biznesowa, mocki Win32, SQLite, architektura, regresja |
| **Prawdziwy Windows 10 x64** | **OCZEKUJE NA WINDOWS VALIDATION** | Wymaga uruchomienia pliku `.bat` oraz testu manualnego na maszynie fizycznej |

---

## 2. Macierz Testów i Scenariusze Walidacyjne Windows

### Scenariusz 1: Instalacja i Odizolowany Katalog Danych
- [ ] Folder instalacyjny programu (np. `C:\Program Files\MyszkaHUD\` lub folder read-only) nie zawiera modyfikowalnych plików stanu.
- [ ] Wszystkie dane dynamiczne trafiają do `%LOCALAPPDATA%\MyszkaHUD\`:
  - `myszkahud.db` (baza SQLite z historią schowka i notatkami)
  - `settings.json` (konfiguracja użytkownika)
  - `myszkahud.lock` (blokada instancji)
- [ ] Aplikacja działa bez uprawnień administratora (*Standard User*).

### Scenariusz 2: Jedna Instancja (Single Instance Guard)
- [ ] Pierwsze uruchomienie `MyszkaHUD.exe` dodaje ikonę do zasobnika systemowego Tray.
- [ ] Próba uruchomienia drugiego procesu `MyszkaHUD.exe` kończy się natychmiastowym bezpiecznym wyjściem (kod 0) bez tworzenia drugiego traya.

### Scenariusz 3: Globalny Skrót Klawiszowy `Alt + Q` i DPI
- [ ] Wciśnięcie `Alt + Q` w dowolnej aplikacji (Notatnik, Przeglądarka, Word) natychmiast wyświetla radialny HUD pod kursorem.
- [ ] Test na różnych skalowaniach DPI (100%, 125%, 150%, 200%) — HUD nie jest rozmyty i nie ucieka poza ekran.
- [ ] Test na konfiguracji wielomonitorowej (Multi-monitor) — HUD pojawia się na monitorze, na którym znajduje się kursor myszy.
- [ ] Wciśnięcie `Esc` lub kliknięcie lewym przyciskiem myszy poza HUD natychmiast ukrywa okno i zwraca fokus.

### Scenariusz 4: Akcje Tekstowe (Text Actions)
- [ ] Zaznaczenie tekstu w Notatniku -> `Alt + Q` -> Kafel `Akcje tekstu`:
  - `Kopiuj` (Ctrl+C)
  - `Wytnij` (Ctrl+X)
  - `Wklej` (Ctrl+V)
  - `Wklej + Enter` (Ctrl+V -> Enter)
  - `Zaznacz wszystko` (Ctrl+A)
- [ ] Fokus przed akcją wraca do poprzedniego aktywnego okna (HWND) przed wysłaniem zdarzenia Win32 SendInput.

### Scenariusz 5: Tłumacz Tekstu (Gemini Translation)
- [ ] Zaznaczenie tekstu w języku obcym -> `Alt + Q` -> Kafel `Tłumacz`:
  - Automatyczne skopiowanie tekstu przez Win32 sequence guard.
  - Wyświetlenie okna tłumacza z wpisanym tekstem źródłowym.
  - Odpowiedź z Gemini API i prezentacja w polu wyniku.
  - Przyciski `Kopiuj`, `Wklej`, `Wklej + Enter`.
- [ ] Test bez połączenia z Internetem / brak klucza API — czytelny komunikat błędu bez awarii programu.

### Scenariusz 6: OCR i Wycinanie Ekranu
- [ ] `Alt + Q` -> Kafel `OCR Ekranu`:
  - Zamrożenie ekranu i półprzezroczysta nakładka z siatką i krzyżowym kursorem.
  - Zaznaczenie prostokątnego obszaru myszką.
  - Wycinek przekazany do silnika OCR.
  - Okno wyników pozwala na edycję tekstu, ponowienie OCR lub przejście do Tłumacza.

### Scenariusz 7: Mowa na Tekst (Speech-to-Text)
- [ ] `Alt + Q` -> Kafel `Głos / STT`:
  - Płynne okno nagrywania z animacją fali i licznikiem czasu (00:00).
  - Limit nagrania: 60 sekund (automatyczne zakończenie).
  - Wciśnięcie Spacji lub kliknięcie mikrofonu kończy nagranie.
  - Wynik w oknie z opcjami Wklej, Kopiuj, Tłumacz.

### Scenariusz 8: Inteligentny Schowek i Notatki (`Alt + V`)
- [ ] Kopiowanie kolejnych tekstów w systemie rejestruje historię (do 200 wpisów).
- [ ] Mechanizm *Self-Write Suppression*: kopiowanie z wnętrza MyszkaHUD nie zapętla historii.
- [ ] Wyszukiwarka filtruje wpisy natychmiastowo.
- [ ] Przypinanie (PIN) chroni wpis przed usunięciem w trakcie automatycznego czyszczenia.
- [ ] Dodawanie, edycja i usuwanie notatek w SQLite.

### Scenariusz 9: Menedżer Procesów i Ochrona Systemowa
- [ ] Lista procesów pokazuje nazwę, PID, RAM (MB) i status.
- [ ] Bezpieczne zamykanie (`WM_CLOSE`) dla zwykłych okien użytkownika.
- [ ] Blokada krytycznych procesów Windows (`System`, `csrss.exe`, `lsass.exe`, `explorer.exe`, itp.) — przycisk Zabij jest zablokowany.
- [ ] Ochrona własnego procesu MyszkaHUD przed przypadkowym zabiciem.

### Scenariusz 10: Monitor RAM i Bezpieczne Zwalnianie
- [ ] Pasek zużycia pamięci RAM (użycie w GB, wolna pamięć, procent).
- [ ] Kliknięcie `Zwolnij pamięć`:
  - Wykonuje bezpieczne trimowanie zestawów roboczych (`EmptyWorkingSet`) i czyszczenie GC.
  - Prezentuje realną deltę pamięci przed i po (bez oszukańczych wskaźników).

### Scenariusz 11: Centrum Ustawień i Autostart Windows
- [ ] Zmiana ustawień zapisuje się w `settings.json`.
- [ ] Zaznaczenie opcji `Uruchamiaj przy starcie Windows`:
  - Dodaje klucz w rejestrze `HKCU\Software\Microsoft\Windows\CurrentVersion\Run`.
  - Nie wymaga praw administratora.
- [ ] Usunięcie zaznaczenia usuwa klucz rejestru.
- [ ] Test uszkodzonego pliku `settings.json` — aplikacja wstaje na wartościach domyślnych bez błędu.

---

## 3. Instrukcja Przeprowadzenia Testu na Windows 10

1. Sklonuj repozytorium lub wypakuj paczkę źródłową.
2. Otwórz `Wiersz polecenia (CMD)` w katalogu projektu.
3. Wykonaj skrypt automatyczny:
   ```cmd
   validate_windows.bat
   ```
4. Zbuduj wersję instalacyjną EXE:
   ```cmd
   build_windows.bat
   ```
5. Uruchom wygenerowany plik `dist\MyszkaHUD.exe` i zweryfikuj powyższą checklistę.
