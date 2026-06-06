# Markify

**Convert Word, PowerPoint, Excel, PDF, and plain text files into clean Markdown — instantly.**

[![Live Demo](https://img.shields.io/badge/Live%20Demo-markify--indol.vercel.app-64b5f6?style=flat-square&logo=vercel&logoColor=white)](https://markify-indol.vercel.app)
[![Python](https://img.shields.io/badge/Python-3.11+-3776ab?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![PyQt6](https://img.shields.io/badge/Desktop-PyQt6-41cd52?style=flat-square&logo=qt&logoColor=white)](https://doc.qt.io/qtforpython)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow?style=flat-square)](LICENSE)

---

## What it does

Markify converts documents into high-fidelity Markdown — preserving headings, tables, bold/italic formatting, images, and more.

| Format | What's preserved |
|--------|-----------------|
| **Word** (.docx, .doc) | Headings, bold/italic/underline, tables, images, footnotes |
| **PowerPoint** (.pptx, .ppt) | Slide titles, bullet points (nested), speaker notes, images |
| **Excel** (.xlsx, .xls) | Sheet names as headings, data as GFM tables, resolved formula values |
| **PDF** (.pdf) | Text with heading detection, tables, embedded images |
| **Text / CSV / RTF** | Plain text passthrough, CSV → GFM table, RTF tag stripping |

---

## Demo

**Web app** → [markify-indol.vercel.app](https://markify-indol.vercel.app)

Drop any supported file onto the page, click **Convert All**, and get clean Markdown with a live preview — download as `.md` or a ZIP.

---

## Features

- **High-fidelity conversion** — images extracted to `/assets/`, tables rendered as GFM pipe tables, nested lists preserved
- **Two surfaces** — a browser-based web app and a native desktop app (PyQt6)
- **Live preview** — rendered HTML view with toggle to raw Markdown
- **Batch conversion** — drop multiple files, convert all at once, download as ZIP
- **Copy to clipboard** — one click, with toast confirmation
- **Modern Glass UI** — deep navy, frosted header, gradient accents, fully responsive
- **Keyboard accessible** — tab navigation, focus rings, ARIA labels, `prefers-reduced-motion` respected

---

## Project structure

```
markify/
├── core/                    # Shared conversion engine (no UI)
│   ├── converters/
│   │   ├── docx.py          # Word → Markdown
│   │   ├── pptx.py          # PowerPoint → Markdown
│   │   ├── xlsx.py          # Excel → Markdown
│   │   ├── pdf.py           # PDF → Markdown
│   │   └── text.py          # TXT / CSV / RTF → Markdown
│   ├── extractor.py         # Image extraction to /assets/
│   ├── models.py            # ConversionJob / ConversionResult dataclasses
│   └── engine.py            # Orchestrator — routes files to converters
│
├── desktop/                 # PyQt6 desktop app
│   ├── main.py              # Entry point
│   ├── ui/
│   │   ├── main_window.py   # Split-panel window + stylesheet
│   │   ├── file_queue.py    # Left panel: drag-drop file list
│   │   └── preview.py       # Right panel: live Markdown preview
│   └── worker.py            # QThread — non-blocking conversion
│
├── web/                     # FastAPI web app
│   ├── main.py              # API routes
│   ├── templates/index.html # Single-page frontend
│   ├── static/style.css     # Modern Glass stylesheet
│   └── static/app.js        # Drop zone, upload, preview logic
│
├── tests/                   # Full test suite (28 tests)
├── requirements.txt         # Web / core dependencies
├── requirements-desktop.txt # + PyQt6 for desktop
├── requirements-dev.txt     # + pytest, httpx for development
└── vercel.json              # Vercel deployment config
```

---

## Getting started

### Prerequisites

- Python 3.11+
- pip

### Web app

```bash
git clone https://github.com/nqobile-x/markify.git
cd markify
pip install -r requirements.txt
uvicorn web.main:app --reload --port 8000
```

Open [http://localhost:8000](http://localhost:8000).

### Desktop app

```bash
pip install -r requirements-desktop.txt
python desktop/main.py
```

The desktop app opens a split-panel window — drag files onto the left panel, click **Convert All**, and the Markdown renders live on the right.

### Tests

```bash
pip install -r requirements-dev.txt
pytest tests/ -v
```

28 tests across all converters, the engine, and the web API — all should pass.

---

## API reference

The web app exposes a simple REST API:

| Method | Route | Description |
|--------|-------|-------------|
| `POST` | `/convert` | Upload a file → returns `{ job_id, markdown, status }` |
| `GET` | `/status/{job_id}` | Poll conversion status |
| `GET` | `/download/{job_id}` | Download the `.md` file |
| `GET` | `/download/{job_id}/zip` | Download all outputs as ZIP |
| `DELETE` | `/job/{job_id}` | Clean up server-side temp files |

**Limits:** 50 MB per file. Supported extensions: `.docx` `.doc` `.pptx` `.ppt` `.xlsx` `.xls` `.pdf` `.txt` `.csv` `.rtf`

---

## Tech stack

| Layer | Tech |
|-------|------|
| Conversion engine | python-docx, python-pptx, openpyxl, pdfplumber, pymupdf, striprtf |
| Web backend | FastAPI, uvicorn, Jinja2 |
| Web frontend | Vanilla HTML/CSS/JS, Plus Jakarta Sans |
| Desktop GUI | PyQt6, QWebEngineView |
| Tests | pytest, httpx |
| Deployment | Vercel (web), PyInstaller (desktop packaging) |

---

## Deployment

The web app is deployed on Vercel and auto-deploys on every push to `master`.

To package the desktop app as a standalone executable:

```bash
pip install pyinstaller
pyinstaller --onefile --windowed --name Markify desktop/main.py
# Output: dist/Markify.exe (Windows) or dist/Markify (macOS)
```

---

## License

MIT — see [LICENSE](LICENSE).
