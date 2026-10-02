import os
import shutil
import tempfile
import threading
import time
import unittest

from dijaview.adapters.terminal import TerminalAdapter
from dijaview.config import Config
from dijaview.core.models import ActivityRecord
from dijaview.core.permissions import PermissionsManager
from dijaview.storage.database import Database
from dijaview.watcher.daemon import SyncWatcher


class TestSyncWatcher(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test.db")
        self.config_path = os.path.join(self.temp_dir, "config.json")
        self.db = Database(db_path=self.db_path)
        self.config = Config(config_path=self.config_path)
        self.permissions = PermissionsManager(config=self.config)

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_watcher_run_once_incremental(self):
        watcher = SyncWatcher(
            db=self.db,
            config=self.config,
            permissions=self.permissions,
            interval_seconds=10,
        )

        # Initial run
        count_first = watcher.run_once()
        self.assertIsInstance(count_first, int)

        # Second run immediately after should index 0 duplicates
        count_second = watcher.run_once()
        self.assertEqual(count_second, 0)

    def test_watcher_stop_event(self):
        watcher = SyncWatcher(
            db=self.db,
            config=self.config,
            permissions=self.permissions,
            interval_seconds=1,
        )

        stop_event = threading.Event()
        thread = threading.Thread(target=watcher.run_loop, args=(stop_event,), daemon=True)
        thread.start()

        time.sleep(0.5)
        stop_event.set()
        thread.join(timeout=3)
        self.assertFalse(thread.is_alive())


if __name__ == "__main__":
    unittest.main()
