# DijaView Data Adapters Specification

This document outlines the technical specifications, file paths, database schemas, and normalization rules for DijaView's modular data adapters.

---

## 1. Adapter Architecture

Every adapter extends `BaseSourceAdapter` and adheres to a pull-based scanning lifecycle:

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, List

@dataclass
class ActivityRecord:
    source_type: str        # 'terminal', 'browser', 'notes', 'git'
    source_identifier: str  # e.g., 'zsh_history', 'brave_history', 'notes_markdown'
    timestamp: float        # Unix epoch in seconds
    title: Optional[str]    # Title or short summary
    content: str            # Raw command, page snippet, or note text
    location: str           # File path or URL
    metadata: dict          # Additional context (e.g. exit code, browser profile)

class BaseSourceAdapter(ABC):
    @abstractmethod
    def detect_sources(self) -> List[str]:
        """Detects available history files or databases on current OS."""
        pass

    @abstractmethod
    def read_entries(self, since_epoch: float = 0.0) -> List[ActivityRecord]:
        """Reads and yields ActivityRecords since the specified timestamp."""
        pass
```

---

## 2. Terminal History Adapter (`TerminalAdapter`)

### Supported Shells & Formats
* **Bash (`~/.bash_history`):**
  * Supports standard commands and timestamp-extended bash history (`HISTTIMEFORMAT`).
* **Zsh (`~/.zsh_history`):**
  * Parses extended Zsh format: `: <timestamp>:<duration>;<command>`.
* **Fish (`~/.local/share/fish/fish_history`):**
  * Parses YAML-like fish history entries:
    ```yaml
    - cmd: git status
      when: 1790924400
    ```

### Normalization & Cleansing
1. Strips shell control comments and empty commands.
2. Filters out noise commands (e.g., standalone `ls`, `cd`, `pwd`, `clear`, `exit`).
3. Runs secret redactor to mask:
   * Tokens passed via CLI flags: `--token <TOKEN>`, `-H "Authorization: Bearer <TOKEN>"`.
   * Inline export statements: `export API_KEY=...`.

---

## 3. Browser History Adapter (`BrowserAdapter`)

### Supported Browsers & Locations (Linux / macOS / Windows)

| Browser | Default Linux Path | Default macOS Path |
| :--- | :--- | :--- |
| **Google Chrome** | `~/.config/google-chrome/Default/History` | `~/Library/Application Support/Google/Chrome/Default/History` |
| **Brave** | `~/.config/BraveSoftware/Brave-Browser/Default/History` | `~/Library/Application Support/BraveSoftware/Brave-Browser/Default/History` |
| **Mozilla Firefox** | `~/.mozilla/firefox/*.default-release/places.sqlite` | `~/Library/Application Support/Firefox/Profiles/*.default/places.sqlite` |

### Database Access & Safety Protocol
Browsers lock their SQLite database files (`History` or `places.sqlite`) while open. Attempting standard SQLite writes or exclusive reads will throw `sqlite3.OperationalError: database is locked`.

DijaView implements a **Non-Locking Read-Only Protocol**:
1. Connects using URI read-only flags: `file:{db_path}?mode=ro&immutable=1`.
2. Fallback: Creates an ephemeral snapshot copy in `/tmp/dijaview_browser_snapshot.db` before executing queries.
3. Extracted query for Chromium-based browsers:
   ```sql
   SELECT 
       urls.url, 
       urls.title, 
       urls.visit_count, 
       (visits.visit_time / 1000000) - 11644473600 AS unix_timestamp
   FROM urls
   JOIN visits ON urls.id = visits.url
   WHERE unix_timestamp > :since_epoch
   ORDER BY visits.visit_time ASC;
   ```

---

## 4. Local Notes & Documents Adapter (`NotesAdapter`)

### Target Directories & Extensions
* Monitored folders: `~/Documents`, `~/notes`, `~/work`, `~/projects` (configurable via `dijaview.yaml`).
* Supported extensions: `.md`, `.markdown`, `.txt`, `.org`, `.rst`.

### Chunking & Context Preservation
* Splits files using markdown header-aware chunking (`#`, `##`, `###`).
* Preserves document title, relative path, and last modification timestamp (`os.path.getmtime`).
* Ignores common dependency and cache directories:
  * `node_modules/`, `.git/`, `.venv/`, `venv/`, `__pycache__/`, `dist/`, `build/`.

---

## 5. Git Context Adapter (`GitAdapter`)

### Scope of Ingestion
* Indexes recent git commits across active user workspaces.
* Extracts:
  * Commit hash & author timestamp.
  * Commit title & full body message.
  * List of touched files and commit diff summary.
* Enables queries like:
  * *"When did I refactor the authentication middleware?"*
  * *"Which branch had the changes for captive portal CORS?"*

---

## 6. Future Extensibility (Roadmap)

* **Window Activity & Desktop Focus:** Ingesting active window titles via `wmctrl` / Wayland protocols.
* **Local OCR Screen Snippets:** Selective screenshot OCR via open-source Tesseract or local vision models for graphical context recall.
