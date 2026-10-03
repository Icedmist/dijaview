import logging
import sqlite3
import threading
import time
from datetime import datetime
from typing import List, Optional

from dijaview.adapters.base import BaseSourceAdapter
from dijaview.adapters.browser import BrowserAdapter
from dijaview.adapters.notes import NotesAdapter
from dijaview.adapters.terminal import TerminalAdapter
from dijaview.config import Config
from dijaview.core.permissions import PermissionsManager
from dijaview.storage.database import Database

logger = logging.getLogger("dijaview.watcher")


class SyncWatcher:
    """Continuously monitors local activity files and automatically indexes updates."""

    def __init__(
        self,
        db: Optional[Database] = None,
        config: Optional[Config] = None,
        permissions: Optional[PermissionsManager] = None,
        adapters: Optional[List[BaseSourceAdapter]] = None,
        interval_seconds: int = 30,
    ):
        self.config = config or Config()
        self.db = db or Database(db_path=self.config.get("storage.db_path"))
        self.permissions = permissions or PermissionsManager(config=self.config)
        self.adapters = adapters
        self.interval_seconds = max(5, interval_seconds)
        self._running = False

    def _get_latest_timestamp(self, source_type: str) -> float:
        """Retrieves the most recent timestamp recorded for a given source."""
        try:
            with self.db._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT MAX(timestamp) FROM activity_records WHERE source_type = ?",
                    (source_type,),
                )
                row = cursor.fetchone()
                if row and row[0] is not None:
                    return float(row[0])
        except Exception:
            pass
        return 0.0

    def run_once(self) -> int:
        """Performs a single incremental scan across all enabled sources."""
        total_indexed = 0

        if self.adapters is not None:
            adapters = self.adapters
        else:
            adapters = []
            if self.permissions.is_source_enabled("terminal"):
                adapters.append(TerminalAdapter(permissions=self.permissions))
            if self.permissions.is_source_enabled("browser"):
                adapters.append(BrowserAdapter(permissions=self.permissions))
            if self.permissions.is_source_enabled("notes"):
                notes_dirs = self.config.get("adapters.notes.directories", [])
                adapters.append(NotesAdapter(directories=notes_dirs, permissions=self.permissions))

        for adapter in adapters:
            try:
                latest_epoch = self._get_latest_timestamp(adapter.source_type())
                records = adapter.scan_records(since_epoch=latest_epoch)
                count = self.db.insert_records(records)
                total_indexed += count
            except Exception as e:
                logger.warning(f"Error scanning source {adapter.source_type()}: {e}")

        return total_indexed

    def run_loop(self, stop_event: Optional[threading.Event] = None) -> None:
        """Runs the continuous synchronization loop until stopped or interrupted."""
        self._running = True
        print(f"Dijaview background watcher started (interval: {self.interval_seconds}s).")
        print("Press Ctrl+C to stop.")

        try:
            while self._running:
                if stop_event and stop_event.is_set():
                    break

                now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                try:
                    new_records = self.run_once()
                    if new_records > 0:
                        print(f"[{now_str}] Sync complete: +{new_records} new activity records indexed.")
                except Exception as e:
                    print(f"[{now_str}] Sync error: {e}")

                # Sleep in 1-second chunks to respond quickly to stop signal
                for _ in range(self.interval_seconds):
                    if stop_event and stop_event.is_set():
                        self._running = False
                        break
                    if not self._running:
                        break
                    time.sleep(1)
        except KeyboardInterrupt:
            print("\nStopping background watcher...")
        finally:
            self._running = False
            print("Dijaview background watcher stopped.")

    def stop(self) -> None:
        """Signals the loop to terminate."""
        self._running = False
