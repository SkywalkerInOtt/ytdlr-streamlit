import os
import pickle
import streamlit as st
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# Constants
DEFAULT_FOLDER_ID = "1OtB4gRxhiA3YvKtOSc_MfFBVdHz4a_28"
SCOPES = ['https://www.googleapis.com/auth/drive.file']

def authenticate_google_drive():
    """Authenticates with Google Drive and returns the service object."""
    creds = None
    error_details = []
    
    # 1. Try Streamlit Secrets (Cloud / production)
    try:
        if "google_drive" in st.secrets:
            secrets = st.secrets["google_drive"]
            if str(secrets.get("refresh_token")) == "None":
                 error_details.append("Secrets Error: 'refresh_token' is None. Please regenerate tokens with force-refresh script.")
            else:
                creds = Credentials(
                    token=None, # access token is transient, we rely on refresh_token
                    refresh_token=secrets["refresh_token"],
                    token_uri=secrets["token_uri"],
                    client_id=secrets["client_id"],
                    client_secret=secrets["client_secret"],
                    scopes=secrets["scopes"]
                )
                error_details.append(f"Secrets loaded. Creds created. Refresh Token present: {bool(secrets.get('refresh_token'))}")
        else:
             error_details.append("Secrets found but 'google_drive' section missing.")
    except Exception as e:
        error_details.append(f"Secrets Load Error: {e}")
        creds = None

    # 2. Fallback to local 'token.pickle' (Local dev)
    if not creds:
        if os.path.exists('token.pickle'):
            try:
                with open('token.pickle', 'rb') as token:
                    creds = pickle.load(token)
            except Exception as e:
                error_details.append(f"Local Pickle Error: {e}")
    
    # 3. Validation / Refresh
    if creds:
         error_details.append(f"Pre-Check: valid={creds.valid}, expired={creds.expired}, has_refresh={bool(creds.refresh_token)}")

    if not creds or not creds.valid:
        if creds and creds.refresh_token:
            try:
                error_details.append("Attempting token refresh...")
                creds.refresh(Request())
                error_details.append(f"Refresh complete. Valid={creds.valid}")
            except Exception as e:
                error_details.append(f"Token Refresh Error: {e}")
                creds = None
        elif creds:
            error_details.append("Creds invalid but refresh skipped (not expired? or no refresh token?)")

        # Re-auth flow only if NO valid creds and we are LOCAL (interactive)
        # We cannot run local server in cloud
        if not creds:
            if os.path.exists('client_secrets.json') and not os.environ.get('STREAMLIT_SERVER_ADDRESS'): 
                 # Poor man's check for "likely local environment" or just check if we can run flow
                try:
                    flow = InstalledAppFlow.from_client_secrets_file('client_secrets.json', SCOPES)
                    creds = flow.run_local_server(port=8080)
                    with open('token.pickle', 'wb') as token:
                        pickle.dump(creds, token)
                except Exception as e:
                    error_details.append(f"Local Interactive Auth Failed: {e}")
            else:
                error_details.append("No valid credentials found. (Interactive auth not available in cloud)")

    if creds and creds.valid:
        return build('drive', 'v3', credentials=creds), None
    
    final_error = " | ".join(error_details) if error_details else "Unknown Auth Error"
    return None, final_error

def upload_file_to_drive(file_path, folder_id=None):
    """
    Uploads a file to Google Drive.
    Returns: (webViewLink, error_message)
        - If success: (link, None)
        - If failure: (None, error_message)
    """
    target_folder = folder_id if folder_id else DEFAULT_FOLDER_ID
    
    service, auth_error = authenticate_google_drive()
    if not service: 
        return None, f"Auth Error: {auth_error}"
    
    file_metadata = {'name': os.path.basename(file_path), 'parents': [target_folder]}
    media = MediaFileUpload(file_path, resumable=True)
    try:
        file = service.files().create(body=file_metadata, media_body=media, fields='id, webViewLink').execute()
        return file.get('webViewLink'), None
    except Exception as e:
        print(f"❌ Upload failed: {e}")
        return None, f"Upload API Error: {str(e)}"
