from __future__ import annotations

from pathlib import Path

from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.responses import FileResponse, HTMLResponse

from .config import settings
from .health import dependency_snapshot
from .jobs import JobStore
from .logging_config import configure_logging
from .pipelines import run_pipeline
from .schemas import JobCreateRequest, JobResponse, JobStatus

configure_logging()

app = FastAPI(title="YouTube AI Reader", version="0.1.0")
job_store = JobStore()
TEMPLATE_PATH = Path(__file__).resolve().parents[1] / "templates" / "index.html"


@app.post("/jobs", response_model=JobResponse, status_code=201)
async def create_job(payload: JobCreateRequest, background_tasks: BackgroundTasks) -> JobResponse:
    job = job_store.create_job(payload)
    background_tasks.add_task(run_pipeline, job.id, payload, job_store)
    return job.to_response()


@app.get("/jobs/{job_id}", response_model=JobResponse)
async def get_job(job_id: str) -> JobResponse:
    try:
        job = job_store.get(job_id)
        return job.to_response()
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get("/jobs/{job_id}/package")
async def download_package(job_id: str):
    try:
        job = job_store.get(job_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    if job.status != JobStatus.complete:
        raise HTTPException(status_code=400, detail="Job not complete yet")
    if not job.package_path:
        raise HTTPException(status_code=404, detail="Bundle not found")
    return FileResponse(path=job.package_path, filename=f"{job_id}.zip")


@app.get("/", response_class=HTMLResponse)
async def ui_root() -> HTMLResponse:
    if not TEMPLATE_PATH.exists():
        raise HTTPException(status_code=500, detail="UI not found")
    return HTMLResponse(TEMPLATE_PATH.read_text(encoding="utf-8"))


@app.get("/health")
async def health() -> dict:
    return {
        "service": app.title,
        "version": app.version,
        "dependencies": dependency_snapshot(),
        "config": {
            "data_root": str(settings.data_root),
            "frame_scene_threshold": settings.frame_scene_threshold,
            "ocr_enabled": settings.enable_ocr,
            "ollama_model": settings.ollama_model,
        },
    }
