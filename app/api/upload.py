import os
import uuid
from fastapi import APIRouter, BackgroundTasks, File, Form, HTTPException, UploadFile

from app.config import settings
from app.storage.job_store import create_job, update_job_status, store_result, JobStatus
from app.analysis.analyzer import analyze_log_file

router = APIRouter()

_ALLOWED_EXT = {".log", ".txt", ".out", ".gz"}


@router.post("/api/upload")
async def upload_log(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    severities: str = Form(default="ERROR,WARN,INFO,DEBUG"),
):
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in _ALLOWED_EXT:
        raise HTTPException(400, detail=f"Unsupported file type '{ext}'. Allowed: {_ALLOWED_EXT}")

    content = await file.read()
    size_mb = len(content) / (1024 * 1024)
    if size_mb > settings.max_upload_size_mb:
        raise HTTPException(413, detail=f"File too large ({size_mb:.1f} MB). Max {settings.max_upload_size_mb} MB.")

    job_id = uuid.uuid4().hex
    safe_name = f"{job_id}_{file.filename}"
    save_path = os.path.join(settings.upload_dir, safe_name)
    with open(save_path, "wb") as fh:
        fh.write(content)

    create_job(job_id, file.filename)
    selected = set(s.strip().upper() for s in severities.split(",") if s.strip())

    background_tasks.add_task(_run_analysis, job_id, save_path, file.filename, selected)
    return {"job_id": job_id, "status": "PENDING", "filename": file.filename}


async def _run_analysis(job_id: str, file_path: str, filename: str, severities: set[str]) -> None:
    try:
        update_job_status(job_id, JobStatus.PARSING)
        result = await analyze_log_file(job_id, file_path, filename, severities)
        store_result(job_id, result)
        update_job_status(job_id, JobStatus.COMPLETE)
    except Exception as exc:
        update_job_status(job_id, JobStatus.FAILED, error=str(exc))
