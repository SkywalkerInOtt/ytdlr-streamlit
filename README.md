# 🎥 ytdlr - YouTube Downloader

A simple and efficient YouTube video downloader built with **Streamlit** and **yt-dlp**.

## ✨ Features

- 📥 **Download Videos**: Fetch videos from YouTube in various qualities (e.g., 1080p, 720p).
- 🎵 **Audio/Video Merge**: Automatically merges high-quality video and audio streams using `ffmpeg`.
- 🚀 **Streamlit Interface**: Clean and easy-to-use web interface.
- ☁️ **Cloud Ready**: Configured for easy deployment on Streamlit Cloud.

## 🛠️ Local Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/SkywalkerInOtt/ytdlr-streamlit.git
   cd ytdlr-streamlit
   ```

2. **Set up a virtual environment (optional but recommended):**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Install FFmpeg:**
   - **Mac:** `brew install ffmpeg`
   - **Windows:** Download from [ffmpeg.org](https://ffmpeg.org/download.html) and add to PATH.
   - **Linux:** `sudo apt install ffmpeg`

5. **Run the app:**
   ```bash
   streamlit run app.py
   ```

## ☁️ Deploy to Streamlit Cloud

This repository is pre-configured for Streamlit Cloud deployment.

1. Go to [share.streamlit.io](https://share.streamlit.io/).
2. Click **New app**.
3. Select your repository (`SkywalkerInOtt/ytdlr-streamlit`).
4. Set **Main file path** to `app.py`.
5. Click **Deploy**.

> **Note:** The `packages.txt` file handles the installation of `ffmpeg` on Streamlit Cloud automatically.

## 📝 Technologies Used

- [Streamlit](https://streamlit.io/) - The web framework
- [yt-dlp](https://github.com/yt-dlp/yt-dlp) - The downloader engine
- [FFmpeg](https://ffmpeg.org/) - For media processing