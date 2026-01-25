import yt_dlp
import sys

import os
import pickle
import subprocess
import shutil
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/drive.file']
FOLDER_ID = "1OtB4gRxhiA3YvKtOSc_MfFBVdHz4a_28"

def authenticate_google_drive():
    creds = None
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists('client_secrets.json'):
                print("\n❌ Error: 'client_secrets.json' not found.")
                return None
            flow = InstalledAppFlow.from_client_secrets_file('client_secrets.json', SCOPES)
            creds = flow.run_local_server(port=8080)
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    return build('drive', 'v3', credentials=creds)

def upload_file(file_path):
    service = authenticate_google_drive()
    if not service: return
    print(f"\n🚀 Uploading '{file_path}' to Google Drive...")
    file_metadata = {'name': os.path.basename(file_path), 'parents': [FOLDER_ID]}
    media = MediaFileUpload(file_path, resumable=True)
    try:
        file = service.files().create(body=file_metadata, media_body=media, fields='id, webViewLink').execute()
        print(f"✅ Upload Complete! 🔗 {file.get('webViewLink')}")
    except Exception as e:
        print(f"❌ Upload failed: {e}")

def remove_vocals(input_path):
    print("\n🎤 separating vocals... (this may take a few minutes)")
    try:
        # Run Demucs: separate into 2 stems (vocals, no_vocals)
        subprocess.run(["demucs", "--mp3", "--two-stems=vocals", "-n", "htdemucs", input_path], check=True)
        
        # Determine output path
        filename_no_ext = os.path.splitext(os.path.basename(input_path))[0]
        demucs_out_dir = os.path.join("separated", "htdemucs", filename_no_ext)
        
        # Fallback search if exact name match fails
        if not os.path.exists(demucs_out_dir):
            potential_dirs = [d for d in os.listdir(os.path.join("separated", "htdemucs")) if d.startswith(filename_no_ext[:10])]
            if potential_dirs:
                demucs_out_dir = os.path.join("separated", "htdemucs", potential_dirs[0])
        
        no_vocals_path = os.path.join(demucs_out_dir, "no_vocals.mp3")
        
        created_files = {}

        if os.path.exists(no_vocals_path):
            # 1. Instrumental MP3
            mp3_file = f"{filename_no_ext}_instrumental.mp3"
            shutil.move(no_vocals_path, mp3_file)
            print(f"✅ Created Instrumental Audio: {mp3_file}")
            created_files['mp3'] = mp3_file
            
            # 2. Instrumental MP4 (Video + Instrumental Audio)
            print("🎥 Merging instrumental audio with video...")
            mp4_file = f"{filename_no_ext}_instrumental.mp4"
            # ffmpeg -i video.mp4 -i audio.mp3 -c:v copy -c:a aac -map 0:v:0 -map 1:a:0 output.mp4
            cmd = [
                "ffmpeg", "-y",
                "-i", input_path,        # Original Video
                "-i", mp3_file,          # Instrumental Audio
                "-c:v", "copy",          # Copy video stream (fast)
                "-c:a", "aac",           # Encode audio to AAC
                "-map", "0:v:0",         # Take video from input 0
                "-map", "1:a:0",         # Take audio from input 1
                "-shortest",             # Stop when shortest stream ends
                mp4_file
            ]
            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            if os.path.exists(mp4_file):
                print(f"✅ Created Karaoke Video:     {mp4_file}")
                created_files['mp4'] = mp4_file
            
            return created_files
        else:
            print("❌ Start separation failed: Could not find output file.")
            return None
    except Exception as e:
        print(f"❌ Error removing vocals: {e}")
        return None

def main():
    print("🎥 YouTube Video Downloader")
    url = input("Enter YouTube Video Link: ").strip()
    if not url: return

    print("\nFetching video information...")
    ydl_opts_info = {'quiet': True, 'no_warnings': True}
    try:
        with yt_dlp.YoutubeDL(ydl_opts_info) as ydl:
            info = ydl.extract_info(url, download=False)
    except Exception as e:
        print(f"Error: {e}"); return

    title = info.get('title', 'Unknown')
    print(f"\nTitle: {title}")
    
    formats = info.get('formats', [])
    heights = sorted(list(set([f['height'] for f in formats if f.get('vcodec')!='none' and f.get('height')])), reverse=True)
    
    print("\nResolutions:")
    for i, h in enumerate(heights): print(f"{i+1}. {h}p")
    
    try:
        idx = int(input("\nChoose (number): ").strip()) - 1
        target_height = heights[idx]
    except:
        print("Invalid."); return

    print(f"\nDownloading {target_height}p...")
    safe_title = "".join([c for c in title if c.isalpha() or c.isdigit() or c in ' ._-']).rstrip()
    output_filename = f"{safe_title}.mp4"
    
    ydl_opts = {
        'format': f'bestvideo[height={target_height}]+bestaudio/best[height={target_height}]',
        'merge_output_format': 'mp4',
        'outtmpl': output_filename,
        'ignoreerrors': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl: ydl.download([url])
        print(f"\n✅ Download complete: {output_filename}")
        
        # --- VOCAL REMOVAL ---
        instrumental_files = None
        if input("\n🎵 AI: Remove vocals (create karaoke)? (y/n): ").strip().lower() == 'y':
            instrumental_files = remove_vocals(output_filename)

        # --- UPLOAD ---
        if input("\nCLOUD: Upload to Google Drive? (y/n): ").strip().lower() == 'y':
            upload_queue = []
            
            # Original
            upload_queue.append(output_filename)
            
            # Instrumentals
            if instrumental_files:
                if 'mp4' in instrumental_files:
                    if input(f"Upload Karaoke Video ({instrumental_files['mp4']})? (y/n): ").strip().lower() == 'y':
                        upload_queue.append(instrumental_files['mp4'])
                if 'mp3' in instrumental_files:
                    if input(f"Upload Instrumental Audio ({instrumental_files['mp3']})? (y/n): ").strip().lower() == 'y':
                         upload_queue.append(instrumental_files['mp3'])
            
            if not instrumental_files: # If simple download, just upload original without asking implies yes (or already handled by queue init)
                 pass 

            print(f"\nUploading {len(upload_queue)} files...")
            for f in upload_queue:
                upload_file(f)

    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    main()
