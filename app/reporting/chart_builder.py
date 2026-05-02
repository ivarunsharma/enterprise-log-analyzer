import json
import plotly.graph_objects as go
from app.models.analysis import AnalysisResult

_SEVERITY_COLORS = {
    "ERROR": "#ef4444",
    "WARN": "#f97316",
    "INFO": "#3b82f6",
    "DEBUG": "#6b7280",
    "UNKNOWN": "#9ca3af",
}


def build_error_timeline(result: AnalysisResult) -> str:
    buckets = result.time_buckets
    if not buckets:
        return json.dumps({})

    times = [b["time"] for b in buckets]
    traces = []
    for sev in ["ERROR", "WARN", "INFO", "DEBUG"]:
        values = [b.get(sev, 0) for b in buckets]
        if any(v > 0 for v in values):
            traces.append(go.Bar(
                name=sev,
                x=times,
                y=values,
                marker_color=_SEVERITY_COLORS[sev],
            ))

    fig = go.Figure(data=traces)
    fig.update_layout(
        title="Log Events Over Time",
        barmode="stack",
        xaxis_title="Time",
        yaxis_title="Event Count",
        legend_title="Severity",
        height=350,
        margin=dict(l=40, r=20, t=50, b=40),
    )
    return fig.to_json()


def build_severity_pie(result: AnalysisResult) -> str:
    counts = result.severity_counts
    if not counts:
        return json.dumps({})

    labels = list(counts.keys())
    values = list(counts.values())
    colors = [_SEVERITY_COLORS.get(l, "#9ca3af") for l in labels]

    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        marker_colors=colors,
        hole=0.4,
    )])
    fig.update_layout(
        title="Severity Distribution",
        height=350,
        margin=dict(l=20, r=20, t=50, b=20),
    )
    return fig.to_json()


def build_component_bar(result: AnalysisResult) -> str:
    comp = result.component_counts
    if not comp:
        return json.dumps({})

    sorted_items = sorted(comp.items(), key=lambda x: x[1], reverse=True)[:10]
    components = [i[0] for i in sorted_items]
    counts = [i[1] for i in sorted_items]

    fig = go.Figure(data=[go.Bar(
        x=counts,
        y=components,
        orientation="h",
        marker_color="#ef4444",
    )])
    fig.update_layout(
        title="Top Components by Error Count",
        xaxis_title="Error + Warn Count",
        height=350,
        margin=dict(l=160, r=20, t=50, b=40),
        yaxis=dict(autorange="reversed"),
    )
    return fig.to_json()
