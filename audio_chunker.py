import argparse
from pathlib import Path
import subprocess
import librosa
import soundfile as sf


def chunk_audio(input_file: Path, output_dir: Path, chunk_duration_minutes: int = 10, overlap_minutes: int = 1):
    """
    Dzieli plik audio na chunki z nakładaniem.
    
    Args:
        input_file: Ścieżka do pliku audio (mp3 lub mp4)
        output_dir: Folder docelowy na chunki (zawsze MP4)
        chunk_duration_minutes: Długość każdego chunku w minutach (domyślnie 10)
        overlap_minutes: Długość nakładania w minutach (domyślnie 1)
    """
    
    # Tworzymy folder na wyjście
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Ładowanie pliku audio: {input_file}")
    
    # Ładujemy plik audio
    audio, sr = librosa.load(str(input_file), sr=None)
    
    total_samples = len(audio)
    total_duration_sec = total_samples / sr
    total_duration_min = total_duration_sec / 60
    
    print(f"Całkowita długość: {total_duration_min:.2f} minut ({total_duration_sec:.1f}s)")
    print(f"Sample rate: {sr} Hz\n")
    
    # Konwertujemy minuty na próbki (samples)
    chunk_samples = int(chunk_duration_minutes * 60 * sr)
    overlap_samples = int(overlap_minutes * 60 * sr)
    
    # Krok między startami chunków (chunk - overlap)
    step_samples = chunk_samples - overlap_samples
    
    chunk_number = 1
    start_sample = 0
    
    # Najpierw zapisujemy chunki jako WAV (szybko), potem konwertujemy do MP3
    temp_dir = output_dir / ".temp_wav"
    temp_dir.mkdir(parents=True, exist_ok=True)
    
    while start_sample < total_samples:
        end_sample = min(start_sample + chunk_samples, total_samples)
        
        # Wyciągamy chunk
        chunk = audio[start_sample:end_sample]
        
        # Tworzymy nazwę pliku
        start_min = int(start_sample / (sr * 60))
        end_min = int(end_sample / (sr * 60))
        temp_file = temp_dir / f"chunk_{chunk_number:03d}.wav"
        output_file = output_dir / f"chunk_{chunk_number:03d}_{start_min:03d}-{end_min:03d}min.mp4"
        
        # Zapisujemy tymczasowy WAV
        sf.write(str(temp_file), chunk, sr)
        
        # Konwertujemy do MP4 za pomocą ffmpeg
        try:
            subprocess.run(
                ["ffmpeg", "-i", str(temp_file), "-q:a", "5", "-c:a", "aac", "-y", str(output_file)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=True
            )
            duration_chunk = len(chunk) / (sr * 60)
            print(f"✓ {output_file.name} ({duration_chunk:.2f} min)")
        except subprocess.CalledProcessError as e:
            print(f"❌ Błąd konwersji: {output_file}")
            return
        
        # Jeśli doszliśmy do końca, przerywamy
        if end_sample >= total_samples:
            break
        
        # Przesuwamy się do następnego chunku
        start_sample += step_samples
        chunk_number += 1
    
    # Usuwamy folder tymczasowy
    import shutil
    shutil.rmtree(temp_dir)
    
    print(f"\nGotowe! Stworzono {chunk_number} chunków w folderze: {output_dir}")


def main():
    p = argparse.ArgumentParser(description="Dzielenie pliku audio na chunki z nakładaniem (wyjście: MP4)")
    p.add_argument("input_file", help="Ścieżka do pliku audio (MP3 lub MP4)")
    p.add_argument("-o", "--out", default="chunks", help="Folder docelowy (domyślnie: chunks)")
    p.add_argument("-d", "--duration", type=int, default=10, help="Długość chunku w minutach (domyślnie: 10)")
    p.add_argument("-ov", "--overlap", type=int, default=1, help="Nakładanie w minutach (domyślnie: 1)")
    
    args = p.parse_args()
    
    input_path = Path(args.input_file)
    output_path = Path(args.out)
    
    if not input_path.exists():
        print(f"❌ Plik nie istnieje: {input_path}")
        exit(1)
    
    chunk_audio(input_path, output_path, args.duration, args.overlap)


if __name__ == "__main__":
    main()
