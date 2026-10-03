# The Dijaview Privacy Manifesto
### *Why Open Innovation is the Only Acceptable Foundation for Personal AI*

---

## 1. The Intimacy of Personal Activity

Your computer activity log is not merely a list of files. It is an unvarnished mirror of your life:
* The unsent thoughts in scratchpad drafts.
* The API tokens, SSH keys, and database connection strings you configure.
* The financial accounts, medical portals, and personal emails you view in browser tabs.
* The late-night terminal commands and internal git commits for unreleased projects.

When software captures and indexes this activity to make it searchable, it is assembling the **single most sensitive database in your entire digital existence**.

---

## 2. The Failure of Closed, Cloud-First AI

In 2024, when Microsoft introduced **Windows Recall**, the security community reacted with justified alarm. Security researchers demonstrated within hours that the feature stored raw screenshots and keystrokes in unencrypted local SQLite files, ripe for exfiltration by infostealer malware. Simultaneously, enterprise cloud assistants upload indexing telemetry to corporate servers to "improve model training."

Closed, proprietary assistants force users into a false dichotomy:
1. **Convenience with Compromise:** Let a corporate cloud index your life, expose you to data breaches, and charge you an ongoing subscription fee for the privilege.
2. **Privacy with Inconvenience:** Remain in the digital dark ages, manually grepping folders and scrolling through thousands of browser history rows.

---

## 3. Why Open Innovation Changes the Equation

Dijaview exists because **open innovation dismantles this false choice**. 

Five foundational pillars make Dijaview trustworthy:

### A. Local Gemma 2 Intelligence
Historically, performing context synthesis over messy logs required sending queries to remote commercial APIs. With the release of **Google's Gemma 2 (2B and 9B)**, high-fidelity reasoning, context synthesis, and source citation run directly on consumer laptops and desktops with zero cloud calls.
* **Open weights mean data sovereignty:** The neural network weights execute on your physical CPU or GPU. No remote company can see your query or your activity logs.
* **Zero recurring cost:** Once downloaded, running queries costs nothing. No credit cards, no token limits, and no sudden subscription paywalls.

### B. Absolute Zero Telemetry
Commercial tools constantly leak diagnostics, event counters, and behavioral telemetry back to mother ships. Dijaview collects zero telemetry. No tracking beacons, no analytics pings, and no cloud dependencies exist anywhere in the codebase. The only network socket ever created is an optional local web server bound to `127.0.0.1` and protected by a random per-launch authentication token.

### C. Auditable Redaction Over Black-Box Promises
In privacy software, "trust us" is not a security guarantee. Proprietary tools hide their filtering behind closed APIs. Dijaview's secret scrubbing rules are completely open, inspectable regular expressions. Anyone can audit how Stripe keys, JWTs, AWS credentials, and CLI passwords are sanitized. If a specific format is missing, you can add custom rules with `dijaview permissions add-filter` rather than hoping a third party protects you.

### D. Swappable Models and Freedom From Lock-In
Dijaview is model-agnostic. Because the inference layer connects through standard local endpoints (Ollama or llama.cpp), you are never trapped. You can run Gemma 2 2B on an ultrabook, upgrade to Gemma 2 9B on a developer workstation, or test newer open-weight models as the open-source ecosystem advances.

### E. Naming the Tradeoff: 2B Model Realities
Being honest about tradeoffs is essential in open-source engineering. The default Gemma 2 2B model is remarkably fast and runs comfortably on modest laptop CPUs with less than 2 GB of memory. But a 2-billion parameter model has real weaknesses:
* Its answers can be terse or overly literal.
* When multiple complex records are retrieved, 2B models can struggle with subtle reasoning, occasionally producing flat summaries or missing nuanced connections.
* It cannot handle massive prompt contexts without losing coherence.

This tradeoff is precisely why Dijaview does not rely on the LLM to search. Instead, deterministic Python regex extracts dates, and SQLite FTS5 with BM25 ranking finds the most relevant records first. Gemma 2 is only asked to synthesize pre-filtered, verified records and cite their exact line locations. And when a user has more RAM and needs richer reasoning, the open architecture allows an instant upgrade to the 9B model.

---

## 4. The Dijaview Oath

1. **Local-First, Always:** Your logs, embeddings, and chat histories never cross the local network interface (`127.0.0.1`).
2. **Transparent Storage:** Stored data is in standard, readable formats (SQLite / JSON) that you can inspect, export, or permanently delete with a single command.
3. **No Vendor Lock-In:** You own your data, your index, and your models. You can run Gemma 2 2B on an ultrabook, or Gemma 2 9B on a workstation.
4. **Active Defense:** Ingestion engines proactively redact secrets, bearer tokens, and private keys before they ever enter the index.
5. **Granular User Agency:** You have complete authority over Dijaview's permissions. You can grant, revoke, modify, or add permissions for data sources, allow or block directories, set file size caps, and define custom secret redaction filters at any time.

---

> *"Open innovation is not just about free code: it is about the right to own your personal intelligence without surrendering your autonomy."*
