# MediaProcessor

Narzędzie do przetwarzania mediów z graficznym interfejsem (GUI). Pozwala na dzielenie plików audio na chunki z nakładaniem oraz łączenie transkrypcji SRT.

**⚠️ WAŻNE: To oprogramowanie jest dostępne "TAK JAK JEST" bez żadnych gwarancji.**

## Funkcje

### 🎵 Audio Chunker

- Dzielenie plików MP3 i MP4 na chunks (fragmenty)
- Konfiguracja długości chunku (domyślnie 10 minut)
- Obsługa nakładania (overlap) - kolejne chunki zaczynają się wcześniej
- Przykład: przy 10-minutowych chunkach i 1-minutowym nakładaniu:
  - chunk 1: 0-10min
  - chunk 2: 9-20min
  - chunk 3: 19-30min
  - itd.
- Wyjście: MP4 z audio AAC
- Live progress bar
- Możliwość anulowania

### 📝 SRT Merger

- Łączenie wielu plików transkrypcji SRT
- Obsługa nakładania - automatyczne usuwanie duplikatów
- Zmiana kolejności plików (drag & drop)
- Generowanie jednej długiej transkrypcji
- Prawidłowe dopasowanie czasów

## Instalacja

### Windows (Standalone)

Pobierz `MediaProcessor.zip` z [Releases](releases) i rozpakuj go. Nie wymagane żadne dodatkowe instalacje!

```
MediaProcessor/
├── MediaProcessor.exe
└── ffmpeg/bin/
```

Kliknij `MediaProcessor.exe` i gotowe.

### Development (z Pythona)

Wymagania:

- Python 3.13+
- ffmpeg (w PATH lub w folderze `ffmpeg/bin/`)

```bash
# Klonuj repo
git clone <repo-url>
cd media-processor

# Stwórz virtual environment
python -m venv .venv
.venv\Scripts\activate  # Windows
# lub
source .venv/bin/activate  # Linux/Mac

# Zainstaluj zależności
pip install -r requirements.txt

# Uruchom aplikację
python audio_chunker_gui.py
```

## Użycie

### Audio Chunker

1. Otwórz zakładkę "🎵 Audio Chunker"
2. Kliknij "Wybierz plik..." i wybierz plik MP3 lub MP4
3. Ustaw parametry:
   - Długość chunku (w minutach)
   - Nakładanie (w minutach)
4. Wybierz folder wyjściowy (domyślnie `chunks`)
5. Kliknij "PODZIEL PLIK"
6. Obserwuj progress bar i log statusu

Wynik: Pliki MP4 o nazwach `chunk_001_000-010min.mp4`, `chunk_002_009-020min.mp4`, itd.

### SRT Merger

1. Otwórz zakładkę "📝 SRT Merger"
2. Kliknij "Dodaj plik SRT" i dodaj pliki (w kolejności)
3. Możesz zmienić kolejność (↑ Wyżej, ↓ Niżej) lub usunąć (Usuń wybrany)
4. Ustaw parametry nakładania (takie same jak w Audio Chunkerze)
5. Kliknij "SCALIĆ TRANSKRYPCJE"
6. Wybierz gdzie zapisać wynik (np. `output.srt`)

Wynik: Jeden plik SRT z wszystkimi wpisami, czasami dopasowanymi dla nakładań.

## Wymagania systemowe

- Windows 10+ (64-bit)
- ~500 MB wolnego miejsca na dysku (dla aplikacji + ffmpeg)
- Procesor: Intel/AMD x64

## Technologia

- **Python 3.13**
- **PyQt5** - GUI
- **librosa** - przetwarzanie audio
- **soundfile** - zapis audio
- **ffmpeg** - konwersja do MP4
- **PyInstaller** - pakowanie na .exe

## Licencja

MIT License - patrz [LICENSE](LICENSE)

## Disclaimer

To oprogramowanie jest dostarczane "AS IS" (TAK JAK JEST) bez żadnych gwarancji, jawnych lub dorozumianych. Autor nie bierze odpowiedzialności za:

- Uszkodzenia lub utratę danych
- Niedziałające funkcje
- Wpływ na wydajność systemu

Używasz go na własne ryzyko.

## Zgłaszanie błędów

Jeśli znalazłeś błąd, otwórz [Issue](issues) na GitHubie z opisem problemu i krokami do reprodukcji.

## TODO

- [ ] Wsparcie dla formatów audio: WAV, FLAC, M4A
- [ ] Eksport chunków w różnych formatach
- [ ] Wizualizacja waveformu
- [ ] Batch processing
- [ ] Multilang GUI

---

**Made with ❤️**
