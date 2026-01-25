import os
import pickle
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
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists('client_secrets.json'):
                print("❌ Error: 'client_secrets.json' not found. Cannot authenticate.")
                return None
            flow = InstalledAppFlow.from_client_secrets_file('client_secrets.json', SCOPES)
            creds = flow.run_local_server(port=8080)
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    return build('drive', 'v3', credentials=creds)

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
