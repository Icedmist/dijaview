import sys
from typing import Optional
from dijaview.engine.search import SearchEngine
from dijaview.storage.database import Database
from dijaview.engine.gemma import GemmaClient


def start_interactive_chat(db: Optional[Database] = None, gemma: Optional[GemmaClient] = None):
    """Launches an interactive terminal chat REPL to query computer activity."""
    db = db or Database()
    gemma = gemma or GemmaClient()
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

        if prompt == "/help":
            print("\nAvailable shell commands:")
            print("  /status  - Display local database stats")
            print("  /help    - Show this help message")
            print("  /exit    - Exit the interactive chat\n")
            print("Example questions you can ask:")
            print("  - Where did I save that API key doc last Tuesday?")
            print("  - What was that curl command I used yesterday?")
            print("  - Which article did I read about postgres indexes?\n")
            continue

        if prompt == "/status":
            current_stats = db.get_stats()
            print(f"\nIndexed Records: {current_stats['total_records']}")
            for src, count in current_stats["by_source"].items():
                print(f"  - {src}: {count}")
            print(f"Database: {current_stats['db_path']} ({current_stats['db_size_kb']} KB)\n")
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
