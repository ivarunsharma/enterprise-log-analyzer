from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field
from app.models.analysis import AnalysisResult

_jobs = {}
_results = {}


class JobStatus(str, Enum):
    PENDING = "PENDING"
    PARSING = "PARSING"
    ANALYZING = "ANALYZING"
    COMPLETE = "COMPLETE"
    FAILED = "FAILED"


class JobState(BaseModel):
    job_id: str
    filename: str
    status: JobStatus = JobStatus.PENDING
    created_at: datetime = Field(default_factory=datetime.utcnow)
    error_message: Optional[str] = None


def create_job(job_id: str, filename: str) -> JobState:
    job = JobState(job_id=job_id, filename=filename)
    _jobs[job_id] = job
    return job


def update_job_status(job_id: str, status: JobStatus, error: str = None) -> None:
    if job_id in _jobs:
        _jobs[job_id].status = status
        if error:
            _jobs[job_id].error_message = error


def get_job(job_id: str) -> Optional[JobState]:
    return _jobs.get(job_id)


def store_result(job_id: str, result: AnalysisResult) -> None:
    _results[job_id] = result


def get_result(job_id: str) -> Optional[AnalysisResult]:
    return _results.get(job_id)
