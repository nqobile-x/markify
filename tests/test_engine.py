import tempfile
from pathlib import Path
import docx
from core.engine import convert, ConversionError
from core.models import ConversionResult

def _make_docx(tmp_dir: Path) -> Path:
    doc = docx.Document()
    doc.add_heading("Test", level=1)
    path = tmp_dir / "test.docx"
    doc.save(str(path))
    return path

def test_engine_routes_docx():
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        path = _make_docx(tmp)
        result = convert(path, output_dir=tmp)
        assert isinstance(result, ConversionResult)
        assert result.success
        assert "# Test" in result.markdown

def test_engine_error_on_unknown_format():
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        path = tmp / "file.xyz"
        path.write_text("data")
        result = convert(path, output_dir=tmp)
        assert not result.success
        assert "Unsupported" in result.error

def test_engine_error_on_missing_file():
    with tempfile.TemporaryDirectory() as tmp:
        result = convert(Path("/nonexistent/file.docx"), output_dir=Path(tmp))
        assert not result.success
