---
title: "DijaView: What Did I Do Last Tuesday? A Privacy-First Local Activity Engine Powered by Gemma 2"
published: true
tags: devchallenge, weekendchallenge, hf26challenge
---

*This is a submission for the [Hacktoberfest Weekend Challenge: Build for a Friend](https://dev.to/challenges/hacktoberfest-weekend-2026-10-01)*

---

## What I Built

**Dijaview** is an open-source, local-first search engine that lets you ask plain-English questions about everything you have done on your computer, without sending any personal data to the cloud.

Instead of manually grepping through project directories, scrolling endlessly through shell history, or searching through thousands of browser tabs:
> *"Where did I save that API key documentation I looked at last Tuesday?"*  
> *"What was that complex curl command with custom headers I ran yesterday?"*  
> *"Where did I write down the database connection settings?"*

DijaView indexes your local shell commands, browser history, notes, and recent file changes, extracts temporal constraints (*"last Tuesday"*), and uses **Google's Gemma 2 open-weight model** to synthesize a direct answer with clickable links and source citations.

### Built for a friend
I built Dijaview for my friend **Mohammed Adamu Aliyu** ([@Adams-404](https://github.com/Adams-404)), a software engineer and active builder who lives in the terminal, maintains multiple projects, and constantly juggles 50+ open documentation tabs. 

Mohammed regularly lost 15 to 30 minutes every day trying to retrace his steps:
> *"I ran this exact curl command three days ago that fixed a weird CORS preflight bug, and now I cannot find it in my history!"*

When commercial solutions like Microsoft Recall launched, Mohammed refused to use them due to the privacy risks of unencrypted surveillance software sending telemetry to corporate servers. Mohammed needed a tool that was fast, local first, zero telemetry, and genuinely helpful.

> **Mohammed's reaction when testing Dijaview:**  
> *"Wait, so I can literally just ask 'What was the curl command I used to test the captive portal CORS endpoint yesterday?' and it gives me the exact command with the headers right on my machine? And nothing goes to a remote server? This is what personal computing was supposed to be."*

---

## Demo

* **GitHub Repository:** [https://github.com/Icedmist/dijaview](https://github.com/Icedmist/dijaview)
* **CLI Quick Run:**
  ```bash
  dijaview query "Where did I save the API key notes last Tuesday?"
  ```
* **Output:**
  ```text
  🔍 Querying DijaView Engine (Gemma 2 Local)...
  
  💡 Answer:
  You saved your API key notes in `~/notes/paystack_integration.md` on Tuesday, 
  September 29 at 3:14 PM. You also ran a related test command in your terminal:
  `curl -H "Authorization: Bearer [REDACTED]" https://api.paystack.co/transaction/verify/...`

  📂 Sources Cited:
  1. [Notes] file:///home/snow/notes/paystack_integration.md (Line 42)
  2. [Terminal] ~/.bash_history (2026-09-29 15:14:22 UTC)
  ```

---

## Code

The entire codebase is open-source under the MIT license:
{% github Icedmist/dijaview %}

---

## How I Built It

DijaView is engineered from the ground up around **open-source AI**:

```
┌───────────────────────────────────────┐
│              Data Sources             │
│   • Shell History (bash/zsh/fish)     │
│   • Browser History (SQLite)          │
│   • Local Notes & Markdown Files      │
└──────────────────┬────────────────────┘
                   │
                   ▼
┌───────────────────────────────────────┐
│     Secret Scrubbing & Ingestion      │
│   • Automated credential masking      │
│   • Timestamp & context normalization │
└──────────────────┬────────────────────┘
                   │
                   ▼
┌───────────────────────────────────────┐
│     Embedded Vector & Temporal Store  │
│   • Local embeddings (nomic-embed)    │
│   • Local SQLite-vec / Chroma storage │
└──────────────────┬────────────────────┘
                   │
                   ▼
┌───────────────────────────────────────┐
│          Gemma 2 RAG Engine           │
│   • Temporal Query Parser             │
│   • Local Gemma 2 2B/9B Inference     │
│   • Strict Source Citation Protocol   │
└───────────────────────────────────────┘
```

1. **Open-Weight Reasoning (Gemma 2):**  
   We use **Google's Gemma 2 (2B / 9B)** running locally via Ollama / llama.cpp. Gemma 2's superior reasoning capability allows it to understand complex temporal expressions (*"earlier this week"*, *"last Thursday afternoon"*) and synthesize concise answers with exact source citations.
2. **Pluggable Source Adapters:**  
   Clean modular adapters parse timestamped shell histories (`~/.bash_history`, `~/.zsh_history`), local browser history databases (Chrome, Brave, Firefox SQLite), and workspace markdown documents.
3. **Embedded Vector Database:**  
   Embeddings are generated locally using `nomic-embed-text` and stored in an embedded SQLite vector store on disk. No external vector SaaS or remote database cluster is needed.
4. **Proactive Secret Redaction:**  
   Every entry passes through an automated regex filter that sanitizes API keys (`ghp_`, `sk-`), private keys, and bearer tokens before saving to the index.

---

## Why Does Open Innovation Matter?

Your computer activity log is the **single most intimate record of your life**: every command you typed, every documentation article you read, every draft note you scribbled, and every credential you configured.

Closed AI solutions create an unacceptable risk:
* **Corporate Surveillance:** Closed cloud tools upload telemetry and private activity logs to remote corporate servers to train future models.
* **Security Catastrophes:** Closed implementations like Windows Recall stored plain-text screenshots and database rows that infostealers immediately learned to exploit.
* **Artificial Paywalls:** Closed tools charge $20+/month for search features that should be an inherent capability of your operating system.

**Open innovation solves this completely:**
* **True Data Sovereignty:** With open-weight models like **Gemma 2**, state-of-the-art reasoning runs directly on your own silicon. 0 bytes ever leave your device.
* **Permanent Freedom:** Open weights cannot be rug-pulled, discontinued, or monetized behind paywalls. Once on your machine, it is yours forever.
* **Verifiable Security:** Because DijaView is 100% open-source, you can inspect every line of code to verify that network sockets never open to outside servers.

---

## Prize Categories

* **Featured Category: Best Use of Gemma**  
  * DijaView utilizes Google's **Gemma 2** open-weight model as its central brain for temporal reasoning, snippet evaluation, and source citation.
* **Overall Challenge Winner**  
  * Delivering a complete, privacy-first alternative to Microsoft Recall built specifically for a developer friend, embodying the true spirit of open-source AI and data sovereignty.
* **Partner Category: Best Use of Sentry Agent Tracing**  
  * Traces local RAG inference latency, token counts, and adapter execution times to ensure zero performance degradation.

---

*Built with ❤️ during Hacktoberfest 2026 Weekend Challenge 1.*
