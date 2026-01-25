import os
import shutil
import subprocess

def check_ffmpeg_installed():
    """Checks if ffmpeg is available in the system path."""
    return shutil.which("ffmpeg") is not None

def process_vocal_removal(input_path, progress_callback=None):
    """
    Removes vocals from the input file using Demucs and merges the result.
    
    Args:
        input_path (str): Path to the input video/audio file.
        progress_callback (func, optional): Callback for status updates (msg: str).
        
    Returns:
        dict: A dictionary containing paths to 'mp3' and 'mp4' instrumental files, or None on failure.
    """
    def log(msg):
        if progress_callback:
            progress_callback(msg)
        else:
            print(msg)

    if not os.path.exists(input_path):
        log(f"❌ Error: File '{input_path}' not found.")
        return None
        
    log(f"🎤 Separating vocals for: {input_path} (this may take a few minutes)...")
    
    try:
        # Run Demucs
        subprocess.run(["demucs", "--mp3", "--two-stems=vocals", "-n", "htdemucs", input_path], check=True)
        
        filename_no_ext = os.path.splitext(os.path.basename(input_path))[0]
        demucs_out_dir = os.path.join("separated", "htdemucs", filename_no_ext)
        
        # Fallback search if directory name is truncated or slightly different
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
            log(f"✅ Created Instrumental Audio: {mp3_file}")
            created_files['mp3'] = mp3_file
            
            # 2. Instrumental MP4
            if check_ffmpeg_installed():
                log("🎥 Merging instrumental audio with video...")
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
                    log(f"✅ Created Karaoke Video: {mp4_file}")
                    created_files['mp4'] = mp4_file
            else:
                log("⚠️ FFmpeg not found. Skipping video merge.")
            
            return created_files
        else:
            log("❌ Separation failed: Output not found.")
            return None
    except Exception as e:
        log(f"❌ Error removing vocals: {e}")
        return None
