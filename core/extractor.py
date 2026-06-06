from pathlib import Path

def save_image(image_bytes: bytes, assets_dir: Path, index: int, ext: str = "png") -> Path:
    """Write image bytes to assets_dir/image_{index}.{ext} and return the path."""
    assets_dir.mkdir(parents=True, exist_ok=True)
    dest = assets_dir / f"image_{index}.{ext}"
    dest.write_bytes(image_bytes)
    return dest
