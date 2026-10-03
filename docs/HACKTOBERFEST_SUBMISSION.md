---
title: "Dijaview: What Did I Do Last Tuesday? A Privacy-First Local Activity Engine Powered by Gemma 2"
published: false
tags: devchallenge, weekendchallenge, hf26challenge
---

*This is a submission for the [Hacktoberfest Weekend Challenge: Build for a Friend](https://dev.to/challenges/hacktoberfest-weekend-2026-10-01)*

---

## What I built

**Dijaview** is an open-source, local-first search engine that lets you ask plain-English questions about everything you have done on your computer, without sending any personal data to the cloud.

Instead of manually grepping through project directories, scrolling endlessly through shell history, or searching through thousands of browser tabs:
> *"Where did I save that API key documentation I looked at last Tuesday?"*  
> *"What was that complex curl command with custom headers I ran yesterday?"*  
> *"Where did I write down the database connection settings?"*

Dijaview indexes your local shell commands, browser history, and notes. It parses time expressions deterministically, filters candidate records using full-text search with BM25 ranking, and uses **Google's Gemma 2 open-weight model** to synthesize a direct answer with clickable links and source citations.

### Built for a friend
I built Dijaview for my friend **Mohammed Adamu Aliyu** ([@Adams-404](https://github.com/Adams-404)), a software engineer and builder who spends hours in terminal sessions, testing endpoints, and juggling dozens of open documentation tabs across multiple projects.

Mohammed frequently ran into the friction of retracing past work:
> *"I was constantly digging through thousands of lines of bash history or searching through browser tabs just to find a curl command or endpoint doc from two days ago. Having a tool on my local machine that lets me ask in plain English where I did something or find a command without uploading my history to anyone else is a game changer."*

Dijaview solves this directly on his local machine with zero telemetry.

---

## Demo

* **GitHub repository:** [https://github.com/Icedmist/dijaview](https://github.com/Icedmist/dijaview)
* **CLI query:**
  ```bash
  dijaview query "When did I run git status?"
  ```
* **Real output from local Gemma 2 2B:**
  ```text
  Answer:
  The user ran `git status` on three separate occasions: index 1, 2, and 3. They are located in the .bash_history file.

  Sources Cited:
    [1] (Terminal) Terminal Command: git status
        Location: /home/snow/.bash_history
        Time:     2026-10-02T13:21:37.095089
    [2] (Terminal) Terminal Command: git status
        Location: /home/snow/.bash_history
        Time:     2026-10-02T13:21:37.095089
    [3] (Terminal) Terminal Command: git status
        Location: /home/snow/.bash_history
        Time:     2026-10-02T13:21:37.095089
  ```

---

## Code

The entire codebase is open-source under the MIT license:
{% github Icedmist/dijaview %}

---

## How I built it

Dijaview is engineered from the ground up around **open-source AI** and local execution:

```
+---------------------------------------+
|              Data Sources             |
|   * Shell History (bash/zsh/fish)     |
|   * Browser History (SQLite)          |
|   * Local Notes & Markdown Files      |
+-------------------┬-------------------+
                    |
                    v
+---------------------------------------+
|     Secret Scrubbing & Ingestion      |
|   * Heuristic credential masking      |
|   * Size caps & path permissions      |
+-------------------┬-------------------+
                    |
                    v
+---------------------------------------+
|     Embedded SQLite & BM25 Store      |
|   * FTS5 Full-Text Search             |
|   * User-only file security (0600)    |
|   * Stopword filtering & BM25 rank    |
+-------------------┬-------------------+
                    |
                    v
+---------------------------------------+
|          Gemma 2 RAG Engine           |
|   * Deterministic Temporal Parser     |
|   * Prompt Injection Defense Pass     |
|   * Local Gemma 2 Synthesis           |
|   * Strict Source Citation Protocol   |
+---------------------------------------+
```

1. **Local Model Synthesis (Gemma 2):**  
   We use **Google's Gemma 2 (2B)** running locally via Ollama. Gemma 2 synthesizes concise answers and extracts source citations from retrieved context. The 2B model is lightweight (1.7 GB) and runs comfortably on CPU with zero external GPUs required. For systems with more memory, the **Gemma 2 9B** model can be used by changing `model.name` in configuration.
2. **Deterministic Time Parsing:**  
   Rather than relying on model guessing for dates, `temporal.py` parses time expressions like "last Tuesday" or "yesterday" using deterministic regular expressions and Python datetime math to calculate exact start and end timestamps.
3. **Embedded SQLite with BM25 Ranking:**  
   Indexed entries are stored in a local SQLite database (`~/.local/share/dijaview/dijaview.db`). Text search strips generic stopwords and uses SQLite FTS5 `bm25()` ranking so records matching multiple keywords appear first.
4. **Proactive Secret Redaction:**  
   Every entry passes through an automated regex filter that sanitizes API keys (`ghp_`, `sk_live_`, `pk_live_`), JWTs, CLI passwords (`mysql -p`, `curl -u`, `sshpass -p`), and shell exports before indexing.
5. **Prompt Injection Defenses:**  
   Retrieved snippets are wrapped in strict passive data tags, code block delimiters are sanitized, and the system prompt explicitly commands Gemma 2 to treat retrieved content as passive historical data, ignoring any embedded instructions like "ignore previous rules".

---

## Why does open innovation matter?

Your computer activity log is the **single most intimate record of your digital life**: every command you typed, every documentation article you read, every draft note you scribbled, and every project you touched.

Closed AI solutions create severe risks:
* **Corporate Surveillance:** Closed cloud tools upload telemetry and private activity logs to remote corporate servers.
* **Security Exposure:** Closed implementations have stored unencrypted screenshots that infostealers immediately learned to exploit.
* **Artificial Paywalls:** Closed tools charge subscription fees for search capabilities that belong on your operating system.

**Open innovation solves this completely:**
* **True Data Sovereignty:** With open-weight models like **Gemma 2**, state-of-the-art reasoning runs directly on your own silicon. 0 bytes ever leave your device.
* **Permanent Freedom:** Open weights cannot be discontinued or monetized behind paywalls. Once on your machine, it is yours forever.
* **Verifiable Security:** Because Dijaview is 100% open-source, you can inspect every line of code to verify that network sockets never open to outside servers.

---

## Limitations

* **Heuristic secret redaction:** Secret redaction uses pattern matching and regular expressions. While it catches standard formats (JWTs, Bearer tokens, GitHub, Stripe, Paystack, AWS, CLI passwords), it is best-effort and cannot guarantee 100% coverage of custom proprietary tokens. Users can register custom patterns with `dijaview permissions add-filter`.
* **Unencrypted local database:** The local SQLite database file is stored unencrypted on disk with user-only permissions (`chmod 600`). Dijaview relies on OS-level full-disk encryption (such as LUKS on Linux, FileVault on macOS, or BitLocker on Windows) to protect data at rest.
* **Compact model reasoning:** Gemma 2 2B is a 2-billion parameter model optimized for fast CPU inference. While it reliably cites evidence and summarizes records, users with 16 GB or more RAM can upgrade to Gemma 2 9B for deeper synthesis.
* **Prompt injection risks:** While Dijaview implements defensive data tagging and snippet sanitization, indexing untrusted external web pages or markdown files requires ongoing defensive vigilance in all local RAG architectures.

---

## Prize categories

* **Featured Category: Best Use of Gemma**  
  * Dijaview utilizes Google's **Gemma 2** open-weight model as its central brain for synthesizing answers and extracting source citations from retrieved computer activity.
* **Overall Challenge Winner**  
  * Delivering a complete, privacy-first local search engine built for a developer friend, embodying the true spirit of open-source AI and data sovereignty.

---

*Built with care during Hacktoberfest 2026 Weekend Challenge 1.*
