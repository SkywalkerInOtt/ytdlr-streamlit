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
        vocals_path = os.path.join(demucs_out_dir, "vocals.mp3")
        created_files = {}

        if os.path.exists(no_vocals_path):
            # 1. Instrumental MP3
            mp3_file = f"{filename_no_ext}_instrumental.mp3"
            shutil.move(no_vocals_path, mp3_file)
            log(f"✅ Created Instrumental Audio: {mp3_file}")
            created_files['mp3'] = mp3_file

            # 2. Isolated Vocals MP3
            if os.path.exists(vocals_path):
                vocals_mp3_file = f"{filename_no_ext}_vocals.mp3"
                shutil.move(vocals_path, vocals_mp3_file)
                log(f"✅ Created Isolated Vocals: {vocals_mp3_file}")
                created_files['vocals_mp3'] = vocals_mp3_file
            
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

def mute_video(input_path, output_path=None):
    """
    Removes audio from the video file using ffmpeg.
    
    Args:
        input_path (str): Path to input video.
        output_path (str, optional): Custom output path. Defaults to *_muted.mp4
        
    Returns:
        str: Path to the muted video, or None if failed.
    """
    if not check_ffmpeg_installed():
        print("❌ Error: FFmpeg not installed.")
        return None
        
    if not os.path.exists(input_path):
        print(f"❌ Error: File '{input_path}' not found.")
        return None

    if not output_path:
        filename_no_ext = os.path.splitext(input_path)[0]
        output_path = f"{filename_no_ext}_muted.mp4"

    try:
        # ffmpeg -i input.mp4 -c copy -an output.mp4
        # -an: No Audio
        cmd = [
            "ffmpeg", "-y",
            "-i", input_path,
            "-c", "copy",
            "-an",
            output_path
        ]
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        if os.path.exists(output_path):
            return output_path
        return None
    except Exception as e:
        print(f"❌ Error muting video: {e}")
        return None

