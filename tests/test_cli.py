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


if __name__ == "__main__":
    unittest.main()
