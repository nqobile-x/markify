from pathlib import Path
from core.models import ConversionJob, ConversionResult
from core.converters.docx import convert_docx
from core.converters.pptx import convert_pptx
from core.converters.xlsx import convert_xlsx
from core.converters.pdf import convert_pdf
from core.converters.text import convert_text


class ConversionError(Exception):
    pass


EXTENSION_MAP = {
    ".docx": convert_docx,
    ".doc": convert_docx,
    ".pptx": convert_pptx,
    ".ppt": convert_pptx,
    ".xlsx": convert_xlsx,
    ".xls": convert_xlsx,
    ".pdf": convert_pdf,
    ".txt": convert_text,
    ".csv": convert_text,
    ".rtf": convert_text,
}


def convert(source: Path, output_dir: Path) -> ConversionResult:
    job = ConversionJob(source_path=source, output_dir=output_dir)

    if not source.exists():
        return ConversionResult(job=job, markdown="", asset_paths=[], error="File not found")

    suffix = source.suffix.lower()
    converter = EXTENSION_MAP.get(suffix)

    if converter is None:
        return ConversionResult(
            job=job, markdown="", asset_paths=[],
            error=f"Unsupported format: {suffix}"
        )

    assets_dir = output_dir / "assets"
    try:
        markdown, asset_paths = converter(source, assets_dir)
        if not markdown.strip():
            markdown = "<!-- No content found in this file -->"
        return ConversionResult(job=job, markdown=markdown, asset_paths=asset_paths, error=None)
    except Exception as exc:
        return ConversionResult(job=job, markdown="", asset_paths=[], error=str(exc))
