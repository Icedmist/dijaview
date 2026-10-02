import os
import tempfile
import unittest
from dijaview.core.models import ActivityRecord, TimeRange
from dijaview.storage.database import Database


class TestDatabase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.tmp.close()
        self.db = Database(db_path=self.tmp.name)

    def tearDown(self):
        if os.path.exists(self.tmp.name):
            os.remove(self.tmp.name)

    def test_database_insert_and_search(self):
        record1 = ActivityRecord(
            id="rec_1",
            source_type="terminal",
            source_identifier="bash",
            timestamp=1790900000.0,
            datetime_iso="2026-10-02T10:00:00Z",
            title="Terminal Command: curl",
            content="curl -X POST https://api.paystack.co/verify -H 'Auth: Bearer token'",
            location="~/.bash_history",
        )

        record2 = ActivityRecord(
            id="rec_2",
            source_type="notes",
            source_identifier="api_doc.md",
            timestamp=1790800000.0,
            datetime_iso="2026-10-01T10:00:00Z",
            title="Note: API Keys",
            content="Paystack webhook configuration details and secret key rotation",
            location="~/notes/api_doc.md",
        )

        count = self.db.insert_records([record1, record2])
        self.assertEqual(count, 2)

        # Duplicate insert check
        duplicate_count = self.db.insert_records([record1])
        self.assertEqual(duplicate_count, 0)

        # Full-text search for 'paystack'
        results = self.db.search("paystack")
        self.assertEqual(len(results), 2)

        # Source filtered search
        terminal_results = self.db.search("paystack", source_type="terminal")
        self.assertEqual(len(terminal_results), 1)
        self.assertEqual(terminal_results[0].id, "rec_1")

        # Temporal filtered search
        time_range = TimeRange(start_timestamp=1790850000.0, end_timestamp=1790950000.0)
        filtered = self.db.search("paystack", time_range=time_range)
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0].id, "rec_1")

        # Check stats
        stats = self.db.get_stats()
        self.assertEqual(stats["total_records"], 2)
        self.assertEqual(stats["by_source"]["terminal"], 1)
        self.assertEqual(stats["by_source"]["notes"], 1)

        # Purge
        purged = self.db.purge(source_type="terminal")
        self.assertEqual(purged, 1)
        self.assertEqual(self.db.get_stats()["total_records"], 1)


if __name__ == "__main__":
    unittest.main()
