import streamlit as st
import yt_dlp
import os
import shutil
import tempfile

from utils.drive import upload_file_to_drive, DEFAULT_FOLDER_ID
from utils.media import process_vocal_removal, mute_video, loop_video

def main():
    st.set_page_config(page_title="ytdlr", page_icon="🎥")
    st.title("🎥 YouTube Downloader & Vocal Remover")
    
    # Check dependencies
    if not shutil.which("ffmpeg"):
        st.warning("⚠️ `ffmpeg` not found. Video processing will be limited.")

    if "processed_files" not in st.session_state:
        st.session_state.processed_files = {}

    tab1, tab2 = st.tabs(["🎥 via YouTube", "📤 via Upload"])

    # --- TAB 1: Download URL ---
    with tab1:
        url = st.text_input("Video URL (YouTube, XiaoHongShu, etc.)")

        if url:
            if "url" not in st.session_state or st.session_state.url != url:
                st.session_state.url = url
                st.session_state.video_info = None
                # Don't clear processed_files here immediately if we want to persist across tabs, 
                # but typically a new URL means new context. Let's keep it specific to this flow.
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
                if info.get('thumbnail'):
                    st.image(info.get('thumbnail'), width=300)

                # Resolution Selection (Adaptive)
                formats = info.get('formats', [])
                # Filter for video-only or combined streams that have height info
                valid_formats = [f for f in formats if f.get('height')]
                heights = sorted(list(set([f['height'] for f in valid_formats])), reverse=True)
                
                resolution = None
                if len(heights) > 1:
                    resolution = st.selectbox("Select Resolution", heights, format_func=lambda x: f"{x}p")
                elif heights:
                    resolution = heights[0]
                    st.info(f"Resolution: {resolution}p")
                else:
                    st.info("Best available quality will be downloaded.")

                # Options
                c1, c2, c3 = st.columns(3)
                remove_vocals_yt = c1.checkbox("🎵 Remove Vocals", key="yt_remove_vocals")
                mute_video_yt = c2.checkbox("🔇 Mute Video", key="yt_mute_video")
                loop_video_yt = c3.checkbox("🔄 Loop Video", key="yt_loop_video")
                
                target_duration_yt = "1m"
                if loop_video_yt:
                    target_duration_yt = st.text_input("Target Duration (e.g., 30s, 1m, 1h)", value="1m", key="yt_duration")
                
                if st.button("Download & Process", key="yt_process"):
                    with st.spinner(f"Downloading..."):
                        safe_title = "".join([c for c in info.get('title', 'video') if c.isalpha() or c.isdigit() or c in ' ._-']).rstrip()
                        if not safe_title: safe_title = "video"
                        output_filename = f"{safe_title}.mp4"
                        
                        if resolution:
                            format_str = f'bestvideo[height={resolution}]+bestaudio/best[height={resolution}]'
                        else:
                            format_str = 'bestvideo+bestaudio/best'

                        ydl_opts_down = {
                            'format': format_str,
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
                            # Reset processed files for this new run
                            st.session_state.processed_files = {'original': output_filename}
                            
                            if remove_vocals_yt:
                                status_text = st.empty()
                                def progress_callback(msg):
                                    status_text.text(msg)
                                    
                                instrumentals = process_vocal_removal(output_filename, progress_callback=progress_callback)
                                
                                status_text.empty() # Clear status after done
                                
                                    if 'mp4' in instrumentals:
                                        st.success(f"✅ Created Karaoke Video")
                                        st.session_state.processed_files['instrumental_mp4'] = instrumentals['mp4']
                                else:
                                    st.error("❌ Vocal removal failed. See logs.")

                            if mute_video_yt:
                                with st.spinner("Muting video..."):
                                    muted_file = mute_video(output_filename)
                                    if muted_file:
                                        st.success(f"✅ Created Muted Video")
                                        st.session_state.processed_files['muted_mp4'] = muted_file
                                    else:
                                        st.error("❌ Failed to mute video.")
                            
                            if loop_video_yt:
                                with st.spinner(f"Looping video to {target_duration_yt}..."):
                                    looped_file = loop_video(output_filename, target_duration_yt)
                                    if looped_file:
                                        st.success(f"✅ Created Looped Video ({target_duration_yt})")
                                        st.session_state.processed_files['looped_mp4'] = looped_file
                                    else:
                                        st.error("❌ Failed to loop video.")

                        except Exception as e:
                            st.error(f"Failed: {e}")

    # --- TAB 2: Upload ---
    with tab2:
        uploaded_file = st.file_uploader("Upload a video file", type=["mp4", "mov", "avi", "mkv"])
        
        if uploaded_file:
            # Show video details
            st.video(uploaded_file)
            
            # Options
            c1, c2, c3 = st.columns(3)
            remove_vocals_up = c1.checkbox("🎵 Remove Vocals", value=True, key="up_remove_vocals")
            mute_video_up = c2.checkbox("🔇 Mute Video", value=False, key="up_mute_video")
            loop_video_up = c3.checkbox("🔄 Loop Video", value=False, key="up_loop_video")
            
            target_duration_up = "1m"
            if loop_video_up:
                target_duration_up = st.text_input("Target Duration (e.g., 30s, 1m, 1h)", value="1m", key="up_duration")
            
            if st.button("Process Uploaded Video", key="up_process"):
                # Save uploaded file to temp file or local dir
                with st.spinner("Processing uploaded file..."):
                    try:
                        # Use original filename
                        safe_filename = "".join([c for c in uploaded_file.name if c.isalpha() or c.isdigit() or c in ' ._-']).rstrip()
                        if not safe_filename: safe_filename = "uploaded_video.mp4"
                        
                        with open(safe_filename, "wb") as f:
                            f.write(uploaded_file.getbuffer())
                            
                        st.success(f"✅ Saved: {safe_filename}")
                        st.session_state.processed_files = {'original': safe_filename}
                        
                        if remove_vocals_up:
                            status_text = st.empty()
                            def progress_callback(msg):
                                status_text.text(msg)
                                
                            instrumentals = process_vocal_removal(safe_filename, progress_callback=progress_callback)
                            
                            status_text.empty()
                            
                            if instrumentals:
                                if 'mp3' in instrumentals:
                                    st.success(f"✅ Created Instrumental Audio")
                                    st.session_state.processed_files['instrumental_mp3'] = instrumentals['mp3']
                                if 'mp4' in instrumentals:
                                    st.success(f"✅ Created Karaoke Video")
                                    st.session_state.processed_files['instrumental_mp4'] = instrumentals['mp4']
                            else:
                                st.error("❌ Vocal removal failed. See logs.")
                        
                        if mute_video_up:
                            with st.spinner("Muting video..."):
                                muted_file = mute_video(safe_filename)
                                if muted_file:
                                    st.success(f"✅ Created Muted Video")
                                    st.session_state.processed_files['muted_mp4'] = muted_file
                                else:
                                    st.error("❌ Failed to mute video.")
                        
                        if loop_video_up:
                            with st.spinner(f"Looping video to {target_duration_up}..."):
                                looped_file = loop_video(safe_filename, target_duration_up)
                                if looped_file:
                                    st.success(f"✅ Created Looped Video ({target_duration_up})")
                                    st.session_state.processed_files['looped_mp4'] = looped_file
                                else:
                                    st.error("❌ Failed to loop video.")
                                
                    except Exception as e:
                        st.error(f"Error processing upload: {e}")

    # --- RESULT & UPLOAD AREA ---
    # This area displays results from EITHER tab, as long as st.session_state.processed_files is populated.
    if "processed_files" in st.session_state and st.session_state.processed_files:
        files = st.session_state.processed_files
        
        st.divider()
        st.subheader("📂 Files Ready")
        
        # Download Buttons
        cols = st.columns(len(files))
        for i, (key, path) in enumerate(files.items()):
            with cols[i]:
                # Verify file exists before showing download button (in case of overwrite/cleanup issues)
                if os.path.exists(path):
                    with open(path, "rb") as f:
                        label = "Original"
                        if key == 'instrumental_mp4': label = "Karaoke Video"
                        elif key == 'instrumental_mp3': label = "Backing Track"
                        elif key == 'muted_mp4': label = "Muted Video"
                        elif key == 'looped_mp4': label = "Looped Video"
                        
                        st.download_button(label=f"⬇️ {label}", data=f, file_name=os.path.basename(path))
                else:
                    st.warning(f"File not found: {path}")

        st.divider()
        st.subheader("☁️ Upload to Google Drive")
        
        folder_id = st.text_input("Folder ID", value=DEFAULT_FOLDER_ID)
        
        # Checkboxes for what to upload
        files_to_upload = []
        c1, c2, c3 = st.columns(3)
        if 'original' in files and os.path.exists(files['original']):
            if c1.checkbox("Original Video", value=True): files_to_upload.append(files['original'])
        if 'instrumental_mp4' in files and os.path.exists(files['instrumental_mp4']):
            if c2.checkbox("Karaoke Video", value=True): files_to_upload.append(files['instrumental_mp4'])
        if 'instrumental_mp3' in files and os.path.exists(files['instrumental_mp3']):
            if c3.checkbox("Backing Track", value=False): files_to_upload.append(files['instrumental_mp3'])
        
        if 'muted_mp4' in files and os.path.exists(files['muted_mp4']):
            if st.checkbox("Muted Video", value=True): files_to_upload.append(files['muted_mp4'])
            
        if 'looped_mp4' in files and os.path.exists(files['looped_mp4']):
            if st.checkbox("Looped Video", value=True): files_to_upload.append(files['looped_mp4'])
            
        if st.button("🚀 Upload Selected"):
            if not files_to_upload:
                st.warning("No files selected.")
            else:
                for f_path in files_to_upload:
                    with st.spinner(f"Uploading {os.path.basename(f_path)}..."):
                        link, error = upload_file_to_drive(f_path, folder_id)
                        if link:
                            st.success(f"Uploaded! [Link]({link})")
                        else:
                            st.error(f"Failed to upload {os.path.basename(f_path)}: {error}")

if __name__ == "__main__":
    main()
