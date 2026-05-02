import io
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.storage.job_store import get_job, get_result, JobStatus
from app.reporting.pdf_generator import generate_pdf

router = APIRouter()


@router.get("/api/report/{job_id}")
async def download_report(job_id: str):
    job = get_job(job_id)
    if not job:
        raise HTTPException(404, detail="Job not found")
    if job.status != JobStatus.COMPLETE:
        raise HTTPException(400, detail=f"Analysis not complete (status: {job.status.value})")

    result = get_result(job_id)
    if not result:
        raise HTTPException(500, detail="Result missing")

    pdf_bytes = generate_pdf(result)
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="analysis_{job_id[:8]}.pdf"'},
    )
