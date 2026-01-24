import yt_dlp
import sys

def main():
    print("🎥 YouTube Video Downloader")
    url = input("Enter YouTube Video Link: ").strip()
    
    if not url:
        print("Error: Empty URL")
        return

    print("\nFetching video information...")
    
    # Options for fetching metadata
    ydl_opts_info = {
        'quiet': True,
        'no_warnings': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts_info) as ydl:
            info = ydl.extract_info(url, download=False)
    except Exception as e:
        print(f"\nError: Could not fetch video info.\n{e}")
        return

    title = info.get('title', 'Unknown Title')
    print(f"\nTitle: {title}")

    # Extract available video heights
    formats = info.get('formats', [])
    available_heights = set()
    
    for f in formats:
        # Check for video stream (vcodec != none) and valid height
        if f.get('vcodec') != 'none' and f.get('height'):
            available_heights.add(f['height'])

    if not available_heights:
        print("No suitable video formats found.")
        return

    # Sort heights descending
    sorted_heights = sorted(list(available_heights), reverse=True)

    print("\nAvailable Resolutions:")
    for i, height in enumerate(sorted_heights):
        print(f"{i + 1}. {height}p")

    selection = input("\nChoose a resolution to download (number): ").strip()

    try:
        index = int(selection) - 1
        if index < 0 or index >= len(sorted_heights):
            print("Invalid selection.")
            return
        target_height = sorted_heights[index]
    except ValueError:
        print("Invalid input. Please enter a number.")
        return

    print(f"\nPreparing to download {target_height}p version in MP4 format...")

    # Options for downloading
    # Select best video with exact height + best audio, OR best pre-merged with exact height
    # Merge into mp4 container
    ydl_opts_download = {
        'format': f'bestvideo[height={target_height}]+bestaudio/best[height={target_height}]',
        'merge_output_format': 'mp4',
        'outtmpl': '%(title)s.%(ext)s',
        # Fallback if specific height construction fails (should be rare given we listed it)
        'ignoreerrors': True, 
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts_download) as ydl:
            ydl.download([url])
        print(f"\n✅ Download complete: {title}")
    except Exception as e:
        print(f"\n❌ Download failed: {e}")

if __name__ == "__main__":
    main()
