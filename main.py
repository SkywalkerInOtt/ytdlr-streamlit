import yt_dlp
import sys
import argparse
import os

from utils.drive import upload_file_to_drive, DEFAULT_FOLDER_ID
from utils.media import process_vocal_removal, mute_video, loop_video, clip_video, replace_audio, mix_audio, image_to_video

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
        # Filter for videos with height
        heights = sorted(list(set([f['height'] for f in formats if f.get('height')])), reverse=True)
        
        if len(heights) > 1:
            print("\nResolutions:")
            for i, h in enumerate(heights): print(f"{i+1}. {h}p")
            try:
                idx = int(input("\nChoose (number): ").strip()) - 1
                target_height = heights[idx]
            except:
                print("Invalid selection. Defaulting to best quality.")
        elif heights:
            print(f"\nResolution: {heights[0]}p")
            target_height = heights[0]
        else:
            print("\nAuto-selecting best quality (no specific resolutions found)...")
    else:
        print("Auto-selecting best quality (CLI mode)...")
    
    print(f"\nDownloading...")
    safe_title = "".join([c for c in title if c.isalpha() or c.isdigit() or c in ' ._-']).rstrip()
    if not safe_title: safe_title = "video"
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
    print("🎥 Video Downloader (Interactive Mode)")
    url = input("Enter Video Link: ").strip()
    if not url: return

    outfile = download_video(url, interactive=True)
    if not outfile: return
    
    # --- VOCAL REMOVAL ---
    instrumental_files = None
    if input("\n🎵 AI: Remove vocals (create karaoke)? (y/n): ").strip().lower() == 'y':
        instrumental_files = process_vocal_removal(outfile)

    # --- MUTE ---
    muted_file = None
    if input("\n🔇 Mute video (remove audio)? (y/n): ").strip().lower() == 'y':
        muted_file = mute_video(outfile)
        if muted_file: print(f"✅ Muted video created: {muted_file}")

    # --- LOOP ---
    looped_file = None
    if input("\n🔄 Loop video? (y/n): ").strip().lower() == 'y':
        duration = input("Target duration (e.g. 30s, 1m, 1h): ").strip()
        looped_file = loop_video(outfile, duration)
        if looped_file: print(f"✅ Looped video created: {looped_file}")
    
    # --- Clip ---
    clipped_file = None
    if input("\n✂️ Clip video? (y/n): ").strip().lower() == 'y':
        start = input("Start time (e.g. 10s): ").strip()
        duration = input("Duration (e.g. 5s) [Leave empty for end]: ").strip()
        if duration == "": duration = None
        clipped_file = clip_video(outfile, start, duration)
        if clipped_file: print(f"✅ Clipped video created: {clipped_file}")

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
            if 'vocals_mp3' in instrumental_files:
                if input(f"Upload Isolated Vocals ({instrumental_files['vocals_mp3']})? (y/n): ").strip().lower() == 'y':
                        upload_queue.append(instrumental_files['vocals_mp3'])
        
        if muted_file:
            if input(f"Upload Muted Video ({muted_file})? (y/n): ").strip().lower() == 'y':
                upload_queue.append(muted_file)

        if looped_file:
            if input(f"Upload Looped Video ({looped_file})? (y/n): ").strip().lower() == 'y':
                upload_queue.append(looped_file)

        if clipped_file:
            if input(f"Upload Clipped Video ({clipped_file})? (y/n): ").strip().lower() == 'y':
                upload_queue.append(clipped_file)
        
        print(f"\nUploading {len(upload_queue)} files...")
        for f in upload_queue:
            print(f"\n🚀 Uploading '{f}' to Google Drive...")
            link = upload_file_to_drive(f, target_folder)
            if link:
                print(f"✅ Upload Complete! 🔗 {link}")

def main():
    parser = argparse.ArgumentParser(description="ytdlr CLI - YouTube Downloader & Processor")
    
    parser.add_argument("--download", metavar="URL", help="Download video from URL (auto-selects best quality)")
    parser.add_argument("--instrumental", metavar="FILE", help="Remove vocals from an existing video/audio file")
    parser.add_argument("--mute", metavar="FILE", help="Mute (remove audio) from a video file")
    parser.add_argument("--loop", metavar="FILE", help="Loop a video file (requires --duration)")
    parser.add_argument("--clip", metavar="FILE", help="Clip a video file (requires --start and --duration)")
    parser.add_argument("--start", metavar="TIME", help="Start time for clip (e.g. '10s')")
    parser.add_argument("--duration", metavar="TIME", help="Target duration for loop or clip (e.g. '1h', '30m')")
    parser.add_argument("--replace-audio", metavar="VIDEO_FILE", help="Replace audio in a video file (requires --audio)")
    parser.add_argument("--mix-audio", metavar="VIDEO_FILE", help="Mix audio into a video file (requires --audio)")
    parser.add_argument("--image-to-video", metavar="IMAGE_FILE", help="Create a 1080p video from an image and audio (requires --audio)")
    parser.add_argument("--audio", metavar="AUDIO_FILE", help="Audio file to use for replacement, mixing, or video generation")
    parser.add_argument("--upload", metavar="FILE", help="Upload a file to Google Drive")
    parser.add_argument("--folder", metavar="ID", help="Google Drive Folder ID (for use with only --upload)")

    args = parser.parse_args()

    # If no arguments provided, run legacy interactive mode
    if not any(vars(args).values()):
        interactive_mode()
        return

    # 1. Download Mode
    if args.download:
        download_video(args.download, interactive=False)
        # Note: In pure flag mode, we don't return the filename to 'downloaded_file' for chaining 
        # because the user might just want to download. Chaining in flags is complex.
        # If they want chaining, they should use interactive mode or script it.

    # 2. Instrumental Mode
    if args.instrumental:
        process_vocal_removal(args.instrumental)

    # 3. Mute Mode
    if args.mute:
        muted = mute_video(args.mute)
        if muted: print(f"✅ Created: {muted}")

    # 4. Loop Mode
    if args.loop:
        if not args.duration:
            print("❌ Error: --loop requires --duration (e.g. --duration '1h')")
            return
        looped = loop_video(args.loop, args.duration)
        if looped: print(f"✅ Created: {looped}")

    # 5. Clip Mode
    if args.clip:
        if not args.start:
            print("❌ Error: --clip requires --start")
            return
        clipped = clip_video(args.clip, args.start, args.duration)
        if clipped: print(f"✅ Created: {clipped}")

    # 6. Replace Audio Mode
    if args.replace_audio:
        if not args.audio:
            print("❌ Error: --replace-audio requires --audio")
            return
        new_video = replace_audio(args.replace_audio, args.audio)
        if new_video: print(f"✅ Created: {new_video}")

    # 7. Mix Audio Mode
    if args.mix_audio:
        if not args.audio:
            print("❌ Error: --mix-audio requires --audio")
            return
        mixed_video = mix_audio(args.mix_audio, args.audio)
        if mixed_video: print(f"✅ Created: {mixed_video}")

    # 8. Image to Video Mode
    if args.image_to_video:
        if not args.audio:
            print("❌ Error: --image-to-video requires --audio")
            return
        video_from_image = image_to_video(args.image_to_video, args.audio)
        if video_from_image: print(f"✅ Created: {video_from_image}")

    # 3. Upload Mode
    if args.upload:
        print(f"\n🚀 Uploading '{args.upload}' to Google Drive...")
        link = upload_file_to_drive(args.upload, args.folder)
        if link:
            print(f"✅ Upload Complete! 🔗 {link}")

if __name__ == "__main__":
    main()
