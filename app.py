import streamlit as st
import yt_dlp
import os
import time

def fetch_video_info(url):
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
        return info
    except Exception as e:
        st.error(f"Error fetching video info: {e}")
        return None

def main():
    st.set_page_config(page_title="ytdlr", page_icon="🎥")
    
    st.title("🎥 YouTube Downloader")
    st.markdown("Enter a YouTube URL below to download the video in MP4 format.")

    url = st.text_input("YouTube URL", placeholder="https://www.youtube.com/watch?v=...")

    if url:
        if "video_info" not in st.session_state or st.session_state.url != url:
            with st.spinner("Fetching video information..."):
                info = fetch_video_info(url)
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
                # Use a unique filename to avoid collisions
                safe_title = "".join([c for c in info['title'] if c.isalpha() or c.isdigit() or c==' ']).rstrip()
                filename = f"{safe_title}_{resolution}p.mp4"
                
                # Download options
                ydl_opts = {
                    'format': f'bestvideo[height={resolution}]+bestaudio/best[height={resolution}]',
                    'merge_output_format': 'mp4',
                    'outtmpl': filename,
                    'quiet': True,
                }

                try:
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        ydl.download([url])
                    
                    if os.path.exists(filename):
                        st.session_state.downloaded_file = filename
                        st.success("Video processed successfully!")
                    else:
                        st.error("Download failed: File not created.")

                except Exception as e:
                    st.error(f"Download failed: {e}")

        if "downloaded_file" in st.session_state and os.path.exists(st.session_state.downloaded_file):
            filename = st.session_state.downloaded_file
            with open(filename, "rb") as file:
                st.download_button(
                    label="⬇️ Save to Device",
                    data=file,
                    file_name=filename,
                    mime="video/mp4"
                )

if __name__ == "__main__":
    main()
