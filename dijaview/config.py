import json
import os
from pathlib import Path
from typing import Any, Dict, Optional

DEFAULT_CONFIG: Dict[str, Any] = {
    "model": {
        "provider": "ollama",
        "name": "gemma2:2b",
        "base_url": "http://localhost:11434",
    },
    "storage": {
        "db_path": str(Path.home() / ".local" / "share" / "dijaview" / "dijaview.db"),
    },
    "adapters": {
        "terminal": {"enabled": True},
        "browser": {"enabled": True},
        "notes": {
            "enabled": True,
            "directories": [
                str(Path.home() / "Documents"),
                str(Path.home() / "notes"),
            ],
        },
    },
    "privacy": {
        "redact_secrets": True,
    },
    "permissions": {
        "sources": {
            "terminal": True,
            "browser": True,
            "notes": True,
        },
        "paths": {
            "allowed": [
                str(Path.home() / "Documents"),
                str(Path.home() / "notes"),
                str(Path.home() / "Notes"),
            ],
            "blocked": [
                str(Path.home() / ".ssh"),
                str(Path.home() / ".gnupg"),
                str(Path.home() / ".aws"),
                str(Path.home() / ".azure"),
                str(Path.home() / ".config" / "gcloud"),
                "*/.git/*",
                "*/node_modules/*",
                "*/venv/*",
                "*/.venv/*",
                "*id_rsa*",
                "*id_ed25519*",
                "*.env*",
            ],
        },
        "limits": {
            "max_file_size_bytes": 1048576,  # 1 MB
        },
        "custom_redactions": [],
    },
}


class Config:
    """Manages Dijaview user configuration."""

    def __init__(self, config_path: Optional[str] = None):
        if config_path:
            self.path = Path(config_path)
        else:
            self.path = Path.home() / ".config" / "dijaview" / "config.json"
        self.data = self._load()

    def _load(self) -> Dict[str, Any]:
        if not self.path.exists():
            return DEFAULT_CONFIG.copy()
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                loaded = json.load(f)
                config = DEFAULT_CONFIG.copy()
                config.update(loaded)
                return config
        except Exception:
            return DEFAULT_CONFIG.copy()

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=2)

    def get(self, key_path: str, default: Any = None) -> Any:
        keys = key_path.split(".")
        current = self.data
        for k in keys:
            if isinstance(current, dict) and k in current:
                current = current[k]
            else:
                return default
        return current

    def set(self, key_path: str, value: Any) -> None:
        keys = key_path.split(".")
        current = self.data
        for k in keys[:-1]:
            if k not in current or not isinstance(current[k], dict):
                current[k] = {}
            current = current[k]
        current[keys[-1]] = value
        self.save()
