import fnmatch
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from dijaview.config import Config


DEFAULT_PERMISSIONS: Dict[str, Any] = {
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
}


class PermissionsManager:
    """Controls access to local computer activity sources, paths, and redaction rules."""

    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config()
        self._ensure_permissions_initialized()

    def _ensure_permissions_initialized(self) -> None:
        """Initializes default permissions in config if missing."""
        if "permissions" not in self.config.data:
            self.config.data["permissions"] = DEFAULT_PERMISSIONS.copy()
            self.config.save()
        else:
            # Backfill any missing top-level keys
            perms = self.config.data["permissions"]
            for key, val in DEFAULT_PERMISSIONS.items():
                if key not in perms:
                    perms[key] = val
            self.config.save()

    @property
    def permissions(self) -> Dict[str, Any]:
        return self.config.data.get("permissions", DEFAULT_PERMISSIONS)

    def is_source_enabled(self, source_name: str) -> bool:
        """Checks if a data source is granted permission."""
        sources = self.permissions.get("sources", {})
        return bool(sources.get(source_name.lower(), False))

    def enable_source(self, source_name: str) -> None:
        """Grants permission to a source."""
        source = source_name.lower()
        if "sources" not in self.permissions:
            self.permissions["sources"] = {}
        self.permissions["sources"][source] = True
        self.save()

    def disable_source(self, source_name: str) -> None:
        """Revokes permission from a source."""
        source = source_name.lower()
        if "sources" not in self.permissions:
            self.permissions["sources"] = {}
        self.permissions["sources"][source] = False
        self.save()

    def get_allowed_paths(self) -> List[str]:
        """Returns the list of permitted directories."""
        return list(self.permissions.get("paths", {}).get("allowed", []))

    def get_blocked_paths(self) -> List[str]:
        """Returns the list of forbidden directories or file patterns."""
        return list(self.permissions.get("paths", {}).get("blocked", []))

    def allow_path(self, path_str: str) -> bool:
        """Adds a path to allowed directories list."""
        expanded = str(Path(path_str).expanduser().resolve())
        allowed = self.get_allowed_paths()
        if expanded not in allowed:
            allowed.append(expanded)
            self.permissions.setdefault("paths", {})["allowed"] = allowed
            self.save()
            return True
        return False

    def block_path(self, path_str: str) -> bool:
        """Adds a path or pattern to the blocked list."""
        expanded = str(Path(path_str).expanduser()) if not any(c in path_str for c in "*?[]") else path_str
        blocked = self.get_blocked_paths()
        if expanded not in blocked:
            blocked.append(expanded)
            self.permissions.setdefault("paths", {})["blocked"] = blocked
            self.save()
            return True
        return False

    def remove_path(self, path_str: str) -> bool:
        """Removes a path from allowed and blocked lists."""
        removed = False
        expanded = str(Path(path_str).expanduser())

        allowed = self.get_allowed_paths()
        if path_str in allowed:
            allowed.remove(path_str)
            removed = True
        elif expanded in allowed:
            allowed.remove(expanded)
            removed = True
        self.permissions.setdefault("paths", {})["allowed"] = allowed

        blocked = self.get_blocked_paths()
        if path_str in blocked:
            blocked.remove(path_str)
            removed = True
        elif expanded in blocked:
            blocked.remove(expanded)
            removed = True
        self.permissions.setdefault("paths", {})["blocked"] = blocked

        if removed:
            self.save()
        return removed

    def is_path_allowed(self, target_path: Union[str, Path]) -> bool:
        """Checks if a filesystem path is permitted for reading."""
        path_obj = Path(target_path).expanduser().resolve()
        path_str = str(path_obj)

        # 1. Check against blocked paths and glob patterns
        blocked_list = self.get_blocked_paths()
        for pattern in blocked_list:
            # Pattern could be an exact directory or glob
            if any(char in pattern for char in "*?[]"):
                if fnmatch.fnmatch(path_str, pattern) or fnmatch.fnmatch(path_obj.name, pattern):
                    return False
            else:
                try:
                    blocked_obj = Path(pattern).expanduser().resolve()
                    if path_obj == blocked_obj or blocked_obj in path_obj.parents:
                        return False
                except Exception:
                    if pattern in path_str:
                        return False

        # 2. Check against allowed directories
        allowed_list = self.get_allowed_paths()
        if not allowed_list:
            # If no allowed directories are specified, default to allowed unless blocked
            return True

        for allowed in allowed_list:
            try:
                allowed_obj = Path(allowed).expanduser().resolve()
                if path_obj == allowed_obj or allowed_obj in path_obj.parents:
                    return True
            except Exception:
                continue

        return False

    def get_max_file_size(self) -> int:
        """Returns the maximum permitted file size in bytes."""
        limits = self.permissions.get("limits", {})
        return limits.get("max_file_size_bytes", 1048576)

    def set_max_file_size(self, size_bytes: int) -> None:
        """Sets the maximum permitted file size in bytes."""
        self.permissions.setdefault("limits", {})["max_file_size_bytes"] = max(1024, size_bytes)
        self.save()

    def get_custom_redactions(self) -> List[Dict[str, str]]:
        """Returns the list of custom redaction rules."""
        return list(self.permissions.get("custom_redactions", []))

    def add_custom_redaction(self, name: str, pattern: str, replacement: str = "[REDACTED]") -> None:
        """Registers a custom regular expression redaction filter."""
        # Validate regex pattern
        re.compile(pattern)

        redactions = self.get_custom_redactions()
        # Remove existing rule with same name if present
        redactions = [r for r in redactions if r.get("name") != name]
        redactions.append({
            "name": name,
            "pattern": pattern,
            "replacement": replacement,
        })
        self.permissions["custom_redactions"] = redactions
        self.save()

    def remove_custom_redaction(self, name: str) -> bool:
        """Removes a custom redaction filter by name."""
        redactions = self.get_custom_redactions()
        initial_len = len(redactions)
        redactions = [r for r in redactions if r.get("name") != name]
        if len(redactions) != initial_len:
            self.permissions["custom_redactions"] = redactions
            self.save()
            return True
        return False

    def get_custom_rules_tuples(self) -> List[Tuple[str, str]]:
        """Returns custom redaction rules as (pattern, replacement) tuples."""
        tuples = []
        for rule in self.get_custom_redactions():
            pat = rule.get("pattern")
            rep = rule.get("replacement", "[REDACTED]")
            if pat:
                tuples.append((pat, rep))
        return tuples

    def reset_defaults(self) -> None:
        """Resets all permissions back to default state."""
        self.config.data["permissions"] = DEFAULT_PERMISSIONS.copy()
        self.save()

    def save(self) -> None:
        """Persists permissions changes to config file."""
        self.config.save()
