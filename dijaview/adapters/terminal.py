import hashlib
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any, List, Optional

from dijaview.adapters.base import BaseSourceAdapter
from dijaview.core.models import ActivityRecord, SourceType
from dijaview.core.redactor import redact_secrets


class TerminalAdapter(BaseSourceAdapter):
    """Ingests shell history from Bash, Zsh, Fish, and PowerShell."""

    def __init__(self, history_paths: Optional[List[str]] = None, permissions: Optional[Any] = None):
        self.permissions = permissions
        self.history_paths = history_paths or self._default_paths()

    def _default_paths(self) -> List[Path]:
        home = Path.home()
        candidates = [
            home / ".bash_history",
            home / ".zsh_history",
            home / ".local" / "share" / "fish" / "fish_history",
            home / "AppData" / "Roaming" / "Microsoft" / "Windows" / "PowerShell" / "PSReadLine" / "ConsoleHost_history.txt",
        ]
        return [p for p in candidates if p.exists() and p.is_file()]

    def source_type(self) -> str:
        return SourceType.TERMINAL.value

    def scan_records(self, since_epoch: float = 0.0) -> List[ActivityRecord]:
        if self.permissions and not self.permissions.is_source_enabled("terminal"):
            return []

        records: List[ActivityRecord] = []
        custom_rules = self.permissions.get_custom_rules_tuples() if self.permissions else None

        for path in self.history_paths:
            records.extend(self._parse_file(Path(path), since_epoch, custom_rules=custom_rules))
        return records

    def _parse_file(self, path: Path, since_epoch: float, custom_rules: Optional[List[tuple]] = None) -> List[ActivityRecord]:
        records: List[ActivityRecord] = []
        if not path.exists():
            return records

        try:
            stat = path.stat()
            mtime = stat.st_mtime
            if mtime <= since_epoch:
                return records
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                lines = f.readlines()
        except Exception:
            return records

        current_timestamp = mtime

        for idx, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue

            has_explicit_timestamp = False
            # Detect Zsh extended format: ': <timestamp>:<duration>;<command>'
            zsh_match = re.match(r"^:\s*(\d+):\d+;(.*)$", line)
            if zsh_match:
                current_timestamp = float(zsh_match.group(1))
                command = zsh_match.group(2).strip()
                has_explicit_timestamp = True
            # Detect Bash timestamp format '#<timestamp>'
            elif line.startswith("#") and line[1:].strip().isdigit():
                current_timestamp = float(line[1:].strip())
                has_explicit_timestamp = True
                continue
            else:
                command = line

            # Filter out entries older than checkpoint if explicit timestamp is known
            if has_explicit_timestamp and current_timestamp < since_epoch:
                continue

            # Skip single-word trivial commands
            if command in {"ls", "cd", "pwd", "clear", "exit", "history", "q"}:
                continue

            sanitized_command = redact_secrets(command, custom_rules=custom_rules)
            if has_explicit_timestamp:
                rec_id = hashlib.sha256(f"{path}_{current_timestamp}_{command}".encode()).hexdigest()[:16]
            else:
                rec_id = hashlib.sha256(f"{path}_{idx}_{command}".encode()).hexdigest()[:16]
            try:
                iso_time = datetime.fromtimestamp(current_timestamp).isoformat()
            except (ValueError, OSError, OverflowError):
                try:
                    iso_time = datetime.fromtimestamp(mtime).isoformat()
                except Exception:
                    continue

            records.append(
                ActivityRecord(
                    id=rec_id,
                    source_type=self.source_type(),
                    source_identifier=path.name,
                    timestamp=current_timestamp,
                    datetime_iso=iso_time,
                    title=f"Terminal Command: {sanitized_command[:40]}",
                    content=sanitized_command,
                    location=str(path),
                    metadata={"line_number": idx + 1, "raw_command": sanitized_command},
                )
            )

        return records
