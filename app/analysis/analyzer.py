import asyncio
from collections import Counter
from typing import Optional, Set

from app.config import settings
from app.ingestion.parser import parse_log_file
from app.ingestion.filter import filter_by_severity, compute_stats
from app.ingestion.chunker import chunk_log_entries, filter_chunks_with_errors
from app.models.log_entry import Severity
from app.models.analysis import AnalysisResult, ErrorPattern, RootCause, Fix
from app.analysis.chains import extract_patterns, extract_root_causes, extract_fixes


def _build_time_buckets(entries) -> list:
    buckets = {}
    for e in entries:
        if not e.timestamp:
            continue
        # Round down to nearest 10 minutes for grouping
        bucket_key = e.timestamp.strftime("%Y-%m-%d %H:%M")[:-1] + "0"
        if bucket_key not in buckets:
            buckets[bucket_key] = {"time": bucket_key, "ERROR": 0, "WARN": 0, "INFO": 0, "DEBUG": 0}
        sev = e.severity.value
        buckets[bucket_key][sev] = buckets[bucket_key].get(sev, 0) + 1
    return list(buckets.values())


def _build_component_counts(entries) -> dict:
    counts = Counter()
    for e in entries:
        if e.logger_name and e.severity in (Severity.ERROR, Severity.WARN):
            counts[e.logger_name] += 1
    return dict(counts.most_common(15))


async def analyze_log_file(
    job_id: str,
    file_path: str,
    filename: str,
    selected_severities: Optional[Set[str]] = None,
) -> AnalysisResult:
    if selected_severities is None:
        selected_severities = {"ERROR", "WARN", "INFO", "DEBUG"}

    all_entries = parse_log_file(file_path)
    stats = compute_stats(all_entries)

    filtered_entries = filter_by_severity(all_entries, selected_severities)
    chunks = chunk_log_entries(
        filtered_entries,
        window_minutes=settings.chunk_window_minutes,
        max_lines=settings.chunk_max_lines,
    )
    error_chunks = filter_chunks_with_errors(chunks)

    capped = error_chunks[:settings.max_chunks_for_llm]
    notes = ""
    if len(error_chunks) > settings.max_chunks_for_llm:
        notes = (
            f"Analysis limited to first {settings.max_chunks_for_llm} error windows out of "
            f"{len(error_chunks)} total. Upload a filtered log for full coverage."
        )

    all_raw_patterns = []
    for chunk in capped:
        raw = await extract_patterns(chunk.text)
        all_raw_patterns.extend(raw)
        await asyncio.sleep(0.3)

    root_causes_raw = await extract_root_causes(all_raw_patterns)
    fixes_raw = await extract_fixes(root_causes_raw)

    patterns = [ErrorPattern(**p) for p in all_raw_patterns]
    root_causes = [RootCause(**rc) for rc in root_causes_raw]
    fixes = [Fix(**f) for f in fixes_raw]

    severity_counts = stats.get("severity_counts", {})
    return AnalysisResult(
        job_id=job_id,
        filename=filename,
        total_lines=stats["total"],
        total_errors=severity_counts.get("ERROR", 0),
        total_warns=severity_counts.get("WARN", 0),
        severity_counts=severity_counts,
        time_buckets=_build_time_buckets(all_entries),
        component_counts=_build_component_counts(all_entries),
        patterns=patterns,
        root_causes=root_causes,
        fixes=fixes,
        analysis_notes=notes,
    )
