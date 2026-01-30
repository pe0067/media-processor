import sys
import os
from pathlib import Path
from threading import Thread
import subprocess
import librosa
import soundfile as sf
from srt_merger import merge_srt_files

# Szukaj ffmpeg w folderze aplikacji
def get_ffmpeg_path():
    """Szuka ffmpeg w folderze aplikacji (dla embedded wersji)"""
    if getattr(sys, 'frozen', False):
        # PyInstaller bundle
        base_path = sys._MEIPASS
    else:
        # Development
        base_path = os.path.dirname(os.path.abspath(__file__))
    
    ffmpeg_path = os.path.join(base_path, 'ffmpeg', 'bin', 'ffmpeg.exe')
    if os.path.exists(ffmpeg_path):
        return ffmpeg_path
    
    # Fallback na system PATH
    return 'ffmpeg'

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QSpinBox, QTextEdit, QFileDialog,
    QProgressBar, QGroupBox, QFormLayout, QTabWidget, QListWidget,
    QListWidgetItem
)
from PyQt5.QtCore import Qt, pyqtSignal, QObject, QThread
from PyQt5.QtGui import QFont


class ChunkerWorker(QObject):
    progress = pyqtSignal(str)
    progress_percent = pyqtSignal(int)
    finished = pyqtSignal(bool)
    
    def __init__(self, input_file, output_dir, chunk_duration, overlap):
        super().__init__()
        self.input_file = input_file
        self.output_dir = output_dir
        self.chunk_duration = chunk_duration
        self.overlap = overlap
        self.cancelled = False
    
    def cancel(self):
        self.cancelled = True
    
    def run(self):
        try:
            self.chunk_audio()
            if not self.cancelled:
                self.finished.emit(True)
            else:
                self.progress.emit("❌ Anulowano przez użytkownika")
                self.finished.emit(False)
        except Exception as e:
            self.progress.emit(f"❌ Błąd: {str(e)}")
            self.finished.emit(False)
    
    def chunk_audio(self):
        input_path = Path(self.input_file)
        output_path = Path(self.output_dir)
        
        output_path.mkdir(parents=True, exist_ok=True)
        self.progress.emit(f"Ładowanie pliku: {input_path.name}")
        
        if self.cancelled:
            return
        
        # Ładujemy plik audio
        audio, sr = librosa.load(str(input_path), sr=None)
        
        total_samples = len(audio)
        total_duration_sec = total_samples / sr
        total_duration_min = total_duration_sec / 60
        
        self.progress.emit(f"Całkowita długość: {total_duration_min:.2f} minut")
        self.progress.emit(f"Sample rate: {sr} Hz\n")
        
        chunk_samples = int(self.chunk_duration * 60 * sr)
        overlap_samples = int(self.overlap * 60 * sr)
        step_samples = chunk_samples - overlap_samples
        
        # Oblicz liczbę chunków
        chunk_number = 1
        start_sample = 0
        total_chunks = 0
        
        # Najpierw policz ile będzie chunków
        temp_start = 0
        while temp_start < total_samples:
            total_chunks += 1
            temp_end = min(temp_start + chunk_samples, total_samples)
            if temp_end >= total_samples:
                break
            temp_start += step_samples
        
        self.progress.emit(f"Przewidywanych chunków: {total_chunks}")
        
        temp_dir = output_path / ".temp_wav"
        temp_dir.mkdir(parents=True, exist_ok=True)
        
        while start_sample < total_samples:
            if self.cancelled:
                import shutil
                shutil.rmtree(temp_dir)
                return
            
            end_sample = min(start_sample + chunk_samples, total_samples)
            chunk = audio[start_sample:end_sample]
            
            start_min = int(start_sample / (sr * 60))
            end_min = int(end_sample / (sr * 60))
            temp_file = temp_dir / f"chunk_{chunk_number:03d}.wav"
            output_file = output_path / f"chunk_{chunk_number:03d}_{start_min:03d}-{end_min:03d}min.mp4"
            
            sf.write(str(temp_file), chunk, sr)
            
            try:
                # CREATE_NO_WINDOW = 0x08000000 - ukryj okno konsoli
                subprocess.run(
                    [get_ffmpeg_path(), "-i", str(temp_file), "-q:a", "5", "-c:a", "aac", "-y", str(output_file)],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    check=True,
                    creationflags=0x08000000 if sys.platform == 'win32' else 0
                )
                duration_chunk = len(chunk) / (sr * 60)
                self.progress.emit(f"✓ {output_file.name} ({duration_chunk:.2f} min)")
                
                # Aktualizuj progress bar (cap na 100%)
                percent = int((chunk_number / total_chunks) * 100) if total_chunks > 0 else 0
                percent = min(percent, 100)  # Nie przekraczaj 100%
                self.progress_percent.emit(percent)
                
            except subprocess.CalledProcessError as e:
                self.progress.emit(f"❌ Błąd konwersji: {output_file}")
                raise
            
            if end_sample >= total_samples:
                break
            
            start_sample += step_samples
            chunk_number += 1
        
        import shutil
        shutil.rmtree(temp_dir)
        
        self.progress_percent.emit(100)
        self.progress.emit(f"\n✅ Gotowe! Stworzono {chunk_number} chunków")




