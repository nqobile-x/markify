import tempfile
from pathlib import Path
import pytest

try:
    from reportlab.pdfgen import canvas as rl_canvas
    HAS_REPORTLAB = True
except ImportError:
    HAS_REPORTLAB = False

from core.converters.pdf import convert_pdf

def _make_pdf(tmp_dir: Path) -> Path:
    path = tmp_dir / "sample.pdf"
    c = rl_canvas.Canvas(str(path))
    c.setFont("Helvetica-Bold", 18)
    c.drawString(72, 750, "Report Title")
    c.setFont("Helvetica", 12)
    c.drawString(72, 720, "This is body text on page one.")
    c.showPage()
    c.save()
    return path

@pytest.mark.skipif(not HAS_REPORTLAB, reason="reportlab not installed")
def test_pdf_extracts_text():
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        path = _make_pdf(tmp)
        md, assets = convert_pdf(path, tmp / "assets")
        assert "Report Title" in md
        assert "body text" in md

@pytest.mark.skipif(not HAS_REPORTLAB, reason="reportlab not installed")
def test_pdf_returns_asset_list():
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        path = _make_pdf(tmp)
        md, assets = convert_pdf(path, tmp / "assets")
        assert isinstance(assets, list)
