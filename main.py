import glob
import os

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse

from app.api import upload, analysis, report
from app.config import settings
from app.storage.job_store import get_job, get_result, JobStatus
from app.reporting.chart_builder import build_error_timeline, build_severity_pie, build_component_bar


app = FastAPI(title="Enterprise Log Analyzer")

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="app/templates")

app.include_router(upload.router)
app.include_router(analysis.router)
app.include_router(report.router)


@app.on_event("startup")
async def startup_event():
    os.makedirs(settings.upload_dir, exist_ok=True)


@app.on_event("shutdown")
async def shutdown_event():
    # Clean up uploaded files when the server stops
    files = glob.glob(os.path.join(settings.upload_dir, "*"))
    for f in files:
        try:
            os.remove(f)
        except OSError:
            pass


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(request, "index.html")


@app.get("/dashboard/{job_id}", response_class=HTMLResponse)
async def dashboard(request: Request, job_id: str):
    job = get_job(job_id)
    if not job or job.status != JobStatus.COMPLETE:
        return templates.TemplateResponse(request, "index.html", {
            "error": "Analysis not ready or job not found.",
        })

    result = get_result(job_id)
    return templates.TemplateResponse(request, "dashboard.html", {
        "result": result,
        "job_id": job_id,
        "chart_timeline": build_error_timeline(result),
        "chart_severity": build_severity_pie(result),
        "chart_components": build_component_bar(result),
    })
