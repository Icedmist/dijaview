import json
import logging
import secrets
import threading
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Any, Dict, List, Optional

from dijaview.config import Config
from dijaview.core.permissions import PermissionsManager
from dijaview.engine.gemma import GemmaClient
from dijaview.engine.search import SearchEngine
from dijaview.storage.database import Database
from dijaview.watcher.daemon import SyncWatcher

logger = logging.getLogger("dijaview.web")


DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Dijaview • Local Activity Search Engine</title>
  <!-- AUTH_TOKEN_INJECTION -->
  <style>
    :root {
      --bg: #0d1117;
      --card-bg: #161b22;
      --card-border: #30363d;
      --text: #f0f6fc;
      --text-muted: #8b949e;
      --accent: #58a6ff;
      --accent-hover: #79c0ff;
      --green: #3fb950;
      --purple: #bc8cff;
      --orange: #f0883e;
      --code-bg: #0d1117;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
      background: var(--bg);
      color: var(--text);
      line-height: 1.5;
      padding: 24px;
    }
    .container {
      max-width: 1000px;
      margin: 0 auto;
    }
    header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 24px;
      padding-bottom: 16px;
      border-bottom: 1px solid var(--card-border);
    }
    .brand {
      display: flex;
      align-items: center;
      gap: 12px;
    }
    .logo-badge {
      background: linear-gradient(135deg, #1f6feb, #238636);
      color: #fff;
      font-weight: bold;
      font-size: 20px;
      width: 40px;
      height: 40px;
      border-radius: 8px;
      display: flex;
      align-items: center;
      justify-content: center;
    }
    .brand-title {
      font-size: 22px;
      font-weight: 700;
      letter-spacing: -0.5px;
    }
    .brand-sub {
      font-size: 13px;
      color: var(--text-muted);
    }
    .header-actions {
      display: flex;
      align-items: center;
      gap: 10px;
    }
    .pill {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 6px 12px;
      border-radius: 20px;
      font-size: 12px;
      font-weight: 600;
      background: var(--card-bg);
      border: 1px solid var(--card-border);
    }
    .pill-green { color: var(--green); border-color: rgba(63, 185, 80, 0.3); }
    .btn {
      background: #21262d;
      color: var(--text);
      border: 1px solid var(--card-border);
      padding: 7px 14px;
      border-radius: 6px;
      font-size: 13px;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.2s;
    }
    .btn:hover { background: #30363d; }
    .btn-primary {
      background: #238636;
      border-color: #2ea043;
      color: #fff;
    }
    .btn-primary:hover { background: #2ea043; }
    
    /* Search Box */
    .search-card {
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: 12px;
      padding: 20px;
      margin-bottom: 24px;
      box-shadow: 0 8px 24px rgba(0,0,0,0.2);
    }
    .search-row {
      display: flex;
      gap: 10px;
      margin-bottom: 14px;
    }
    .search-input {
      flex: 1;
      background: var(--bg);
      border: 1px solid var(--card-border);
      color: var(--text);
      font-size: 16px;
      padding: 12px 16px;
      border-radius: 8px;
      outline: none;
      transition: border-color 0.2s;
    }
    .search-input:focus { border-color: var(--accent); }
    .filters-row {
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      gap: 10px;
    }
    .filter-group {
      display: flex;
      gap: 8px;
    }
    .filter-chip {
      background: var(--bg);
      border: 1px solid var(--card-border);
      color: var(--text-muted);
      padding: 5px 12px;
      border-radius: 16px;
      font-size: 12px;
      cursor: pointer;
      transition: all 0.15s;
    }
    .filter-chip.active {
      background: rgba(88, 166, 255, 0.15);
      border-color: var(--accent);
      color: var(--accent);
      font-weight: 600;
    }
    .example-queries {
      display: flex;
      align-items: center;
      gap: 8px;
      margin-top: 12px;
      font-size: 12px;
      color: var(--text-muted);
      flex-wrap: wrap;
    }
    .example-pill {
      background: rgba(255,255,255,0.05);
      padding: 3px 8px;
      border-radius: 4px;
      cursor: pointer;
      color: var(--accent);
    }
    .example-pill:hover { text-decoration: underline; }

    /* Answer Box */
    .answer-card {
      display: none;
      background: rgba(31, 111, 235, 0.08);
      border: 1px solid rgba(88, 166, 255, 0.3);
      border-radius: 12px;
      padding: 20px;
      margin-bottom: 24px;
    }
    .answer-title {
      font-size: 14px;
      font-weight: 700;
      color: var(--accent);
      margin-bottom: 8px;
      display: flex;
      align-items: center;
      gap: 6px;
    }
    .answer-content {
      font-size: 15px;
      line-height: 1.6;
      white-space: pre-wrap;
      color: #e6edf3;
    }
    .citations {
      margin-top: 14px;
      display: flex;
      flex-direction: column;
      gap: 6px;
    }
    .citation-item {
      font-size: 12px;
      color: var(--text-muted);
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      padding: 8px 12px;
      border-radius: 6px;
    }

    /* Section Tabs */
    .section-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 16px;
    }
    .section-title {
      font-size: 16px;
      font-weight: 700;
    }

    /* Timeline Items */
    .timeline {
      display: flex;
      flex-direction: column;
      gap: 10px;
    }
    .activity-card {
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: 8px;
      padding: 14px 16px;
      transition: border-color 0.2s;
    }
    .activity-card:hover { border-color: var(--accent); }
    .activity-meta {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 6px;
    }
    .source-tag {
      font-size: 11px;
      font-weight: 700;
      text-transform: uppercase;
      padding: 2px 8px;
      border-radius: 4px;
    }
    .tag-terminal { background: rgba(63, 185, 80, 0.15); color: var(--green); }
    .tag-browser  { background: rgba(88, 166, 255, 0.15); color: var(--accent); }
    .tag-notes    { background: rgba(188, 140, 255, 0.15); color: var(--purple); }
    .activity-time {
      font-size: 12px;
      color: var(--text-muted);
    }
    .activity-title {
      font-size: 14px;
      font-weight: 600;
      margin-bottom: 4px;
      color: #fff;
    }
    .activity-location {
      font-size: 12px;
      color: var(--accent);
      word-break: break-all;
      margin-bottom: 6px;
    }
    .activity-snippet {
      font-size: 13px;
      color: var(--text-muted);
      background: var(--code-bg);
      padding: 8px 10px;
      border-radius: 6px;
      font-family: monospace;
      max-height: 80px;
      overflow-y: auto;
      white-space: pre-wrap;
    }

    /* Permissions Modal */
    .modal-overlay {
      display: none;
      position: fixed;
      top: 0; left: 0; right: 0; bottom: 0;
      background: rgba(0,0,0,0.7);
      backdrop-filter: blur(4px);
      justify-content: center;
      align-items: center;
      z-index: 100;
    }
    .modal {
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: 12px;
      width: 90%;
      max-width: 600px;
      max-height: 85vh;
      overflow-y: auto;
      padding: 24px;
    }
    .modal-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 16px;
      padding-bottom: 10px;
      border-bottom: 1px solid var(--card-border);
    }
    .toggle-row {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 10px 0;
      border-bottom: 1px solid rgba(255,255,255,0.05);
    }
    .status-toast {
      position: fixed;
      bottom: 24px;
      right: 24px;
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      padding: 10px 18px;
      border-radius: 8px;
      font-size: 13px;
      box-shadow: 0 4px 12px rgba(0,0,0,0.3);
      display: none;
      z-index: 200;
    }
  </style>
</head>
<body>
  <div class="container">
    <header>
      <div class="brand">
        <div class="logo-badge">D</div>
        <div>
          <div class="brand-title">Dijaview</div>
          <div class="brand-sub">Privacy-First Local Activity Search Engine</div>
        </div>
      </div>
      <div class="header-actions">
        <span class="pill pill-green" id="recordsPill">● Loading...</span>
        <button class="btn" onclick="openPermissionsModal()">Permissions</button>
        <button class="btn btn-primary" onclick="triggerSync()">Sync Now</button>
      </div>
    </header>

    <div class="search-card">
      <div class="search-row">
        <input type="text" id="searchInput" class="search-input" placeholder="Ask anything about what you did on your computer..." onkeydown="if(event.key==='Enter') executeSearch()">
        <button class="btn btn-primary" onclick="executeSearch()">Search</button>
      </div>
      <div class="filters-row">
        <div class="filter-group">
          <button class="filter-chip active" data-source="" onclick="setSourceFilter('')">All Sources</button>
          <button class="filter-chip" data-source="terminal" onclick="setSourceFilter('terminal')">Terminal</button>
          <button class="filter-chip" data-source="browser" onclick="setSourceFilter('browser')">Browser</button>
          <button class="filter-chip" data-source="notes" onclick="setSourceFilter('notes')">Notes</button>
        </div>
        <div style="font-size: 12px; color: var(--text-muted);" id="modelStatusText">Model: Gemma 2</div>
      </div>
      <div class="example-queries">
        <span>Try asking:</span>
        <span class="example-pill" onclick="runSample('api key')">"api key"</span>
        <span class="example-pill" onclick="runSample('curl command yesterday')">"curl command yesterday"</span>
        <span class="example-pill" onclick="runSample('github pull request')">"github pull request"</span>
        <span class="example-pill" onclick="runSample('python projects')">"python projects"</span>
      </div>
    </div>

    <div id="answerCard" class="answer-card">
      <div class="answer-title">💡 Dijaview Answer</div>
      <div class="answer-content" id="answerContent"></div>
      <div class="citations" id="citationsBox"></div>
    </div>

    <div class="section-header">
      <div class="section-title" id="timelineTitle">Recent Computer Activity</div>
      <button class="btn" onclick="loadTimeline()">Refresh</button>
    </div>

    <div class="timeline" id="timelineContainer">
      <div style="color: var(--text-muted); text-align: center; padding: 40px;">Loading recent activities...</div>
    </div>
  </div>

  <!-- Permissions Modal -->
  <div class="modal-overlay" id="permModal">
    <div class="modal">
      <div class="modal-header">
        <h3>Permissions Matrix</h3>
        <button class="btn" onclick="closePermissionsModal()">✕ Close</button>
      </div>
      <div style="font-size: 13px; color: var(--text-muted); margin-bottom: 16px;">
        Control what Dijaview is permitted to index on your computer.
      </div>
      <div id="permToggles"></div>
      <h4 style="margin: 20px 0 8px 0; font-size: 14px;">Allowed Directories</h4>
      <div id="permAllowed" style="font-size: 13px; color: var(--text-muted);"></div>
      <h4 style="margin: 20px 0 8px 0; font-size: 14px;">Blocked Paths and Patterns</h4>
      <div id="permBlocked" style="font-size: 13px; color: var(--text-muted);"></div>
    </div>
  </div>

  <div class="status-toast" id="toast"></div>

  <script>
    let activeSource = '';
    const urlParams = new URLSearchParams(window.location.search);
    const AUTH_TOKEN = window.__DIJAVIEW_TOKEN__ || urlParams.get('token') || '';

    async function apiFetch(endpoint, options = {}) {
      const headers = Object.assign({}, options.headers || {}, {
        'X-Dijaview-Token': AUTH_TOKEN
      });
      const separator = endpoint.includes('?') ? '&' : '?';
      const authedUrl = `${endpoint}${separator}token=${encodeURIComponent(AUTH_TOKEN)}`;
      return fetch(authedUrl, Object.assign({}, options, { headers }));
    }

    function showToast(msg) {
      const toast = document.getElementById('toast');
      toast.innerText = msg;
      toast.style.display = 'block';
      setTimeout(() => { toast.style.display = 'none'; }, 3000);
    }

    function setSourceFilter(src) {
      activeSource = src;
      document.querySelectorAll('.filter-chip').forEach(chip => {
        chip.classList.toggle('active', chip.getAttribute('data-source') === src);
      });
      loadTimeline();
    }

    function runSample(text) {
      document.getElementById('searchInput').value = text;
      executeSearch();
    }

    async function loadStatus() {
      try {
        const res = await apiFetch('/api/status');
        const data = await res.json();
        document.getElementById('recordsPill').innerText = `${data.total_records.toLocaleString()} Records • 100% Local`;
        document.getElementById('modelStatusText').innerText = `Model: ${data.gemma_model} [${data.gemma_status}]`;
      } catch (e) {
        console.error(e);
      }
    }

    async function loadTimeline() {
      const container = document.getElementById('timelineContainer');
      const params = new URLSearchParams({ limit: '30' });
      if (activeSource) params.append('source', activeSource);

      try {
        const res = await apiFetch(`/api/timeline?${params.toString()}`);
        const records = await res.json();

        if (!records.length) {
          container.innerHTML = '<div style="color: var(--text-muted); text-align: center; padding: 40px;">No recent activities found for this source.</div>';
          return;
        }

        container.innerHTML = records.map(r => `
          <div class="activity-card">
            <div class="activity-meta">
              <span class="source-tag tag-${r.source_type}">${r.source_type}</span>
              <span class="activity-time">${r.datetime_iso.replace('T', ' ').slice(0, 19)}</span>
            </div>
            <div class="activity-title">${escapeHtml(r.title)}</div>
            <div class="activity-location">${escapeHtml(r.location)}</div>
            <div class="activity-snippet">${escapeHtml(r.content)}</div>
          </div>
        `).join('');
      } catch (e) {
        container.innerHTML = `<div style="color: #f85149; text-align: center; padding: 20px;">Failed to load activities: ${e}</div>`;
      }
    }

    async function executeSearch() {
      const query = document.getElementById('searchInput').value.trim();
      if (!query) return;

      const answerCard = document.getElementById('answerCard');
      const answerContent = document.getElementById('answerContent');
      const citationsBox = document.getElementById('citationsBox');

      answerCard.style.display = 'block';
      answerContent.innerText = 'Searching activity logs...';
      citationsBox.innerHTML = '';

      const params = new URLSearchParams({ q: query, limit: '10' });
      if (activeSource) params.append('source', activeSource);

      try {
        const res = await apiFetch(`/api/query?${params.toString()}`);
        const data = await res.json();

        answerContent.innerText = data.answer;
        if (data.sources && data.sources.length) {
          citationsBox.innerHTML = '<div style="font-weight: 600; font-size: 13px; margin-bottom: 4px;">Cited Sources:</div>' + 
            data.sources.map((s, idx) => `
              <div class="citation-item">
                [${idx + 1}] (${s.source_type.toUpperCase()}) <strong>${escapeHtml(s.title)}</strong><br>
                Location: ${escapeHtml(s.location)} • ${s.datetime_iso.replace('T', ' ').slice(0, 19)}
              </div>
            `).join('');
        }
      } catch (e) {
        answerContent.innerText = `Search error: ${e}`;
      }
    }

    async function triggerSync() {
      showToast('Indexing activity sources...');
      try {
        const res = await apiFetch('/api/index', { method: 'POST' });
        const data = await res.json();
        showToast(`Sync complete! ${data.indexed} new entries added.`);
        loadStatus();
        loadTimeline();
      } catch (e) {
        showToast(`Sync failed: ${e}`);
      }
    }

    async function openPermissionsModal() {
      const modal = document.getElementById('permModal');
      modal.style.display = 'flex';

      try {
        const res = await apiFetch('/api/permissions');
        const perms = await res.json();

        const togglesContainer = document.getElementById('permToggles');
        togglesContainer.innerHTML = Object.entries(perms.sources || {}).map(([src, enabled]) => `
          <div class="toggle-row">
            <div>
              <strong style="text-transform: capitalize;">${src}</strong>
              <div style="font-size: 12px; color: var(--text-muted);">${enabled ? 'Currently permitted to scan' : 'Scanning disabled'}</div>
            </div>
            <button class="btn ${enabled ? 'btn-primary' : ''}" onclick="toggleSource('${src}')">
              ${enabled ? 'Enabled' : 'Disabled'}
            </button>
          </div>
        `).join('');

        const allowedContainer = document.getElementById('permAllowed');
        allowedContainer.innerHTML = (perms.paths?.allowed || []).map(p => `<div>+ ${escapeHtml(p)}</div>`).join('') || 'None specified';

        const blockedContainer = document.getElementById('permBlocked');
        blockedContainer.innerHTML = (perms.paths?.blocked || []).map(p => `<div>- ${escapeHtml(p)}</div>`).join('') || 'None specified';
      } catch (e) {
        console.error(e);
      }
    }

    function closePermissionsModal() {
      document.getElementById('permModal').style.display = 'none';
    }

    async function toggleSource(source) {
      try {
        await apiFetch('/api/permissions/toggle', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ source })
        });
        openPermissionsModal();
        loadStatus();
      } catch (e) {
        showToast(`Failed to toggle: ${e}`);
      }
    }

    function escapeHtml(str) {
      if (!str) return '';
      return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
    }

    // Initialize on load
    loadStatus();
    loadTimeline();
  </script>
