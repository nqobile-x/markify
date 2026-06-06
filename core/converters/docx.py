from pathlib import Path
import docx
from core.extractor import save_image


def _table_to_gfm(table) -> str:
    rows = [[cell.text.strip() for cell in row.cells] for row in table.rows]
    if not rows:
        return ""
    header = "| " + " | ".join(rows[0]) + " |"
    separator = "| " + " | ".join(["---"] * len(rows[0])) + " |"
    body = "\n".join("| " + " | ".join(row) + " |" for row in rows[1:])
    return "\n".join(filter(None, [header, separator, body]))


def _run_text(run) -> str:
    text = run.text
    if not text.strip():
        return text
    if run.bold:
        text = f"**{text}**"
    if run.italic:
        text = f"_{text}_"
    if run.underline:
        text = f"<u>{text}</u>"
    return text


def convert_docx(source: Path, assets_dir: Path) -> tuple[str, list[Path]]:
    doc = docx.Document(str(source))
    lines: list[str] = []
    asset_paths: list[Path] = []
    img_index = 1

    heading_map = {1: "#", 2: "##", 3: "###", 4: "####"}

    # Extract all images from the document once, keyed by relationship rId
    image_map: dict[str, tuple[int, str]] = {}
    for rId, rel in doc.part.rels.items():
        if "image" in rel.reltype:
            try:
                image_bytes = rel.target_part.blob
                ext = rel.target_part.content_type.split("/")[-1]
                path = save_image(image_bytes, assets_dir, img_index, ext)
                asset_paths.append(path)
                image_map[rId] = (img_index, ext)
                img_index += 1
            except Exception:
                image_map[rId] = (-1, "")  # sentinel for failed extraction

    for block in doc.element.body:
        tag = block.tag.split("}")[-1]

        if tag == "p":
            para = docx.text.paragraph.Paragraph(block, doc)
            style_name = para.style.name if para.style else ""

            if style_name.startswith("Heading"):
                try:
                    level = int(style_name.split()[-1])
                except ValueError:
                    level = 1
                prefix = heading_map.get(level, "#")
                lines.append(f"{prefix} {para.text}")
            else:
                text = "".join(_run_text(r) for r in para.runs)
                if text.strip():
                    lines.append(text)
                else:
                    lines.append("")

            # Reference images that appear in THIS paragraph via blip elements
            nsmap = {"a": "http://schemas.openxmlformats.org/drawingml/2006/main"}
            for blip in block.findall(".//a:blip", nsmap):
                rId = blip.get("{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed")
                if rId and rId in image_map:
                    idx, ext = image_map[rId]
                    if idx == -1:
                        lines.append("<!-- image could not be extracted -->")
                    else:
                        lines.append(f"![image_{idx}](assets/image_{idx}.{ext})")

        elif tag == "tbl":
            table = docx.table.Table(block, doc)
            lines.append(_table_to_gfm(table))
            lines.append("")

    return "\n".join(lines), asset_paths
