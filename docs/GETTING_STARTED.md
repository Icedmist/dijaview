# Getting started with Dijaview

Follow this guide to set up and run Dijaview locally on your system.

---

## 1. General prerequisites

* Python 3.10 or higher
* Git
* Ollama (for running Gemma 2 locally)

---

## 2. Linux setup guide

### Step 1: Install system packages
Install Python, development tools, and Git for your distribution:

**Ubuntu / Debian:**
```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip git curl
```

**Fedora / RHEL:**
```bash
sudo dnf install -y python3 python3-pip git curl
```

**Arch Linux:**
```bash
sudo pacman -Syu --noconfirm python python-pip git curl
```

### Step 2: Install Ollama and pull Gemma 2
On Linux, install the Ollama daemon:
```bash
curl -fsSL https://ollama.com/install.sh | sh
```

Verify that the Ollama service is active:
```bash
systemctl status ollama
# If not running:
sudo systemctl enable --now ollama
```

Pull Google's Gemma 2 model and the local embedding model:
```bash
# Recommended model (compact, fast, runs smoothly on 4GB+ RAM)
ollama pull gemma2:2b

# Embedding model for vector similarity
ollama pull nomic-embed-text
```

### Step 3: Clone and install Dijaview
```bash
git clone https://github.com/Icedmist/dijaview.git
cd dijaview

python3 -m venv .venv
source .venv/bin/activate

pip install -e .
```

### Step 4: Run your initial index
Scan your Linux shell history (`~/.bash_history` or `~/.zsh_history`) and notes:
```bash
dijaview index
```

### Step 5: Start the interactive terminal chat
You can launch an interactive chat session directly in your Linux terminal:
```bash
dijaview
# or
dijaview chat
```

Dijaview will launch an interactive prompt where you can ask continuous questions about your activity:
```text
Dijaview (Interactive Local Shell)
Powered by Gemma 2 • 100% Local • Zero Telemetry
Type your question, or '/exit' to quit.

>>> What projects did I commit to yesterday?
Thinking...
Yesterday you worked on dijaview in ~/projects/dijaview and committed documentation changes.

>>> /exit
```

---

## 3. Configuration (`dijaview.yaml`)

Dijaview can be configured with an optional `dijaview.yaml` file in your project directory or in `~/.config/dijaview/config.yaml`:

```yaml
model:
  provider: "ollama"
  name: "gemma2:2b"
  embedding_model: "nomic-embed-text"
  base_url: "http://localhost:11434"

storage:
  db_path: "~/.local/share/dijaview/dijaview.db"

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
