# desktop/ui/file_queue.py
from pathlib import Path
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QListWidget, QListWidgetItem,
    QPushButton, QLabel, QFileDialog, QAbstractItemView
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor

FORMAT_COLORS = {
    ".docx": "#4fc3f7", ".doc": "#4fc3f7",
    ".pptx": "#ff8a65", ".ppt": "#ff8a65",
    ".xlsx": "#81c784", ".xls": "#81c784",
    ".pdf": "#ce93d8",
    ".txt": "#e0e0e0", ".csv": "#fff176", ".rtf": "#ffcc80",
}

class FileQueueWidget(QWidget):
    files_changed = pyqtSignal(list)
    convert_requested = pyqtSignal(list, object)  # files: list[Path], output_dir: Path|None
    file_selected = pyqtSignal(Path)

    def __init__(self):
        super().__init__()
        self.files: list[Path] = []
        self.output_dir: Path | None = None
        self._build_ui()
        self.setAcceptDrops(True)

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        drop_label = QLabel("✦ Drop files here")
        drop_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        drop_label.setObjectName("dropZone")
        drop_label.setFixedHeight(72)
        drop_label.mousePressEvent = lambda _: self._browse_files()
        layout.addWidget(drop_label)

        self.list_widget = QListWidget()
        self.list_widget.setObjectName("fileList")
        self.list_widget.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.list_widget.itemClicked.connect(self._on_item_clicked)
        self.list_widget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.list_widget.customContextMenuRequested.connect(self._on_right_click)
        layout.addWidget(self.list_widget)

        self.output_btn = QPushButton("Output: same as source")
        self.output_btn.setObjectName("secondaryBtn")
        self.output_btn.clicked.connect(self._pick_output_dir)
        layout.addWidget(self.output_btn)

        self.convert_btn = QPushButton("Convert All")
        self.convert_btn.setObjectName("primaryBtn")
        self.convert_btn.clicked.connect(self._on_convert)
        layout.addWidget(self.convert_btn)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        for url in event.mimeData().urls():
            path = Path(url.toLocalFile())
            if path.is_file():
                self._add_file(path)

    def _browse_files(self):
        paths, _ = QFileDialog.getOpenFileNames(
            self, "Select files", "",
            "Documents (*.docx *.doc *.pptx *.ppt *.xlsx *.xls *.pdf *.txt *.csv *.rtf)"
        )
        for p in paths:
            self._add_file(Path(p))

    def _add_file(self, path: Path):
        if path not in self.files:
            self.files.append(path)
            self._refresh_list()
            self.files_changed.emit(self.files)

    def _refresh_list(self):
        self.list_widget.clear()
        for path in self.files:
            item = QListWidgetItem(f"{path.name}  [{path.suffix.upper().lstrip('.')}]")
            color = FORMAT_COLORS.get(path.suffix.lower(), "#e0e0e0")
            item.setForeground(QColor(color))
            self.list_widget.addItem(item)

    def _on_item_clicked(self, item):
        row = self.list_widget.row(item)
        self.file_selected.emit(self.files[row])

    def _on_right_click(self, pos):
        item = self.list_widget.itemAt(pos)
        if item:
            row = self.list_widget.row(item)
            self.files.pop(row)
            self._refresh_list()
            self.files_changed.emit(self.files)

    def _pick_output_dir(self):
        d = QFileDialog.getExistingDirectory(self, "Select output folder")
        if d:
            self.output_dir = Path(d)
            self.output_btn.setText(f"Output: {self.output_dir.name}")

    def _on_convert(self):
        if not self.files:
            return
        self.convert_requested.emit(self.files, self.output_dir)

    def set_file_status(self, path: Path, status: str):
        status_icons = {"converting": "⏳", "done": "✓", "error": "✗"}
        icon = status_icons.get(status, "")
        for i, f in enumerate(self.files):
            if f == path:
                suffix = f.suffix.upper().lstrip(".")
                self.list_widget.item(i).setText(f"{icon} {f.name}  [{suffix}]")
                break
