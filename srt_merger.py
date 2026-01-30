import re
from pathlib import Path
from typing import List, Tuple


class SRTEntry:
    def __init__(self, index: int, start: str, end: str, text: str):
        self.index = index
        self.start = start
        self.end = end
        self.text = text
    
    def time_to_ms(self, time_str: str) -> int:
        """Konwertuj HH:MM:SS,mmm na milisekundy"""
        match = re.match(r'(\d+):(\d+):(\d+),(\d+)', time_str)
        if match:
            h, m, s, ms = map(int, match.groups())
            return h * 3600000 + m * 60000 + s * 1000 + ms
        return 0
    
    def ms_to_time(self, ms: int) -> str:
        """Konwertuj milisekundy na HH:MM:SS,mmm"""
        h = ms // 3600000
        m = (ms % 3600000) // 60000
        s = (ms % 60000) // 1000
        ms_part = ms % 1000
        return f"{h:02d}:{m:02d}:{s:02d},{ms_part:03d}"
    
    def get_start_ms(self) -> int:
        return self.time_to_ms(self.start)
    
    def get_end_ms(self) -> int:
        return self.time_to_ms(self.end)


def parse_srt(file_path: str) -> List[SRTEntry]:
    """Parsuj plik SRT"""
    entries = []
    
    with open(file_path, 'r', encoding='utf-8-sig') as f:
        content = f.read()
    
    # Podziel na bloki (rozdzielone pustymi liniami)
    blocks = re.split(r'\n\s*\n', content.strip())
    
    for block in blocks:
        lines = block.strip().split('\n')
        if len(lines) >= 3:
            try:
                index = int(lines[0])
                time_range = lines[1]
                text = '\n'.join(lines[2:])
                
                match = re.match(r'(\d+:\d+:\d+,\d+)\s+-->\s+(\d+:\d+:\d+,\d+)', time_range)
                if match:
                    start, end = match.groups()
                    entries.append(SRTEntry(index, start, end, text))
            except:
                pass
    
    return entries


def merge_srt_files(
    files: List[Tuple[str, int, int]],  # [(path, chunk_duration_min, overlap_min), ...]
    output_file: str
) -> str:
    """
    Merge SRT files z obsługą nakładania.
    
    Args:
        files: Lista tupli (path, chunk_duration_min, overlap_min)
        output_file: Ścieżka do wyjściowego pliku
    
    Returns:
        Komunikat statusu
    """
    
    all_entries = []
    entry_index = 1
    time_offset = 0  # Offset czasowy w ms dla obecnego pliku
    
    for file_path, chunk_duration, overlap in files:
        entries = parse_srt(file_path)
        
        if not entries:
            return f"❌ Błąd: plik {file_path} jest pusty lub nie parsuje się prawidłowo"
        
        # Konwertuj minuty na ms
        chunk_ms = chunk_duration * 60 * 1000
        overlap_ms = overlap * 60 * 1000
        
        # Jeśli to nie pierwszy plik, usuń ostatnie wpisy z poprzedniego (które się nakładają)
        if all_entries and overlap_ms > 0:
            # Ostatni wpis z poprzedniego chunku
            last_entry = all_entries[-1] if all_entries else None
            if last_entry:
                last_start = last_entry.get_start_ms()
                
                # Usuń wpisy z okresu nakładania (ostatnia minuta poprzedniego)
                cutoff_time = last_start + chunk_ms - overlap_ms
                all_entries = [e for e in all_entries if e.get_end_ms() <= cutoff_time]
        
        # Dodaj wpisy z obecnego pliku z przesunięciem czasowym
        for entry in entries:
            new_entry = SRTEntry(
                index=entry_index,
                start=entry.ms_to_time(entry.get_start_ms() + time_offset),
                end=entry.ms_to_time(entry.get_end_ms() + time_offset),
                text=entry.text
            )
            all_entries.append(new_entry)
            entry_index += 1
        
        # Zaktualizuj offset dla następnego pliku
        # Następny plik zaczyna się (chunk_duration - overlap) minut później
        time_offset += (chunk_ms - overlap_ms)
    
    # Zapisz wynik
    with open(output_file, 'w', encoding='utf-8') as f:
        for entry in all_entries:
            f.write(f"{entry.index}\n")
            f.write(f"{entry.start} --> {entry.end}\n")
            f.write(f"{entry.text}\n\n")
    
    return f"✅ Wygenerowano transkrypcję: {output_file}\nŁącznie wpisów: {len(all_entries)}"
