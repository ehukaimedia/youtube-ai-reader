# Repository Guidelines

## Project Structure & Module Organization
The FastAPI app lives under `app/`: `main.py` wires routes, `schemas.py` holds request/response contracts, `jobs.py` tracks state, and `pipelines.py` orchestrates download/transcript/frame capture. Supporting modules include `config.py` (pydantic settings/env parsing), `transcripts.py` (YouTube + Whisper alignment), `vision.py` (OpenCV frame extraction + scene detection), `captions.py` (Tesseract + optional Ollama captions), `quality.py` (artifact QA), `health.py` (dependency probes), and `storage.py` (manifests/bundles). The lightweight HTML client is in `templates/index.html`. Runtime artifacts land in `data/jobs/<job_id>/` (configurable via `DATA_ROOT`).

## Build, Test, and Development Commands
- `python3 -m venv .venv && source .venv/bin/activate`: create the project virtualenv.
- `pip install -r requirements.txt`: install FastAPI + pipeline deps (pytest included for unit tests).
- `uvicorn app.main:app --reload`: run the API with hot reload on http://localhost:8000/.
- `pytest`: execute module-aligned tests in `tests/`; mock network/filesystem edges for determinism.
- `ruff check app tests` / `black app tests`: lint and format.

## Coding Style & Naming Conventions
Follow PEP 8 with 4-space indentation, type-hinted signatures, and concise docstrings. Favor `snake_case` for functions/variables, `PascalCase` for classes, and keep FastAPI route handlers in `app.main`. Prefer dependency injection over module-level globals, drive config through `pydantic` settings or env vars, and keep filenames singular while co-locating helpers with their pipeline stage.

## Testing Guidelines
Use `pytest` with `httpx.AsyncClient` for route tests and `tmp_path` fixtures for filesystem-heavy logic. Mirror modules with `tests/test_<module>.py`, naming async tests `test_<scenario>`. Assert pipelines emit `manifest.json`, transcript artifacts, and `frames/` metadata for happy paths, and mock subprocess/network calls to simulate missing transcripts or ffmpeg failures. Prioritize `pipelines.py` and `storage.py` coverage before submitting.

## Commit & Pull Request Guidelines
Write imperative, present-tense commit subjects under 72 chars (e.g., `Add transcript manifest checksum`). Describe reasoning + side effects in the body when touching pipeline behavior. Pull requests should summarize motivation, list testing evidence (`pytest`, manual curl, UI check), and link related issues or job IDs. Document config changes (new env vars, CLI flags) in README and note any data migrations.

## Security & Configuration Tips
Never commit generated artifacts from `data/jobs/` or API keys. Validate user-provided URLs server-side before invoking yt-dlp, run `ruff check --select S` when available, and confirm ffmpeg + yt-dlp are present on `PATH` (Homebrew on macOS, Chocolatey/winget on Windows, distro packages on Linux). Install `tesseract` only if OCR is desired; otherwise the code auto-disables it. Ollama captioning is optional—set `OLLAMA_MODEL` only on machines you trust (macOS/Linux natively, Windows via WSL with `OLLAMA_URL`). Point `DATA_ROOT` to external volumes when processing large batches to avoid exhausting repo disk space.
