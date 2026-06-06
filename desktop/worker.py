# desktop/worker.py
from pathlib import Path
from PyQt6.QtCore import QThread, pyqtSignal
from core.engine import convert
from core.models import ConversionResult

class ConversionWorker(QThread):
    finished = pyqtSignal(ConversionResult)
    error = pyqtSignal(str)

    def __init__(self, source: Path, output_dir: Path):
        super().__init__()
        self.source = source
        self.output_dir = output_dir

    def run(self):
        try:
            result = convert(self.source, self.output_dir)
            self.finished.emit(result)
        except Exception as exc:
            self.error.emit(str(exc))
