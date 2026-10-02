import unittest
from datetime import datetime
from dijaview.core.temporal import parse_temporal_expression


class TestTemporal(unittest.TestCase):
    def test_parse_yesterday(self):
        ref = datetime(2026, 10, 2, 12, 0, 0)
        tr = parse_temporal_expression("what did I do yesterday?", reference_date=ref)
        self.assertIsNotNone(tr)
        self.assertEqual(tr.description, "yesterday")
        start_dt = datetime.fromtimestamp(tr.start_timestamp)
        self.assertEqual(start_dt.day, 1)
        self.assertEqual(start_dt.month, 10)
        self.assertEqual(start_dt.year, 2026)

    def test_parse_last_weekday(self):
        # Oct 2, 2026 is a Friday
        ref = datetime(2026, 10, 2, 12, 0, 0)
        tr = parse_temporal_expression("Where was that note from last Tuesday?", reference_date=ref)
        self.assertIsNotNone(tr)
        self.assertEqual(tr.description, "last Tuesday")
        start_dt = datetime.fromtimestamp(tr.start_timestamp)
        # Tuesday before Friday Oct 2 is Sep 29
        self.assertEqual(start_dt.day, 29)
        self.assertEqual(start_dt.month, 9)
        self.assertEqual(start_dt.year, 2026)

    def test_parse_days_ago(self):
        ref = datetime(2026, 10, 2, 12, 0, 0)
        tr = parse_temporal_expression("Show commands from 3 days ago", reference_date=ref)
        self.assertIsNotNone(tr)
        self.assertEqual(tr.description, "3 days ago")
        start_dt = datetime.fromtimestamp(tr.start_timestamp)
        self.assertEqual(start_dt.day, 29)
        self.assertEqual(start_dt.month, 9)

    def test_parse_no_temporal(self):
        tr = parse_temporal_expression("How do I configure nginx?")
        self.assertIsNone(tr)


if __name__ == "__main__":
    unittest.main()
