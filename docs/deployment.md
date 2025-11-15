# Deployment Guide

This service is intentionally lightweight: a single FastAPI process (uvicorn) that
runs background pipelines for each submitted job. The following guidance makes it
safe to run on macOS, Linux servers, or Windows via WSL2.

## 1. Environment preparation
1. **Python environment**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
2. **System dependencies**
   - ffmpeg + yt-dlp on PATH (`brew install ffmpeg yt-dlp`, `sudo apt install ffmpeg yt-dlp`, or Chocolatey on Windows).
   - Optional: `tesseract` for OCR, [Ollama](https://github.com/ollama/ollama) for frame captions, Faster-Whisper settings via env vars.
3. **Environment variables** – create `.env` next to the repo to override defaults. Key options:
   ```env
   YTAI_DATA_ROOT=/srv/youtube-ai-reader/jobs
   YTAI_FRAME_SCENE_THRESHOLD=0.2
   YTAI_DOWNLOAD_RETRIES=3
   YTAI_LOG_LEVEL=INFO
   YTAI_OLLAMA_MODEL=qwen3
   YTAI_ENABLE_OCR=true
   ```

## 2. Running with systemd (Linux)
Create `/etc/systemd/system/yta-reader.service`:
```ini
[Unit]
Description=YouTube AI Reader
After=network.target

[Service]
WorkingDirectory=/opt/YouTube-AI-Reader
ExecStart=/opt/YouTube-AI-Reader/.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
EnvironmentFile=/opt/YouTube-AI-Reader/.env
Restart=on-failure
User=yta
Group=yta

[Install]
WantedBy=multi-user.target
```
Then enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable --now yta-reader
```
Logs are available with `journalctl -u yta-reader -f`.

## 3. macOS launchctl
Use `brew services` for uvicorn or create `~/Library/LaunchAgents/com.yta.reader.plist`
that runs the same `uvicorn` command. Ensure the `.venv` activation script is sourced
via a wrapper shell script if you need custom env vars.

## 4. Reverse proxy & TLS
Behind nginx or Caddy:
```nginx
location / {
    proxy_pass http://127.0.0.1:8000;
    proxy_set_header Host $host;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
}
```
Terminate TLS at the proxy, not inside uvicorn.

## 5. Monitoring & backup
- Poll `/health` and alert if dependencies turn `false`.
- Monitor disk usage of `YTAI_DATA_ROOT`; production deploys typically move it to a
  separate volume.
- Snapshot or rsync job folders if you need to retain data long-term.

## 6. Windows / WSL2
- Run everything inside WSL2 Ubuntu. Install Ollama on Windows (with GPU) or WSL2
  and expose `YTAI_OLLAMA_URL` so the service can reach it.
- Use `nssm` or Task Scheduler to keep the uvicorn process running.

With these pieces in place, `uvicorn` stays up, jobs persist across restarts, and
observability is available through the logs + health endpoint.