def get_video_duration(input_path):
    """
    Returns the duration of the video in seconds using ffprobe.
    """
    try:
        cmd = [
            "ffprobe", 
            "-v", "error", 
            "-show_entries", "format=duration", 
            "-of", "default=noprint_wrappers=1:nokey=1", 
            input_path
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return float(result.stdout.strip())
    except Exception as e:
        print(f"❌ Error getting duration: {e}")
        return None

def loop_video(input_path, target_duration_str):
    """
    Loops the input video until it reaches the target duration.
    
    Args:
        input_path (str): Path to input video.
        target_duration_str (str): Duration string (e.g., "1h", "30m", "10s", or plain seconds).
        
    Returns:
        str: Path to looped video or None.
    """
    if not check_ffmpeg_installed():
        print("❌ Error: FFmpeg/ffprobe not installed.")
        return None
        
    if not os.path.exists(input_path):
        print(f"❌ Error: File '{input_path}' not found.")
        return None

    # Parse duration
    total_seconds = 0
    try:
        s = target_duration_str.lower().strip()
        if s.endswith('h'):
            total_seconds = float(s[:-1]) * 3600
        elif s.endswith('m'):
            total_seconds = float(s[:-1]) * 60
        elif s.endswith('s'):
            total_seconds = float(s[:-1])
        else:
            total_seconds = float(s)
    except:
        print(f"❌ Invalid duration format: {target_duration_str}")
        return None
        
    filename_no_ext = os.path.splitext(input_path)[0]
    output_path = f"{filename_no_ext}_looped.mp4"
    
    current_duration = get_video_duration(input_path)
    if not current_duration:
        return None
        
    if current_duration >= total_seconds:
        print(f"⚠️ Video is already longer ({current_duration:.2f}s) than target ({total_seconds:.2f}s).")
        return input_path

    print(f"🔄 Looping video ({current_duration:.2f}s) to target {total_seconds}s...")

    try:
        # ffmpeg -stream_loop -1 -i input -t duration -c copy output
        cmd = [
            "ffmpeg", "-y",
            "-stream_loop", "-1",
            "-i", input_path,
            "-t", str(total_seconds),
            "-c", "copy",
            output_path
        ]
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        if os.path.exists(output_path):
            return output_path
        return None
    except Exception as e:
        print(f"❌ Error looping video: {e}")
        return None

def clip_video(input_path, start_time, duration=None):
    """
    Clips the input video from start_time.
    
    Args:
        input_path (str): Path to input video.
        start_time (str): Start time (e.g., "00:00:10", "10", "10s").
        duration (str, optional): Duration to keep. If None, clips to end.
        
    Returns:
        str: Path to clipped video or None.
    """
    if not check_ffmpeg_installed():
        print("❌ Error: FFmpeg not installed.")
        return None
        
    if not os.path.exists(input_path):
        print(f"❌ Error: File '{input_path}' not found.")
        return None
        
    filename_no_ext = os.path.splitext(input_path)[0]
    output_path = f"{filename_no_ext}_clipped.mp4"
    
    msg = f"✂️ Clipping video from {start_time}"
    if duration:
        msg += f" for {duration}"
    else:
        msg += " to the end"
    print(f"{msg}...")

    try:
        # ffmpeg -ss start -i input [-t duration] -c:v libx264 -c:a aac output
        # Re-encoding is required for accurate seeking (frame-perfect), 
        # as -c copy snaps to the nearest keyframe.
        cmd = [
            "ffmpeg", "-y",
            "-ss", str(start_time),
            "-i", input_path
        ]
        
        if duration:
            cmd.extend(["-t", str(duration)])
            
        cmd.extend([
            "-c:v", "libx264",
            "-preset", "fast",
            "-c:a", "aac",
            "-avoid_negative_ts", "make_zero",
            output_path
        ])
        
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        if os.path.exists(output_path):
            return output_path
        return None
    except Exception as e:
        print(f"❌ Error clipping video: {e}")
        return None

def replace_audio(video_path, audio_path, output_path=None):
    """
    Replaces the audio track of a video with the specified audio file.
    
    Args:
        video_path (str): Path to the input video.
        audio_path (str): Path to the new audio file.
        output_path (str, optional): Path for the output video.
        
    Returns:
        str: Path to the new video file, or None if failed.
    """
    if not check_ffmpeg_installed():
        print("❌ Error: FFmpeg not installed.")
        return None
        
    if not os.path.exists(video_path):
        print(f"❌ Error: Video file '{video_path}' not found.")
        return None
    if not os.path.exists(audio_path):
        print(f"❌ Error: Audio file '{audio_path}' not found.")
        return None
        
    filename_no_ext = os.path.splitext(video_path)[0]
    if not output_path:
        output_path = f"{filename_no_ext}_new_audio.mp4"
        
    print(f"🔄 Replacing audio in '{os.path.basename(video_path)}' with '{os.path.basename(audio_path)}'...")
    
    try:
        # ffmpeg -i video -i audio -c:v copy -c:a aac -map 0:v:0 -map 1:a:0 -shortest output
        cmd = [
            "ffmpeg", "-y",
            "-i", video_path,
            "-i", audio_path,
            "-c:v", "copy",
            "-c:a", "aac",
            "-map", "0:v:0",
            "-map", "1:a:0",
            "-shortest",
            output_path
        ]
        
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        if os.path.exists(output_path):
            print(f"✅ Created: {output_path}")
            return output_path
        return None
    except Exception as e:
        print(f"❌ Error replacing audio: {e}")
        return None

def mix_audio(video_path, audio_path, output_path=None, volume_video=1.0, volume_audio=1.0):
    """
    Mixes the audio from an audio file into the video, keeping the original video audio.
    
    Args:
        video_path (str): Path to the input video.
        audio_path (str): Path to the audio file to mix in.
        output_path (str, optional): Path for the output video.
        volume_video (float): Volume multiplier for original video audio (default 1.0).
        volume_audio (float): Volume multiplier for added audio (default 1.0).
        
    Returns:
        str: Path to the new video file, or None if failed.
    """
    if not check_ffmpeg_installed():
        print("❌ Error: FFmpeg not installed.")
        return None
        
    if not os.path.exists(video_path):
        print(f"❌ Error: Video file '{video_path}' not found.")
        return None
    if not os.path.exists(audio_path):
        print(f"❌ Error: Audio file '{audio_path}' not found.")
        return None
        
    filename_no_ext = os.path.splitext(video_path)[0]
    if not output_path:
        output_path = f"{filename_no_ext}_mixed_audio.mp4"
        
    print(f"🎛️ Mixing audio into '{os.path.basename(video_path)}'...")
    
    try:
        # ffmpeg -i video -i audio -filter_complex "[0:a]volume=V1[a1];[1:a]volume=V2[a2];[a1][a2]amix=inputs=2:duration=first:dropout_transition=2[a]" -map 0:v -map "[a]" -c:v copy -c:a aac -shortest output
        cmd = [
            "ffmpeg", "-y",
            "-i", video_path,
            "-i", audio_path,
            "-filter_complex", 
            f"[0:a]volume={volume_video}[a1];[1:a]volume={volume_audio}[a2];[a1][a2]amix=inputs=2:duration=first:dropout_transition=2[a]",
            "-map", "0:v",
            "-map", "[a]",
            "-c:v", "copy",
            "-c:a", "aac",
            "-shortest",
            output_path
        ]
        
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        if os.path.exists(output_path):
            print(f"✅ Created: {output_path}")
            return output_path
        return None
    except Exception as e:
        print(f"❌ Error mixing audio: {e}")
        return None

def image_to_video(image_path, audio_path, output_path=None):
    """
    Creates a 1080p video from a static image and an audio file.
    
    Args:
        image_path (str): Path to the input image.
        audio_path (str): Path to the audio file.
        output_path (str, optional): Path for the output video.
        
    Returns:
        str: Path to the new video file, or None if failed.
    """
    if not check_ffmpeg_installed():
        print("❌ Error: FFmpeg not installed.")
        return None
        
    if not os.path.exists(image_path):
        print(f"❌ Error: Image file '{image_path}' not found.")
        return None
    if not os.path.exists(audio_path):
        print(f"❌ Error: Audio file '{audio_path}' not found.")
        return None
        
    filename_no_ext = os.path.splitext(image_path)[0]
    if not output_path:
        output_path = f"{filename_no_ext}_video.mp4"
        
    print(f"🖼️ Creating video from '{os.path.basename(image_path)}' and '{os.path.basename(audio_path)}'...")
    
    try:
        # ffmpeg -loop 1 -i image -i audio -c:v libx264 -tune stillimage -c:a aac -b:a 192k -pix_fmt yuv420p -shortest -vf "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2" output
        cmd = [
            "ffmpeg", "-y",
            "-loop", "1",
            "-i", image_path,
            "-i", audio_path,
            "-c:v", "libx264",
            "-tune", "stillimage",
            "-c:a", "aac",
            "-b:a", "192k",
            "-pix_fmt", "yuv420p",
            "-shortest",
            "-vf", "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2",
            output_path
        ]
        
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        if os.path.exists(output_path):
            print(f"✅ Created: {output_path}")
            return output_path
        return None
    except Exception as e:
        print(f"❌ Error creating video from image: {e}")
        return None
