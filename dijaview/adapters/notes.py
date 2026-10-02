import hashlib
import os
from datetime import datetime
from pathlib import Path
from typing import Any, List, Optional

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
DEFAULT_MAX_FILE_SIZE = 1048576  # 1 MB


class NotesAdapter(BaseSourceAdapter):
    """Scans and indexes user markdown notes and text documents."""

    def __init__(self, directories: Optional[List[str]] = None, permissions: Optional[Any] = None):
        self.permissions = permissions
        if directories:
            self.directories = [Path(d).expanduser() for d in directories]
        elif self.permissions and self.permissions.get_allowed_paths():
            self.directories = [Path(d).expanduser() for d in self.permissions.get_allowed_paths()]
        else:
            self.directories = [Path(d).expanduser() for d in self._default_directories()]

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
        if self.permissions and not self.permissions.is_source_enabled("notes"):
            return []

        records: List[ActivityRecord] = []
        max_size = self.permissions.get_max_file_size() if self.permissions else DEFAULT_MAX_FILE_SIZE
        custom_rules = self.permissions.get_custom_rules_tuples() if self.permissions else None

        for base_dir in self.directories:
            if not base_dir.exists():
                continue

            if self.permissions and not self.permissions.is_path_allowed(base_dir):
                continue

            for root, dirs, files in os.walk(base_dir):
                # Filter out excluded or unpermitted directories
                dirs[:] = [
                    d for d in dirs
                    if d not in EXCLUDED_DIRS
                    and (not self.permissions or self.permissions.is_path_allowed(Path(root) / d))
                ]

                for file in files:
                    ext = Path(file).suffix.lower()
                    if ext not in SUPPORTED_EXTENSIONS:
                        continue

                    file_path = Path(root) / file

                    # Verify permissions
                    if self.permissions and not self.permissions.is_path_allowed(file_path):
                        continue

                    try:
                        stat = file_path.stat()
                        # Skip oversized files to preserve memory and speed
                        if stat.st_size > max_size:
                            continue

                        mtime = stat.st_mtime
                        if mtime < since_epoch:
                            continue

                        records.extend(self._process_file(file_path, mtime, custom_rules=custom_rules))
                    except Exception:
                        continue

        return records

    def _process_file(self, path: Path, mtime: float, custom_rules: Optional[List[tuple]] = None) -> List[ActivityRecord]:
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

            clean_chunk = redact_secrets(chunk.strip(), custom_rules=custom_rules)
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
