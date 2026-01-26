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
    
    # 1. Try Streamlit Secrets (Cloud / production)
    try:
        if "google_drive" in st.secrets:
            secrets = st.secrets["google_drive"]
            creds = Credentials(
                token=None, # access token is transient, we rely on refresh_token
                refresh_token=secrets["refresh_token"],
                token_uri=secrets["token_uri"],
                client_id=secrets["client_id"],
                client_secret=secrets["client_secret"],
                scopes=secrets["scopes"]
            )
    except Exception:
        # st.secrets raises an error if no secrets.toml exists locally. 
        # We catch this to fall back to the local token.pickle method.
        creds = None

    # 2. Fallback to local 'token.pickle' (Local dev)
    if not creds:
        if os.path.exists('token.pickle'):
            with open('token.pickle', 'rb') as token:
                creds = pickle.load(token)
    
    # 3. Validation / Refresh
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception as e:
                print(f"❌ Error refreshing token: {e}")
                creds = None

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
                    print(f"❌ Local auth failed: {e}")
                    return None
            else:
                return None # Cannot auth in cloud without secrets

    if creds and creds.valid:
        return build('drive', 'v3', credentials=creds)
    return None

def upload_file_to_drive(file_path, folder_id=None):
    """
    Uploads a file to Google Drive.
    Returns the webViewLink if successful, None otherwise.
    """
    target_folder = folder_id if folder_id else DEFAULT_FOLDER_ID
    
    service = authenticate_google_drive()
    if not service: return None
    
    file_metadata = {'name': os.path.basename(file_path), 'parents': [target_folder]}
    media = MediaFileUpload(file_path, resumable=True)
    try:
        file = service.files().create(body=file_metadata, media_body=media, fields='id, webViewLink').execute()
        return file.get('webViewLink')
    except Exception as e:
        print(f"❌ Upload failed: {e}")
        return None
