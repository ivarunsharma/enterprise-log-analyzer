from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from app.storage.job_store import get_job, get_result, JobStatus

router = APIRouter()


@router.get("/api/analysis/{job_id}")
async def get_analysis(job_id: str):
    job = get_job(job_id)
    if not job:
        raise HTTPException(404, detail="Job not found")

    if job.status == JobStatus.FAILED:
        raise HTTPException(500, detail=job.error_message or "Analysis failed")

    if job.status != JobStatus.COMPLETE:
        return JSONResponse(
            status_code=202,
            content={"job_id": job_id, "status": job.status.value, "filename": job.filename},
        )

    result = get_result(job_id)
    if not result:
        raise HTTPException(500, detail="Result missing")

    return result.model_dump()
