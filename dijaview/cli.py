import argparse
import sys
from typing import List

from dijaview import __version__
from dijaview.adapters.browser import BrowserAdapter
from dijaview.adapters.notes import NotesAdapter
from dijaview.adapters.terminal import TerminalAdapter
from dijaview.config import Config
from dijaview.engine.gemma import GemmaClient
from dijaview.engine.search import SearchEngine
from dijaview.interactive.chat import start_interactive_chat
from dijaview.storage.database import Database


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

    # Command: purge
    purge_parser = subparsers.add_parser("purge", help="Delete indexed records from the local database")
    purge_parser.add_argument("--all", action="store_true", help="Purge all indexed records")
    purge_parser.add_argument("--source", type=str, choices=["terminal", "browser", "notes"], help="Purge records by source")

    # Command: config
    config_parser = subparsers.add_parser("config", help="View or update configuration")
    config_parser.add_argument("action", choices=["show"], default="show", nargs="?", help="Action to perform")

    parsed = parser.parse_args(args)

    if parsed.command in {None, "chat"}:
        start_interactive_chat()
        return 0

    config = Config()
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
        print(f"\n💡 Answer:\n{result.answer}\n")
        if result.sources:
            print("📂 Sources Cited:")
            for idx, src in enumerate(result.sources, 1):
                print(f"  [{idx}] ({src.source_type.capitalize()}) {src.title}")
                print(f"      Location: {src.location}")
                print(f"      Time:     {src.datetime_iso}")
        return 0

    if parsed.command == "index":
        if parsed.rebuild:
            print("Rebuilding database...")
            db.purge(purge_all=True)

        adapters = []
        if parsed.source in {None, "terminal"}:
            adapters.append(TerminalAdapter())
        if parsed.source in {None, "browser"}:
            adapters.append(BrowserAdapter())
        if parsed.source in {None, "notes"}:
            notes_dirs = config.get("adapters.notes.directories", [])
            adapters.append(NotesAdapter(directories=notes_dirs))

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
        import json
        print(json.dumps(config.data, indent=2))
        return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
