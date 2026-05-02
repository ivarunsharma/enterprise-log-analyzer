from app.models.log_entry import LogEntry, Severity

# Map severity name strings to Severity enum values
_VALID_SEVERITIES = {
    "ERROR": Severity.ERROR,
    "WARN": Severity.WARN,
    "INFO": Severity.INFO,
    "DEBUG": Severity.DEBUG,
}


def filter_by_severity(entries: list, selected: set) -> list:
    if not selected:
        return entries

    allowed = set()
    for s in selected:
        if s in _VALID_SEVERITIES:
            allowed.add(_VALID_SEVERITIES[s])
    # Always include UNKNOWN so unrecognised log formats are not dropped
    allowed.add(Severity.UNKNOWN)

    result = []
    for entry in entries:
        if entry.severity in allowed:
            result.append(entry)
    return result


def compute_stats(entries: list) -> dict:
    counts = {}
    for e in entries:
        sev = e.severity.value
        counts[sev] = counts.get(sev, 0) + 1

    timestamps = []
    for e in entries:
        if e.timestamp:
            timestamps.append(e.timestamp)

    return {
        "total": len(entries),
        "severity_counts": counts,
        "start_time": min(timestamps).isoformat() if timestamps else None,
        "end_time": max(timestamps).isoformat() if timestamps else None,
        "unique_loggers": list({e.logger_name for e in entries if e.logger_name}),
    }
