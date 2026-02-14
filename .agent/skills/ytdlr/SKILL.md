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

- **Isolate Vocals**:
  `uv run main.py --instrumental "video.mp4"`
  Creates instrumental MP3, karaoke MP4, AND isolated vocals MP3.

- **Replace Audio**:
  `uv run main.py --replace-audio "video.mp4" --audio "new.mp3"`
  Replaces video audio.

- **Mix Audio**:
  `uv run main.py --mix-audio "video.mp4" --audio "bg.mp3"`
  Mixes new audio into video.

- **Image to Video**:
  `uv run main.py --image-to-video "img.jpg" --audio "audio.mp3"`
  Creates 1080p video from image.

- **Slideshow** (shows all images once):
  `uv run main.py --slideshow "./folder" --audio "audio.mp3" [--duration-per-image 3]`
  Creates slideshow with Ken Burns effects. Shows each image once.
  Supports: JPG, PNG, BMP, HEIC

- **Images to Video** (loops to match audio):
  `uv run main.py --images-to-video "./folder" --audio "audio.mp3" [--duration-per-image 3]`
  Creates video with Ken Burns effects. Loops images to match full audio duration.
  Supports: JPG, PNG, BMP, HEIC

- **Mute Video**:
  `uv run main.py --mute "video.mp4"`
  Removes audio from the video.

- **Loop Video**:
  `uv run main.py --loop "video.mp4" --duration "1h"`
  Loops video to target duration.

- **Clip Video**:
  `uv run main.py --clip "video.mp4" --start "20s" [--duration "10s"]`
  Clips video segment. Duration optional.

- **Upload to Drive**:
  `uv run main.py --upload "file.mp4" [--folder "ID"]`
  Requires `client_secrets.json`.

## Interactive Mode
Run `uv run main.py` without arguments for an interactive wizard.

## Web Interface
Run `uv run streamlit run app.py` to launch the GUI at `http://localhost:8501`.
- Tab 1: Download from URL
- Tab 2: Process uploaded files
- Tab 3: Tools (Replace/Mix Audio, Image to Video)
