import os
import base64
import json
import io
from typing import List, Dict, Any
from fastmcp import FastMCP
from dotenv import load_dotenv
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseDownload
from PyPDF2 import PdfReader
from pymilvus import Collection, connections, utility
from sentence_transformers import SentenceTransformer

# Load environment variables
load_dotenv()

# ===================
# FastMCP Instance
# ===================
mcp = FastMCP("final-mcp-server")

# ===================
# Gmail Tools
# ===================
# GMAIL_CREDS_FILE_PATH = "C://Users//shiv//.google//client_creds.json"
# GMAIL_TOKEN_FILE_PATH = "C://Users//shiv//.google//app_tokens.json"
# GMAIL_SCOPES = ["https://www.googleapis.com/auth/gmail.modify"]

GMAIL_CREDS_FILE_PATH = "absolute_path//to//client_creds.json"
GMAIL_TOKEN_FILE_PATH = "absolute_path//to//app_tokens.json"
GMAIL_SCOPES = ["https://www.googleapis.com/auth/gmail.modify"]

def get_gmail_service():
    creds = None
    if os.path.exists(GMAIL_TOKEN_FILE_PATH):
        creds = Credentials.from_authorized_user_file(GMAIL_TOKEN_FILE_PATH, GMAIL_SCOPES)
    else:
        flow = InstalledAppFlow.from_client_secrets_file(GMAIL_CREDS_FILE_PATH, GMAIL_SCOPES)
        creds = flow.run_local_server(port=0)
        with open(GMAIL_TOKEN_FILE_PATH, "w") as token:
            token.write(creds.to_json())
    return build("gmail", "v1", credentials=creds)

gmail_service = get_gmail_service()

@mcp.tool()
def get_unread_emails(limit: int = 5) -> List[Dict[str, str]]:
    """Fetch unread emails from your Gmail inbox."""
    try:
        results = gmail_service.users().messages().list(userId="me", labelIds=["INBOX", "UNREAD"], maxResults=limit).execute()
        messages = results.get("messages", [])
        unread_emails = []
        for msg in messages:
            msg_data = gmail_service.users().messages().get(userId="me", id=msg["id"]).execute()
            headers = msg_data.get("payload", {}).get("headers", [])
            subject = next((h["value"] for h in headers if h["name"] == "Subject"), "(No Subject)")
            sender = next((h["value"] for h in headers if h["name"] == "From"), "Unknown")
            snippet = msg_data.get("snippet", "")
            unread_emails.append({
                "id": msg["id"],
                "subject": subject,
                "from": sender,
                "snippet": snippet
            })
            # Mark as read
            gmail_service.users().messages().modify(userId="me", id=msg["id"], body={"removeLabelIds": ["UNREAD"]}).execute()
        return unread_emails
    except HttpError as e:
        return [{"error": str(e)}]

@mcp.tool()
def read_email(email_id: str) -> Dict[str, str]:
    """Read the full content of a given email by ID."""
    try:
        message = gmail_service.users().messages().get(userId="me", id=email_id, format="full").execute()
        headers = message["payload"].get("headers", [])
        subject = next((h["value"] for h in headers if h["name"] == "Subject"), "(No Subject)")
        sender = next((h["value"] for h in headers if h["name"] == "From"), "Unknown")
        body = ""
        if "parts" in message["payload"]:
            for part in message["payload"]["parts"]:
                if part.get("mimeType") == "text/plain":
                    body_data = part["body"].get("data")
                    if body_data:
                        body += base64.urlsafe_b64decode(body_data).decode("utf-8")
        else:
            body_data = message["payload"]["body"].get("data")
            if body_data:
                body = base64.urlsafe_b64decode(body_data).decode("utf-8")
        return {
            "subject": subject,
            "from": sender,
            "body": body
        }
    except HttpError as e:
        return {"error": str(e)}

@mcp.tool()
def get_read_emails(limit: int = 50) -> List[Dict[str, str]]:
    """Fetch recently read (non-unread) emails from the Gmail inbox."""
    try:
        results = gmail_service.users().messages().list(userId="me", labelIds=["INBOX"], maxResults=limit).execute()
        messages = results.get("messages", [])
        read_emails = []
        for msg in messages:
            msg_data = gmail_service.users().messages().get(userId="me", id=msg["id"]).execute()
            if "UNREAD" in msg_data.get("labelIds", []):
                continue
            headers = msg_data.get("payload", {}).get("headers", [])
            subject = next((h["value"] for h in headers if h["name"] == "Subject"), "(No Subject)")
            sender = next((h["value"] for h in headers if h["name"] == "From"), "Unknown")
            snippet = msg_data.get("snippet", "")
            read_emails.append({
                "id": msg["id"],
                "subject": subject,
                "from": sender,
                "snippet": snippet
            })
        return read_emails
    except HttpError as e:
        return [{"error": str(e)}]

