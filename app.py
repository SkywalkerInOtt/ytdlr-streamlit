import streamlit as st
import yt_dlp
import os
import shutil

from utils.drive import upload_file_to_drive, DEFAULT_FOLDER_ID
from utils.media import process_vocal_removal

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
                            status_text = st.empty()
                            def progress_callback(msg):
                                status_text.text(msg)
                                
                            instrumentals = process_vocal_removal(output_filename, progress_callback=progress_callback)
                            
                            status_text.empty() # Clear status after done
                            
                            if instrumentals:
                                if 'mp3' in instrumentals:
                                    st.success(f"✅ Created Instrumental Audio")
                                    st.session_state.processed_files['instrumental_mp3'] = instrumentals['mp3']
                                if 'mp4' in instrumentals:
                                    st.success(f"✅ Created Karaoke Video")
                                    st.session_state.processed_files['instrumental_mp4'] = instrumentals['mp4']
                            else:
                                st.error("❌ Vocal removal failed. See logs.")

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
