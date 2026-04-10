# Vision Workbench

## Requirements
- Python 3.12 (tested with 3.12.12)

## Setup

```bash
git clone <repo>
cd <repo>

python3.12 -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt
```

## Run

```bash
uvicorn app.main:app --reload
```

## System Requirements

The following dependencies must be installed on your system:

### FFmpeg

Required for video processing and streaming.

#### macOS
```bash
brew install ffmpeg
ffmpeg -version
```

#### macOS
```bash
sudo apt update
sudo apt install ffmpeg
ffmpeg -version
```

## OpenCV
The app uses opencv-python, which is installed via pip.
However, video/stream functionality depends on system codecs (provided by FFmpeg).

# Start up
```bash
python -m venv .venv
source .venv/bin/activate   # mac/linux
pip install -r requirements.txt
uvicorn app.main:app --reload
```
