# Dijaview Architecture Specification

This document details the internal design, component relationships, data flow, and privacy boundaries of **Dijaview**.

---

## 1. System Philosophy

Dijaview operates under four non-negotiable architectural invariants:

1. **Local-First Boundary:** All raw computer activity data, embeddings, and generative inference execute strictly within `localhost`. No network sockets connect to external cloud AI providers for search or inference.
2. **Zero-Trust Ingestion:** All raw text scraped from shell histories, browser tables, or markdown files passes through an automated regex and entropy redaction filter before reaching the vector store.
3. **Temporal Awareness:** Human memory is grounded in time (*"what did I do yesterday morning?"*). Time metadata is preserved as a first-class dimension alongside semantic vector similarity.
4. **Lightweight Footprint:** The background indexer and query engine must operate comfortably on consumer hardware without consuming excessive RAM or battery.

---

## 2. End-to-End Component Diagram

```mermaid
flowchart TD
    subgraph Data Sources [Local Machine Data Sources]
        A1[Shell History: bash / zsh / fish]
        A2[Browser History: Chrome / Brave / Firefox SQLite]
        A3[User Notes: Markdown / Text / Code]
        A4[File Touches: Recent modified files]
    end

    subgraph Ingestion Layer [Ingestion & Normalization]
        B1[Source Adapters]
        B2[Secrets & Credential Redactor]
        B3[Chunker & Timestamp Normalizer]
    end

    subgraph Storage Layer [Embedded Storage]
        C1[(Local Vector Store: SQLite-vec / Chroma)]
        C2[(Temporal Metadata DB: SQLite)]
    end

    subgraph RAG & Reasoning [Local Intelligence Engine]
        D1[Query Analyzer & Temporal Extractor]
        D2[Hybrid Searcher: Vector + BM25 Keyword]
        D3[Gemma 2 2B/9B Inference via Ollama]
    end

    subgraph User Interface [Interaction Layer]
        E1[CLI Utility: dijaview query]
        E2[Local Web UI / Spotlight]
    end

    Data Sources --> B1
    B1 --> B2
    B2 --> B3
    B3 --> C1
    B3 --> C2

    E1 --> D1
    E2 --> D1
    D1 --> D2
    C1 --> D2
    C2 --> D2
    D2 --> D3
    D3 --> E1
    D3 --> E2
```

---

## 3. Data Ingestion Pipeline

### 3.1 Adapter Framework
Every data source implements the unified `BaseAdapter` interface:

```python
class BaseAdapter(ABC):
    @abstractmethod
    def scan_new_entries(self, since_timestamp: float) -> list[RawEntry]:
        """Scans and yields newly generated activity entries since last checkpoint."""
        pass

    @abstractmethod
    def source_type(self) -> str:
        """Returns unique identifier e.g., 'terminal', 'browser', 'notes'."""
        pass
```

### 3.2 Secret Scrubbing Engine
Before storage, every snippet is filtered through pattern matching to protect sensitive data:
* **Private Keys & Certificates:** `-----BEGIN PRIVATE KEY-----`, RSA, SSH keys.
* **API Keys & Tokens:** GitHub Personal Access Tokens (`ghp_`), OpenAI (`sk-`), AWS Access Keys (`AKIA...`), generic bearer tokens.
* **Passwords & Connection Strings:** URI credentials (`postgres://user:pass@...`), basic auth headers.
* **Excluded File Patterns:** Files named `.env*`, `id_rsa*`, `*credential*`, `*secret*` are strictly ignored during file scanning.

### 3.3 Permissions and Access Control Engine
Ingestion is strictly governed by the `PermissionsManager` subsystem before any disk reads occur:
* **Source Level Gates:** Each adapter (`terminal`, `browser`, `notes`) must be explicitly enabled. Revoking a source prevents scanning entirely.
* **Filesystem Whitelists & Blacklists:** Notes and document ingestion validates paths against allowed directories and blocked glob patterns before opening any file.
* **Memory & Resource Safeguards:** Enforces maximum file size limits (default 1 MB) to prevent runaway memory usage on large binary dumps or search archives.
* **User-Defined Redaction Rules:** Users can register custom regular expression filters to mask proprietary tokens, customer IDs, or personal identification data during ingestion.

---

## 4. Storage & Retrieval Strategy

### 4.1 Schema Definition
Each indexed record possesses both vector representation and structured metadata:

```json
{
  "id": "entry_9f82d1c",
  "source": "terminal",
  "subsource": "/home/snow/.bash_history",
  "timestamp": 1790924400,
  "datetime_iso": "2026-10-02T08:00:00Z",
  "content": "curl -X POST https://api.example.com/v1/auth -H 'Content-Type: application/json'",
  "sanitized_content": "curl -X POST https://api.example.com/v1/auth -H 'Content-Type: application/json'",
  "context_url": null,
  "file_path": "/home/snow/.bash_history",
  "embedding": [0.0142, -0.0521, 0.0891, "..."]
}
```

### 4.2 Temporal Extraction & Hybrid Search
When a user asks:
> *"Where did I read that tutorial about PostgreSQL indexing last Tuesday?"*

The Query Analyzer executes two parallel tasks:
1. **Temporal Expression Normalization:**
   * Recognizes `"last Tuesday"` $\rightarrow$ Computes target range `[2026-09-29T00:00:00, 2026-09-29T23:59:59]`.
   * Expands range buffer by $\pm 24$ hours to account for subjective memory drift.
2. **Semantic Similarity Scoring:**
   * Embeds `"PostgreSQL indexing tutorial"` using a lightweight local model (`nomic-embed-text` or `all-MiniLM-L6-v2`).
   * Scores records based on a weighted combination of semantic proximity and temporal relevance:
   $$\text{FinalScore} = \alpha \cdot \text{VectorSimilarity} + (1 - \alpha) \cdot \text{TemporalDecayPenalty}$$

---

## 5. Gemma 2 Reasoning & Synthesis Pipeline

Retrieved snippets are injected into Gemma 2's context with a strict citation protocol:

```text
You are Dijaview, an intelligent, privacy-first local activity assistant.
Answer the user's question using ONLY the provided computer activity logs below.
Always cite the exact timestamp, source file, or URL where the answer was found.
If the answer is not in the logs, state clearly that no matching activity was found.

--- RECENT ACTIVITY LOGS ---
[1] 2026-09-29 14:22:10 UTC | Browser: Brave | URL: https://use-the-index-luke.com/sql/indexing
Title: SQL Indexing and Tuning Tutorial
Snippet: B-Tree indexes store sorted keys and leaf nodes containing row pointers...

[2] 2026-09-29 14:35:04 UTC | Terminal: zsh | Path: ~/projects/db-optimization
Command: git checkout -b feat/add-composite-index

--- USER QUERY ---
Where did I read that tutorial about PostgreSQL indexing last Tuesday?
```

### Gemma 2 Output:
> *"You read the tutorial titled **'SQL Indexing and Tuning Tutorial'** on Tuesday, September 29, at 2:22 PM in your Brave browser at [https://use-the-index-luke.com/sql/indexing](https://use-the-index-luke.com/sql/indexing). Shortly after at 2:35 PM, you switched to your terminal in `~/projects/db-optimization` and created the branch `feat/add-composite-index`."*

---

## 6. Security & Sandboxing Boundaries

* **Read-Only SQLite Connectors:** All browser database connections open with URI parameters `?mode=ro&immutable=1` to guarantee that browser databases cannot be locked or corrupted while the browser is running.
* **Ephemeral Memory Option:** Users can flag private mode periods to pause ingestion or purge entries from specific timeframes (`dijaview purge --since "2 hours ago"`).
