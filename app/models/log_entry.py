from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel


class Severity(str, Enum):
    ERROR = "ERROR"
    WARN = "WARN"
    INFO = "INFO"
    DEBUG = "DEBUG"
    UNKNOWN = "UNKNOWN"


class LogEntry(BaseModel):
    line_number: int
    raw_line: str
    timestamp: Optional[datetime] = None
    severity: Severity = Severity.UNKNOWN
    logger_name: Optional[str] = None
    thread: Optional[str] = None
    message: str = ""


class LogChunk(BaseModel):
    chunk_id: int
    entries: list[LogEntry]
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    error_count: int = 0
    warn_count: int = 0

    @property
    def text(self) -> str:
        lines = []
        for e in self.entries:
            ts = e.timestamp.isoformat() if e.timestamp else "unknown"
            parts = [f"[{ts}]", e.severity.value]
            if e.logger_name:
                parts.append(e.logger_name)
            parts.append("—")
            parts.append(e.message)
            lines.append(" ".join(parts))
        return "\n".join(lines)
