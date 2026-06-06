import tempfile
from pathlib import Path
from core.converters.text import convert_text

def test_txt_passthrough():
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        f = tmp / "notes.txt"
        f.write_text("Hello world\nLine two")
        md, assets = convert_text(f, tmp / "assets")
        assert "Hello world" in md
        assert "Line two" in md
        assert assets == []

def test_csv_to_table():
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        f = tmp / "data.csv"
        f.write_text("Name,Age\nAlice,30\nBob,25")
        md, assets = convert_text(f, tmp / "assets")
        assert "| Name | Age |" in md
        assert "| Alice | 30 |" in md

def test_rtf_strips_tags():
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        f = tmp / "doc.rtf"
        f.write_text(r"{\rtf1\ansi Hello RTF World}")
        md, assets = convert_text(f, tmp / "assets")
        assert "Hello RTF World" in md
        assert "{" not in md
