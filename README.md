# Dijaview

> **A privacy-first, local search engine for your computer activity powered by Gemma 2.**  
> *Ask questions about what you did on your computer without sending any data to the cloud.*

---

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Hacktoberfest 2026](https://img.shields.io/badge/Hacktoberfest-2026-orange.svg)](https://hacktoberfest.com)
[![Model: Gemma 2](https://img.shields.io/badge/Model-Gemma%202-green.svg)](https://ai.google.dev/gemma)
[![Local first](https://img.shields.io/badge/Privacy-100%25%20Local-success.svg)](#privacy-guarantee)
[![Open for contributions](https://img.shields.io/badge/Contributions-Welcome-brightgreen.svg)](CONTRIBUTING.md)

---

## The problem

Developers and computer users lose time every day trying to remember where they saw or did something:
* *"Where did I save that API key documentation I read last Tuesday?"*
* *"What was that complex curl command with custom headers I ran yesterday?"*
* *"Which browser tab had the article about Fastify CORS configuration?"*
* *"Where in my notes did I write down the database connection schema?"*

Normally, you have to remember which tool you used, grep through folders, scroll through thousands of shell history lines, or dig through browser history tables.

Tools like Microsoft Recall tried to solve this, but they generated widespread security criticism. They stored plain text files and sent data across the network. Cloud based tools charge monthly subscription fees and upload your private digital life to remote servers.

---

## What is Dijaview?

Dijaview is an open source, local search engine for your computer activity. It runs entirely on your own computer using Google's Gemma 2 open-weight model and a local database.

You ask in plain, everyday English:
```bash
dijaview query "Where is that API key doc I looked at last Tuesday?"
```

Dijaview searches your local shell history, browser history, notes, and recent documents. It recognizes time phrases like "last Tuesday", finds the right items, and uses Gemma 2 to give you a clear answer with direct file paths and links.

---

## Built for a friend

Dijaview was created for my friend Mohammed Adamu Aliyu ([@Adams-404](https://github.com/Adams-404)), a software engineer and active builder who spends hours in the terminal, maintains multiple projects, and constantly juggles dozens of open documentation tabs.

Mohammed regularly lost time trying to retrace his commands and notes:
> *"I ran this exact curl command three days ago that fixed a weird endpoint bug, and now I cannot find it in my history!"*

Dijaview solves this directly on his local machine with zero data leaving his computer.

---

## Privacy guarantee

1. **Zero telemetry:** Zero bytes leave your computer.
2. **Local AI reasoning:** Gemma 2 runs on your machine through Ollama or llama.cpp.
3. **Local storage:** Your data and search index stay on your hard drive in a local SQLite database.
4. **Automatic secret masking:** API keys, passwords, and private tokens are masked before indexing.
5. **Open source:** The code is completely open under the MIT license, so you can inspect how it works.

---

## Complete shell command reference

Dijaview comes with a straightforward command line interface that covers every part of your workflow:

### 1. Interactive terminal chat (`dijaview` or `dijaview chat`)
Running `dijaview` with no arguments (or `dijaview chat`) opens an interactive chat session directly in your terminal. You can ask follow up questions about your computer activity continuously.

```bash
# Simply run dijaview to start chatting
dijaview

# Or explicitly launch chat mode
dijaview chat
```

*Example session:*
```text
Dijaview (Interactive Local Shell)
Powered by Gemma 2 • 100% Local • Zero Telemetry
Type your question, or '/exit' to quit.

>>> Where did I save that API key doc last Tuesday?
Thinking...
You saved it in ~/notes/paystack_integration.md on Tuesday, September 29 at 3:14 PM.

>>> What was the curl command I used to test it?
Thinking...
At 3:16 PM on the same day, you ran:
curl -H "Authorization: Bearer [REDACTED]" https://api.paystack.co/transaction/verify/abc123

>>> /exit
Goodbye!
```

### 2. Ingesting and indexing activity (`dijaview index`)
Scans your local activity sources and adds them to your local index.

```bash
# Index all enabled sources (terminal, browser, notes)
dijaview index

# Index only your shell commands
dijaview index --source terminal

# Index only your browser history
dijaview index --source browser

# Index only your notes directory
dijaview index --source notes

# Perform a fresh, full re-index from scratch
dijaview index --rebuild
```

### 3. Asking one-off questions (`dijaview query`)
Asks a single question in natural language. Dijaview figures out the time frame, finds relevant records, and uses Gemma 2 to answer.

```bash
# General query with a time phrase
dijaview query "Where did I save the API key notes last Tuesday?"

# Query about shell commands
dijaview query "What was the curl command I used to test CORS yesterday?"

# Query restricted to a specific source
dijaview query "Which article discussed Postgres index types?" --source browser

# Quick search without calling Gemma 2 (pure local keyword and vector match)
dijaview query "paystack webhook" --raw
```

### 4. Checking system health and stats (`dijaview status`)
Shows you what is currently indexed, model availability, and disk usage.

```bash
dijaview status
```

### 5. Running the local web dashboard (`dijaview serve`)
Starts an interactive local web user interface with a search bar and visual timeline.

```bash
# Start local dashboard on default port (8080)
dijaview serve

# Start on a custom port
dijaview serve --port 3000
```

### 6. Managing privacy and purging data (`dijaview purge`)
Lets you delete indexed data whenever you want.

```bash
# Delete indexed history from the last 2 hours
dijaview purge --since "2 hours ago"

# Delete all indexed browser history while keeping terminal commands
dijaview purge --source browser

# Completely wipe the entire local search index
dijaview purge --all
```

### 7. Managing configuration (`dijaview config`)
Inspects and modifies your local settings.

```bash
# Show current configuration settings
dijaview config show

# Set the active model
dijaview config set model.name gemma2:2b

# Add a new folder to watch for notes
dijaview config add adapters.notes.directories "~/my-notes"
```

---

## Quick setup

### Prerequisites
* Python 3.10 or higher.
* Ollama installed on your machine.
* Pull the Gemma 2 model:
  ```bash
  ollama pull gemma2:2b
  ```

### Installation
```bash
git clone https://github.com/Icedmist/dijaview.git
cd dijaview

python3 -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt
```

### First run
```bash
# 1. Index your local shell history and notes
dijaview index

# 2. Ask your first question
dijaview query "What projects did I work on yesterday?"
```

---

## Open for contribution

Dijaview is an open project and we welcome contributions from everyone.

Here are great ways to contribute:
* **Add new data adapters:** Help us build adapters for VS Code recent files, Obsidian vaults, Tmux sessions, or Docker containers.
* **Improve time parsing:** Help extend temporal queries for different languages and formats.
* **UI improvements:** Help build out the local web dashboard and keyboard shortcuts.
* **Documentation & tutorials:** Improve setup guides for different Linux distributions, macOS, and Windows.

Read our [Contributing guide](CONTRIBUTING.md) to get started.

---

## Documentation directory

* [Architecture overview](docs/ARCHITECTURE.md)
* [Privacy manifesto: Why open innovation matters](docs/PRIVACY_MANIFESTO.md)
* [Data adapters specification](docs/ADAPTERS_SPEC.md)
* [Getting started guide](docs/GETTING_STARTED.md)
* [Hacktoberfest submission details](docs/HACKTOBERFEST_SUBMISSION.md)
* [Contributing guidelines](CONTRIBUTING.md)

---

## License

Distributed under the [MIT License](LICENSE). Copyright (c) 2026 icedmist.
