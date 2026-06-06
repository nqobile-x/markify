# desktop/ui/preview.py
from pathlib import Path
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QTextEdit, QFileDialog, QApplication
)
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtCore import Qt
import markdown as md_lib

class PreviewWidget(QWidget):
    def __init__(self):
        super().__init__()
        self._raw_markdown = ""
        self._show_raw = False
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        header = QHBoxLayout()
        self.title = QLabel("Preview")
        self.title.setObjectName("panelTitle")
        header.addWidget(self.title)
        header.addStretch()

        self.toggle_btn = QPushButton("Raw Markdown")
        self.toggle_btn.setObjectName("secondaryBtn")
        self.toggle_btn.clicked.connect(self._toggle_view)
        header.addWidget(self.toggle_btn)

        self.copy_btn = QPushButton("Copy")
        self.copy_btn.setObjectName("secondaryBtn")
        self.copy_btn.clicked.connect(self._copy)
        header.addWidget(self.copy_btn)

        self.save_btn = QPushButton("Save As…")
        self.save_btn.setObjectName("secondaryBtn")
        self.save_btn.clicked.connect(self._save)
        header.addWidget(self.save_btn)

        layout.addLayout(header)

        self.web_view = QWebEngineView()
        self.web_view.setObjectName("previewWeb")
        layout.addWidget(self.web_view)

        self.raw_edit = QTextEdit()
        self.raw_edit.setReadOnly(True)
        self.raw_edit.setObjectName("rawEdit")
        self.raw_edit.hide()
        layout.addWidget(self.raw_edit)

    def set_markdown(self, text: str):
        self._raw_markdown = text
        self._render()

    def _render(self):
        if self._show_raw:
            self.raw_edit.setPlainText(self._raw_markdown)
        else:
            html = md_lib.markdown(self._raw_markdown, extensions=["tables", "fenced_code"])
            styled = f"""<html><head><style>
body {{ background: #0d1b2a; color: #e0e0e0; font-family: system-ui; padding: 16px; }}
h1,h2,h3 {{ color: #64b5f6; }}
table {{ border-collapse: collapse; width: 100%; }}
th, td {{ border: 1px solid #333; padding: 6px 10px; }}
th {{ background: rgba(100,181,246,0.1); }}
blockquote {{ border-left: 3px solid #7c4dff; padding-left: 12px; color: #aaa; }}
code {{ background: #1a2a3a; padding: 2px 6px; border-radius: 4px; }}
</style></head><body>{html}</body></html>"""
            self.web_view.setHtml(styled)

    def _toggle_view(self):
        self._show_raw = not self._show_raw
        self.toggle_btn.setText("Preview" if self._show_raw else "Raw Markdown")
        self.web_view.setVisible(not self._show_raw)
        self.raw_edit.setVisible(self._show_raw)
        self._render()

    def _copy(self):
        QApplication.clipboard().setText(self._raw_markdown)

    def _save(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save Markdown", "", "Markdown (*.md)")
        if path:
            Path(path).write_text(self._raw_markdown, encoding="utf-8")
