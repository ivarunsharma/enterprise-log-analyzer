from datetime import timedelta
from app.models.log_entry import LogEntry, LogChunk, Severity


def chunk_log_entries(
    entries: list,
    window_minutes: int = 5,
    max_lines: int = 50,
) -> list:
    if not entries:
        return []

    chunks = []
    current_batch = []
    window_start = entries[0].timestamp
    chunk_id = 0

    for entry in entries:
        ts = entry.timestamp
        window_exceeded = (
            ts is not None
            and window_start is not None
            and (ts - window_start) > timedelta(minutes=window_minutes)
        )

        if window_exceeded or len(current_batch) >= max_lines:
            if current_batch:
                chunks.append(_make_chunk(chunk_id, current_batch))
                chunk_id += 1
            current_batch = []
            window_start = ts

        current_batch.append(entry)

    if current_batch:
        chunks.append(_make_chunk(chunk_id, current_batch))

    return chunks


def _make_chunk(chunk_id: int, batch: list) -> LogChunk:
    error_count = 0
    warn_count = 0
    timestamps = []

    for e in batch:
        if e.severity == Severity.ERROR:
            error_count += 1
        elif e.severity == Severity.WARN:
            warn_count += 1
        if e.timestamp:
            timestamps.append(e.timestamp)

    return LogChunk(
        chunk_id=chunk_id,
        entries=batch,
        start_time=min(timestamps) if timestamps else None,
        end_time=max(timestamps) if timestamps else None,
        error_count=error_count,
        warn_count=warn_count,
    )


def filter_chunks_with_errors(chunks: list) -> list:
    result = []
    for chunk in chunks:
        if chunk.error_count > 0 or chunk.warn_count > 0:
            result.append(chunk)
    return result
