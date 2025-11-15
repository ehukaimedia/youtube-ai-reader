# YouTube-AI-Reader

A FastAPI service that converts any public YouTube video into AI-ready bundles. Each job downloads the source video, aligns transcripts (YouTube + Whisper), captures interval + scene-detected frames, enriches them with OCR/captions (when available), and emits:

- `transcript.json` and `transcript_bundle.json` with timing + confidence metadata
- `frames/` PNGs sized for ML ingestion alongside OCR/caption-rich `frames.json`
- `manifest.json` + `quality_report.json` describing capture parameters and coverage
- A zipped package for easy transport to downstream agents

## Quickstart
1. **Install deps**
   ```bash
   python3 -m venv .venv && source .venv/bin/activate
   pip install -r requirements.txt
   ```
2. **Run the API**
   ```bash
   uvicorn app.main:app --reload
   ```
3. **Open the UI** at http://localhost:8000/ and submit a video via the form, or use the API directly:
   ```bash
   curl -X POST http://localhost:8000/jobs \
     -H 'Content-Type: application/json' \
     -d '{"video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ", "interval_sec": 20}'
   ```
4. **Check progress (API)**
   ```bash
   curl http://localhost:8000/jobs/<job_id>
   ```
5. **Download the bundle** when the job is `complete` (UI download button or API):
   ```bash
   curl -L http://localhost:8000/jobs/<job_id>/package --output bundle.zip
   ```

## Environment Notes
- ffmpeg and yt-dlp must be present on `PATH`. On Apple Silicon, `brew install ffmpeg yt-dlp` places them under `/opt/homebrew/bin`.
- Configure storage paths with `DATA_ROOT` (defaults to `data/jobs` in the repo root).
- Optional extras:
  - **Whisper alignment:** `faster-whisper` is installed via `requirements.txt`. Control behaviour with `WHISPER_MODEL`, `WHISPER_DEVICE`, and `WHISPER_COMPUTE_TYPE`. If loading fails, the worker falls back to YouTube transcripts.
  - **OCR:** install the native `tesseract` binary (`brew install tesseract`). Presence is auto-detected by `pytesseract` and toggles OCR fields in `frames.json`.
  - **Frame captions via Ollama:** run `ollama serve`, pull a multimodal model (e.g., `ollama pull qwen3`), and set `OLLAMA_MODEL=qwen3` plus `OLLAMA_URL` if not default.
 - **Scene sensitivity:** override `FRAME_SCENE_THRESHOLD` (default `0.28`) to capture more/fewer change-triggered frames.

Refer to [`docs/deployment.md`](docs/deployment.md) for systemd/launchctl recipes and production tips.

### Cross-platform setup
- **macOS (Intel/Apple Silicon):** install deps with Homebrew commands above. `python3 -m venv` ships with macOS 12+; install Xcode Command Line Tools if missing.
- **Windows:** install [Python 3.11+](https://www.python.org/downloads/windows/) with “Add to PATH”, then `py -m venv .venv && .venv\\Scripts\\activate && pip install -r requirements.txt`. Install ffmpeg + yt-dlp via [Chocolatey](https://chocolatey.org/) (`choco install ffmpeg yt-dlp`) or place binaries on `%PATH%`. Use the [Windows Tesseract installer](https://github.com/UB-Mannheim/tesseract/wiki) for OCR. Ollama currently requires macOS/Linux; on Windows use WSL2 or run the captioning step on another host and set `OLLAMA_URL` accordingly.
- **Linux:** install `python3-venv`, `ffmpeg`, `yt-dlp`, and `tesseract-ocr` via your distro. Ollama provides `.deb/.rpm` packages—follow the [official docs](https://github.com/ollama/ollama) and export `OLLAMA_MODEL`/`OLLAMA_URL` for the FastAPI service.

## Project Structure
```
YouTube-AI-Reader/
├─ app/
│  ├─ main.py          # FastAPI routes + dependency wiring
│  ├─ schemas.py       # Pydantic request/response contracts
│  ├─ jobs.py          # In-memory job store + status transitions
│  ├─ pipelines.py     # Download/transcript/frame pipeline
│  ├─ transcripts.py   # YouTube + Whisper alignment helpers
│  ├─ vision.py        # Frame extraction, scene detection, OCR + captions
│  ├─ captions.py      # OCR + optional Ollama caption helpers
│  ├─ quality.py       # Artifact QA utilities
│  └─ storage.py       # Filesystem helpers (manifest writing, zip packaging)
├─ templates/
│  └─ index.html       # Bootstrap UI for human submissions
├─ data/jobs           # Generated at runtime; per-job artifacts
├─ requirements.txt
└─ README.md
```

## Roadmap
- Swap in Redis/Postgres for distributed job state
- Publish embeddings + semantic search API for generated artifacts
- Provide webhook callbacks when jobs finish

## Testing
```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pytest
```
