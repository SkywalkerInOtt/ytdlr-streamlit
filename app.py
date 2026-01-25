import streamlit as st
import yt_dlp
import os
import time
import shutil
import tempfile
import subprocess
import pickle
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# Constants
DEFAULT_FOLDER_ID = "1OtB4gRxhiA3YvKtOSc_MfFBVdHz4a_28"
SCOPES = ['https://www.googleapis.com/auth/drive.file']

# --- GOOGLE DRIVE HELPER ---
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
                st.error("Error: 'client_secrets.json' not found. Cannot authenticate.")
                return None
            flow = InstalledAppFlow.from_client_secrets_file('client_secrets.json', SCOPES)
            creds = flow.run_local_server(port=8080)
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    return build('drive', 'v3', credentials=creds)

def upload_file_to_drive(file_path, folder_id):
    service = authenticate_google_drive()
    if not service: return None
    
    file_metadata = {'name': os.path.basename(file_path), 'parents': [folder_id]}
    media = MediaFileUpload(file_path, resumable=True)
    try:
        file = service.files().create(body=file_metadata, media_body=media, fields='id, webViewLink').execute()
        return file.get('webViewLink')
    except Exception as e:
        st.error(f"Upload failed: {e}")
        return None

# --- DEMUCS HELPER ---
def process_vocal_removal(input_path):
    status_text = st.empty()
    status_text.text("🎤 Separating vocals... (this may take a few minutes)")
    
    try:
        # Run Demucs
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
            created_files['mp3'] = mp3_file
            
            # 2. Instrumental MP4
            status_text.text("🎥 Merging instrumental audio with video...")
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
                created_files['mp4'] = mp4_file
            
            status_text.empty()
            return created_files
        else:
            status_text.text("❌ Separation failed: Output not found.")
            return None
    except Exception as e:
        status_text.text(f"❌ Error: {e}")
        return None

def main():
    st.set_page_config(page_title="ytdlr", page_icon="🎥")
    st.title("🎥 YouTube Downloader")
    
    # Check dependencies
    if not shutil.which("ffmpeg"):
        st.warning("⚠️ `ffmpeg` not found. Video processing will be limited.")

    # URL Input
    url = st.text_input("YouTube URL")

    if url:
        if "url" not in st.session_state or st.session_state.url != url:
            st.session_state.url = url
            st.session_state.video_info = None
            st.session_state.processed_files = {}

        # Fetch Info
        if not st.session_state.video_info:
            with st.spinner("Fetching video info..."):
                ydl_opts = {'quiet': True, 'no_warnings': True}
                try:
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        info = ydl.extract_info(url, download=False)
                        st.session_state.video_info = info
                except Exception as e:
                    st.error(f"Error: {e}")

        if st.session_state.video_info:
            info = st.session_state.video_info
            st.subheader(info.get('title', 'Unknown Title'))
            st.image(info.get('thumbnail'), width=300)

            # Resolution Selection
            formats = info.get('formats', [])
            heights = sorted(list(set([f['height'] for f in formats if f.get('vcodec')!='none' and f.get('height')])), reverse=True)
            resolution = st.selectbox("Select Resolution", heights, format_func=lambda x: f"{x}p")
            
            # Options
            remove_vocals = st.checkbox("🎵 Create Karaoke (Remove Vocals)")
            
            if st.button("Download & Process"):
                with st.spinner(f"Downloading {resolution}p..."):
                    safe_title = "".join([c for c in info['title'] if c.isalpha() or c.isdigit() or c in ' ._-']).rstrip()
                    output_filename = f"{safe_title}.mp4"
                    
                    ydl_opts_down = {
                        'format': f'bestvideo[height={resolution}]+bestaudio/best[height={resolution}]',
                        'merge_output_format': 'mp4',
                        'outtmpl': output_filename,
                        'quiet': True,
                    }
                    
                    try:
                        # cleanup old
                        if os.path.exists(output_filename): os.remove(output_filename)
                        
                        with yt_dlp.YoutubeDL(ydl_opts_down) as ydl:
                            ydl.download([url])
                        
                        st.success(f"✅ Downloaded: {output_filename}")
                        st.session_state.processed_files = {'original': output_filename}
                        
                        if remove_vocals:
                            instrumentals = process_vocal_removal(output_filename)
                            if instrumentals:
                                if 'mp3' in instrumentals:
                                    st.success(f"✅ Created Instrumental Audio")
                                    st.session_state.processed_files['instrumental_mp3'] = instrumentals['mp3']
                                if 'mp4' in instrumentals:
                                    st.success(f"✅ Created Karaoke Video")
                                    st.session_state.processed_files['instrumental_mp4'] = instrumentals['mp4']

                    except Exception as e:
                        st.error(f"Failed: {e}")

    # --- RESULT & UPLOAD AREA ---
    if "processed_files" in st.session_state and st.session_state.processed_files:
        files = st.session_state.processed_files
        
        st.divider()
        st.subheader("📂 Files Ready")
        
        # Download Buttons
        cols = st.columns(len(files))
        for i, (key, path) in enumerate(files.items()):
            with cols[i]:
                with open(path, "rb") as f:
                    label = "Original MP4" if key == 'original' else ("Karaoke Video" if key == 'instrumental_mp4' else "Backing Track MP3")
                    st.download_button(label=f"⬇️ {label}", data=f, file_name=os.path.basename(path))

        st.divider()
        st.subheader("☁️ Upload to Google Drive")
        
        folder_id = st.text_input("Folder ID", value=DEFAULT_FOLDER_ID)
        
        # Checkboxes for what to upload
        files_to_upload = []
        c1, c2, c3 = st.columns(3)
        if 'original' in files:
            if c1.checkbox("Original Video", value=True): files_to_upload.append(files['original'])
        if 'instrumental_mp4' in files:
            if c2.checkbox("Karaoke Video", value=True): files_to_upload.append(files['instrumental_mp4'])
        if 'instrumental_mp3' in files:
            if c3.checkbox("Backing Track", value=False): files_to_upload.append(files['instrumental_mp3'])
            
        if st.button("🚀 Upload Selected"):
            for f_path in files_to_upload:
                with st.spinner(f"Uploading {os.path.basename(f_path)}..."):
                    link = upload_file_to_drive(f_path, folder_id)
                    if link:
                        st.success(f"Uploaded! [Link]({link})")

if __name__ == "__main__":
    main()
