import re
from datetime import datetime
from typing import Optional
from app.models.log_entry import LogEntry, Severity

_SEVERITY_MAP = {
    "ERROR": Severity.ERROR,
    "FATAL": Severity.ERROR,
    "CRITICAL": Severity.ERROR,
    "WARN": Severity.WARN,
    "WARNING": Severity.WARN,
    "INFO": Severity.INFO,
    "DEBUG": Severity.DEBUG,
    "TRACE": Severity.DEBUG,
}

# Keywords to guess severity when the log line has no explicit level
_ERROR_KEYWORDS = [
    "fail", "failure", "error", "fatal", "critical", "alert", "denied",
    "refused", "exception", "abort", "panic", "crash", "invalid", "illegal",
    "unauthorized", "forbidden", "unreachable", "abnormally", "segfault",
]
_WARN_KEYWORDS = [
    "warn", "warning", "deprecated", "slow", "retry", "degraded",
    "expired", "unknown", "suspicious", "timeout", "check pass",
]


def _infer_severity_from_message(msg: str) -> Severity:
    lower = msg.lower()
    for kw in _ERROR_KEYWORDS:
        if kw in lower:
            return Severity.ERROR
    for kw in _WARN_KEYWORDS:
        if kw in lower:
            return Severity.WARN
    return Severity.INFO


# Common log format patterns
_PATTERNS = [
    # Python logging: 2024-01-15 10:23:45,123 ERROR root — message
    re.compile(
        r"^(?P<ts>\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2}[,\.]\d+)\s+"
        r"(?P<sev>ERROR|WARN(?:ING)?|INFO|DEBUG|TRACE|FATAL|CRITICAL)\s+"
        r"(?P<logger>\S+)\s+[—\-]+\s*(?P<msg>.+)$"
    ),
    # Log4j / Java: 2024-01-15 10:23:45.123 [thread] ERROR com.example — message
    re.compile(
        r"^(?P<ts>\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2}[,\.]\d+)\s+"
        r"\[(?P<thread>[^\]]+)\]\s+"
        r"(?P<sev>ERROR|WARN(?:ING)?|INFO|DEBUG|TRACE|FATAL|CRITICAL)\s+"
        r"(?P<logger>\S+)\s+[—\-]+\s*(?P<msg>.+)$"
    ),
    # Simple: 2024-01-15 10:23:45 ERROR message
    re.compile(
        r"^(?P<ts>\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2})\s+"
        r"(?P<sev>ERROR|WARN(?:ING)?|INFO|DEBUG|TRACE|FATAL|CRITICAL)\s+"
        r"(?P<msg>.+)$"
    ),
    # Syslog: Jan 15 10:23:45 hostname process[pid]: message
    re.compile(
        r"^(?P<ts>[A-Za-z]{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2})\s+"
        r"\S+\s+"
        r"(?P<logger>[^\(\[\s:]+)"
        r"(?:\([^)]*\))?(?:\[\d+\])?:\s*"
        r"(?P<msg>.+)$"
    ),
]

_TS_FORMATS = [
    "%Y-%m-%d %H:%M:%S,%f",
    "%Y-%m-%dT%H:%M:%S,%f",
    "%Y-%m-%d %H:%M:%S.%f",
    "%Y-%m-%dT%H:%M:%S.%f",
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%dT%H:%M:%S",
    "%b %d %H:%M:%S",
    "%b  %d %H:%M:%S",
]


def _parse_ts(raw: str) -> Optional[datetime]:
    # Normalize whitespace so "Jan  4" parses the same as "Jan 4"
    normalized = " ".join(raw.strip().split())
    for fmt in _TS_FORMATS:
        try:
            dt = datetime.strptime(normalized, fmt)
            if dt.year == 1900:
                dt = dt.replace(year=datetime.now().year)
            return dt
        except ValueError:
            continue
    return None


def parse_log_file(path: str) -> list:
    entries = []
    with open(path, "r", errors="replace") as fh:
        for line_num, raw in enumerate(fh, start=1):
            raw = raw.rstrip("\n")
            if not raw.strip():
                continue
            entry = _match_line(line_num, raw)
            entries.append(entry)
    return entries


def _match_line(line_num: int, raw: str) -> LogEntry:
    for pat in _PATTERNS:
        m = pat.match(raw)
        if m:
            d = m.groupdict()
            sev_str = d.get("sev", "").upper()
            severity = _SEVERITY_MAP.get(sev_str)
            msg = d.get("msg", raw).strip()
            if severity is None:
                severity = _infer_severity_from_message(msg)
            return LogEntry(
                line_number=line_num,
                raw_line=raw,
                timestamp=_parse_ts(d.get("ts", "") or ""),
                severity=severity,
                logger_name=d.get("logger"),
                thread=d.get("thread"),
                message=msg,
            )
    # No pattern matched — guess severity from the raw line
    return LogEntry(
        line_number=line_num,
        raw_line=raw,
        severity=_infer_severity_from_message(raw),
        message=raw.strip(),
    )
