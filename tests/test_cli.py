import io
import sys
import unittest
from dijaview.cli import main


class TestCLI(unittest.TestCase):
    def test_cli_help(self):
        saved_stdout = sys.stdout
        sys.stdout = io.StringIO()
        try:
            try:
                main(["--help"])
            except SystemExit as e:
                self.assertEqual(e.code, 0)
            output = sys.stdout.getvalue()
            self.assertIn("dijaview", output)
            self.assertIn("query", output)
            self.assertIn("index", output)
        finally:
            sys.stdout = saved_stdout

    def test_cli_status(self):
        saved_stdout = sys.stdout
        sys.stdout = io.StringIO()
        try:
            code = main(["status"])
            self.assertEqual(code, 0)
            output = sys.stdout.getvalue()
            self.assertIn("Dijaview Status:", output)
        finally:
            sys.stdout = saved_stdout

    def test_cli_config(self):
        saved_stdout = sys.stdout
        sys.stdout = io.StringIO()
        try:
            code = main(["config", "show"])
            self.assertEqual(code, 0)
            output = sys.stdout.getvalue()
            self.assertIn("model", output)
        finally:
            sys.stdout = saved_stdout

    def test_cli_version(self):
        saved_stdout = sys.stdout
        sys.stdout = io.StringIO()
        try:
            code = main(["version"])
            self.assertEqual(code, 0)
            output = sys.stdout.getvalue()
            self.assertIn("Dijaview v", output)
            self.assertIn("Python:", output)
            self.assertIn("Gemma 2 Model:", output)
            self.assertIn("Releases:", output)
        finally:
            sys.stdout = saved_stdout

    def test_cli_version_check_update(self):
        from unittest.mock import patch
        saved_stdout = sys.stdout
        sys.stdout = io.StringIO()
        try:
            with patch("dijaview.cli.check_for_updates", return_value="9.9.9"):
                code = main(["version", "--check-update"])
                self.assertEqual(code, 0)
                output = sys.stdout.getvalue()
                self.assertIn("Update available: v9.9.9", output)

            with patch("dijaview.cli.check_for_updates", return_value="0.1.0"):
                code = main(["version", "--check-update"])
                self.assertEqual(code, 0)
                output = sys.stdout.getvalue()
                self.assertIn("You are running the latest version", output)
        finally:
            sys.stdout = saved_stdout


if __name__ == "__main__":
    unittest.main()
