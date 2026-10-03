import argparse
import json
import platform
import sys
import urllib.request
from pathlib import Path
from typing import List, Optional

from dijaview import __version__
from dijaview.adapters.browser import BrowserAdapter
from dijaview.adapters.notes import NotesAdapter
from dijaview.adapters.terminal import TerminalAdapter
from dijaview.config import Config
from dijaview.core.permissions import PermissionsManager
from dijaview.engine.gemma import GemmaClient
from dijaview.engine.search import SearchEngine
from dijaview.interactive.chat import start_interactive_chat
from dijaview.storage.database import Database


def check_for_updates(timeout_seconds: float = 3.0) -> Optional[str]:
    """Queries GitHub API for the latest release tag."""
    url = "https://api.github.com/repos/Icedmist/dijaview/releases/latest"
    try:
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": f"dijaview/{__version__}",
                "Accept": "application/vnd.github.v3+json",
            },
        )
        with urllib.request.urlopen(req, timeout=timeout_seconds) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            tag = data.get("tag_name", "").lstrip("v")
            return tag if tag else None
    except Exception:
        return None


def print_permissions_summary(permissions: PermissionsManager) -> None:
    """Prints a clear and formatted view of current permissions."""
    print("=" * 60)
    print("  Dijaview Permissions Matrix")
    print("=" * 60)

    print("\nData Sources:")
    for src in ["terminal", "browser", "notes"]:
        enabled = permissions.is_source_enabled(src)
        status_tag = "[ENABLED]" if enabled else "[DISABLED]"
        print(f"  {status_tag} {src.capitalize()}")

    print("\nAllowed Note Directories:")
    allowed = permissions.get_allowed_paths()
    if allowed:
        for p in allowed:
            print(f"  + {p}")
    else:
        print("  (None configured. All non-blocked directories permitted.)")

    print("\nBlocked Paths and Patterns:")
    blocked = permissions.get_blocked_paths()
    if blocked:
        for b in blocked:
            print(f"  - {b}")
    else:
        print("  (None configured.)")

    max_size = permissions.get_max_file_size()
    max_mb = max_size / (1024 * 1024)
    print(f"\nFile Size Limit:")
    print(f"  Max file size: {max_size} bytes ({max_mb:.1f} MB)")

    print("\nCustom Redaction Filters:")
    redactions = permissions.get_custom_redactions()
    if redactions:
        for r in redactions:
            print(f"  * {r['name']}: {r['pattern']} -> {r.get('replacement', '[REDACTED]')}")
    else:
        print("  (None configured. Add one with 'dijaview permissions add-filter <name> <regex>')")
    print()


