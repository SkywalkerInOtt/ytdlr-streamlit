# 🎥 ytdlr - YouTube Downloader

A simple and efficient YouTube video downloader built with **Streamlit** and **yt-dlp**.

## ✨ Features

- 📥 **Download Videos**: Fetch videos from YouTube in various qualities (e.g., 1080p, 720p).
- 🎵 **Audio/Video Merge**: Automatically merges high-quality video and audio streams using `ffmpeg`.
- 🚀 **Streamlit Interface**: Clean and easy-to-use web interface.
- 💻 **CLI Mode**: Terminal-based downloader for quick local use.
- ☁️ **Google Drive Upload**: (CLI only) Automatically upload downloaded videos to your Google Drive.

---

## 🛠️ Usage Options

### Option 1: Web Interface (Streamlit)

Best for visual selection and easy formatting.

1. **Run the app:**
   ```bash
   uv run app.py
   ```
   *(Or `streamlit run app.py` if installed manually)*

2. Open `http://localhost:8501`.
3. Paste a URL, select quality, and download.

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
   - **Upload to Google Drive:**
     ```bash
     uv run main.py --upload "my_video.mp4"
     ```
     *(Optional: Specify folder with `--folder "FOLDER_ID"`)*

3. **Google Drive Upload Setup:**
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