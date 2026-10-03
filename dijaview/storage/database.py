import json
import sqlite3
import os
from contextlib import contextmanager
from pathlib import Path
from typing import Dict, List, Optional, Any

from dijaview.core.models import ActivityRecord, TimeRange

STOPWORDS = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and", "any", "are",
    "as", "at", "be", "because", "been", "before", "being", "below", "between", "both", "but",
    "by", "can", "could", "did", "do", "does", "doing", "down", "during", "each", "few", "for",
    "from", "further", "had", "has", "have", "having", "he", "her", "here", "hers", "herself",
    "him", "himself", "his", "how", "i", "if", "in", "into", "is", "it", "its", "itself",
    "me", "more", "most", "my", "myself", "no", "nor", "not", "of", "off", "on", "once",
    "only", "or", "other", "ought", "our", "ours", "ourselves", "out", "over", "own", "same",
    "she", "should", "so", "some", "such", "than", "that", "the", "their", "theirs", "them",
    "themselves", "then", "there", "these", "they", "this", "those", "through", "to", "too",
    "under", "until", "up", "very", "was", "we", "were", "what", "when", "where", "which",
    "while", "who", "whom", "why", "with", "would", "you", "your", "yours", "yourself", "yourselves",
    "look", "looked", "looking", "find", "see", "show", "tell", "give", "search", "searched",
    "check", "checked", "get", "got", "read", "use", "used", "using", "work", "worked", "working",
    "open", "opened", "ran", "run", "running"
}

TEMPORAL_WORDS = {
    "yesterday", "today", "tomorrow", "last", "past", "ago", "tuesday", "monday",
    "wednesday", "thursday", "friday", "saturday", "sunday", "morning", "afternoon",
    "evening", "night", "week", "month", "year", "days", "hours", "minutes", "seconds"
}


