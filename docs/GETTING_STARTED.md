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

## 3. Windows setup guide (PowerShell)

### Step 1: Install prerequisites with winget
Open PowerShell as an Administrator and install Python, Git, and Ollama using the Windows Package Manager (`winget`):

```powershell
winget install Python.Python.3.11
winget install Git.Git
winget install Ollama.Ollama
```

*Note: Restart your PowerShell terminal after installation so that Python, Git, and Ollama are available on your PATH.*

### Step 2: Start Ollama and download Gemma 2
Ollama typically starts automatically as a Windows background task in your system tray. In PowerShell, pull the models:

```powershell
# Pull the recommended Gemma 2 model
ollama pull gemma2:2b

# Pull the embedding model for vector search
ollama pull nomic-embed-text
```

### Step 3: Clone and install Dijaview
In PowerShell:

```powershell
git clone https://github.com/Icedmist/dijaview.git
cd dijaview

# Create and activate Python virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Install in editable mode
pip install -e .
```

*Tip: If PowerShell blocks running the activate script, enable local scripts once by running `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`.*

### Step 4: Run your initial index on Windows
Dijaview automatically reads your PowerShell history (`%APPDATA%\Microsoft\Windows\PowerShell\PSReadLine\ConsoleHost_history.txt`), Chrome browser history (`%LOCALAPPDATA%\Google\Chrome\User Data\Default\History`), and documents folder:

```powershell
dijaview index
```

### Step 5: Start the interactive chat in PowerShell
Run the single command `dijaview` to start chatting with Gemma 2:

```powershell
dijaview
# or
dijaview chat
```

*Example session in PowerShell:*
```text
Dijaview (Interactive Local Shell)
Powered by Gemma 2 • 100% Local • Zero Telemetry
Type your question, or '/exit' to quit.

>>> Where did I save that API key doc last Tuesday?
Thinking...
You saved it in C:\Users\YourUser\Documents\notes\api_keys.md on Tuesday, September 29 at 3:14 PM.

>>> /exit
```

---

## 4. macOS setup guide

### Step 1: Install Homebrew and prerequisites
If you have not already installed Homebrew, install it from [brew.sh](https://brew.sh), then install Python, Git, and Ollama:

```bash
brew install python git ollama
```

### Step 2: Start Ollama and download Gemma 2
You can start the Ollama background service or run the desktop app:

```bash
brew services start ollama
```

Pull Google's Gemma 2 model and the embedding model:

```bash
# Recommended default model (runs fast on Apple Silicon M1/M2/M3/M4)
ollama pull gemma2:2b

# Pull the embedding model
ollama pull nomic-embed-text
```

### Step 3: Clone and install Dijaview
Open Terminal (zsh) on your Mac:

```bash
git clone https://github.com/Icedmist/dijaview.git
cd dijaview

python3 -m venv .venv
source .venv/bin/activate

pip install -e .
```

### Step 4: Run your initial index on macOS
Dijaview will read your zsh history (`~/.zsh_history`), local Chrome or Brave history (`~/Library/Application Support/Google/Chrome/Default/History`), and your documents:

```bash
dijaview index
```

### Step 5: Start the interactive chat in macOS Terminal
Run the single command `dijaview` to start chatting with Gemma 2:

```bash
dijaview
# or
dijaview chat
```

*Example session on macOS:*
```text
Dijaview (Interactive Local Shell)
Powered by Gemma 2 • 100% Local • Zero Telemetry
Type your question, or '/exit' to quit.

>>> Where did I save that API key doc last Tuesday?
Thinking...
You saved it in ~/Documents/notes/api_keys.md on Tuesday, September 29 at 3:14 PM.

>>> /exit
```

---

## 5. Configuration (`dijaview.yaml`)

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

---

## 6. Permissions and privacy management

Dijaview gives you granular control over every aspect of what it accesses. You can customize, edit, modify, or add permissions at any time:

### Inspect current permissions
```bash
dijaview permissions show
```

### Toggle data source access
Grant or revoke access to any data source:
```bash
# Disable browser history scanning
dijaview permissions disable browser

# Re-enable browser history scanning
dijaview permissions enable browser

# Disable shell command indexing
dijaview permissions disable terminal
```

### Allow or block directories
Tell Dijaview which directories are safe to index and which to strictly ignore:
```bash
# Add a trusted folder to notes scanning
dijaview permissions allow-path ~/WorkNotes

# Block a sensitive directory
dijaview permissions block-path ~/Documents/TaxReturns

# Remove a path from the permissions list
dijaview permissions remove-path ~/Documents/TaxReturns
```

### Add custom secret redaction filters
In addition to built-in detection for API keys and passwords, you can add custom regular expressions to mask personal identifiers or company secrets:
```bash
# Mask social security or tax identification numbers
dijaview permissions add-filter ssn "\d{3}-\d{2}-\d{4}" --replacement "[REDACTED_SSN]"

# Mask customer identification codes
dijaview permissions add-filter cust_code "CUST-[0-9]{6}" --replacement "[REDACTED_CUSTOMER]"

# Remove a custom redaction filter
dijaview permissions remove-filter ssn
```

### Reset permissions
To return to the default secure profile:
```bash
dijaview permissions reset
```

---

## 7. Running the local web dashboard

Dijaview includes a local, self-contained web user interface for visual search and timeline browsing:

```bash
# Launch the local dashboard on http://localhost:8080
dijaview serve

# Specify a custom port
dijaview serve --port 3000
```

Open `http://localhost:8080` in your web browser to:
* Search activity logs with instant answers and citations.
* Filter results by source (All, Terminal, Browser, Notes).
* Browse your chronological computer activity timeline.
* Inspect and toggle source permissions on the fly.

---

## 8. Automatic background activity sync

Keep your local search index synchronized with your ongoing work automatically:

```bash
# Start background watcher daemon (checks every 30 seconds)
dijaview watch

# Run with a custom sync interval
dijaview watch --interval 60

# Run a single incremental sync sweep and exit
dijaview watch --once
```
