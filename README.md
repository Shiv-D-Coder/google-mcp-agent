# 🚀 Google MCP Agent

A unified FastMCP-powered agent that connects **Gmail**, **Google Drive**, and **Google Classroom** with LLM-ready tools for automation, parsing, and intelligent retrieval.

---

## 📌 What This Repo Offers

- ✅ Read and manage Gmail (inbox, unread, spam)
- ✅ Read file content from Google Drive (Docs, PDFs, TXT)
- ✅ List Google Classroom courses
- ✅ LLM-compatible tools exposed via FastMCP
- ✅ Easily deployable with `uv` in an agentic RAG pipeline

---

## ⚙️ Setup Guide

> Before running the project, set up your Google Cloud project for OAuth.

### 🔑 1. Enable APIs in Google Cloud Console
1. Go to [GCP Console](https://console.cloud.google.com/)
2. Navigate to **"APIs & Services" > "OAuth consent screen"**
3. Choose **"External"** > Fill in app name and support email
4. Under **Scopes**, you don't need to add anything manually now
5. Under **Test users**, add the **Gmail/Drive account** you want to access (must match the email you're using)

### 🧾 2. Create OAuth 2.0 Credentials
1. Go to **"APIs & Services" > "Credentials"**
2. Click **"Create Credentials" > "OAuth client ID"**
3. Choose **"Desktop App"** or **"Web App"**
4. Download the **`client_creds.json`** file

## 🔐 Authentication Info (One-time Manual, Then Persistent)

- The **first time** you run the server, a **browser window will open** asking you to log in and authorize access.
- After successful login, a `token.json` file will be created automatically in your local directory.
- This file contains your OAuth access/refresh token and is reused for future runs.
- You won’t need to re-authenticate unless the token expires or is deleted.
   

> ⚠️ _No need to publish the app — keeping it in testing mode is fine as long as the user is whitelisted._

---

## 🛠️ Configuration Example

Add this block to your `msp.json` or equivalent MCP config to run the main server:

```
{
    "mcpServers": {
      "main_mcp_server": {
        "command": "uv",
        "args": [
          "--directory",
          "absolute_path\\to\\current_project",
          "run",
          "server.py",
          "--creds-file-path",
          "absolute_path\\to\\client_creds.json",
          "--token-path",
          "absolute_path\\to\\app_tokens.json"
        ]
      }
}
```

🧰 Available Tools (Exposed via FastMCP)
These tools are registered with FastMCP and can be used directly by your copilot system or any agent pipeline.

📬 Gmail Tools
🔹 get_unread_emails(limit: int = 5)
Returns a list of unread emails from the user's inbox with metadata like subject, sender, and snippet. Automatically marks them as read.

🔹 read_email(email_id: str)
Reads and decodes the full plain-text body of a specific email by its ID.

🔹 get_read_emails(limit: int = 50)
Fetches recently read (non-unread) emails from the inbox.

🔹 get_spam_emails(limit: int = 20)
Retrieves a list of emails from the Gmail spam folder with minimal metadata.

📂 Google Drive Tools
🔹 list_my_drive_files(limit: int = 10)
Returns a list of recent files in the user's Google Drive, including ID, name, MIME type, and last modified time.


🔹 read_file_content(file_id: str)
Reads and extracts text from a file in Drive. Supports:

Google Docs (exported as plain text)

Plain .txt files

PDFs (parsed using PyPDF2)

🏫 Google Classroom Tool
🔹 list_courses()
Fetches the list of enrolled Google Classroom courses (read-only).

Each tool can be invoked via MCP runtime or LLM-powered interfaces. This setup enables rich, context-aware workflows that interact with the user's real data.