class Database:
    """Embedded SQLite database managing full-text search and temporal metadata."""

    def __init__(self, db_path: Optional[str] = None):
        if db_path:
            self.db_path = Path(db_path).expanduser()
        else:
            default_dir = Path.home() / ".local" / "share" / "dijaview"
            default_dir.mkdir(parents=True, exist_ok=True)
            self.db_path = default_dir / "dijaview.db"

        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    @contextmanager
    def _get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def _init_schema(self) -> None:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            # Records metadata table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS activity_records (
                    id TEXT PRIMARY KEY,
                    source_type TEXT NOT NULL,
                    source_identifier TEXT NOT NULL,
                    timestamp REAL NOT NULL,
                    datetime_iso TEXT NOT NULL,
                    title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    location TEXT NOT NULL,
                    metadata_json TEXT
                )
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_activity_timestamp 
                ON activity_records(timestamp);
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_activity_source 
                ON activity_records(source_type);
            """)

            # FTS5 Full-Text Search virtual table
            cursor.execute("""
                CREATE VIRTUAL TABLE IF NOT EXISTS activity_fts USING fts5(
                    id UNINDEXED,
                    title,
                    content,
                    location,
                    tokenize = 'porter unicode61'
                )
            """)
            conn.commit()
        try:
            if self.db_path.exists():
                os.chmod(self.db_path, 0o600)
        except Exception:
            pass

    def insert_records(self, records: List[ActivityRecord]) -> int:
        if not records:
            return 0

        inserted_count = 0
        with self._get_connection() as conn:
            cursor = conn.cursor()
            for r in records:
                # Check if record already exists to prevent duplicate re-indexing
                cursor.execute("SELECT id FROM activity_records WHERE id = ?", (r.id,))
                if cursor.fetchone():
                    continue

                cursor.execute("""
                    INSERT INTO activity_records (
                        id, source_type, source_identifier, timestamp, 
                        datetime_iso, title, content, location, metadata_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    r.id,
                    r.source_type,
                    r.source_identifier,
                    r.timestamp,
                    r.datetime_iso,
                    r.title,
                    r.content,
                    r.location,
                    json.dumps(r.metadata),
                ))

                cursor.execute("""
                    INSERT INTO activity_fts (id, title, content, location)
                    VALUES (?, ?, ?, ?)
                """, (r.id, r.title, r.content, r.location))
                inserted_count += 1

            conn.commit()
        return inserted_count

    def search(
        self,
        query: str,
        time_range: Optional[TimeRange] = None,
        source_type: Optional[str] = None,
        limit: int = 10,
    ) -> List[ActivityRecord]:
        """Performs full-text search with temporal filtering and BM25 relevance ranking."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Sanitize FTS query string and extract words
            clean_query = "".join(c if c.isalnum() or c.isspace() else " " for c in query).strip()
            raw_terms = clean_query.split()

            # Strip English stopwords and temporal words handled by time_range
            meaningful_terms = [
                term for term in raw_terms
                if term.lower() not in STOPWORDS and term.lower() not in TEMPORAL_WORDS and len(term) > 1
            ]

            if not meaningful_terms:
                meaningful_terms = [t for t in raw_terms if t.lower() not in STOPWORDS and len(t) > 1]
            if not meaningful_terms and raw_terms:
                meaningful_terms = [t for t in raw_terms if len(t) > 1]

            where_clauses: List[str] = []
            params: List[Any] = []

            if not meaningful_terms:
                # Return most recent if empty query or non-searchable text
                from_clause = "activity_records r"
                where_clauses.append("1=1")
                order_by = "r.timestamp DESC"
            else:
                fts_query_str = " OR ".join(f'"{term}"*' for term in meaningful_terms)
                from_clause = "activity_records r JOIN activity_fts ON r.id = activity_fts.id"
                where_clauses.append("activity_fts MATCH ?")
                params.append(fts_query_str)
                order_by = "bm25(activity_fts) ASC, r.timestamp DESC"

            if time_range:
                if time_range.start_timestamp is not None:
                    where_clauses.append("r.timestamp >= ?")
                    params.append(time_range.start_timestamp)
                if time_range.end_timestamp is not None:
                    where_clauses.append("r.timestamp <= ?")
                    params.append(time_range.end_timestamp)

            if source_type:
                where_clauses.append("r.source_type = ?")
                params.append(source_type)

            params.append(limit)
            sql = f"""
                SELECT r.* FROM {from_clause}
                WHERE {" AND ".join(where_clauses)}
                ORDER BY {order_by}
                LIMIT ?
            """

            cursor.execute(sql, params)
            rows = cursor.fetchall()

            return [
                ActivityRecord(
                    id=row["id"],
                    source_type=row["source_type"],
                    source_identifier=row["source_identifier"],
                    timestamp=row["timestamp"],
                    datetime_iso=row["datetime_iso"],
                    title=row["title"],
                    content=row["content"],
                    location=row["location"],
                    metadata=json.loads(row["metadata_json"]) if row["metadata_json"] else {},
                )
                for row in rows
            ]

    def get_stats(self) -> Dict[str, Any]:
        """Returns statistics on total records and storage size."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM activity_records")
            total = cursor.fetchone()[0]

            cursor.execute("""
                SELECT source_type, COUNT(*) 
                FROM activity_records 
                GROUP BY source_type
            """)
            by_source = {row[0]: row[1] for row in cursor.fetchall()}

            db_size_bytes = self.db_path.stat().st_size if self.db_path.exists() else 0

            return {
                "total_records": total,
                "by_source": by_source,
                "db_path": str(self.db_path),
                "db_size_kb": round(db_size_bytes / 1024, 2),
            }

    def purge(
        self,
        since_epoch: Optional[float] = None,
        source_type: Optional[str] = None,
        purge_all: bool = False,
    ) -> int:
        """Deletes records matching criteria."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if purge_all:
                cursor.execute("SELECT COUNT(*) FROM activity_records")
                count = cursor.fetchone()[0]
                cursor.execute("DELETE FROM activity_records")
                cursor.execute("DELETE FROM activity_fts")
                conn.commit()
                return count

            clauses = []
            params = []
            if since_epoch is not None:
                clauses.append("timestamp >= ?")
                params.append(since_epoch)
            if source_type:
                clauses.append("source_type = ?")
                params.append(source_type)

            if not clauses:
                return 0

            where_sql = " AND ".join(clauses)
            cursor.execute(f"SELECT id FROM activity_records WHERE {where_sql}", params)
            ids_to_delete = [r[0] for r in cursor.fetchall()]

            for rec_id in ids_to_delete:
                cursor.execute("DELETE FROM activity_records WHERE id = ?", (rec_id,))
                cursor.execute("DELETE FROM activity_fts WHERE id = ?", (rec_id,))

            conn.commit()
            return len(ids_to_delete)
