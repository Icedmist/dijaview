import json
import os
import shutil
import tempfile
import threading
import urllib.error
import urllib.request
import unittest

from dijaview.config import Config
from dijaview.core.models import ActivityRecord
from dijaview.core.permissions import PermissionsManager
from dijaview.storage.database import Database
from dijaview.web.server import create_server


class TestWebServer(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test.db")
        self.config_path = os.path.join(self.temp_dir, "config.json")
        self.db = Database(db_path=self.db_path)
        self.config = Config(config_path=self.config_path)
        self.permissions = PermissionsManager(config=self.config)
        self.token = "sec-token-abcdef1234567890"

        # Seed sample record
        self.db.insert_records([
            ActivityRecord(
                id="rec_web_1",
                source_type="terminal",
                source_identifier="bash",
                timestamp=1700000000.0,
                datetime_iso="2023-11-14T22:13:20",
                title="Terminal Command: git status",
                content="git status",
                location="/home/test/.bash_history",
                metadata={"cmd": "git status"},
            )
        ])

        # Bind to port 0 for automatic port allocation
        self.server = create_server(
            host="127.0.0.1",
            port=0,
            config=self.config,
            db=self.db,
            permissions=self.permissions,
            auth_token=self.token,
        )
        self.port = self.server.server_address[1]
        self.base_url = f"http://127.0.0.1:{self.port}"

        self.server_thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.server_thread.start()

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _authed_request(self, path: str, data: bytes = None, headers: dict = None, method: str = None) -> urllib.request.Request:
        req_headers = {"X-Dijaview-Token": self.token}
        if headers:
            req_headers.update(headers)
        return urllib.request.Request(
            f"{self.base_url}{path}",
            data=data,
            headers=req_headers,
            method=method,
        )

    def test_dashboard_home_page_authenticated(self):
        req = urllib.request.urlopen(f"{self.base_url}/?token={self.token}")
        self.assertEqual(req.status, 200)
        content = req.read().decode("utf-8")
        self.assertIn("Dijaview", content)
        self.assertIn("Local Activity Search Engine", content)
        self.assertIn(self.token, content)

    def test_unauthenticated_request_rejected(self):
        # Home page without token
        with self.assertRaises(urllib.error.HTTPError) as ctx:
            urllib.request.urlopen(f"{self.base_url}/")
        self.assertEqual(ctx.exception.code, 401)
        ctx.exception.close()

        # API without token
        with self.assertRaises(urllib.error.HTTPError) as ctx:
            urllib.request.urlopen(f"{self.base_url}/api/status")
        self.assertEqual(ctx.exception.code, 401)
        ctx.exception.close()

    def test_invalid_host_header_rejected(self):
        req = urllib.request.Request(
            f"{self.base_url}/api/status",
            headers={"Host": "evil-rebinding-site.com", "X-Dijaview-Token": self.token},
        )
        with self.assertRaises(urllib.error.HTTPError) as ctx:
            urllib.request.urlopen(req)
        self.assertEqual(ctx.exception.code, 403)
        ctx.exception.close()

    def test_no_cors_headers(self):
        req = self._authed_request("/api/status")
        res = urllib.request.urlopen(req)
        self.assertEqual(res.status, 200)
        self.assertIsNone(res.headers.get("Access-Control-Allow-Origin"))
        self.assertEqual(res.headers.get("X-Frame-Options"), "DENY")
        self.assertEqual(res.headers.get("X-Content-Type-Options"), "nosniff")

    def test_api_status(self):
        req = self._authed_request("/api/status")
        res = urllib.request.urlopen(req)
        self.assertEqual(res.status, 200)
        data = json.loads(res.read().decode("utf-8"))
        self.assertEqual(data["total_records"], 1)
        self.assertIn("terminal", data["by_source"])
        self.assertIn("gemma_status", data)

    def test_api_timeline(self):
        req = self._authed_request("/api/timeline?limit=10")
        res = urllib.request.urlopen(req)
        self.assertEqual(res.status, 200)
        records = json.loads(res.read().decode("utf-8"))
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["id"], "rec_web_1")

    def test_api_query(self):
        req = self._authed_request("/api/query?q=git&limit=5")
        res = urllib.request.urlopen(req)
        self.assertEqual(res.status, 200)
        data = json.loads(res.read().decode("utf-8"))
        self.assertIn("answer", data)
        self.assertIn("sources", data)
        self.assertEqual(len(data["sources"]), 1)

    def test_api_permissions_and_toggle(self):
        req = self._authed_request("/api/permissions")
        res = urllib.request.urlopen(req)
        self.assertEqual(res.status, 200)
        perms = json.loads(res.read().decode("utf-8"))
        self.assertTrue(perms["sources"]["terminal"])

        # Toggle terminal off
        post_req = self._authed_request(
            "/api/permissions/toggle",
            data=json.dumps({"source": "terminal"}).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        post_res = urllib.request.urlopen(post_req)
        self.assertEqual(post_res.status, 200)
        res_data = json.loads(post_res.read().decode("utf-8"))
        self.assertFalse(res_data["enabled"])
        self.assertFalse(self.permissions.is_source_enabled("terminal"))

    def test_api_index(self):
        post_req = self._authed_request(
            "/api/index",
            data=b"{}",
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        res = urllib.request.urlopen(post_req)
        self.assertEqual(res.status, 200)
        data = json.loads(res.read().decode("utf-8"))
        self.assertEqual(data["status"], "success")
        self.assertIsInstance(data["indexed"], int)


if __name__ == "__main__":
    unittest.main()
