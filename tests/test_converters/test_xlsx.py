import tempfile
from pathlib import Path
import openpyxl
from core.converters.xlsx import convert_xlsx

def _make_xlsx(tmp_dir: Path) -> Path:
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Sales"
    ws.append(["Month", "Revenue"])
    ws.append(["January", 12000])
    ws.append(["February", 15000])
    ws2 = wb.create_sheet("Summary")
    ws2.append(["Total", 27000])
    path = tmp_dir / "sample.xlsx"
    wb.save(str(path))
    return path

def test_xlsx_sheet_headings():
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        path = _make_xlsx(tmp)
        md, assets = convert_xlsx(path, tmp / "assets")
        assert "## Sales" in md
        assert "## Summary" in md

def test_xlsx_table_headers():
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        path = _make_xlsx(tmp)
        md, assets = convert_xlsx(path, tmp / "assets")
        assert "| Month | Revenue |" in md

def test_xlsx_table_data():
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        path = _make_xlsx(tmp)
        md, assets = convert_xlsx(path, tmp / "assets")
        assert "| January | 12000 |" in md

def test_xlsx_returns_empty_assets():
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        path = _make_xlsx(tmp)
        md, assets = convert_xlsx(path, tmp / "assets")
        assert assets == []