class SRTMergerTab(QWidget):
    def __init__(self):
        super().__init__()
        self.srt_files = []  # List of (filepath, chunk_duration, overlap)
        self.init_ui()
    
    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(15, 15, 15, 15)
        
        # --- LISTA PLIKÓW ---
        list_group = QGroupBox("Pliki SRT do scalenia")
        list_layout = QVBoxLayout()
        
        self.file_list = QListWidget()
        self.file_list.setSelectionMode(QListWidget.SingleSelection)
        self.file_list.setMaximumHeight(200)
        list_layout.addWidget(self.file_list)
        
        # Przyciski do zarządzania listą
        buttons_layout = QHBoxLayout()
        
        add_btn = QPushButton("Dodaj plik SRT")
        add_btn.clicked.connect(self.add_srt_file)
        buttons_layout.addWidget(add_btn)
        
        remove_btn = QPushButton("Usuń wybrany")
        remove_btn.clicked.connect(self.remove_srt_file)
        buttons_layout.addWidget(remove_btn)
        
        up_btn = QPushButton("↑ Wyżej")
        up_btn.clicked.connect(self.move_up)
        buttons_layout.addWidget(up_btn)
        
        down_btn = QPushButton("↓ Niżej")
        down_btn.clicked.connect(self.move_down)
        buttons_layout.addWidget(down_btn)
        
        list_layout.addLayout(buttons_layout)
        list_group.setLayout(list_layout)
        main_layout.addWidget(list_group)
        
        # --- PARAMETRY ---
        params_group = QGroupBox("Parametry nakładania")
        params_layout = QFormLayout()
        
        self.chunk_spin = QSpinBox()
        self.chunk_spin.setValue(10)
        self.chunk_spin.setMinimum(1)
        self.chunk_spin.setSuffix(" minut")
        params_layout.addRow("Długość chunku:", self.chunk_spin)
        
        self.overlap_spin = QSpinBox()
        self.overlap_spin.setValue(1)
        self.overlap_spin.setMinimum(0)
        self.overlap_spin.setSuffix(" minut")
        params_layout.addRow("Nakładanie:", self.overlap_spin)
        
        params_group.setLayout(params_layout)
        main_layout.addWidget(params_group)
        
        # --- PRZYCISK MERGE ---
        self.merge_btn = QPushButton("SCALIĆ TRANSKRYPCJE")
        self.merge_btn.setFont(QFont("Arial", 12, QFont.Bold))
        self.merge_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                padding: 10px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0b7dda;
            }
            QPushButton:pressed {
                background-color: #0a68b7;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        self.merge_btn.clicked.connect(self.merge_files)
        main_layout.addWidget(self.merge_btn)
        
        # --- LOG ---
        log_label = QLabel("Status:")
        log_label.setFont(QFont("Arial", 10, QFont.Bold))
        main_layout.addWidget(log_label)
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont("Courier", 9))
        self.log_text.setMaximumHeight(200)
        main_layout.addWidget(self.log_text)
        
        main_layout.addStretch()
    
    def add_srt_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Wybierz plik SRT", "", "SRT files (*.srt);;All files (*)"
        )
        if file_path:
            chunk_dur = self.chunk_spin.value()
            overlap = self.overlap_spin.value()
            self.srt_files.append((file_path, chunk_dur, overlap))
            self.update_file_list()
    
    def remove_srt_file(self):
        current_row = self.file_list.currentRow()
        if current_row >= 0:
            del self.srt_files[current_row]
            self.update_file_list()
    
    def move_up(self):
        current_row = self.file_list.currentRow()
        if current_row > 0:
            self.srt_files[current_row], self.srt_files[current_row - 1] = \
                self.srt_files[current_row - 1], self.srt_files[current_row]
            self.update_file_list()
            self.file_list.setCurrentRow(current_row - 1)
    
    def move_down(self):
        current_row = self.file_list.currentRow()
        if current_row >= 0 and current_row < len(self.srt_files) - 1:
            self.srt_files[current_row], self.srt_files[current_row + 1] = \
                self.srt_files[current_row + 1], self.srt_files[current_row]
            self.update_file_list()
            self.file_list.setCurrentRow(current_row + 1)
    
    def update_file_list(self):
        self.file_list.clear()
        for i, (filepath, chunk_dur, overlap) in enumerate(self.srt_files, 1):
            filename = Path(filepath).name
            self.file_list.addItem(f"{i}. {filename} ({chunk_dur}m, {overlap}m overlap)")
    
    def merge_files(self):
        if not self.srt_files:
            self.log("❌ Dodaj co najmniej jeden plik SRT!")
            return
        
        # Zaktualizuj parametry dla wszystkich plików
        self.srt_files = [
            (filepath, self.chunk_spin.value(), self.overlap_spin.value())
            for filepath, _, _ in self.srt_files
        ]
        
        # Zapytaj o plik wyjściowy
        output_file, _ = QFileDialog.getSaveFileName(
            self, "Zapisz scalą transkrypcję", "", "SRT files (*.srt)"
        )
        
        if not output_file:
            return
        
        self.log_text.clear()
        self.log("Scalanie transkrypcji...")
        
        try:
            result = merge_srt_files(self.srt_files, output_file)
            self.log(result)
        except Exception as e:
            self.log(f"❌ Błąd: {str(e)}")
    
    def log(self, message):
        self.log_text.append(message)
        self.log_text.verticalScrollBar().setValue(
            self.log_text.verticalScrollBar().maximum()
        )


class AudioChunkerGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Audio Chunker & SRT Merger")
        self.setGeometry(100, 100, 800, 700)
        self.worker_thread = None
        self.worker = None
        self.init_ui()
    
    def init_ui(self):
        tabs = QTabWidget()
        self.setCentralWidget(tabs)
        
        # Tab 1: Audio Chunker (stary kod)
        chunker_widget = QWidget()
        chunker_layout = QVBoxLayout(chunker_widget)
        chunker_layout.setSpacing(15)
        chunker_layout.setContentsMargins(15, 15, 15, 15)
        
        # --- PLIKI ---
        files_group = QGroupBox("Pliki")
        files_layout = QFormLayout()
        
        self.input_line = QLineEdit()
        self.input_line.setReadOnly(True)
        input_btn = QPushButton("Wybierz plik...")
        input_btn.clicked.connect(self.select_input_file)
        input_layout = QHBoxLayout()
        input_layout.addWidget(self.input_line)
        input_layout.addWidget(input_btn)
        files_layout.addRow("Plik wejściowy (MP3/MP4):", input_layout)
        
        self.output_line = QLineEdit()
        self.output_line.setText("chunks")
        output_btn = QPushButton("Wybierz folder...")
        output_btn.clicked.connect(self.select_output_folder)
        output_layout = QHBoxLayout()
        output_layout.addWidget(self.output_line)
        output_layout.addWidget(output_btn)
        files_layout.addRow("Folder wyjściowy:", output_layout)
        
        files_group.setLayout(files_layout)
        chunker_layout.addWidget(files_group)
        
        # --- PARAMETRY ---
        params_group = QGroupBox("Parametry")
        params_layout = QFormLayout()
        
        self.chunk_spin = QSpinBox()
        self.chunk_spin.setValue(10)
        self.chunk_spin.setMinimum(1)
        self.chunk_spin.setSuffix(" minut")
        params_layout.addRow("Długość chunku:", self.chunk_spin)
        
        self.overlap_spin = QSpinBox()
        self.overlap_spin.setValue(1)
        self.overlap_spin.setMinimum(0)
        self.overlap_spin.setSuffix(" minut")
        params_layout.addRow("Nakładanie:", self.overlap_spin)
        
        params_group.setLayout(params_layout)
        chunker_layout.addWidget(params_group)
        
        # --- PRZYCISK START ---
        self.start_btn = QPushButton("PODZIEL PLIK")
        self.start_btn.setFont(QFont("Arial", 12, QFont.Bold))
        self.start_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 10px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        self.start_btn.clicked.connect(self.start_chunking)
        
        self.cancel_btn = QPushButton("ANULUJ")
        self.cancel_btn.setFont(QFont("Arial", 12, QFont.Bold))
        self.cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                padding: 10px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #da190b;
            }
            QPushButton:pressed {
                background-color: #ba0000;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        self.cancel_btn.clicked.connect(self.cancel_chunking)
        self.cancel_btn.setEnabled(False)
        
        buttons_layout = QHBoxLayout()
        buttons_layout.addWidget(self.start_btn)
        buttons_layout.addWidget(self.cancel_btn)
        chunker_layout.addLayout(buttons_layout)
        
        # --- PROGRESS BAR ---
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        chunker_layout.addWidget(self.progress_bar)
        
        # --- LOG ---
        log_label = QLabel("Status:")
        log_label.setFont(QFont("Arial", 10, QFont.Bold))
        chunker_layout.addWidget(log_label)
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont("Courier", 9))
        self.log_text.setMaximumHeight(200)
        chunker_layout.addWidget(self.log_text)
        
        chunker_layout.addStretch()
        
        # Dodaj zakładki
        tabs.addTab(chunker_widget, "🎵 Audio Chunker")
        tabs.addTab(SRTMergerTab(), "📝 SRT Merger")
    
    def select_input_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Wybierz plik audio", "", "Audio files (*.mp3 *.mp4);;All files (*)"
        )
        if file_path:
            self.input_line.setText(file_path)
    
    def select_output_folder(self):
        folder_path = QFileDialog.getExistingDirectory(self, "Wybierz folder docelowy")
        if folder_path:
            self.output_line.setText(folder_path)
    
    def start_chunking(self):
        input_file = self.input_line.text()
        output_dir = self.output_line.text()
        
        if not input_file:
            self.log("❌ Wybierz plik wejściowy!")
            return
        
        if not os.path.exists(input_file):
            self.log("❌ Plik nie istnieje!")
            return
        
        self.log_text.clear()
        self.progress_bar.setValue(0)  # Reset progress bar
        self.progress_bar.setVisible(True)
        self.start_btn.setEnabled(False)
        self.cancel_btn.setEnabled(True)
        
        self.worker = ChunkerWorker(input_file, output_dir, self.chunk_spin.value(), self.overlap_spin.value())
        self.worker_thread = QThread()
        self.worker.moveToThread(self.worker_thread)
        
        self.worker_thread.started.connect(self.worker.run)
        self.worker.progress.connect(self.log)
        self.worker.progress_percent.connect(self.progress_bar.setValue)
        self.worker.finished.connect(self.on_chunking_finished)
        
        self.worker_thread.start()
    
    def cancel_chunking(self):
        if self.worker:
            self.log("⏹️ Anulowanie...")
            self.worker.cancel()
            self.cancel_btn.setEnabled(False)
    
    def on_chunking_finished(self, success):
        self.start_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)
        self.progress_bar.setVisible(False)
        if self.worker_thread:
            self.worker_thread.quit()
            self.worker_thread.wait()
    
    def log(self, message):
        self.log_text.append(message)
        self.log_text.verticalScrollBar().setValue(
            self.log_text.verticalScrollBar().maximum()
        )


def main():
    app = QApplication(sys.argv)
    window = AudioChunkerGUI()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
