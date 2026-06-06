# Markify — Design Spec
**Date:** 2026-06-06  
**Status:** Approved

---

## Overview

Markify is a high-fidelity document-to-markdown converter supporting Word, PowerPoint, Excel, PDF, and plain text/CSV files. It ships as two surfaces sharing a single Python conversion engine:

1. **Desktop app** — PyQt6, split-panel UI (file queue + live preview)
2. **Web app** — FastAPI backend + vanilla HTML/CSS/JS frontend

**Visual style:** Modern Glass — deep navy background, glass-morphism cards, gradient accents (`#64b5f6` → `#7c4dff`).  
**Target users:** Personal use and general public (production quality).  
**Fidelity goal:** High — images extracted to `/assets/`, tables preserved as GFM, formatting kept as close to source as possible.

---

## Architecture

```
markify/
├── core/                  # Shared conversion engine (pure Python, no UI)
│   ├── converters/
│   │   ├── docx.py        # Word → Markdown
│   │   ├── pptx.py        # PowerPoint → Markdown
│   │   ├── xlsx.py        # Excel → Markdown
│   │   ├── pdf.py         # PDF → Markdown
│   │   └── text.py        # TXT / CSV / RTF → Markdown
│   ├── extractor.py       # Image extraction (saves to /assets/ folder)
│   ├── models.py          # ConversionJob, ConversionResult dataclasses
│   └── engine.py          # Orchestrator — routes files to correct converter
│
├── desktop/               # PyQt6 desktop app
│   ├── main.py            # Entry point
│   ├── ui/
│   │   ├── main_window.py # Split-panel window
│   │   ├── file_queue.py  # Left panel — drag/drop file list
│   │   └── preview.py     # Right panel — live markdown preview
│   └── worker.py          # QThread worker (non-blocking conversion)
│
├── web/                   # FastAPI web app
│   ├── main.py            # FastAPI app + routes
│   ├── static/            # HTML/CSS/JS frontend
│   └── templates/         # Jinja2 HTML templates
│
└── requirements.txt
```

**Data flow:** Both desktop and web import `core.engine` directly. The engine accepts a file path, detects the format via magic bytes, calls the correct converter, extracts images to a sibling `/assets/` folder, and returns a `ConversionResult` with the markdown string and asset paths.

---

## Conversion Engine

Each converter follows the same contract: accepts a file path, returns markdown string + list of extracted asset paths.

### Word (.docx, .doc) — `python-docx`
- Heading styles → `#` `##` `###`
- Bold / italic / underline → `**bold**` / `_italic_` / `<u>underline</u>`
- Tables → GFM pipe tables
- Images → extracted to `/assets/`, referenced as `![img](assets/image_1.png)`
- Footnotes → `[^1]` inline footnotes

### PowerPoint (.pptx, .ppt) — `python-pptx`
- Each slide separated by `---` horizontal rule
- Slide title → `# Title`
- Bullet points → nested markdown lists (indent levels preserved)
- Speaker notes → `> Note: ...` blockquotes
- Images / charts → extracted to `/assets/`

### Excel (.xlsx, .xls) — `openpyxl`
- Each sheet → `## Sheet Name` heading
- Data range → GFM pipe table (auto-detects header row)
- Merged cells → unmerged, value repeated
- Formulas → resolved value (not formula string)

### PDF (.pdf) — `pdfplumber` + `pymupdf`
- Text extracted with layout awareness (multi-column handled)
- Larger-font text detected as headings → `#` headings
- Tables → best-effort GFM tables via `pdfplumber`
- Images → extracted per page to `/assets/`

### Plain text / CSV / RTF — stdlib + `striprtf`
- `.txt` → wrapped as-is in markdown
- `.rtf` → RTF tags stripped via `striprtf`, then treated as plain text
- `.csv` → parsed and rendered as GFM pipe table with header row

---

## Desktop App (PyQt6)

### Layout — Split Panel
- **Left panel (File Queue)**
  - Drag-and-drop zone at top — accepts multiple files
  - File list: filename, format badge (color-coded), status (pending / converting / done / error)
  - "Convert All" gradient button at bottom
  - Right-click to remove a file from queue
  - Output folder selector (defaults to source file's directory)
- **Right panel (Live Preview)**
  - Renders markdown as styled HTML
  - Auto-updates when a file finishes converting
  - Toggle: "Preview" / "Raw Markdown"
  - "Copy to Clipboard" and "Save As..." buttons in panel header
  - Clicking a file in the queue switches preview to that file's output

### Threading
Conversion runs on a `QThread` worker — UI never freezes during large file processing.

### Styling
Modern Glass theme applied via a single Qt stylesheet (deep navy, glass cards, gradient accents).

### Packaging
`PyInstaller` produces a standalone `.exe` (Windows) / `.app` (macOS) — no Python install required by end users.

---

## Web App (FastAPI)

### Frontend (vanilla HTML/CSS/JS)
- Same Modern Glass visual style as desktop
- Full-width drop zone hero — drag files or click to browse
- File queue with status badges below drop zone
- After conversion: download individual `.md` files or "Download All as ZIP"
- Split-panel preview appears after first file converts
- Fully responsive — works on mobile

### API Routes
| Method | Route | Description |
|--------|-------|-------------|
| `POST` | `/convert` | Multipart file upload → `{ markdown, assets }` JSON |
| `GET` | `/download/{job_id}` | Download single `.md` file |
| `GET` | `/download/{job_id}/zip` | Download all outputs as `.zip` |
| `DELETE` | `/job/{job_id}` | Clean up server-side temp files |

### Storage
- Files stored in `/tmp/markify/{job_id}/` during session
- Auto-deleted after 1 hour
- No database — fully stateless

### Running locally
```bash
uvicorn web.main:app --reload --port 8000
```

### Security
- File type validated by magic bytes (not just extension)
- Max upload size: 50MB per file
- Temp files scoped to job UUID — no path traversal possible

---

## Error Handling & UX States

| Scenario | Behaviour |
|----------|-----------|
| Converter failure | File marked "Error" (red badge); other files continue |
| Scanned/image-only PDF | Graceful message: "PDF may be image-only — no text extracted" |
| Password-protected file | Detected early: "Protected — cannot convert" |
| Corrupt / unsupported file | Caught and reported without crash |
| Image extraction failure | Markdown still generated; broken ref replaced with `<!-- image could not be extracted -->` |
| Empty document | Warning: "No content found in this file" |

**Progress feedback:**
- Per-file spinner while converting, checkmark when done
- Web app polls `GET /status/{job_id}` for progress bar updates
- Desktop runs conversion on `QThread` — UI stays responsive throughout

---

## Dependencies

```
python-docx       # Word
python-pptx       # PowerPoint
openpyxl          # Excel
pdfplumber        # PDF text + tables
pymupdf           # PDF image extraction
striprtf          # RTF stripping
fastapi           # Web backend
uvicorn           # ASGI server
jinja2            # HTML templates
PyQt6             # Desktop GUI
pyinstaller       # Desktop packaging
python-magic      # Magic byte file type detection
```
