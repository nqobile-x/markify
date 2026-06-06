import csv
import io
from pathlib import Path
from striprtf.striprtf import rtf_to_text


def _csv_to_gfm(content: str) -> str:
    reader = csv.reader(io.StringIO(content))
    rows = list(reader)
    if not rows:
        return ""
    header = "| " + " | ".join(rows[0]) + " |"
    sep = "| " + " | ".join(["---"] * len(rows[0])) + " |"
    body = "\n".join("| " + " | ".join(row) + " |" for row in rows[1:])
    return "\n".join(filter(None, [header, sep, body]))


def convert_text(source: Path, assets_dir: Path) -> tuple[str, list[Path]]:
    suffix = source.suffix.lower()
    if suffix == ".csv":
        content = source.read_text(encoding="utf-8", errors="replace")
        return _csv_to_gfm(content), []
    elif suffix == ".rtf":
        content = source.read_text(encoding="utf-8", errors="replace")
        plain = rtf_to_text(content).strip()
        # Remove any residual RTF brace artifacts
        plain = plain.replace("{", "").replace("}", "")
        return plain, []
    else:  # .txt and fallback
        content = source.read_text(encoding="utf-8", errors="replace")
        return content, []
