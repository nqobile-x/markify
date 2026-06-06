from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class ConversionJob:
    source_path: Path
    output_dir: Path


@dataclass
class ConversionResult:
    job: ConversionJob
    markdown: str
    asset_paths: list[Path]
    error: Optional[str]

    @property
    def success(self) -> bool:
        return self.error is None
