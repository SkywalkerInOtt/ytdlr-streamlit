import yt_dlp
import sys
import argparse
import os

from utils.drive import upload_file_to_drive, DEFAULT_FOLDER_ID
from utils.media import process_vocal_removal

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
        heights = sorted(list(set([f['height'] for f in formats if f.get('vcodec')!='none' and f.get('height')])), reverse=True)
        print("\nResolutions:")
        for i, h in enumerate(heights): print(f"{i+1}. {h}p")
        try:
            idx = int(input("\nChoose (number): ").strip()) - 1
            target_height = heights[idx]
        except:
            print("Invalid selection."); return None
    else:
        print("Auto-selecting best quality (CLI mode)...")
    
    print(f"\nDownloading...")
    safe_title = "".join([c for c in title if c.isalpha() or c.isdigit() or c in ' ._-']).rstrip()
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
    print("🎥 YouTube Video Downloader (Interactive Mode)")
    url = input("Enter YouTube Video Link: ").strip()
    if not url: return

    outfile = download_video(url, interactive=True)
    if not outfile: return
    
    # --- VOCAL REMOVAL ---
    instrumental_files = None
    if input("\n🎵 AI: Remove vocals (create karaoke)? (y/n): ").strip().lower() == 'y':
        instrumental_files = process_vocal_removal(outfile)

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
    parser.add_argument("--upload", metavar="FILE", help="Upload a file to Google Drive")
    parser.add_argument("--folder", metavar="ID", help="Google Drive Folder ID (for use with --upload)")

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

    # 3. Upload Mode
    if args.upload:
        print(f"\n🚀 Uploading '{args.upload}' to Google Drive...")
        link = upload_file_to_drive(args.upload, args.folder)
        if link:
            print(f"✅ Upload Complete! 🔗 {link}")

if __name__ == "__main__":
    main()
