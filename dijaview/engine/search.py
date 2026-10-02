import time
from typing import Optional, List
from dijaview.core.models import ActivityRecord, QueryResult
from dijaview.core.temporal import parse_temporal_expression
from dijaview.engine.gemma import GemmaClient
from dijaview.storage.database import Database


class SearchEngine:
    """Orchestrates temporal query parsing, database search, and Gemma 2 RAG synthesis."""

    def __init__(self, db: Database, gemma: Optional[GemmaClient] = None):
        self.db = db
        self.gemma = gemma or GemmaClient()

    def query(
        self,
        query_text: str,
        source_type: Optional[str] = None,
        limit: int = 5,
        raw_mode: bool = False,
    ) -> QueryResult:
        start_time = time.time()
        time_range = parse_temporal_expression(query_text)

        # 1. Retrieve matching activity records from database
        records = self.db.search(
            query=query_text,
            time_range=time_range,
            source_type=source_type,
            limit=limit,
        )

        latency = time.time() - start_time

        if not records:
            return QueryResult(
                query=query_text,
                answer="No relevant activity found matching your query.",
                sources=[],
                time_range=time_range,
                model_used=self.gemma.model_name,
                latency_seconds=round(latency, 3),
            )

        # In raw mode, return records without calling LLM
        if raw_mode:
            summary = f"Found {len(records)} relevant records:\n" + "\n".join(
                f"- [{r.source_type.upper()}] {r.title} ({r.datetime_iso}): {r.location}"
                for r in records[:5]
            )
            return QueryResult(
                query=query_text,
                answer=summary,
                sources=records,
                time_range=time_range,
                model_used="none (raw search)",
                latency_seconds=round(latency, 3),
            )

        # 2. Check if local Gemma is available
        if not self.gemma.is_available():
            # Graceful local fallback formatting
            fallback_answer = (
                "Local Gemma 2 is offline (run 'ollama serve' to enable AI synthesis).\n\n"
                f"Directly matched records ({len(records)} found):\n"
            )
            for idx, r in enumerate(records, 1):
                fallback_answer += f"{idx}. [{r.source_type.capitalize()}] {r.title} ({r.datetime_iso})\n   Path/URL: {r.location}\n"

            return QueryResult(
                query=query_text,
                answer=fallback_answer.strip(),
                sources=records,
                time_range=time_range,
                model_used="offline_fallback",
                latency_seconds=round(time.time() - start_time, 3),
            )

        # 3. Construct Gemma 2 citation prompt
        prompt = self._build_prompt(query_text, records, time_range)
        system_prompt = (
            "You are Dijaview, a privacy-first computer activity assistant. "
            "Answer the user's question using ONLY the provided local activity logs below. "
            "Always cite the exact timestamp, source file, or URL where the answer was found. "
            "Be concise, plain, and direct. Do not make up information."
        )

        llm_result = self.gemma.generate(prompt=prompt, system_prompt=system_prompt)
        answer = llm_result.get("response", "Could not synthesize response.")
        total_latency = time.time() - start_time

        return QueryResult(
            query=query_text,
            answer=answer,
            sources=records,
            time_range=time_range,
            model_used=self.gemma.model_name,
            latency_seconds=round(total_latency, 3),
        )

    def _build_prompt(self, query: str, records: List[ActivityRecord], time_range) -> str:
        prompt_lines = [
            f"User Question: {query}",
            "",
            "Activity Logs:",
        ]

        if time_range and time_range.description:
            prompt_lines.append(f"Note: User specified time range is {time_range.description}.")

        for idx, r in enumerate(records, 1):
            prompt_lines.append(f"\n--- Record [{idx}] ---")
            prompt_lines.append(f"Source: {r.source_type} ({r.source_identifier})")
            prompt_lines.append(f"Timestamp: {r.datetime_iso}")
            prompt_lines.append(f"Location: {r.location}")
            prompt_lines.append(f"Title: {r.title}")
            prompt_lines.append(f"Snippet:\n{r.content[:500]}")

        prompt_lines.append("\nAnswer the user question concisely citing the record numbers and locations.")
        return "\n".join(prompt_lines)
