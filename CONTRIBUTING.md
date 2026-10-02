# Contributing to Dijaview

Thank you for your interest in contributing to Dijaview. Dijaview is an open source project, and we welcome contributions of all shapes and sizes.

Whether you want to add a new data source adapter, fix a bug, improve documentation, or share feedback, your help makes a big difference.

---

## Code of conduct

We strive to create a welcoming, friendly, and respectful environment for everyone. Please be kind, collaborative, and considerate when interacting with fellow contributors.

---

## How you can contribute

### 1. Adding new data source adapters
Dijaview is designed to be modular. You can add new adapters to index different activity sources:
* **Editors and IDEs:** Recent files and workspaces from VS Code, JetBrains, or Sublime Text.
* **Knowledge bases:** Local Obsidian vaults, Logseq, or Joplin notes.
* **Terminal tools:** Tmux sessions, Neovim registers, or Docker logs.
* **Productivity apps:** Local calendar events or task files.

To add an adapter, see the [Adapters specification](docs/ADAPTERS_SPEC.md) and implement the standard `BaseSourceAdapter` interface.

### 2. Improving query understanding and time parsing
Help us improve natural language time parsing so Dijaview can accurately understand phrases like:
* *"three days ago"*
* *"last weekend"*
* *"yesterday afternoon"*
* Relative dates in languages other than English.

### 3. Improving the web dashboard and CLI
* Add keyboard shortcuts to the web interface.
* Create a lightweight spotlight launcher for desktop environments.
* Improve CLI output formatting and speed.

### 4. Improving documentation and guides
* Write setup guides for different operating systems (Fedora, Ubuntu, Arch, macOS, Windows).
* Add examples of interesting queries and workflows.

---

## Development workflow

### 1. Fork and clone the repository
```bash
git clone https://github.com/Icedmist/dijaview.git
cd dijaview
```

### 2. Set up your local environment
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. Create a feature branch
Use clear, descriptive branch names with conventional prefixes:
```bash
git checkout -b feat/add-obsidian-adapter
# or
git checkout -b fix/browser-lock-retry
```

### 4. Commit your changes
We use conventional commits:
* `feat:` A new feature or capability.
* `fix:` A bug fix.
* `docs:` Documentation improvements.
* `test:` Adding or updating tests.
* `refactor:` Code improvements that do not change functionality.

### 5. Submit a pull request
1. Push your branch to GitHub:
   ```bash
   git push -u origin feat/add-obsidian-adapter
   ```
2. Open a Pull Request on GitHub against the `main` branch.
3. Describe your changes clearly and link any related issues.

---

## Getting help

If you have questions, run into trouble, or want to discuss an idea before writing code, open an issue on GitHub. We are happy to help you get started.
