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

import argparse

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/drive.file']
DEFAULT_FOLDER_ID = "1OtB4gRxhiA3YvKtOSc_MfFBVdHz4a_28"

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

def upload_file(file_path, folder_id=None):
    target_folder = folder_id if folder_id else DEFAULT_FOLDER_ID
    
    service = authenticate_google_drive()
    if not service: return
    print(f"\n🚀 Uploading '{file_path}' to Google Drive (Folder: {target_folder})...")
    file_metadata = {'name': os.path.basename(file_path), 'parents': [target_folder]}
    media = MediaFileUpload(file_path, resumable=True)
    try:
        file = service.files().create(body=file_metadata, media_body=media, fields='id, webViewLink').execute()
        print(f"✅ Upload Complete! 🔗 {file.get('webViewLink')}")
    except Exception as e:
        print(f"❌ Upload failed: {e}")

def remove_vocals(input_path):
    if not os.path.exists(input_path):
        print(f"❌ Error: File '{input_path}' not found.")
        return None
        
    print(f"\n🎤 Separating vocals for: {input_path}")
    print("(this may take a few minutes)...")
    try:
        subprocess.run(["demucs", "--mp3", "--two-stems=vocals", "-n", "htdemucs", input_path], check=True)
        
        filename_no_ext = os.path.splitext(os.path.basename(input_path))[0]
        demucs_out_dir = os.path.join("separated", "htdemucs", filename_no_ext)
        
        # Fallback search
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
            
            # 2. Instrumental MP4
            print("🎥 Merging instrumental audio with video...")
            mp4_file = f"{filename_no_ext}_instrumental.mp4"
            cmd = [
                "ffmpeg", "-y",
                "-i", input_path,
                "-i", mp3_file,
                "-c:v", "copy",
                "-c:a", "aac",
                "-map", "0:v:0",
                "-map", "1:a:0",
                "-shortest",
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

def download_video(url, interactive=True):
    print("\nFetching video information...")
    ydl_opts_info = {'quiet': True, 'no_warnings': True}
    try:
        with yt_dlp.YoutubeDL(ydl_opts_info) as ydl:
            info = ydl.extract_info(url, download=False)
    except Exception as e:
        print(f"Error: {e}"); return None

    title = info.get('title', 'Unknown')
    print(f"\nTitle: {title}")
    
    target_height = None
    
    if interactive:
        formats = info.get('formats', [])
        heights = sorted(list(set([f['height'] for f in formats if f.get('vcodec')!='none' and f.get('height')])), reverse=True)
        print("\nResolutions:")
        for i, h in enumerate(heights): print(f"{i+1}. {h}p")
        try:
            idx = int(input("\nChoose (number): ").strip()) - 1
            target_height = heights[idx]
        except:
            print("Invalid selection."); return None
    else:
        print("Auto-selecting best quality (CLI mode)...")
        # Let yt-dlp handle 'best' logic or just passing 'best' format
    
    print(f"\nDownloading...")
    safe_title = "".join([c for c in title if c.isalpha() or c.isdigit() or c in ' ._-']).rstrip()
    output_filename = f"{safe_title}.mp4"
    
    if target_height:
        format_str = f'bestvideo[height={target_height}]+bestaudio/best[height={target_height}]'
    else:
        format_str = 'bestvideo+bestaudio/best' # Default best

    ydl_opts = {
        'format': format_str,
        'merge_output_format': 'mp4',
        'outtmpl': output_filename,
        'ignoreerrors': True,
        'quiet': not interactive, 
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl: ydl.download([url])
        print(f"\n✅ Download complete: {output_filename}")
        return output_filename
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return None

def interactive_mode():
    print("🎥 YouTube Video Downloader (Interactive Mode)")
    url = input("Enter YouTube Video Link: ").strip()
    if not url: return

    outfile = download_video(url, interactive=True)
    if not outfile: return
    
    # --- VOCAL REMOVAL ---
    instrumental_files = None
    if input("\n🎵 AI: Remove vocals (create karaoke)? (y/n): ").strip().lower() == 'y':
        instrumental_files = remove_vocals(outfile)

    # --- UPLOAD ---
    print(f"\nCLOUD: Upload to Google Drive? [Default Folder ID: {DEFAULT_FOLDER_ID}]")
    upload_input = input("(Press Enter to accept default, type new Folder ID to override, or 'n' to skip): ").strip()
    
    if upload_input.lower() not in ['n', 'no']:
        target_folder = DEFAULT_FOLDER_ID
        if upload_input and upload_input.lower() not in ['y', 'yes']:
            target_folder = upload_input
            
        upload_queue = []
        upload_queue.append(outfile)
        if instrumental_files:
            if 'mp4' in instrumental_files:
                if input(f"Upload Karaoke Video ({instrumental_files['mp4']})? (y/n): ").strip().lower() == 'y':
                    upload_queue.append(instrumental_files['mp4'])
            if 'mp3' in instrumental_files:
                if input(f"Upload Instrumental Audio ({instrumental_files['mp3']})? (y/n): ").strip().lower() == 'y':
                        upload_queue.append(instrumental_files['mp3'])
        
        print(f"\nUploading {len(upload_queue)} files...")
        for f in upload_queue:
            upload_file(f, target_folder)

def main():
    parser = argparse.ArgumentParser(description="ytdlr CLI - YouTube Downloader & Processor")
    
    parser.add_argument("--download", metavar="URL", help="Download video from URL (auto-selects best quality)")
    parser.add_argument("--instrumental", metavar="FILE", help="Remove vocals from an existing video/audio file")
    parser.add_argument("--upload", metavar="FILE", help="Upload a file to Google Drive")
    parser.add_argument("--folder", metavar="ID", help="Google Drive Folder ID (for use with --upload)")

    args = parser.parse_args()

    # If no arguments provided, run legacy interactive mode
    if not any(vars(args).values()):
        interactive_mode()
        return

    # 1. Download Mode
    downloaded_file = None
    if args.download:
        downloaded_file = download_video(args.download, interactive=False)
        if not downloaded_file:
            sys.exit(1)

    # 2. Instrumental Mode
    # Can run on the downloaded file (if chained logic was implied) OR the specific file passed
    target_file_for_instrumental = args.instrumental
    # Note: If user passes BOTH --download and --instrumental, do they mean "download X then process X"?
    # The flag `--instrumental <FILE>` implies explicit file. 
    # BUT if they want to chain: `main.py --download URL --instrumental AUTO`? 
    # The user request said: "2) with --instrumental <file>.mp4". This implies explicit file.
    
    if args.instrumental:
        remove_vocals(args.instrumental)

    # 3. Upload Mode
    if args.upload:
        upload_file(args.upload, args.folder)

if __name__ == "__main__":
    main()
