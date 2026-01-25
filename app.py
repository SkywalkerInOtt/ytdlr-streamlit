import streamlit as st
import yt_dlp
import os
import time
import shutil
import tempfile
import subprocess
import re

CACHE_DIR = "/tmp/yt-dlp-cache"

def fetch_video_info(url, client_type='default'):
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'nocheckcertificate': True,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'cache_dir': CACHE_DIR,
    }
    
    if client_type != 'default':
        ydl_opts['extractor_args'] = {'youtube': {'player_client': [client_type]}}

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
        return info
    except Exception as e:
        st.error(f"Error fetching video info: {e}")
        return None

class MyLogger:
    def __init__(self):
        self.logs = []

    def debug(self, msg):
        self.logs.append(msg)

    def warning(self, msg):
        self.logs.append(f"WARNING: {msg}")

    def error(self, msg):
        self.logs.append(f"ERROR: {msg}")

def main():
    st.set_page_config(page_title="ytdlr", page_icon="🎥")
    
    st.title("🎥 YouTube Downloader")
    
    if not shutil.which("ffmpeg"):
        st.error("⚠️ `ffmpeg` is not installed or not in PATH. Merging video+audio will fail. Please install ffmpeg.")

    st.markdown("Enter a YouTube URL below to download the video in MP4 format.")

    st.sidebar.header("⚙️ Settings")
    
    # --- OAuth Login Section ---
    st.sidebar.subheader("🔑 Authentication")
    if st.sidebar.button("Login with Google (Fix 403)"):
        with st.sidebar.status("Authenticating...") as status:
            st.write("Initializing...")
            # Use a dummy URL that requires auth or just extracting to trigger the login prompt
            # Actually, the most reliable way to trigger oauth is to try to fetch a private video or use --username oauth2
            # We will use subprocess to capture the output interactively
            
            cmd = [
                "yt-dlp",
                "--username", "oauth2",
                "--password", "",
                "--cache-dir", CACHE_DIR,
                "--simulate", # Don't download
                "https://www.youtube.com/watch?v=dQw4w9WgXcQ" # Dummy public video to trigger auth flow check
            ]
            
            process = subprocess.Popen(
                cmd, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.STDOUT, 
                text=True, 
                bufsize=1
            )
            
            auth_url = None
            auth_code = None
            
            while True:
                line = process.stdout.readline()
                if not line and process.poll() is not None:
                    break
                if line:
                    # Look for: "Go to https://www.google.com/device and enter code ABCD-1234"
                    # pattern varies slightly by version, but usually contains URL and Code
                    match = re.search(r"Go to (https://.*) and enter code ([\w-]+)", line)
                    if match:
                        auth_url = match.group(1)
                        auth_code = match.group(2)
                        st.sidebar.warning(f"**Action Required!**")
                        st.sidebar.markdown(f"1. Go to: [Link]({auth_url})")
                        st.sidebar.code(auth_code, language="text")
                        st.sidebar.write("Waiting for you to approve...")
                    
                    if "Authentication successful" in line or "Loading youtube-oauth2" in line:
                         st.write("Login detected!")

            if process.returncode == 0:
                status.update(label="✅ Login Successful!", state="complete", expanded=False)
                st.sidebar.success("Authenticated!")
                st.session_state.authenticated = True
            else:
                status.update(label="❌ Login Failed", state="error")
                st.sidebar.error("Login process failed or timed out.")

    if st.session_state.get("authenticated"):
        st.sidebar.success("✅ Authenticated")

    st.sidebar.info("💡 **Tip**: If downloads fail with 403, try changing the **Client Bypass** to 'iOS' or 'Android'.")
    
    client_type = st.sidebar.selectbox(
        "Client Bypass", 
        ["default", "ios", "android", "web", "mweb", "tv"],
        help="Try changing this if downloads fail. 'ios' or 'android' often bypass restrictions."
    )

    # Invalidate cache if client changes
    if "current_client" not in st.session_state:
        st.session_state.current_client = client_type
    elif st.session_state.current_client != client_type:
        st.session_state.current_client = client_type
        if "video_info" in st.session_state:
            del st.session_state.video_info

    safe_mode = st.sidebar.checkbox("🛡️ Safe Mode (No Merging)", help="Use this if download fails. Downloads single file (max 720p) without using ffmpeg.")
    
    url = st.text_input("YouTube URL", placeholder="https://www.youtube.com/watch?v=...")

    if url:
        if "video_info" not in st.session_state or st.session_state.url != url:
            with st.spinner("Fetching video information..."):
                info = fetch_video_info(url, client_type)
                if info:
                    st.session_state.video_info = info
                    st.session_state.url = url
                else:
                    if "video_info" in st.session_state:
                        del st.session_state.video_info

    if "video_info" in st.session_state:
        info = st.session_state.video_info
        st.subheader(info.get('title', 'Unknown Title'))
        st.image(info.get('thumbnail'), width=300)

        formats = info.get('formats', [])
        available_heights = set()
        for f in formats:
            if f.get('vcodec') != 'none' and f.get('height'):
                available_heights.add(f['height'])
        
        if not available_heights:
            st.error("No suitable video formats found.")
            return

        sorted_heights = sorted(list(available_heights), reverse=True)
        
        if safe_mode:
            st.warning("🛡️ Safe Mode enabled. Resolution selection is disabled. Best single file will be downloaded.")
            resolution = "best"
        else:
            resolution = st.selectbox("Select Resolution", sorted_heights, format_func=lambda x: f"{x}p")

        if st.button("Download Video"):
            logger = MyLogger()
            with st.spinner(f"Downloading {resolution} video..."):
                # Use system temp dir and Video ID for safe filename
                video_id = info.get('id', 'video')
                temp_dir = tempfile.gettempdir()
                temp_filename = os.path.join(temp_dir, f"{video_id}_{resolution}.mp4")
                
                # Download options
                ydl_opts = {
                    'merge_output_format': 'mp4',
                    'outtmpl': temp_filename,
                    'quiet': False,
                    'no_warnings': False,
                    'verbose': True,
                    'nocheckcertificate': True,
                    'logger': logger,
                    'hls_prefer_native': True, 
                    'cache_dir': CACHE_DIR,
                }

                if client_type != 'default':
                    ydl_opts['extractor_args'] = {'youtube': {'player_client': [client_type]}}

                if safe_mode:
                    ydl_opts['format'] = 'best[ext=mp4]/best'
                else:
                    ydl_opts['format'] = f'bestvideo[height={resolution}]+bestaudio/best[height={resolution}]'
                
                try:
                    # Clean up if exists
                    if os.path.exists(temp_filename):
                        os.remove(temp_filename)

                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        ydl.download([url])
                    
                    # Log display (Success)
                    with st.expander("Show Download Logs (for debugging)"):
                        st.code("\n".join(logger.logs))

                    if os.path.exists(temp_filename):
                        st.session_state.downloaded_file = temp_filename
                        st.session_state.final_filename = f"{info['title']}.mp4" 
                        st.success("Video processed successfully!")
                    else:
                        st.error("Download failed: File not created.")

                except Exception as e:
                    st.error(f"Download failed: {e}")
                    
                    # Log display (Failure)
                    with st.expander("Show specific error logs"):
                        st.code("\n".join(logger.logs))

        if "downloaded_file" in st.session_state and os.path.exists(st.session_state.downloaded_file):
            file_path = st.session_state.downloaded_file
            display_name = st.session_state.get('final_filename', 'video.mp4')
            
            # Sanitize display name for browser
            display_name = "".join([c for c in display_name if c.isalpha() or c.isdigit() or c in ' ._-']).rstrip()
            if not display_name.endswith('.mp4'): display_name += '.mp4'

            with open(file_path, "rb") as file:
                st.download_button(
                    label="⬇️ Save to Device",
                    data=file,
                    file_name=display_name,
                    mime="video/mp4"
                )
    
    st.markdown("---")
    st.caption(f"yt-dlp version: {yt_dlp.version.__version__}")

if __name__ == "__main__":
    main()
