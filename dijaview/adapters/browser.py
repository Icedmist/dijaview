import hashlib
import os
import shutil
import sqlite3
import tempfile
from datetime import datetime
from pathlib import Path
from typing import List

from dijaview.adapters.base import BaseSourceAdapter
from dijaview.core.models import ActivityRecord, SourceType
from dijaview.core.redactor import redact_secrets


class BrowserAdapter(BaseSourceAdapter):
    """Safely reads local browser history from Chrome, Brave, and Firefox."""

    def __init__(self, custom_paths: List[str] = None):
        self.custom_paths = custom_paths

    def source_type(self) -> str:
        return SourceType.BROWSER.value

    def _find_history_databases(self) -> List[Path]:
        if self.custom_paths:
            return [Path(p) for p in self.custom_paths if Path(p).exists()]

        home = Path.home()
        candidates = [
            # Linux paths
            home / ".config" / "google-chrome" / "Default" / "History",
            home / ".config" / "BraveSoftware" / "Brave-Browser" / "Default" / "History",
            home / ".config" / "chromium" / "Default" / "History",
            # macOS paths
            home / "Library" / "Application Support" / "Google" / "Chrome" / "Default" / "History",
            home / "Library" / "Application Support" / "BraveSoftware" / "Brave-Browser" / "Default" / "History",
            # Windows paths
            home / "AppData" / "Local" / "Google" / "Chrome" / "User Data" / "Default" / "History",
            home / "AppData" / "Local" / "BraveSoftware" / "Brave-Browser" / "User Data" / "Default" / "History",
        ]

        # Check Firefox profiles
        firefox_linux = home / ".mozilla" / "firefox"
        if firefox_linux.exists():
            for p in firefox_linux.glob("*.default*/places.sqlite"):
                candidates.append(p)

        firefox_mac = home / "Library" / "Application Support" / "Firefox" / "Profiles"
        if firefox_mac.exists():
            for p in firefox_mac.glob("*.default*/places.sqlite"):
                candidates.append(p)

        return [p for p in candidates if p.exists() and p.is_file()]

    def scan_records(self, since_epoch: float = 0.0) -> List[ActivityRecord]:
        records: List[ActivityRecord] = []
        dbs = self._find_history_databases()

        for db_path in dbs:
            try:
                if "places.sqlite" in db_path.name:
                    records.extend(self._read_firefox(db_path, since_epoch))
                else:
                    records.extend(self._read_chromium(db_path, since_epoch))
            except Exception:
                continue

        return records

    def _read_chromium(self, db_path: Path, since_epoch: float) -> List[ActivityRecord]:
        records: List[ActivityRecord] = []

        # Create a temp snapshot to bypass locks if browser is currently active
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
            tmp_path = Path(tmp.name)

        try:
            shutil.copy2(db_path, tmp_path)
            conn = sqlite3.connect(tmp_path)
            cursor = conn.cursor()

            # WebKit timestamp conversion: microseconds since Jan 1 1601
            query = """
                SELECT 
                    urls.url, 
                    urls.title, 
                    urls.visit_count,
                    ((visits.visit_time / 1000000) - 11644473600) AS unix_time
                FROM urls
                JOIN visits ON urls.id = visits.url
                WHERE ((visits.visit_time / 1000000) - 11644473600) > ?
                ORDER BY visits.visit_time DESC
                LIMIT 1000
            """
            cursor.execute(query, (since_epoch,))
            rows = cursor.fetchall()
            conn.close()

            browser_name = "Brave" if "Brave" in str(db_path) else "Chrome"
            for url, title, count, unix_time in rows:
                if not url or url.startswith("chrome://") or url.startswith("about:"):
                    continue

                clean_title = redact_secrets(title or url)
                clean_url = redact_secrets(url)
                rec_id = hashlib.sha256(f"{url}_{unix_time}".encode()).hexdigest()[:16]
                iso_time = datetime.fromtimestamp(unix_time).isoformat()

                records.append(
                    ActivityRecord(
                        id=rec_id,
                        source_type=self.source_type(),
                        source_identifier=browser_name,
                        timestamp=float(unix_time),
                        datetime_iso=iso_time,
                        title=f"Visited: {clean_title[:60]}",
                        content=f"URL: {clean_url}\nTitle: {clean_title}",
                        location=clean_url,
                        metadata={"visit_count": count, "browser": browser_name},
                    )
                )
        finally:
            if tmp_path.exists():
                os.remove(tmp_path)

        return records

    def _read_firefox(self, db_path: Path, since_epoch: float) -> List[ActivityRecord]:
        records: List[ActivityRecord] = []

        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
            tmp_path = Path(tmp.name)

        try:
            shutil.copy2(db_path, tmp_path)
            conn = sqlite3.connect(tmp_path)
            cursor = conn.cursor()

            query = """
                SELECT 
                    p.url, 
                    p.title, 
                    p.visit_count,
                    (h.visit_date / 1000000) AS unix_time
                FROM moz_places p
                JOIN moz_historyvisits h ON p.id = h.place_id
                WHERE (h.visit_date / 1000000) > ?
                ORDER BY h.visit_date DESC
                LIMIT 1000
            """
            cursor.execute(query, (since_epoch,))
            rows = cursor.fetchall()
            conn.close()

            for url, title, count, unix_time in rows:
                if not url or url.startswith("about:"):
                    continue

                clean_title = redact_secrets(title or url)
                clean_url = redact_secrets(url)
                rec_id = hashlib.sha256(f"{url}_{unix_time}".encode()).hexdigest()[:16]
                iso_time = datetime.fromtimestamp(unix_time).isoformat()

                records.append(
                    ActivityRecord(
                        id=rec_id,
                        source_type=self.source_type(),
                        source_identifier="Firefox",
                        timestamp=float(unix_time),
                        datetime_iso=iso_time,
                        title=f"Visited: {clean_title[:60]}",
                        content=f"URL: {clean_url}\nTitle: {clean_title}",
                        location=clean_url,
                        metadata={"visit_count": count, "browser": "Firefox"},
                    )
                )
        finally:
            if tmp_path.exists():
                os.remove(tmp_path)

        return records
