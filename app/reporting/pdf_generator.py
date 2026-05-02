import io
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable,
)
from app.models.analysis import AnalysisResult

_PRIORITY_COLORS = {
    "high": colors.red,
    "medium": colors.orange,
    "low": colors.green,
}


def generate_pdf(result: AnalysisResult) -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )
    styles = getSampleStyleSheet()
    h1 = styles["Heading1"]
    h2 = styles["Heading2"]
    normal = styles["Normal"]
    small = ParagraphStyle("small", parent=normal, fontSize=9)

    story = []

    # Title and metadata
    story.append(Paragraph("Enterprise Log Analysis Report", h1))
    story.append(Spacer(1, 0.3 * cm))
    story.append(Paragraph(f"<b>File:</b> {result.filename}", normal))
    story.append(Paragraph(
        f"<b>Generated:</b> {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}",
        normal,
    ))
    story.append(HRFlowable(width="100%", spaceAfter=0.5 * cm))

    # Summary table
    story.append(Paragraph("Executive Summary", h2))
    summary_data = [
        ["Metric", "Value"],
        ["Total Log Lines", str(result.total_lines)],
        ["Total Errors", str(result.total_errors)],
        ["Total Warnings", str(result.total_warns)],
        ["Unique Error Patterns", str(len(result.patterns))],
        ["Root Causes Identified", str(len(result.root_causes))],
        ["Fix Recommendations", str(len(result.fixes))],
    ]
    t = Table(summary_data, colWidths=[8 * cm, 6 * cm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e293b")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#f8fafc")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f1f5f9")]),
    ]))
    story.append(t)
    story.append(Spacer(1, 0.5 * cm))

    if result.analysis_notes:
        story.append(Paragraph(f"<i>Note: {result.analysis_notes}</i>", small))
        story.append(Spacer(1, 0.3 * cm))

    # Error patterns section
    if result.patterns:
        story.append(Paragraph("Error Patterns Detected", h2))
        pat_data = [["Pattern ID", "Description", "Count", "Severity", "Affected Components"]]
        for p in result.patterns:
            pat_data.append([
                p.pattern_id,
                Paragraph(p.description[:80], small),
                str(p.count),
                p.severity,
                ", ".join(p.affected_components[:3]),
            ])
        pt = Table(pat_data, colWidths=[2 * cm, 7 * cm, 1.5 * cm, 2 * cm, 4 * cm])
        pt.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e293b")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#fef2f2")]),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ]))
        story.append(pt)
        story.append(Spacer(1, 0.5 * cm))

    # Root cause analysis section
    if result.root_causes:
        story.append(Paragraph("Root Cause Analysis", h2))
        for rc in result.root_causes:
            confidence_pct = int(rc.confidence_score * 100)
            story.append(Paragraph(
                f"<b>{rc.cause_id}: {rc.title}</b> (Confidence: {confidence_pct}%)",
                normal,
            ))
            for ev in rc.evidence:
                story.append(Paragraph(f"• {ev}", small))
            story.append(Spacer(1, 0.2 * cm))

    # Fix recommendations section
    if result.fixes:
        story.append(Paragraph("Remediation Recommendations", h2))
        for fix in result.fixes:
            priority_color = _PRIORITY_COLORS.get(fix.priority.lower(), colors.grey)
            story.append(Paragraph(
                f"<b>{fix.fix_id}: {fix.title}</b> "
                f"[Priority: {fix.priority.upper()}]"
                f" — {fix.estimated_effort}",
                normal,
            ))
            for i, step in enumerate(fix.steps, 1):
                story.append(Paragraph(f"  {i}. {step}", small))
            story.append(Spacer(1, 0.2 * cm))

    doc.build(story)
    return buf.getvalue()
