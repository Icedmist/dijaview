import sys
from typing import Optional
from dijaview import __version__
from dijaview.config import Config
from dijaview.core.permissions import PermissionsManager
from dijaview.engine.gemma import GemmaClient
from dijaview.engine.search import SearchEngine
from dijaview.storage.database import Database


def start_interactive_chat(
    db: Optional[Database] = None,
    gemma: Optional[GemmaClient] = None,
    config: Optional[Config] = None,
):
    """Launches an interactive terminal chat REPL to query computer activity."""
    config = config or Config()
    db = db or Database(db_path=config.get("storage.db_path"))
    gemma = gemma or GemmaClient(
        model_name=config.get("model.name", "gemma2:2b"),
        base_url=config.get("model.base_url", "http://localhost:11434"),
    )
    permissions = PermissionsManager(config=config)
    engine = SearchEngine(db=db, gemma=gemma)

    stats = db.get_stats()
    gemma_status = "Online" if gemma.is_available() else "Offline (Run 'ollama serve')"

    print("=" * 60)
    print("  Dijaview (Interactive Local Shell)")
    print(f"  Model: {gemma.model_name} [{gemma_status}]")
    print(f"  Indexed Records: {stats['total_records']} • 100% Local")
    print("=" * 60)
    print("Type your question in plain English, '/help' for tips, or '/exit' to quit.\n")

    while True:
        try:
            prompt = input("dijaview >>> ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nGoodbye!")
            break

        if not prompt:
            continue

        if prompt in {"/exit", "/quit", "exit", "quit"}:
            print("Goodbye!")
            break

        if prompt == "/version":
            print(f"\nDijaview v{__version__}\n")
            continue

        if prompt == "/clear":
            print("\033c", end="")
            continue

        if prompt == "/help":
            print("\nAvailable shell commands:")
            print("  /status       Display local database stats and model status")
            print("  /permissions  Inspect active sources and path permissions")
            print("  /version      Show current Dijaview version")
            print("  /clear        Clear terminal screen")
            print("  /help         Show this help message")
            print("  /exit         Exit the interactive chat\n")
            print("Example questions you can ask:")
            print("  Where did I save that API key doc last Tuesday?")
            print("  What was that curl command I used yesterday?")
            print("  Which article did I read about postgres indexes?\n")
            continue

        if prompt == "/status":
            current_stats = db.get_stats()
            print(f"\nIndexed Records: {current_stats['total_records']}")
            for src, count in current_stats["by_source"].items():
                print(f"  - {src}: {count}")
            print(f"Database: {current_stats['db_path']} ({current_stats['db_size_kb']} KB)\n")
            continue

        if prompt == "/permissions":
            print("\nDijaview Permissions Summary:")
            for src in ["terminal", "browser", "notes"]:
                state = "Enabled" if permissions.is_source_enabled(src) else "Disabled"
                print(f"  - {src.capitalize()}: {state}")
            print(f"  Allowed Directories: {len(permissions.get_allowed_paths())}")
            print(f"  Blocked Paths:       {len(permissions.get_blocked_paths())}")
            print(f"  Custom Filters:      {len(permissions.get_custom_redactions())}")
            print("Tip: Use 'dijaview permissions --help' in your terminal to modify permissions.\n")
            continue

        if prompt.startswith("/"):
            print(f"\nUnknown command: '{prompt}'. Type '/help' for available commands.\n")
            continue

        print("\nSearching activity logs...")
        result = engine.query(prompt)

        print(f"\nAnswer:\n{result.answer}\n")

        if result.sources:
            print("Sources Cited:")
            for idx, src in enumerate(result.sources, 1):
                print(f"  [{idx}] ({src.source_type.capitalize()}) {src.title}")
                print(f"      Location: {src.location}")
                print(f"      Time:     {src.datetime_iso}")
        print()
