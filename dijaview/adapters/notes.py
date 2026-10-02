import hashlib
import os
from datetime import datetime
from pathlib import Path
from typing import List

from dijaview.adapters.base import BaseSourceAdapter
from dijaview.core.models import ActivityRecord, SourceType
from dijaview.core.redactor import redact_secrets

EXCLUDED_DIRS = {
    ".git",
    ".venv",
    "venv",
    "node_modules",
    "__pycache__",
    ".idea",
    ".vscode",
    "dist",
    "build",
}

SUPPORTED_EXTENSIONS = {".md", ".markdown", ".txt", ".rst"}


class NotesAdapter(BaseSourceAdapter):
    """Scans and indexes user markdown notes and text documents."""

    def __init__(self, directories: List[str] = None):
        self.directories = [Path(d).expanduser() for d in (directories or self._default_directories())]

    def _default_directories(self) -> List[str]:
        home = Path.home()
        candidates = [
            home / "Documents",
            home / "notes",
            home / "Notes",
        ]
        return [str(p) for p in candidates if p.exists() and p.is_dir()]

    def source_type(self) -> str:
        return SourceType.NOTES.value

    def scan_records(self, since_epoch: float = 0.0) -> List[ActivityRecord]:
        records: List[ActivityRecord] = []

        for base_dir in self.directories:
            if not base_dir.exists():
                continue

            for root, dirs, files in os.walk(base_dir):
                dirs[:] = [d for d in dirs if d not in EXCLUDED_DIRS]

                for file in files:
                    ext = Path(file).suffix.lower()
                    if ext not in SUPPORTED_EXTENSIONS:
                        continue

                    file_path = Path(root) / file
                    try:
                        mtime = file_path.stat().st_mtime
                        if mtime < since_epoch:
                            continue

                        records.extend(self._process_file(file_path, mtime))
                    except Exception:
                        continue

        return records

    def _process_file(self, path: Path, mtime: float) -> List[ActivityRecord]:
        records: List[ActivityRecord] = []
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
        except Exception:
            return records

        if not content.strip():
            return records

        # Chunk by markdown headers or large paragraphs
        chunks = self._chunk_content(content)
        iso_time = datetime.fromtimestamp(mtime).isoformat()

        for chunk_idx, chunk in enumerate(chunks):
            if not chunk.strip():
                continue

            clean_chunk = redact_secrets(chunk.strip())
            first_line = clean_chunk.split("\n")[0].strip("# ").strip()
            title = first_line[:60] if first_line else path.name

            rec_id = hashlib.sha256(f"{path}_{chunk_idx}_{mtime}".encode()).hexdigest()[:16]

            records.append(
                ActivityRecord(
                    id=rec_id,
                    source_type=self.source_type(),
                    source_identifier=path.name,
                    timestamp=mtime,
                    datetime_iso=iso_time,
                    title=f"Note: {title}",
                    content=clean_chunk,
                    location=str(path),
                    metadata={
                        "chunk_index": chunk_idx,
                        "file_name": path.name,
                        "file_path": str(path),
                    },
                )
            )

        return records

    def _chunk_content(self, text: str, max_chars: int = 1500) -> List[str]:
        # Split on markdown headers
        sections = []
        current_section = []
        current_len = 0

        for line in text.splitlines():
            if line.startswith("#") and current_section:
                sections.append("\n".join(current_section))
                current_section = [line]
                current_len = len(line)
            else:
                current_section.append(line)
                current_len += len(line) + 1

                if current_len >= max_chars:
                    sections.append("\n".join(current_section))
                    current_section = []
                    current_len = 0

        if current_section:
            sections.append("\n".join(current_section))

        return sections if sections else [text]
