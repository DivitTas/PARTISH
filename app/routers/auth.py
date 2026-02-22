from fastapi import APIRouter, HTTPException, Request, Depends
from fastapi.responses import RedirectResponse
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request as GoogleAuthRequest
from google.oauth2.credentials import Credentials
import os
import pickle
from dotenv import load_dotenv

load_dotenv()

router = APIRouter()

# Google OAuth 2.0 configuration
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
GOOGLE_REDIRECT_URI = "http://localhost:8000/auth/google/callback" # Must match Authorized redirect URI in Google Cloud Console

# If modifying these scopes, delete the file token.pickle.
SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/calendar.events',
    'https://www.googleapis.com/auth/calendar.readonly'
]

# A simple in-memory store for user credentials (NOT for production!)
# In a real app, this would be stored securely in a database associated with a user session.
# Key: user_id (or some session ID), Value: Google Credentials object
_credentials_store = {}

def get_google_oauth_flow():
    """Initializes and returns a Google OAuth 2.0 Flow object."""
    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
        raise HTTPException(
            status_code=500,
            detail="Google Client ID and Secret not configured."
        )

    # Use a "web" type client config here as we are building a web application
    flow = Flow.from_client_config(
        client_config={
            "web": {
                "client_id": GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                "redirect_uris": [GOOGLE_REDIRECT_URI]
            }
        },
        scopes=SCOPES,
        redirect_uri=GOOGLE_REDIRECT_URI
    )
    return flow

@router.get("/login/google")
async def google_login(request: Request):
    """Initiates the Google OAuth 2.0 login flow."""
    flow = get_google_oauth_flow()
    authorization_url, state = flow.authorization_url(
        access_type='offline',  # Request a refresh token
        include_granted_scopes='true',
        prompt='consent' # Ensure refresh token is granted
    )
    # Store the state in the user's session (or in a temporary store) to prevent CSRF
    # For now, we'll store it in a global dict (NOT production ready)
    request.session['oauth_state'] = state 
    return RedirectResponse(authorization_url)

@router.get("/google/callback")
async def google_callback(request: Request, code: str = None, state: str = None):
    """Handles the callback from Google after user authorization."""
    if state != request.session.get('oauth_state'):
        raise HTTPException(status_code=400, detail="State mismatch. Possible CSRF attack.")
    
    if code is None:
        raise HTTPException(status_code=400, detail="Authorization code not received.")

    flow = get_google_oauth_flow()
    flow.fetch_token(code=code)

    credentials = flow.credentials
    # Store credentials for the current session/user
    # In a real app, you'd associate this with a user ID in a database.
    # For now, we'll use a placeholder key.
    _credentials_store['current_user'] = credentials

    return {"message": "Authentication successful!", "access_token": credentials.token}

# Dependency to get credentials for protected routes
async def get_google_credentials():
    """Dependency that provides Google API credentials for a user."""
    credentials = _credentials_store.get('current_user')
    if not credentials:
        raise HTTPException(status_code=401, detail="Not authenticated with Google.")
    
    # Refresh token if expired
    if credentials.expired and credentials.refresh_token:
        credentials.refresh(GoogleAuthRequest())
        _credentials_store['current_user'] = credentials # Update store
    
    return credentials
