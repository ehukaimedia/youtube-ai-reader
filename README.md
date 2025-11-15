# YouTube-AI-Reader

A FastAPI service that converts any public YouTube video into AI-ready bundles. Each job downloads the source video, fetches the transcript, captures periodic frames, and emits:

- `transcript.json` and `transcript.md` for structured + human-friendly text
- `frames/` PNGs sized for ML ingestion and `frames.json` metadata (timestamps, dimensions)
- `manifest.json` describing the capture parameters and checksums
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

## Project Structure
```
YouTube-AI-Reader/
├─ app/
│  ├─ main.py          # FastAPI routes + dependency wiring
│  ├─ schemas.py       # Pydantic request/response contracts
│  ├─ jobs.py          # In-memory job store + status transitions
│  ├─ pipelines.py     # Download/transcript/frame pipeline
│  └─ storage.py       # Filesystem helpers (manifest writing, zip packaging)
├─ templates/
│  └─ index.html       # Bootstrap UI for human submissions
├─ data/jobs           # Generated at runtime; per-job artifacts
├─ requirements.txt
└─ README.md
```

## Roadmap
- Swap in Redis/Postgres for distributed job state
- Add OCR + embedding steps for richer AI context
- Provide webhook callbacks when jobs finish