</body>
</html>
"""


class DijaviewRequestHandler(BaseHTTPRequestHandler):
    """Handles REST API and dashboard requests for Dijaview."""

    config: Config
    db: Database
    gemma: GemmaClient
    permissions: PermissionsManager
    engine: SearchEngine
    auth_token: str = ""

    def _validate_host(self) -> bool:
        """Protects against DNS rebinding and cross-site requests by validating Host and Origin."""
        host_header = self.headers.get("Host", "").strip()
        if not host_header:
            return False
        hostname = host_header.split(":")[0].strip().lower()
        if hostname not in {"127.0.0.1", "localhost", "::1"}:
            return False

        origin_header = self.headers.get("Origin", "").strip()
        if origin_header:
            parsed = urllib.parse.urlparse(origin_header)
            origin_host = (parsed.hostname or "").lower()
            if origin_host not in {"127.0.0.1", "localhost", "::1"}:
                return False
        return True

    def _validate_auth(self, query_params: Dict[str, List[str]]) -> bool:
        """Validates the per-launch security token via header or query parameter."""
        token = self.headers.get("X-Dijaview-Token", "").strip()
        if not token:
            auth_hdr = self.headers.get("Authorization", "").strip()
            if auth_hdr.lower().startswith("bearer "):
                token = auth_hdr[7:].strip()
        if not token:
            token = query_params.get("token", [""])[0].strip()
        return bool(self.auth_token and token == self.auth_token)

    def do_GET(self) -> None:
        if not self._validate_host():
            self.send_error(403, "Forbidden: Invalid Host or Origin header")
            return

        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path
        query_params = urllib.parse.parse_qs(parsed_url.query)

        if path in {"", "/"}:
            if not self._validate_auth(query_params):
                unauth_html = (
                    "<!DOCTYPE html><html><body style='font-family:sans-serif;padding:40px;"
                    "background:#0d1117;color:#f0f6fc;'><h2>401 Unauthorized</h2>"
                    "<p>Dijaview dashboard requires an authentication token. "
                    "Use the authenticated URL printed in your terminal.</p>"
                    "</body></html>"
                )
                self._send_html(unauth_html, status=401)
                return

            html = DASHBOARD_HTML.replace(
                "<!-- AUTH_TOKEN_INJECTION -->",
                f'<script>window.__DIJAVIEW_TOKEN__ = "{self.auth_token}";</script>',
            )
            self._send_html(html)
            return

        if path.startswith("/api/"):
            if not self._validate_auth(query_params):
                self._send_json({"error": "Unauthorized: valid authentication token required"}, status=401)
                return

            if path == "/api/status":
                self._handle_api_status()
                return

            if path == "/api/timeline":
                self._handle_api_timeline(query_params)
                return

            if path == "/api/query":
                self._handle_api_query(query_params)
                return

            if path == "/api/permissions":
                self._handle_api_permissions()
                return

        self.send_error(404, "Not Found")

    def do_POST(self) -> None:
        if not self._validate_host():
            self.send_error(403, "Forbidden: Invalid Host or Origin header")
            return

        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path
        query_params = urllib.parse.parse_qs(parsed_url.query)

        if path.startswith("/api/"):
            if not self._validate_auth(query_params):
                self._send_json({"error": "Unauthorized: valid authentication token required"}, status=401)
                return

            if path == "/api/index":
                self._handle_api_index()
                return

            if path == "/api/permissions/toggle":
                self._handle_api_permissions_toggle()
                return

        self.send_error(404, "Not Found")

    def _send_json(self, data: Any, status: int = 200) -> None:
        body = json.dumps(data, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.end_headers()
        self.wfile.write(body)

    def _send_html(self, html_text: str, status: int = 200) -> None:
        body = html_text.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.end_headers()
        self.wfile.write(body)

    def _handle_api_status(self) -> None:
        stats = self.db.get_stats()
        is_online = self.gemma.is_available()
        payload = {
            "total_records": stats["total_records"],
            "by_source": stats["by_source"],
            "db_size_kb": stats["db_size_kb"],
            "db_path": stats["db_path"],
            "gemma_model": self.gemma.model_name,
            "gemma_status": "Online" if is_online else "Offline",
            "permissions": self.permissions.permissions,
        }
        self._send_json(payload)

    def _handle_api_timeline(self, params: Dict[str, List[str]]) -> None:
        limit = int(params.get("limit", [30])[0])
        source_type = params.get("source", [None])[0] or None

        records = self.db.search(query="", source_type=source_type, limit=limit)
        payload = [
            {
                "id": r.id,
                "source_type": r.source_type,
                "source_identifier": r.source_identifier,
                "timestamp": r.timestamp,
                "datetime_iso": r.datetime_iso,
                "title": r.title,
                "content": r.content,
                "location": r.location,
            }
            for r in records
        ]
        self._send_json(payload)

    def _handle_api_query(self, params: Dict[str, List[str]]) -> None:
        q = params.get("q", [""])[0]
        source = params.get("source", [None])[0] or None
        limit = int(params.get("limit", [5])[0])
        raw_mode = params.get("raw", ["false"])[0].lower() in {"true", "1"}

        result = self.engine.query(
            query_text=q,
            source_type=source,
            limit=limit,
            raw_mode=raw_mode,
        )

        payload = {
            "query": q,
            "answer": result.answer,
            "sources": [
                {
                    "id": s.id,
                    "source_type": s.source_type,
                    "title": s.title,
                    "location": s.location,
                    "datetime_iso": s.datetime_iso,
                }
                for s in result.sources
            ],
            "sources_count": len(result.sources),
            "model_used": result.model_used,
            "latency_seconds": result.latency_seconds,
        }
        self._send_json(payload)

    def _handle_api_permissions(self) -> None:
        self._send_json(self.permissions.permissions)

    def _handle_api_index(self) -> None:
        watcher = SyncWatcher(db=self.db, config=self.config, permissions=self.permissions)
        indexed_count = watcher.run_once()
        self._send_json({"status": "success", "indexed": indexed_count})

    def _handle_api_permissions_toggle(self) -> None:
        content_len = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_len) if content_len > 0 else b"{}"
        try:
            payload = json.loads(body)
            source = payload.get("source", "").lower()
            if source in {"terminal", "browser", "notes"}:
                currently_enabled = self.permissions.is_source_enabled(source)
                if currently_enabled:
                    self.permissions.disable_source(source)
                else:
                    self.permissions.enable_source(source)
                self._send_json({"status": "success", "source": source, "enabled": not currently_enabled})
                return
            self.send_error(400, "Invalid source")
        except Exception as e:
            self.send_error(400, f"Error: {e}")

    def log_message(self, format: str, *args: Any) -> None:
        # Suppress routine GET logging to keep terminal tidy
        return


def create_server(
    host: str = "127.0.0.1",
    port: int = 8080,
    config: Optional[Config] = None,
    db: Optional[Database] = None,
    gemma: Optional[GemmaClient] = None,
    permissions: Optional[PermissionsManager] = None,
    auth_token: Optional[str] = None,
) -> HTTPServer:
    """Creates a configured HTTPServer instance for Dijaview with security controls."""
    cfg = config or Config()
    database = db or Database(db_path=cfg.get("storage.db_path"))
    gemma_client = gemma or GemmaClient(
        model_name=cfg.get("model.name", "gemma2:2b"),
        base_url=cfg.get("model.base_url", "http://localhost:11434"),
    )
    perms = permissions or PermissionsManager(config=cfg)
    engine = SearchEngine(db=database, gemma=gemma_client)
    token = auth_token or secrets.token_hex(16)

    class CustomHandler(DijaviewRequestHandler):
        pass

    CustomHandler.config = cfg
    CustomHandler.db = database
    CustomHandler.gemma = gemma_client
    CustomHandler.permissions = perms
    CustomHandler.engine = engine
    CustomHandler.auth_token = token

    server = HTTPServer((host, port), CustomHandler)
    server.auth_token = token  # type: ignore[attr-defined]
    return server


def start_web_server(
    host: str = "127.0.0.1",
    port: int = 8080,
    config: Optional[Config] = None,
    auth_token: Optional[str] = None,
) -> None:
    """Launches the Dijaview local web dashboard server."""
    server = create_server(host=host, port=port, config=config, auth_token=auth_token)
    token = getattr(server, "auth_token", "")
    print("=" * 60)
    print("  Dijaview Local Web Dashboard")
    print(f"  URL: http://{host}:{port}/?token={token}")
    print("  100% Local • Protected by Session Token")
    print("=" * 60)
    print("Press Ctrl+C to stop the dashboard.\n")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping Dijaview dashboard server...")
    finally:
        server.server_close()
        print("Dashboard server stopped.")
