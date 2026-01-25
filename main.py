import yt_dlp
import sys

import os
import pickle
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/drive.file']
FOLDER_ID = "1OtB4gRxhiA3YvKtOSc_MfFBVdHz4a_28"

def authenticate_google_drive():
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
            
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists('client_secrets.json'):
                print("\n❌ Error: 'client_secrets.json' not found.")
                print("Please download it from Google Cloud Console and place it in this folder.")
                return None
                
            flow = InstalledAppFlow.from_client_secrets_file(
                'client_secrets.json', SCOPES)
            creds = flow.run_local_server(port=0)
            
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    return build('drive', 'v3', credentials=creds)

def upload_file(file_path):
    service = authenticate_google_drive()
    if not service:
        return

    print(f"\n🚀 Uploading '{file_path}' to Google Drive...")
    
    file_metadata = {
        'name': os.path.basename(file_path),
        'parents': [FOLDER_ID]
    }
    
    media = MediaFileUpload(file_path, resumable=True)
    
    try:
        file = service.files().create(body=file_metadata,
                                    media_body=media,
                                    fields='id, webViewLink').execute()
        print(f"✅ Upload Complete!")
        print(f"🔗 Link: {file.get('webViewLink')}")
    except Exception as e:
        print(f"❌ Upload failed: {e}")

def main():
    print("🎥 YouTube Video Downloader")
    url = input("Enter YouTube Video Link: ").strip()
    
    if not url:
        print("Error: Empty URL")
        return

    print("\nFetching video information...")
    
    # Options for fetching metadata
    ydl_opts_info = {
        'quiet': True,
        'no_warnings': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts_info) as ydl:
            info = ydl.extract_info(url, download=False)
    except Exception as e:
        print(f"\nError: Could not fetch video info.\n{e}")
        return

    title = info.get('title', 'Unknown Title')
    print(f"\nTitle: {title}")

    # Extract available video heights
    formats = info.get('formats', [])
    available_heights = set()
    
    for f in formats:
        # Check for video stream (vcodec != none) and valid height
        if f.get('vcodec') != 'none' and f.get('height'):
            available_heights.add(f['height'])

    if not available_heights:
        print("No suitable video formats found.")
        return

    # Sort heights descending
    sorted_heights = sorted(list(available_heights), reverse=True)

    print("\nAvailable Resolutions:")
    for i, height in enumerate(sorted_heights):
        print(f"{i + 1}. {height}p")

    selection = input("\nChoose a resolution to download (number): ").strip()

    try:
        index = int(selection) - 1
        if index < 0 or index >= len(sorted_heights):
            print("Invalid selection.")
            return
        target_height = sorted_heights[index]
    except ValueError:
        print("Invalid input. Please enter a number.")
        return

    print(f"\nPreparing to download {target_height}p version in MP4 format...")
    
    # Use explicit filename to easily find it later
    safe_title = "".join([c for c in title if c.isalpha() or c.isdigit() or c in ' ._-']).rstrip()
    output_filename = f"{safe_title}.mp4"

    # Options for downloading
    ydl_opts_download = {
        'format': f'bestvideo[height={target_height}]+bestaudio/best[height={target_height}]',
        'merge_output_format': 'mp4',
        'outtmpl': output_filename,
        # Fallback if specific height construction fails (should be rare given we listed it)
        'ignoreerrors': True, 
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts_download) as ydl:
            ydl.download([url])
        print(f"\n✅ Download complete: {output_filename}")
        
        # --- UPLOAD SECTION ---
        upload_choice = input("\nCLOUD: Upload to Google Drive? (y/n): ").strip().lower()
        if upload_choice == 'y':
            if os.path.exists(output_filename):
                upload_file(output_filename)
            else:
                 print("Error: File not found for upload.")
                 
    except Exception as e:
        print(f"\n❌ Download failed: {e}")

if __name__ == "__main__":
    main()
