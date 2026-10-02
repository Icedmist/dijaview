import os
import tempfile
import unittest
from pathlib import Path
from dijaview.adapters.terminal import TerminalAdapter
from dijaview.adapters.notes import NotesAdapter


class TestAdapters(unittest.TestCase):
    def test_terminal_adapter_parsing(self):
        with tempfile.NamedTemporaryFile(mode="w+", suffix="_history", delete=False) as tmp:
            tmp.write(": 1790900000:0;git status\n")
            tmp.write(": 1790900100:0;curl -H 'Authorization: Bearer mysecrettoken123' https://api.com\n")
            tmp.write(": 1790900200:0;ls\n")  # should be filtered as noise
            tmp_path = tmp.name

        try:
            adapter = TerminalAdapter(history_paths=[tmp_path])
            records = adapter.scan_records()

            self.assertEqual(len(records), 2)
            # Verify secret was redacted
            self.assertIn("[REDACTED_TOKEN]", records[1].content)
            self.assertNotIn("mysecrettoken123", records[1].content)
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    def test_notes_adapter_parsing(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            note_file = Path(tmpdir) / "test_note.md"
            note_file.write_text("# API Integration\nThis is a note about connecting the webhook endpoint.")

            adapter = NotesAdapter(directories=[tmpdir])
            records = adapter.scan_records()

            self.assertEqual(len(records), 1)
            self.assertIn("API Integration", records[0].title)
            self.assertIn("webhook endpoint", records[0].content)


if __name__ == "__main__":
    unittest.main()
