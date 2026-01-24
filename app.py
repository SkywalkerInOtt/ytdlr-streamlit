import streamlit as st
import yt_dlp
import os
import time

def fetch_video_info(url, cookies_file=None):
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'nocheckcertificate': True,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    }
    if cookies_file:
         ydl_opts['cookiefile'] = cookies_file

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
        return info
    except Exception as e:
        st.error(f"Error fetching video info: {e}")
        return None

import shutil
import tempfile

def main():
    st.set_page_config(page_title="ytdlr", page_icon="🎥")
    
    st.title("🎥 YouTube Downloader")
    
    if not shutil.which("ffmpeg"):
        st.error("⚠️ `ffmpeg` is not installed or not in PATH. Merging video+audio will fail. Please install ffmpeg.")

    st.markdown("Enter a YouTube URL below to download the video in MP4 format.")

    st.sidebar.header("⚙️ Settings")
    st.sidebar.info("💡 **Tip**: If you see a 403 error, uploading cookies is the most reliable fix.")
    st.sidebar.markdown("[Get cookies.txt LOCALLY extension](https://chrome.google.com/webstore/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc)")
    
    cookies_file = st.sidebar.file_uploader("Upload cookies.txt", type=["txt"])
    
    cookies_path = None
    if cookies_file:
        # Save cookies to a temporary file in /tmp
        temp_dir = tempfile.gettempdir()
        cookies_path = os.path.join(temp_dir, "cookies.txt")
        with open(cookies_path, "wb") as f:
            f.write(cookies_file.getbuffer())
        st.sidebar.success("Cookies loaded!")

    url = st.text_input("YouTube URL", placeholder="https://www.youtube.com/watch?v=...")

    if url:
        if "video_info" not in st.session_state or st.session_state.url != url:
            with st.spinner("Fetching video information..."):
                info = fetch_video_info(url, cookies_path)
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
        resolution = st.selectbox("Select Resolution", sorted_heights, format_func=lambda x: f"{x}p")

        if st.button("Download Video"):
            with st.spinner(f"Downloading {resolution}p video..."):
                # Use system temp dir and Video ID for safe filename
                video_id = info.get('id', 'video')
                temp_dir = tempfile.gettempdir()
                temp_filename = os.path.join(temp_dir, f"{video_id}_{resolution}.mp4")
                
                # Download options
                ydl_opts = {
                    'format': f'bestvideo[height={resolution}]+bestaudio/best[height={resolution}]',
                    'merge_output_format': 'mp4',
                    'outtmpl': temp_filename,
                    'quiet': False,
                    'no_warnings': False,
                    'verbose': True,
                    'nocheckcertificate': True,
                    'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'hls_prefer_native': True, 
                }
                
                if cookies_path:
                    ydl_opts['cookiefile'] = cookies_path

                try:
                    # Clean up if exists
                    if os.path.exists(temp_filename):
                        os.remove(temp_filename)

                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        ydl.download([url])
                    
                    if os.path.exists(temp_filename):
                        st.session_state.downloaded_file = temp_filename
                        st.session_state.final_filename = f"{info['title']}.mp4" 
                        st.success("Video processed successfully!")
                    else:
                        st.error("Download failed: File not created. Check logs.")

                except Exception as e:
                    st.error(f"Download failed: {e}")

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
