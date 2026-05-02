from typing import Optional
from pydantic import BaseModel


class ErrorPattern(BaseModel):
    pattern_id: str
    description: str
    count: int = 1
    severity: str = "ERROR"
    first_seen: Optional[str] = None
    last_seen: Optional[str] = None
    affected_components: list[str] = []
    sample_message: str = ""


class RootCause(BaseModel):
    cause_id: str
    title: str
    confidence_score: float = 0.0
    evidence: list[str] = []
    related_pattern_ids: list[str] = []


class Fix(BaseModel):
    fix_id: str
    title: str
    steps: list[str] = []
    priority: str = "medium"
    estimated_effort: str = ""
    related_cause_ids: list[str] = []


class AnalysisResult(BaseModel):
    job_id: str
    filename: str
    total_lines: int = 0
    total_errors: int = 0
    total_warns: int = 0
    severity_counts: dict[str, int] = {}
    time_buckets: list[dict] = []
    component_counts: dict[str, int] = {}
    patterns: list[ErrorPattern] = []
    root_causes: list[RootCause] = []
    fixes: list[Fix] = []
    analysis_notes: str = ""
