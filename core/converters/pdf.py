from pathlib import Path
import pdfplumber
import fitz  # pymupdf
from core.extractor import save_image


def convert_pdf(source: Path, assets_dir: Path) -> tuple[str, list[Path]]:
    asset_paths: list[Path] = []
    sections: list[str] = []
    img_index = 1

    # Extract images via pymupdf
    fitz_doc = fitz.open(str(source))
    page_images: dict[int, list] = {}
    for page_num in range(len(fitz_doc)):
        page = fitz_doc[page_num]
        page_images[page_num] = []
        for img_info in page.get_images(full=True):
            xref = img_info[0]
            try:
                base_image = fitz_doc.extract_image(xref)
                image_bytes = base_image["image"]
                ext = base_image["ext"]
                path = save_image(image_bytes, assets_dir, img_index, ext)
                asset_paths.append(path)
                page_images[page_num].append((img_index, ext))
                img_index += 1
            except Exception:
                page_images[page_num].append(None)
    fitz_doc.close()

    # Extract text + tables via pdfplumber
    with pdfplumber.open(str(source)) as pdf:
        for page_num, page in enumerate(pdf.pages):
            page_lines: list[str] = []

            # Detect headings by font size
            words = page.extract_words(extra_attrs=["size"])
            if words:
                sizes = [w.get("size", 12) for w in words]
                avg_size = sum(sizes) / len(sizes)
                current_line: list[str] = []
                current_size: float = 0.0
                for word in words:
                    size = word.get("size", 12)
                    text = word["text"]
                    if current_size and abs(size - current_size) > 2:
                        line_text = " ".join(current_line)
                        if current_size > avg_size + 2:
                            page_lines.append(f"# {line_text}")
                        else:
                            page_lines.append(line_text)
                        current_line = []
                    current_line.append(text)
                    current_size = size
                if current_line:
                    line_text = " ".join(current_line)
                    if current_size > avg_size + 2:
                        page_lines.append(f"# {line_text}")
                    else:
                        page_lines.append(line_text)

            # Tables
            for table in page.extract_tables():
                if not table:
                    continue
                rows = [[str(cell or "").strip() for cell in row] for row in table]
                if not rows:
                    continue
                header = "| " + " | ".join(rows[0]) + " |"
                sep = "| " + " | ".join(["---"] * len(rows[0])) + " |"
                body = "\n".join("| " + " | ".join(row) + " |" for row in rows[1:])
                page_lines.append("\n".join(filter(None, [header, sep, body])))

            # Image references for this page
            for img_ref in page_images.get(page_num, []):
                if img_ref is None:
                    page_lines.append("<!-- image could not be extracted -->")
                else:
                    idx, ext = img_ref
                    page_lines.append(f"![image_{idx}](assets/image_{idx}.{ext})")

            if page_lines:
                sections.append("\n".join(page_lines))

    if not sections:
        return "<!-- PDF may be image-only — no text extracted -->", asset_paths

    return "\n\n".join(sections), asset_paths
