from pathlib import Path
from core.models import ConversionJob, ConversionResult

def test_conversion_job_defaults():
    job = ConversionJob(source_path=Path("report.docx"), output_dir=Path("/tmp/out"))
    assert job.source_path == Path("report.docx")
    assert job.output_dir == Path("/tmp/out")

def test_conversion_result_success():
    result = ConversionResult(
        job=ConversionJob(source_path=Path("x.docx"), output_dir=Path("/tmp")),
        markdown="# Hello",
        asset_paths=[Path("/tmp/assets/img1.png")],
        error=None,
    )
    assert result.success is True
    assert result.markdown == "# Hello"

def test_conversion_result_failure():
    job = ConversionJob(source_path=Path("x.docx"), output_dir=Path("/tmp"))
    result = ConversionResult(job=job, markdown="", asset_paths=[], error="File corrupt")
    assert result.success is False

import tempfile
from core.extractor import save_image

def test_save_image_creates_file():
    with tempfile.TemporaryDirectory() as tmp:
        assets = Path(tmp) / "assets"
        path = save_image(b"\x89PNG\r\n", assets, index=1, ext="png")
        assert path.exists()
        assert path.name == "image_1.png"
