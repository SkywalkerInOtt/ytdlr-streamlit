import streamlit as st
import yt_dlp
import os
import shutil
import tempfile

from utils.drive import upload_file_to_drive, DEFAULT_FOLDER_ID
from utils.media import process_vocal_removal, mute_video, loop_video, clip_video, replace_audio, mix_audio, image_to_video

def main():
    st.set_page_config(page_title="ytdlr", page_icon="🎥")
    st.title("🎥 YouTube Downloader & Vocal Remover")
    
    # Check dependencies
    if not shutil.which("ffmpeg"):
        st.warning("⚠️ `ffmpeg` not found. Video processing will be limited.")

    if "processed_files" not in st.session_state:
        st.session_state.processed_files = {}

    tab1, tab2, tab3 = st.tabs(["🎥 via YouTube", "📤 via Upload", "🛠️ Tools"])

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
                c1, c2, c3, c4 = st.columns(4)
                remove_vocals_yt = c1.checkbox("🎵 Remove Vocals", key="yt_remove_vocals")
                mute_video_yt = c2.checkbox("🔇 Mute Video", key="yt_mute_video")
                loop_video_yt = c3.checkbox("🔄 Loop Video", key="yt_loop_video")
                clip_video_yt = c4.checkbox("✂️ Clip Video", key="yt_clip_video")
                
                target_duration_yt = "1m"
                clip_start_yt = "0s"
                clip_duration_yt = "10s"

                if loop_video_yt:
                    target_duration_yt = st.text_input("Loop Target Duration", value="1m", key="yt_loop_dur")
                if clip_video_yt:
                    cc1, cc2 = st.columns(2)
                    clip_start_yt = cc1.text_input("Start Time (e.g. 10s)", value="0s", key="yt_clip_start")
                    clip_duration_yt = cc2.text_input("Clip Duration (Empty = End)", value="", key="yt_clip_dur")
                
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
                                
                                if instrumentals:
                                    if 'mp4' in instrumentals:
                                        st.success(f"✅ Created Karaoke Video")
                                        st.session_state.processed_files['instrumental_mp4'] = instrumentals['mp4']
                                    if 'vocals_mp3' in instrumentals:
                                        st.success(f"✅ Created Isolated Vocals")
                                        st.session_state.processed_files['vocals_mp3'] = instrumentals['vocals_mp3']
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
                            
                            if clip_video_yt:
                                with st.spinner(f"Clipping video ({clip_duration_yt} from {clip_start_yt})..."):
                                    clipped_file = clip_video(output_filename, clip_start_yt, clip_duration_yt)
                                    if clipped_file:
                                        st.success("✅ Created Clipped Video")
                                        st.session_state.processed_files['clipped_mp4'] = clipped_file
                                    else:
                                        st.error("❌ Failed to clip video.")

                        except Exception as e:
                            st.error(f"Failed: {e}")

    # --- TAB 2: Upload ---
    with tab2:
        uploaded_file = st.file_uploader("Upload a video file", type=["mp4", "mov", "avi", "mkv"])
        
        if uploaded_file:
            # Show video details
            st.video(uploaded_file)
            
            # Options
            c1, c2, c3, c4 = st.columns(4)
            remove_vocals_up = c1.checkbox("🎵 Remove Vocals", value=True, key="up_remove_vocals")
            mute_video_up = c2.checkbox("🔇 Mute Video", value=False, key="up_mute_video")
            loop_video_up = c3.checkbox("🔄 Loop Video", value=False, key="up_loop_video")
            clip_video_up = c4.checkbox("✂️ Clip Video", value=False, key="up_clip_video")
            
            target_duration_up = "1m"
            clip_start_up = "0s"
            clip_duration_up = "10s"

            if loop_video_up:
                target_duration_up = st.text_input("Loop Duration", value="1m", key="up_loop_dur")
            if clip_video_up:
                cc1, cc2 = st.columns(2)
                clip_start_up = cc1.text_input("Start Time", value="0s", key="up_clip_start")
                clip_duration_up = cc2.text_input("Clip Duration (Empty = End)", value="", key="up_clip_dur")
            
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
                                if 'vocals_mp3' in instrumentals:
                                    st.success(f"✅ Created Isolated Vocals")
                                    st.session_state.processed_files['vocals_mp3'] = instrumentals['vocals_mp3']
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
                        
                        if clip_video_up:
                            with st.spinner(f"Clipping video ({clip_duration_up} from {clip_start_up})..."):
                                clipped_file = clip_video(safe_filename, clip_start_up, clip_duration_up)
                                if clipped_file:
                                    st.success("✅ Created Clipped Video")
                                    st.session_state.processed_files['clipped_mp4'] = clipped_file
                                else:
                                    st.error("❌ Failed to clip video.")
                                
                    except Exception as e:
                        st.error(f"Error processing upload: {e}")

    # --- TAB 3: Tools (Audio Replacement) ---
    with tab3:
        st.header("🎵 Replace Video Audio")
        st.info("Upload a video and an audio file to merge them.")
        
        col1, col2 = st.columns(2)
        with col1:
            tool_video = st.file_uploader("1. Upload Video or Image", type=["mp4", "mov", "avi", "mkv", "jpg", "jpeg", "png"], key="tool_vid")
        with col2:
            tool_audio = st.file_uploader("2. Upload Audio", type=["mp3", "wav", "m4a"], key="tool_aud")
            
        if tool_video and tool_audio:
            is_image = tool_video.type.startswith('image')
            
            modes = []
            if is_image:
                 modes = ["Image to Video"]
            else:
                 modes = ["Replace Audio", "Mix Audio"]
            
            mode = st.radio("Mode", modes, horizontal=True)
            
            vol_video = 1.0
            vol_audio = 1.0
            
            if mode == "Mix Audio":
                c1, c2 = st.columns(2)
                vol_video = c1.slider("Original Video Volume", 0.0, 2.0, 1.0)
                vol_audio = c2.slider("Added Audio Volume", 0.0, 2.0, 1.0)
            
            if mode == "Image to Video":
                st.info("Creating a 1080p video from this image.")
                st.image(tool_video, width=300)

            if st.button(f"🔄 {mode}"):
                with st.spinner("Processing..."):
                    try:
                        # Save files
                        v_ext = os.path.splitext(tool_video.name)[1]
                        a_ext = os.path.splitext(tool_audio.name)[1]
                        v_name = f"temp_vid_{tool_video.name}"
                        a_name = f"temp_aud_{tool_audio.name}"
                        
                        with open(v_name, "wb") as f: f.write(tool_video.getbuffer())
                        with open(a_name, "wb") as f: f.write(tool_audio.getbuffer())
                        
                        output_path = f"processed_{os.path.splitext(tool_video.name)[0]}.mp4"
                        result = None
                        key_name = ""
                        
                        if mode == "Replace Audio":
                             result = replace_audio(v_name, a_name, output_path)
                             key_name = 'replaced_audio_mp4'
                        elif mode == "Mix Audio":
                             result = mix_audio(v_name, a_name, output_path, vol_video, vol_audio)
                             key_name = 'mixed_audio_mp4'
                        elif mode == "Image to Video":
                             result = image_to_video(v_name, a_name, output_path)
                             key_name = 'image_video_mp4'
                        
                        if result and os.path.exists(result):
                            st.success("✅ Success!")
                            # Initialize if needed
                            if "processed_files" not in st.session_state:
                                st.session_state.processed_files = {}
                            st.session_state.processed_files[key_name] = result
                            
                            # Clean up temps
                            os.remove(v_name)
                            os.remove(a_name)
                        else:
                            st.error(f"Failed to process ({mode}).")
                    except Exception as e:
                        st.error(f"Error: {e}")

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
                        elif key == 'vocals_mp3': label = "Isolated Vocals"
                        elif key == 'muted_mp4': label = "Muted Video"
                        elif key == 'looped_mp4': label = "Looped Video"
                        elif key == 'clipped_mp4': label = "Clipped Video"
                        elif key == 'replaced_audio_mp4': label = "Video with New Audio"
                        elif key == 'mixed_audio_mp4': label = "Video with Mixed Audio"
                        elif key == 'image_video_mp4': label = "Video from Image"
                        
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
        
        if 'vocals_mp3' in files and os.path.exists(files['vocals_mp3']):
            if st.checkbox("Isolated Vocals", value=False): files_to_upload.append(files['vocals_mp3'])
        
        if 'muted_mp4' in files and os.path.exists(files['muted_mp4']):
            if st.checkbox("Muted Video", value=True): files_to_upload.append(files['muted_mp4'])
            
        if 'looped_mp4' in files and os.path.exists(files['looped_mp4']):
            if st.checkbox("Looped Video", value=True): files_to_upload.append(files['looped_mp4'])

        if 'clipped_mp4' in files and os.path.exists(files['clipped_mp4']):
            if st.checkbox("Clipped Video", value=True): files_to_upload.append(files['clipped_mp4'])

        if 'replaced_audio_mp4' in files and os.path.exists(files['replaced_audio_mp4']):
            if st.checkbox("Video with New Audio", value=True): files_to_upload.append(files['replaced_audio_mp4'])

        if 'mixed_audio_mp4' in files and os.path.exists(files['mixed_audio_mp4']):
            if st.checkbox("Video with Mixed Audio", value=True): files_to_upload.append(files['mixed_audio_mp4'])

        if 'image_video_mp4' in files and os.path.exists(files['image_video_mp4']):
            if st.checkbox("Video from Image", value=True): files_to_upload.append(files['image_video_mp4'])
            
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
