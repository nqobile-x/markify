from pathlib import Path
from PyQt6.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QSplitter, QApplication
from PyQt6.QtCore import Qt
from desktop.ui.file_queue import FileQueueWidget
from desktop.ui.preview import PreviewWidget
from desktop.worker import ConversionWorker
from core.models import ConversionResult

STYLESHEET = """
QMainWindow, QWidget#root {
    background-color: #0d1b2a;
    color: #e0e0e0;
    font-family: 'Segoe UI', system-ui, sans-serif;
}
QLabel#dropZone {
    border: 2px dashed rgba(100,181,246,0.4);
    border-radius: 8px;
    color: rgba(255,255,255,0.4);
    font-size: 13px;
}
QLabel#dropZone:hover { border-color: #64b5f6; color: #64b5f6; }
QListWidget#fileList {
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 6px;
    color: #e0e0e0;
}
QPushButton#primaryBtn {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #64b5f6,stop:1 #7c4dff);
    color: white; border: none; border-radius: 16px;
    padding: 8px 16px; font-weight: bold;
}
QPushButton#secondaryBtn {
    background: rgba(255,255,255,0.06);
    color: #64b5f6; border: 1px solid rgba(100,181,246,0.3);
    border-radius: 8px; padding: 5px 12px;
}
QPushButton#secondaryBtn:hover { background: rgba(100,181,246,0.1); }
QLabel#panelTitle { color: #64b5f6; font-size: 11px; letter-spacing: 2px; }
QSplitter::handle { background: rgba(255,255,255,0.06); width: 2px; }
"""

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Markify")
        self.setMinimumSize(900, 600)
        self.setStyleSheet(STYLESHEET)
        self._workers: list[ConversionWorker] = []
        self._results: dict[Path, ConversionResult] = {}

        root = QWidget()
        root.setObjectName("root")
        self.setCentralWidget(root)

        splitter = QSplitter(Qt.Orientation.Horizontal, root)
        layout = QHBoxLayout(root)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(splitter)

        self.queue = FileQueueWidget()
        self.preview = PreviewWidget()

        splitter.addWidget(self.queue)
        splitter.addWidget(self.preview)
        splitter.setSizes([300, 600])

        self.queue.convert_requested.connect(self._on_convert_requested)
        self.queue.file_selected.connect(self._on_file_selected)

    def _on_convert_requested(self, files: list, output_dir):
        for path in files:
            out = output_dir or path.parent
            self.queue.set_file_status(path, "converting")
            worker = ConversionWorker(path, out)
            worker.finished.connect(lambda r, p=path: self._on_conversion_done(r, p))
            worker.error.connect(lambda e, p=path: self._on_conversion_error(e, p))
            self._workers.append(worker)
            worker.start()

    def _on_conversion_done(self, result: ConversionResult, path: Path):
        self._results[path] = result
        if result.success:
            self.queue.set_file_status(path, "done")
            self.preview.set_markdown(result.markdown)
        else:
            self.queue.set_file_status(path, "error")
            self.preview.set_markdown(f"**Error:** {result.error}")

    def _on_conversion_error(self, error: str, path: Path):
        self.queue.set_file_status(path, "error")
        self.preview.set_markdown(f"**Error:** {error}")

    def _on_file_selected(self, path: Path):
        if path in self._results:
            result = self._results[path]
            self.preview.set_markdown(result.markdown if result.success else f"**Error:** {result.error}")
