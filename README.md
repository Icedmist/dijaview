# DijaView 🔍

> **Privacy-first, local-first computer activity & context search engine powered by Gemma 2.**  
> *Ask questions about everything you've done on your computer — without a single byte leaving your machine.*

---

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Hacktoberfest 2026](https://img.shields.io/badge/Hacktoberfest-2026-orange.svg)](https://hacktoberfest.com)
[![Model: Gemma 2](https://img.shields.io/badge/Model-Gemma%202%20(Open--Weight)-green.svg)](https://ai.google.dev/gemma)
[![Local First](https://img.shields.io/badge/Privacy-100%25%20Local-success.svg)](#privacy-guarantee)

---

## 💡 The Problem

How often do you ask yourself:
* *"Where did I save that API key documentation I read last Tuesday?"*
* *"What was that complex curl command with custom headers I ran yesterday?"*
* *"Which browser tab had the article about Fastify CORS configuration?"*
* *"Where in my notes did I write down the database connection schema?"*

Modern operating systems force you to remember **where** you put something (grep files, search browser history SQLite databases, scroll through bash history, or dig through notes folders). 

Commercial solutions like **Microsoft Recall** attempted to solve this by continuously capturing everything — but at the catastrophic cost of privacy: unencrypted plain-text SQLite databases, telemetry, and security vulnerabilities. Proprietary cloud tools like Rewind AI charge expensive recurring subscriptions and upload your private digital life to remote servers.

---

## ✨ Enter DijaView

**DijaView** (derived from *déjà vu*) is an open-source, local-first personal activity search engine. It runs entirely on your local hardware using **Google's Gemma 2 open-weight model** and an embedded vector index.

You ask in plain, natural English:
```text
> dijaview query "Where is that API key doc I looked at last Tuesday?"
```

DijaView searches your local terminal history, browser history, notes, and documents, applies temporal filters ("last Tuesday"), retrieves the relevant source chunks, and has Gemma 2 synthesize a direct answer with clickable local file and web citations.

---

## 🔒 The Privacy Guarantee

1. **Zero Telemetry:** 0 bytes are transmitted to any external server.
2. **Local AI Inference:** Powered by **Gemma 2** running locally via Ollama or llama.cpp.
3. **Local Vector Storage:** Embeddings and chunk metadata reside inside your local SQLite / Chroma vector database on disk.
4. **Automated Secret Redaction:** API keys, private tokens, passwords, and `.env` files are automatically masked before ingestion.
5. **Inspectable & Auditable:** 100% open-source code under the MIT license.

---

## 🚀 Key Features

* **Multi-Source Ingestion:**
  * 🖥️ **Terminal Commands:** Parses timestamped history from `bash`, `zsh`, and `fish`.
  * 🌐 **Browser History:** Safely reads local browser history databases (Chrome, Brave, Firefox) in read-only mode.
  * 📝 **Local Notes & Documents:** Watches and indexes Markdown (`.md`), text (`.txt`), code repositories, and documentation.
  * 🕒 **Recent File Touches:** Tracks newly modified or created files across designated directories.
* **Temporal Query Resolution:**
  * Understands relative and absolute time expressions: *"yesterday"*, *"last Tuesday"*, *"earlier this morning"*, *"two weeks ago"*.
* **Open-Source AI Synthesis:**
  * Leverages **Gemma 2 (2B / 9B)** to reason over retrieved snippets and formulate concise, helpful responses with direct references (`file:///...` and URLs).
* **Spotlight & CLI Access:**
  * Lightweight CLI for terminal power users (`dijaview query "..."`, `dijaview index`, `dijaview status`).
  * Modern, distraction-free local web dashboard for interactive searches and timeline navigation.

---

## 🏗️ Architecture at a Glance

```
┌────────────────────────────────────────────────────────┐
│                   Local Data Sources                   │
│   • Shell History (~/.bash_history, ~/.zsh_history)    │
│   • Browser History (Local Chrome/Firefox SQLite DB)   │
│   • Workspace Notes & Markdown Files                   │
│   • Git Commits & Modified Files                       │
└──────────────────────────┬─────────────────────────────┘
                           │
                           ▼
┌────────────────────────────────────────────────────────┐
│              Ingestion & Redaction Engine              │
│   • Pluggable source adapters                          │
│   • Automated regex-based secret/token scrubbing       │
│   • Text chunking & timestamp normalization            │
└──────────────────────────┬─────────────────────────────┘
                           │
                           ▼
┌────────────────────────────────────────────────────────┐
│             Local Vector & Metadata Store              │
│   • Local embeddings (nomic-embed-text / MiniLM)       │
│   • Embedded vector storage (SQLite-vec / Chroma)      │
│   • Temporal index (timestamps, source types, tags)    │
└──────────────────────────┬─────────────────────────────┘
                           │
                           ▼
┌────────────────────────────────────────────────────────┐
│              Gemma 2 Local RAG Pipeline                │
│   • Temporal query parser ("last Tuesday" -> date)     │
│   • Hybrid search: Vector similarity + keyword match   │
│   • Gemma 2 reasoning & synthesis (via Ollama/local)   │
└──────────────────────────┬─────────────────────────────┘
                           │
                           ▼
┌────────────────────────────────────────────────────────┐
│                   User Interfaces                      │
│   • CLI: `dijaview query "..."`                        │
│   • Local Web UI: Interactive timeline & direct links  │
└────────────────────────────────────────────────────────┘
```

For an in-depth breakdown, read [Architecture Guide](docs/ARCHITECTURE.md).

---

## 🛠️ Quickstart

### Prerequisites
* **Python 3.10+**
* **Ollama** installed with Gemma 2:
  ```bash
  ollama pull gemma2:2b
  ```

### Installation
```bash
# Clone the repository
git clone https://github.com/Icedmist/dijaview.git
cd dijaview

# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Initial Indexing
```bash
# Ingest terminal history and local notes
dijaview index --sources shell,notes

# Run your first query
dijaview query "Where did I save the API key notes last Tuesday?"
```

See [Getting Started Guide](docs/GETTING_STARTED.md) for full configuration options.

---

## 🏆 Hacktoberfest 2026 Submission

This project is built for the **Hacktoberfest 2026 Weekend Challenge 1: Build for a Friend** hosted on DEV.

* **Target Categories:**
  * 🥇 **Overall Challenge Winner**
  * 🌟 **Best Use of Gemma** (Google's open-weight model)
  * 🎧 **Best Use of ElevenLabs** (Voice query & audio answer synthesis)
  * 📊 **Best Use of Sentry Agent Tracing** (Inference latency and execution tracing)
* **Theme:** *"Build for a Friend"* — Built for a developer friend who constantly loses track of shell one-liners, documentation links, and scattered notes across long coding sessions.

Read the complete submission post draft in [docs/HACKTOBERFEST_SUBMISSION.md](docs/HACKTOBERFEST_SUBMISSION.md).

---

## 📖 Documentation Directory

* [System Architecture](docs/ARCHITECTURE.md)
* [Privacy Manifesto: Why Open Innovation Matters](docs/PRIVACY_MANIFESTO.md)
* [Source Adapters Technical Specification](docs/ADAPTERS_SPEC.md)
* [Getting Started & Local Setup](docs/GETTING_STARTED.md)
* [Hacktoberfest Submission Draft](docs/HACKTOBERFEST_SUBMISSION.md)

---

## 📄 License

Distributed under the [MIT License](LICENSE). Copyright © 2026 icedmist.
