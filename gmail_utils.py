import os
import pickle
import re
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
TOKEN_FILE = "token.pkl"
CREDS_FILE = "credentials.json"

def get_gmail_credentials():
    """Return Gmail credentials. If not present, guide user through OAuth."""
    creds = None
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, "rb") as f:
            creds = pickle.load(f)

    return creds

def authorize_gmail_flow():
    """Return a Flow object for OAuth authorization URL."""
    flow = Flow.from_client_secrets_file(
        CREDS_FILE,
        scopes=SCOPES,
        redirect_uri="http://localhost:8501/"  # Out-of-band flow
    )
    auth_url, _ = flow.authorization_url(access_type="offline")
    return flow, auth_url

def save_credentials(creds):
    with open(TOKEN_FILE, "wb") as f:
        pickle.dump(creds, f)

def fetch_emails(creds, max_results=20):
    """Fetch recent email snippets from Gmail."""
    service = build("gmail", "v1", credentials=creds)
    results = service.users().messages().list(userId="me", maxResults=max_results).execute()
    messages = results.get("messages", [])
    email_snippets = []
    for msg in messages:
        m = service.users().messages().get(userId="me", id=msg["id"]).execute()
        snippet = m.get("snippet", "")
        email_snippets.append(snippet)
    return email_snippets

def extract_items_from_emails(snippets):
    """Extract items with format 'Name $Price' from email snippets."""
    items = []
    for snippet in snippets:
        found = re.findall(r"([A-Za-z\s]+)\s+\$?(\d+\.\d{2})", snippet)
        items.extend([{"name": n.strip(), "price": float(p)} for n, p in found])
    return items
