import os
import pickle
import json
from google_auth_oauthlib.flow import InstalledAppFlow

# Constants
SCOPES = ['https://www.googleapis.com/auth/drive.file']

def main():
    print("🚀 Google Drive Token Generator for Streamlit Cloud")
    print("--------------------------------------------------")
    
    if not os.path.exists('client_secrets.json'):
        print("❌ Error: 'client_secrets.json' not found. Please download it from Google Cloud Console.")
        return

    flow = InstalledAppFlow.from_client_secrets_file('client_secrets.json', SCOPES)
    # prompt='consent' forces a refresh token to be returned
    creds = flow.run_local_server(port=8080, access_type='offline', prompt='consent')
    
    # Extract relevant data for st.secrets
    secrets_data = {
        "token": creds.token,
        "refresh_token": creds.refresh_token,
        "token_uri": creds.token_uri,
        "client_id": creds.client_id,
        "client_secret": creds.client_secret,
        "scopes": creds.scopes
    }
    
    print("\n✅ Authentication successful!")
    print("\nCopy the following into your Streamlit Cloud secrets (or .streamlit/secrets.toml locally):")
    print("--------------------------------------------------")
    print("[google_drive]")
    for key, value in secrets_data.items():
        # Ensure list is formatted effectively
        if isinstance(value, list):
            print(f'{key} = {json.dumps(value)}')
        else:
            print(f'{key} = "{value}"')
    print("--------------------------------------------------")

if __name__ == "__main__":
    main()