@mcp.tool()
def get_spam_emails(limit: int = 20) -> List[Dict[str, str]]:
    """Fetch emails from your Gmail spam folder."""
    try:
        results = gmail_service.users().messages().list(userId="me", labelIds=["SPAM"], maxResults=limit).execute()
        messages = results.get("messages", [])
        spam_emails = []
        for msg in messages:
            msg_data = gmail_service.users().messages().get(userId="me", id=msg["id"]).execute()
            headers = msg_data.get("payload", {}).get("headers", [])
            subject = next((h["value"] for h in headers if h["name"] == "Subject"), "(No Subject)")
            sender = next((h["value"] for h in headers if h["name"] == "From"), "Unknown")
            snippet = msg_data.get("snippet", "")
            spam_emails.append({
                "id": msg["id"],
                "subject": subject,
                "from": sender,
                "snippet": snippet
            })
        return spam_emails
    except HttpError as e:
        return [{"error": str(e)}]

# ===================
# Google Drive Tools
# ===================
DRIVE_CREDS_FILE_PATH = "absolute_path//to//client_creds.json"
DRIVE_TOKEN_FILE_PATH = "absolute_path//to//app_tokens.json"
DRIVE_SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]

def get_drive_service():
    creds = None
    if os.path.exists(DRIVE_TOKEN_FILE_PATH):
        creds = Credentials.from_authorized_user_file(DRIVE_TOKEN_FILE_PATH, DRIVE_SCOPES)
    else:
        flow = InstalledAppFlow.from_client_secrets_file(DRIVE_CREDS_FILE_PATH, DRIVE_SCOPES)
        creds = flow.run_local_server(port=0)
        with open(DRIVE_TOKEN_FILE_PATH, "w") as token:
            token.write(creds.to_json())
    return build("drive", "v3", credentials=creds)

drive_service = get_drive_service()

@mcp.tool()
def list_my_drive_files(limit: int = 10) -> List[Dict[str, str]]:
    """List recent files in your Google Drive."""
    results = drive_service.files().list(
        pageSize=limit,
        fields="files(id, name, mimeType, modifiedTime)").execute()
    return results.get("files", [])

@mcp.tool()
def read_file_content(file_id: str) -> str:
    """Read the content of a Google Drive file by file_id. Supports Google Docs, plain text, and PDFs."""
    file = drive_service.files().get(fileId=file_id, fields="name, mimeType").execute()
    mime_type = file["mimeType"]
    name = file["name"]
    # For Google Docs: export to plain text
    if mime_type == "application/vnd.google-apps.document":
        content = drive_service.files().export(fileId=file_id, mimeType="text/plain").execute()
        return content.decode("utf-8")
    # For plain text
    elif mime_type == "text/plain":
        request = drive_service.files().get_media(fileId=file_id)
        buffer = io.BytesIO()
        downloader = MediaIoBaseDownload(buffer, request)
        done = False
        while not done:
            status, done = downloader.next_chunk()
        buffer.seek(0)
        return buffer.read().decode("utf-8")
    # For PDFs
    elif mime_type == "application/pdf":
        request = drive_service.files().get_media(fileId=file_id)
        buffer = io.BytesIO()
        downloader = MediaIoBaseDownload(buffer, request)
        done = False
        while not done:
            status, done = downloader.next_chunk()
        buffer.seek(0)
        reader = PdfReader(buffer)
        return "\n".join(page.extract_text() for page in reader.pages if page.extract_text())
    else:
        return f"Unsupported MIME type: {mime_type}"

# ===================
# Google Classroom Tools
# ===================
CLASS_CREDS_FILE = "C://Users//shiv//.google//client_creds.json"
CLASS_TOKEN_FILE = "C://Users//shiv//.google//classroom_tokens.json"
CLASS_SCOPES = ["https://www.googleapis.com/auth/classroom.courses.readonly"]

def get_classroom_service():
    creds = None
    if os.path.exists(CLASS_TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(CLASS_TOKEN_FILE, CLASS_SCOPES)
    else:
        flow = InstalledAppFlow.from_client_secrets_file(CLASS_CREDS_FILE, CLASS_SCOPES)
        creds = flow.run_local_server(port=0)
        with open(CLASS_TOKEN_FILE, "w") as token:
            token.write(creds.to_json())
    return build("classroom", "v1", credentials=creds)

@mcp.tool()
def list_courses():
    """List all your Google Classroom courses."""
    service = get_classroom_service()
    courses = service.courses().list().execute().get("courses", [])
    return {
        "courses": [course["name"] for course in courses] if courses else []
    }


if __name__ == "__main__":
    mcp.run() 