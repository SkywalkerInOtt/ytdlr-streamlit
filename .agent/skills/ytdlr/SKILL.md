---
name: ytdlr
description: Tools for downloading videos (YouTube, XiaoHongShu) and processing audio (vocal removal).
---

# ytdlr Usage

## CLI Commands
Run commands using `uv run main.py`.

- **Download Video**: 
  `uv run main.py --download "URL"`
  Supports YouTube, XiaoHongShu, etc. Auto-selects best quality.

- **Remove Vocals**:
  `uv run main.py --instrumental "video.mp4"`
  Creates instrumental MP3 and karaoke MP4.

- **Mute Video**:
  `uv run main.py --mute "video.mp4"`
  Removes audio from the video.

- **Loop Video**:
  `uv run main.py --loop "video.mp4" --duration "1h"`
  Loops video to target duration.

- **Upload to Drive**:
  `uv run main.py --upload "file.mp4" [--folder "ID"]`
  Requires `client_secrets.json`.

## Interactive Mode
Run `uv run main.py` without arguments for an interactive wizard.

## Web Interface
Run `uv run streamlit run app.py` to launch the GUI at `http://localhost:8501`.
- Tab 1: Download from URL
- Tab 2: Process uploaded files
