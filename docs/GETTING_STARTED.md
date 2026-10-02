# Getting Started with DijaView

Follow this guide to set up and run DijaView locally on your machine.

---

## 1. Prerequisites

* **Python 3.10 or higher**
* **Git**
* **Ollama** (for local Gemma 2 inference)

### Install Ollama & Pull Gemma 2
If you haven't installed Ollama yet:
* **Linux:** `curl -fsSL https://ollama.com/install.sh | sh`
* **macOS:** Download from [ollama.com/download](https://ollama.com/download)
* **Windows:** Download the Windows installer from [ollama.com](https://ollama.com)

Pull the Gemma 2 model:
```bash
# Recommended default (compact, fast, runs on 4GB+ RAM):
ollama pull gemma2:2b

# Optional high-capacity model (for workstations with 16GB+ RAM / GPU):
ollama pull gemma2:9b
```

Also pull a lightweight embedding model:
```bash
ollama pull nomic-embed-text
```

---

## 2. Installation

Clone the private repository and set up a virtual environment:

```bash
git clone https://github.com/Icedmist/dijaview.git
cd dijaview

python3 -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt
```

---

## 3. Configuration (`dijaview.yaml`)

DijaView can be configured with an optional `dijaview.yaml` in your project root or `~/.config/dijaview/config.yaml`:

```yaml
# DijaView Configuration
model:
  provider: "ollama"
  name: "gemma2:2b"
  embedding_model: "nomic-embed-text"
  base_url: "http://localhost:11434"

storage:
  db_path: "~/.local/share/dijaview/dijaview.db"
  vector_store: "sqlite_vec"

adapters:
  terminal:
    enabled: true
    shells: ["bash", "zsh"]
    max_history_entries: 5000

  browser:
    enabled: true
    browsers: ["brave", "chrome", "firefox"]
    max_days: 30

  notes:
    enabled: true
    directories:
      - "~/Documents"
      - "~/notes"
      - "~/projects"
    extensions: [".md", ".txt"]
    exclude_dirs:
      - "node_modules"
      - ".git"
      - ".venv"
      - "dist"

privacy:
  redact_secrets: true
  ignore_dotfiles: true
```

---

## 4. Running DijaView

### Step 1: Index Your Local Activity
Scan your configured adapters to build the initial local index:
```bash
# Index all enabled sources
python -m dijaview.cli index

# Or index a specific adapter
python -m dijaview.cli index --source terminal
```

### Step 2: Query Your History
Ask questions in plain English:
```bash
python -m dijaview.cli query "Where did I save the API key notes last Tuesday?"
```

### Step 3: Run the Local Web Dashboard (Optional)
Launch the interactive web UI:
```bash
python -m dijaview.cli serve --port 8080
```
Then open [http://localhost:8080](http://localhost:8080) in your browser.