def main(args: List[str] = None) -> int:
    if args is None:
        args = sys.argv[1:]

    # If called with no arguments, launch the interactive terminal chat REPL directly
    if not args:
        start_interactive_chat()
        return 0

    parser = argparse.ArgumentParser(
        prog="dijaview",
        description="A privacy-first local search engine for your computer activity powered by Gemma 2.",
    )
    parser.add_argument("--version", action="version", version=f"dijaview {__version__}")

    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # Command: chat
    subparsers.add_parser("chat", help="Start the interactive terminal chat shell")

    # Command: query
    query_parser = subparsers.add_parser("query", help="Ask a question about your computer activity")
    query_parser.add_argument("question", type=str, help="The question to ask")
    query_parser.add_argument("--source", type=str, choices=["terminal", "browser", "notes"], help="Limit search to a source")
    query_parser.add_argument("--raw", action="store_true", help="Print matched records without invoking Gemma 2")
    query_parser.add_argument("--limit", type=int, default=5, help="Maximum records to retrieve")

    # Command: index
    index_parser = subparsers.add_parser("index", help="Scan and index local activity sources")
    index_parser.add_argument("--source", type=str, choices=["terminal", "browser", "notes"], help="Index a specific source")
    index_parser.add_argument("--rebuild", action="store_true", help="Wipe database and rebuild from scratch")

    # Command: status
    subparsers.add_parser("status", help="Show system status and index statistics")

    # Command: version
    version_parser = subparsers.add_parser("version", help="Show Dijaview version and check for GitHub release updates")
    version_parser.add_argument("--check-update", action="store_true", help="Check GitHub for the latest release")

    # Command: purge
    purge_parser = subparsers.add_parser("purge", help="Delete indexed records from the local database")
    purge_parser.add_argument("--all", action="store_true", help="Purge all indexed records")
    purge_parser.add_argument("--source", type=str, choices=["terminal", "browser", "notes"], help="Purge records by source")

    # Command: config
    config_parser = subparsers.add_parser("config", help="View or update configuration")
    config_parser.add_argument("action", choices=["show"], default="show", nargs="?", help="Action to perform")

    # Command: permissions
    perm_parser = subparsers.add_parser("permissions", help="Manage data source access, path permissions, and redaction rules")
    perm_sub = perm_parser.add_subparsers(dest="perm_action", help="Permissions actions")

    perm_sub.add_parser("show", help="Display current permissions matrix")

    enable_parser = perm_sub.add_parser("enable", help="Enable access to a data source")
    enable_parser.add_argument("source", choices=["terminal", "browser", "notes"], help="Source to enable")

    disable_parser = perm_sub.add_parser("disable", help="Disable access to a data source")
    disable_parser.add_argument("source", choices=["terminal", "browser", "notes"], help="Source to disable")

    allow_parser = perm_sub.add_parser("allow-path", help="Add a directory to permitted scanning paths")
    allow_parser.add_argument("path", type=str, help="Directory path to allow")

    block_parser = perm_sub.add_parser("block-path", help="Add a directory or pattern to blocked paths")
    block_parser.add_argument("path", type=str, help="Directory or glob pattern to block")

    remove_parser = perm_sub.add_parser("remove-path", help="Remove a directory or pattern from permissions")
    remove_parser.add_argument("path", type=str, help="Path to remove")

    filter_parser = perm_sub.add_parser("add-filter", help="Add a custom secret redaction regular expression")
    filter_parser.add_argument("name", type=str, help="Name of the redaction filter")
    filter_parser.add_argument("pattern", type=str, help="Regular expression pattern to match")
    filter_parser.add_argument("--replacement", type=str, default="[REDACTED]", help="Replacement text")

    rm_filter_parser = perm_sub.add_parser("remove-filter", help="Remove a custom redaction filter")
    rm_filter_parser.add_argument("name", type=str, help="Filter name to remove")

    perm_sub.add_parser("reset", help="Reset permissions back to secure defaults")

    # Command: serve
    serve_parser = subparsers.add_parser("serve", help="Start the local web dashboard")
    serve_parser.add_argument("--port", type=int, default=8080, help="Port to listen on (default: 8080)")
    serve_parser.add_argument("--host", type=str, default="127.0.0.1", help="Host interface (default: 127.0.0.1)")

    # Command: watch
    watch_parser = subparsers.add_parser("watch", help="Continuously monitor and automatically index activity")
    watch_parser.add_argument("--interval", type=int, default=30, help="Scan interval in seconds (default: 30)")
    watch_parser.add_argument("--once", action="store_true", help="Run a single incremental sync sweep and exit")

    parsed = parser.parse_args(args)

    if parsed.command in {None, "chat"}:
        start_interactive_chat()
        return 0

    config = Config()
    permissions = PermissionsManager(config=config)
    db_path = config.get("storage.db_path")
    db = Database(db_path=db_path)
    gemma = GemmaClient(
        model_name=config.get("model.name", "gemma2:2b"),
        base_url=config.get("model.base_url", "http://localhost:11434"),
    )

    if parsed.command == "query":
        engine = SearchEngine(db=db, gemma=gemma)
        result = engine.query(
            query_text=parsed.question,
            source_type=parsed.source,
            limit=parsed.limit,
            raw_mode=parsed.raw,
        )
        print(f"\nAnswer:\n{result.answer}\n")
        if result.sources:
            print("Sources Cited:")
            for idx, src in enumerate(result.sources, 1):
                print(f"  [{idx}] ({src.source_type.capitalize()}) {src.title}")
                print(f"      Location: {src.location}")
                print(f"      Time:     {src.datetime_iso}")
        return 0

    if parsed.command == "index":
        if parsed.rebuild:
            print("Rebuilding database...")
            db.purge(purge_all=True)

        if parsed.source:
            if not permissions.is_source_enabled(parsed.source):
                print(f"Error: Source '{parsed.source}' is currently disabled in permissions.")
                print(f"Run 'dijaview permissions enable {parsed.source}' to grant access.")
                return 1

        adapters = []
        if parsed.source in {None, "terminal"} and permissions.is_source_enabled("terminal"):
            adapters.append(TerminalAdapter(permissions=permissions))
        if parsed.source in {None, "browser"} and permissions.is_source_enabled("browser"):
            adapters.append(BrowserAdapter(permissions=permissions))
        if parsed.source in {None, "notes"} and permissions.is_source_enabled("notes"):
            notes_dirs = config.get("adapters.notes.directories", [])
            adapters.append(NotesAdapter(directories=notes_dirs, permissions=permissions))

        if not adapters:
            print("No enabled sources available to index.")
            print("Run 'dijaview permissions show' to inspect active permissions.")
            return 0

        total_inserted = 0
        for adapter in adapters:
            print(f"Scanning source: {adapter.source_type()}...")
            records = adapter.scan_records()
            count = db.insert_records(records)
            print(f"  -> Indexed {count} new entries from {adapter.source_type()}.")
            total_inserted += count

        print(f"\nIndex complete! Total newly indexed records: {total_inserted}")
        return 0

    if parsed.command == "status":
        stats = db.get_stats()
        is_online = gemma.is_available()
        print("Dijaview Status:")
        print(f"  Database Path:   {stats['db_path']}")
        print(f"  Database Size:   {stats['db_size_kb']} KB")
        print(f"  Total Records:   {stats['total_records']}")
        for src, count in stats["by_source"].items():
            print(f"    - {src}: {count}")
        print(f"  Gemma 2 Model:   {gemma.model_name}")
        print(f"  Ollama Status:   {'Online' if is_online else 'Offline (Start with ollama serve)'}")
        print("  Permissions:")
        for src in ["terminal", "browser", "notes"]:
            status_str = "Enabled" if permissions.is_source_enabled(src) else "Disabled"
            print(f"    - {src.capitalize()}: {status_str}")
        custom_filters = permissions.get_custom_redactions()
        print(f"    - Custom Redaction Filters: {len(custom_filters)} active")
        return 0

    if parsed.command == "version":
        print(f"Dijaview v{__version__}")
        print(f"Python:        {platform.python_version()} ({platform.system()} {platform.machine()})")
        print(f"Gemma 2 Model: {gemma.model_name} ({'Online' if gemma.is_available() else 'Offline'})")
        print("Repository:    https://github.com/Icedmist/dijaview")
        print("Releases:      https://github.com/Icedmist/dijaview/releases")

        if parsed.check_update:
            print("\nChecking for updates...")
            latest = check_for_updates()
            if latest:
                if latest != __version__:
                    print(f"Update available: v{latest} (current: v{__version__})")
                    print(f"Download release at: https://github.com/Icedmist/dijaview/releases/tag/v{latest}")
                else:
                    print(f"You are running the latest version (v{__version__}).")
            else:
                print("Could not retrieve latest release information from GitHub.")
        return 0

    if parsed.command == "purge":
        if parsed.all:
            count = db.purge(purge_all=True)
            print(f"Purged all {count} records from database.")
        elif parsed.source:
            count = db.purge(source_type=parsed.source)
            print(f"Purged {count} records from source: {parsed.source}.")
        else:
            print("Please specify --all or --source to purge records.")
        return 0

    if parsed.command == "config":
        print(json.dumps(config.data, indent=2))
        return 0

    if parsed.command == "permissions":
        action = parsed.perm_action or "show"

        if action == "show":
            print_permissions_summary(permissions)
            return 0

        if action == "enable":
            permissions.enable_source(parsed.source)
            print(f"Granted permission for source: {parsed.source}")
            return 0

        if action == "disable":
            permissions.disable_source(parsed.source)
            print(f"Revoked permission for source: {parsed.source}")
            return 0

        if action == "allow-path":
            added = permissions.allow_path(parsed.path)
            if added:
                print(f"Added allowed path: {parsed.path}")
            else:
                print(f"Path already in allowed list: {parsed.path}")
            return 0

        if action == "block-path":
            added = permissions.block_path(parsed.path)
            if added:
                print(f"Added blocked path: {parsed.path}")
            else:
                print(f"Path already in blocked list: {parsed.path}")
            return 0

        if action == "remove-path":
            removed = permissions.remove_path(parsed.path)
            if removed:
                print(f"Removed path from permissions: {parsed.path}")
            else:
                print(f"Path not found in permissions: {parsed.path}")
            return 0

        if action == "add-filter":
            try:
                permissions.add_custom_redaction(
                    name=parsed.name,
                    pattern=parsed.pattern,
                    replacement=parsed.replacement,
                )
                print(f"Added custom redaction filter '{parsed.name}' matching pattern: {parsed.pattern}")
            except Exception as e:
                print(f"Error registering filter '{parsed.name}': {e}")
                return 1
            return 0

        if action == "remove-filter":
            removed = permissions.remove_custom_redaction(parsed.name)
            if removed:
                print(f"Removed custom redaction filter: {parsed.name}")
            else:
                print(f"Filter not found: {parsed.name}")
            return 0

        if action == "reset":
            permissions.reset_defaults()
            print("Permissions successfully reset to secure defaults.")
            return 0

    if parsed.command == "serve":
        from dijaview.web.server import start_web_server
        start_web_server(host=parsed.host, port=parsed.port, config=config)
        return 0

    if parsed.command == "watch":
        from dijaview.watcher.daemon import SyncWatcher
        watcher = SyncWatcher(db=db, config=config, permissions=permissions, interval_seconds=parsed.interval)
        if parsed.once:
            count = watcher.run_once()
            print(f"Sync sweep complete: +{count} new activity entries indexed.")
            return 0
        watcher.run_loop()
        return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
