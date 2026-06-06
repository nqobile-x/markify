import io
import tempfile
from pathlib import Path
import docx as docx_lib
import pytest
from fastapi.testclient import TestClient

def _make_docx_bytes() -> bytes:
    doc = docx_lib.Document()
    doc.add_heading("Web Test", level=1)
    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()

def test_convert_docx_returns_markdown():
    from web.main import app
    client = TestClient(app)
    data = _make_docx_bytes()
    response = client.post("/convert", files={"file": ("test.docx", data, "application/octet-stream")})
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "done"
    assert "# Web Test" in body["markdown"]

def test_convert_unsupported_format():
    from web.main import app
    client = TestClient(app)
    response = client.post("/convert", files={"file": ("test.xyz", b"data", "text/plain")})
    assert response.status_code == 400

def test_download_md():
    from web.main import app
    client = TestClient(app)
    data = _make_docx_bytes()
    r = client.post("/convert", files={"file": ("dl_test.docx", data, "application/octet-stream")})
    job_id = r.json()["job_id"]
    r2 = client.get(f"/download/{job_id}")
    assert r2.status_code == 200
    assert "# Web Test" in r2.text

def test_delete_job():
    from web.main import app
    client = TestClient(app)
    data = _make_docx_bytes()
    r = client.post("/convert", files={"file": ("del_test.docx", data, "application/octet-stream")})
    job_id = r.json()["job_id"]
    r2 = client.delete(f"/job/{job_id}")
    assert r2.status_code == 200
