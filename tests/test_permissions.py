import os
import shutil
import tempfile
import unittest
from pathlib import Path

from dijaview.adapters.notes import NotesAdapter
from dijaview.cli import main
from dijaview.config import Config
from dijaview.core.permissions import DEFAULT_PERMISSIONS, PermissionsManager
from dijaview.core.redactor import redact_secrets


class TestPermissions(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = os.path.join(self.temp_dir, "config.json")
        self.config = Config(config_path=self.config_path)
        self.permissions = PermissionsManager(config=self.config)

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_default_permissions_initialization(self):
        self.assertTrue(self.permissions.is_source_enabled("terminal"))
        self.assertTrue(self.permissions.is_source_enabled("browser"))
        self.assertTrue(self.permissions.is_source_enabled("notes"))
        self.assertFalse(self.permissions.is_source_enabled("camera"))
        self.assertGreater(len(self.permissions.get_allowed_paths()), 0)
        self.assertGreater(len(self.permissions.get_blocked_paths()), 0)
        self.assertEqual(self.permissions.get_max_file_size(), 1048576)
        self.assertEqual(self.permissions.get_custom_redactions(), [])

    def test_enable_and_disable_sources(self):
        self.permissions.disable_source("terminal")
        self.assertFalse(self.permissions.is_source_enabled("terminal"))

        self.permissions.enable_source("terminal")
        self.assertTrue(self.permissions.is_source_enabled("terminal"))

    def test_path_allow_and_block(self):
        work_dir = os.path.join(self.temp_dir, "work_notes")
        secret_dir = os.path.join(work_dir, "secrets")
        os.makedirs(secret_dir, exist_ok=True)

        note_file = os.path.join(work_dir, "task.md")
        secret_file = os.path.join(secret_dir, "passwords.txt")
        env_file = os.path.join(work_dir, ".env.production")

        with open(note_file, "w") as f:
            f.write("# Task\nReview PR")
        with open(secret_file, "w") as f:
            f.write("secret_password=123")
        with open(env_file, "w") as f:
            f.write("KEY=value")

        # Initially, work_dir is not in allowed paths
        self.assertFalse(self.permissions.is_path_allowed(note_file))

        # Add work_dir to allowed paths
        self.permissions.allow_path(work_dir)
        self.assertTrue(self.permissions.is_path_allowed(note_file))

        # Block secret_dir specifically
        self.permissions.block_path(secret_dir)
        self.assertFalse(self.permissions.is_path_allowed(secret_file))

        # Glob pattern blocking: *.env* is blocked by default
        self.assertFalse(self.permissions.is_path_allowed(env_file))

        # Remove path from blocked
        self.permissions.remove_path(secret_dir)
        self.assertTrue(self.permissions.is_path_allowed(secret_file))

    def test_custom_redaction_filters(self):
        self.permissions.add_custom_redaction(
            name="customer_id",
            pattern=r"CUST-[0-9]{5}",
            replacement="[REDACTED_CUSTOMER]",
        )
        redactions = self.permissions.get_custom_redactions()
        self.assertEqual(len(redactions), 1)
        self.assertEqual(redactions[0]["name"], "customer_id")

        tuples = self.permissions.get_custom_rules_tuples()
        text = "Order placed for CUST-98765 today."
        redacted = redact_secrets(text, custom_rules=tuples)
        self.assertIn("[REDACTED_CUSTOMER]", redacted)
        self.assertNotIn("CUST-98765", redacted)

        # Remove filter
        removed = self.permissions.remove_custom_redaction("customer_id")
        self.assertTrue(removed)
        self.assertEqual(len(self.permissions.get_custom_redactions()), 0)

    def test_invalid_custom_filter_raises_error(self):
        with self.assertRaises(Exception):
            self.permissions.add_custom_redaction("broken", r"[a-z(")

    def test_reset_defaults(self):
        self.permissions.disable_source("notes")
        self.permissions.set_max_file_size(500)
        self.permissions.add_custom_redaction("sample", "test")

        self.permissions.reset_defaults()

        self.assertTrue(self.permissions.is_source_enabled("notes"))
        self.assertEqual(self.permissions.get_max_file_size(), 1048576)
        self.assertEqual(len(self.permissions.get_custom_redactions()), 0)

    def test_notes_adapter_permissions_and_size_limit(self):
        notes_dir = os.path.join(self.temp_dir, "notes")
        os.makedirs(notes_dir, exist_ok=True)
        small_file = os.path.join(notes_dir, "small.md")
        huge_file = os.path.join(notes_dir, "huge.txt")

        with open(small_file, "w") as f:
            f.write("# Small Note\nEverything is fine.")
        with open(huge_file, "w") as f:
            f.write("A" * 2000)

        # Allow notes_dir and set max size to 1000 bytes
        self.permissions.allow_path(notes_dir)
        self.permissions.set_max_file_size(1000)

        adapter = NotesAdapter(directories=[notes_dir], permissions=self.permissions)
        records = adapter.scan_records()

        # Only small.md should be indexed; huge.txt is skipped due to size cap
        indexed_names = [r.source_identifier for r in records]
        self.assertIn("small.md", indexed_names)
        self.assertNotIn("huge.txt", indexed_names)

        # Now disable notes source
        self.permissions.disable_source("notes")
        records_after_disable = adapter.scan_records()
        self.assertEqual(len(records_after_disable), 0)

    def test_cli_permissions_commands(self):
        # Test permissions show
        exit_code = main(["permissions", "show"])
        self.assertEqual(exit_code, 0)

        # Test enable and disable
        exit_code = main(["permissions", "disable", "browser"])
        self.assertEqual(exit_code, 0)

        exit_code = main(["permissions", "enable", "browser"])
        self.assertEqual(exit_code, 0)

        # Test allow-path and block-path
        exit_code = main(["permissions", "allow-path", self.temp_dir])
        self.assertEqual(exit_code, 0)

        exit_code = main(["permissions", "block-path", os.path.join(self.temp_dir, "blocked")])
        self.assertEqual(exit_code, 0)

        exit_code = main(["permissions", "remove-path", os.path.join(self.temp_dir, "blocked")])
        self.assertEqual(exit_code, 0)

        # Test filter commands
        exit_code = main(["permissions", "add-filter", "order_id", r"ORD-\d+"])
        self.assertEqual(exit_code, 0)

        exit_code = main(["permissions", "remove-filter", "order_id"])
        self.assertEqual(exit_code, 0)

        # Test reset
        exit_code = main(["permissions", "reset"])
        self.assertEqual(exit_code, 0)


if __name__ == "__main__":
    unittest.main()
