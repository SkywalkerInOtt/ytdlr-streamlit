# 🎥 ytdlr - YouTube Downloader

A simple and efficient YouTube video downloader built with **Streamlit** and **yt-dlp**.

## ✨ Features

- 📥 **Download Videos**: Fetch videos from YouTube, XiaoHongShu, and other platforms supported by `yt-dlp`.
- 🎵 **Audio/Video Merge**: Automatically merges high-quality video and audio streams using `ffmpeg`.
- 🎤 **Isolate Vocals**: Remove background noise, music, and instruments to keep only the vocals (creates `*_vocals.mp3`).
- 🎶 **Remove Vocals**: Create karaoke versions by removing the vocal track (creates `*_instrumental.mp3/mp4`).
- 🔇 **Mute Video**: Remove all audio from a video file.
- 🔄 **Loop Video**: Loop a video to a specific duration (e.g., 1 hour for long background videos).
- 🎛️ **Replace/Mix Audio**: Replace video audio or mix new audio (e.g., background music) into a video.
- �️ **Image to Video**: Create a 1080p video from a static image and an audio file.
- 🎞️ **Images to Video (Slideshow)**: Create a video slideshow from a folder of images.
- �🚀 **Streamlit Interface**: Clean and easy-to-use web interface.
- 💻 **CLI Mode**: Terminal-based downloader for quick local use.
- ☁️ **Google Drive Upload**: (CLI only) Automatically upload downloaded videos to your Google Drive.

### 🔗 Supported URL Examples
- **YouTube**: `https://www.youtube.com/watch?v=dQw4w9WgXcQ`
- **XiaoHongShu (Web)**: `https://www.xiaohongshu.com/explore/675fa24f0000000001029bd5`
- **XiaoHongShu (Share)**: `http://xhslink.com/U59H0v`

> [!NOTE]
> XiaoHongShu support depends on `yt-dlp`. If you see "No video formats found", it means `yt-dlp` cannot currently extract the video. Support may break or be restored with `yt-dlp` updates.


---

## 🛠️ Usage Options

### Option 1: Web Interface (Streamlit)

Best for visual selection and easy formatting.

1. **Run the app:**
   ```bash
   uv run python -m streamlit run app.py
   ```
   *(Or `streamlit run app.py` if installed manually)*

2. Open `http://localhost:8501`.
3. **Download via YouTube**: Paste a URL, select quality, and download.
4. **Upload Video**: Switch to the "via Upload" tab to process your own video files.

### ☁️ Setup for Streamlit Cloud

To enable Google Drive uploads on Streamlit Cloud, you need to configure app secrets:

1. **Generate Token Locally**:
   Run the included helper script in your local environment:
   ```bash
   uv run get_drive_token.py
   ```
   Follow the browser prompt to authenticate.

2. **Configure Secrets**:
   - Copy the output starting with `[google_drive]`.
   - Go to your Streamlit Cloud Dashboard.
   - Click **Manage App** -> **Settings** -> **Secrets**.
   - Paste the configuration and save.
   
   *Note: Locally, the app will fall back to using `token.pickle` if secrets are not found.*

### Option 2: Command Line (CLI)

Best for automation and **uploading to Google Drive**.

1. **Interactive Mode (Wizard):**
   ```bash
   uv run main.py
   ```

2. **Automated Mode (Flags):**
   - **Download Only:**
     ```bash
     uv run main.py --download "https://youtu.be/..."
     ```
   - **Remove Vocals (Create Karaoke):**
     ```bash
     uv run main.py --instrumental "my_video.mp4"
     ```
     *(Generates both MP3 and MP4 instrumental versions)*
   - **Mute Video (Remove Audio):**
     ```bash
     uv run main.py --mute "my_video.mp4"
     ```
   - **Loop Video:**
     ```bash
     uv run main.py --loop "my_video.mp4" --duration "1h"
     ```
   - **Clip Video:**
     ```bash
     uv run main.py --clip "my_video.mp4" --start "20s"
     ```
     *(Duration is optional. If omitted, clips to the end)*
   - **Upload to Google Drive:**
     ```bash
     uv run main.py --upload "my_video.mp4"
     ```
     *(Optional: Specify folder with `--folder "FOLDER_ID"`)*

### Option 2: Command Line (CLI)

Best for quick downloads or batch jobs.

1. **Standard Download:**
   ```bash
   uv run main.py --download "URL"
   ```

2. **Isolate Vocals (Remove Noise):**
   ```bash
   uv run main.py --instrumental "video.mp4"
   ```
   *This will create both `video_instrumental.mp3` (music only) and `video_vocals.mp3` (speech/vocals only).*

3. **Replace or Mix Audio:**
   - **Replace**:
     ```bash
     uv run main.py --replace-audio "video.mp4" --audio "new_audio.mp3"
     ```
   - **Mix (Merge)**:
     ```bash
     uv run main.py --mix-audio "video.mp4" --audio "background.mp3"
     ```

4. **Image to Video:**
   - Create a 1080p video from an image and audio:
     ```bash
     uv run main.py --image-to-video "image.jpg" --audio "audio.mp3"
     ```

5. **Slideshow (shows all images once):**
   - Create a slideshow with Ken Burns effects:
     ```bash
     uv run main.py --slideshow "./my_images" --audio "music.mp3" --duration-per-image 3
     ```
   - Supports: JPG, JPEG, PNG, BMP, HEIC

6. **Images to Video (loops to match audio):**
   - Create a video that loops images to fill the entire audio duration:
     ```bash
     uv run main.py --images-to-video "./my_images" --audio "music.mp3" --duration-per-image 3
     ```
   - Supports: JPG, JPEG, PNG, BMP, HEIC

7. **Google Drive Upload Setup:**
   - To use the upload feature, you need a `client_secrets.json` file in this folder.
   - Download "OAuth 2.0 Client IDs" (Desktop App) JSON from [Google Cloud Console](https://console.cloud.google.com/).
   - Rename it to `client_secrets.json`.
   - On first run, a browser window will open to authorize access.

---

## 📦 Building a Standalone App

You can package the CLI version into a single executable file (Mac app / Windows .exe) using **PyInstaller**.

1. **Install PyInstaller:**
   ```bash
   uv add pyinstaller
   ```
   *(Or `pip install pyinstaller`)*

2. **Build the App:**
   ```bash
   uv run python -m PyInstaller --onefile --name "ytdlr" main.py
   ```
   *(On Mac, this creates a Unix executable. on Windows, an `.exe`)*

3. **Run your App:**
   - The verified file will be in the `dist/` folder.
   - You can drag this file anywhere and run it without needing Python installed!
   - **Note:** Keep `client_secrets.json` in the same folder as the app if you want to use Drive Upload.

---

## 🛠️ Installation Development

1. **Clone the repository:**
   ```bash
   git clone https://github.com/SkywalkerInOtt/ytdlr-streamlit.git
   cd ytdlr-streamlit
   ```

2. **Install dependencies:**
   ```bash
   uv sync
   ```
   *(Or `pip install -r requirements.txt`)*

3. **Install FFmpeg:**
   - **Mac:** `brew install ffmpeg`
   - **Windows:** Download from [ffmpeg.org](https://ffmpeg.org/download.html) and add to PATH.
   - **Linux:** `sudo apt install ffmpeg`

## 📝 Technologies Used

- [Streamlit](https://streamlit.io/) - The web framework
- [yt-dlp](https://github.com/yt-dlp/yt-dlp) - The downloader engine
- [FFmpeg](https://ffmpeg.org/) - For media processing
- [Google Drive API](https://developers.google.com/drive) - For cloud uploads