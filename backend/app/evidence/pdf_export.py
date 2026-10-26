"""PDF incident/evidence record — pure serialization of InvestigationResult.

Structured to map onto the SBP Technology Risk Management Framework's
evidence categories per docs/ARCHITECTURE.md: incident record, root-cause
analysis, incident timeline, and the audit trail (evidence artifacts).
"""
from __future__ import annotations

from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


def to_pdf_bytes(result) -> bytes:
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=2 * cm, bottomMargin=2 * cm)
    styles = getSampleStyleSheet()
    story = []
    twin = result.twin

    story.append(Paragraph("AI Payment Operations Engineer — Incident / Evidence Record", styles["Title"]))
    story.append(
        Paragraph(
            f"Reference: {twin.ref.reference} ({twin.ref.reference_type}, rail: {twin.ref.rail})",
            styles["Normal"],
        )
    )
    story.append(Paragraph(f"Investigation ID: {twin.id}", styles["Normal"]))
    model_note = f"{result.model_version}" + (" (self-corrected on review)" if result.self_corrected else "")
    story.append(Paragraph(f"Generated: {result.generated_at.isoformat()} — model {model_note}", styles["Normal"]))
    story.append(Paragraph(f"Correlation engine version: {twin.correlation_version}", styles["Normal"]))
    story.append(Spacer(1, 0.5 * cm))

    story.append(Paragraph("Explanation", styles["Heading2"]))
    story.append(Paragraph(result.explanation, styles["BodyText"]))
    story.append(Spacer(1, 0.4 * cm))

    story.append(Paragraph("Timeline", styles["Heading2"]))
    table_data = [["#", "Stage", "Status", "Started", "Notes"]]
    for hop in twin.hops:
        table_data.append(
            [
                str(hop.sequence),
                hop.stage.value,
                hop.status,
                hop.started_at.isoformat() if hop.started_at else "-",
                (hop.notes or "-")[:80],
            ]
        )
    table = Table(table_data, colWidths=[1.2 * cm, 3.6 * cm, 2 * cm, 4.2 * cm, 6 * cm])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f2937")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTSIZE", (0, 0), (-1, -1), 7.5),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f3f4f6")]),
            ]
        )
    )
    story.append(table)
    story.append(Spacer(1, 0.4 * cm))

    story.append(Paragraph("Root Cause Candidates", styles["Heading2"]))
    if result.root_causes:
        for rc in result.root_causes:
            pattern_note = f" (pattern: {rc.pattern_id})" if rc.pattern_id else ""
            story.append(
                Paragraph(f"<b>{rc.label}</b> — confidence {rc.confidence:.0%}{pattern_note}", styles["BodyText"])
            )
    else:
        story.append(Paragraph("No break detected.", styles["BodyText"]))
    story.append(Spacer(1, 0.4 * cm))

    story.append(Paragraph("Recommendation (drafted — requires human approval; not auto-executed)", styles["Heading2"]))
    story.append(Paragraph(result.recommendation, styles["BodyText"]))
    story.append(Spacer(1, 0.4 * cm))

    story.append(Paragraph("Evidence Artifacts (audit trail)", styles["Heading2"]))
    for hop in twin.hops:
        if not hop.artifacts:
            continue
        story.append(Paragraph(f"Hop {hop.sequence} — {hop.stage.value}", styles["Heading3"]))
        for artifact in hop.artifacts:
            story.append(
                Paragraph(
                    f"source={artifact.source} &middot; type={artifact.artifact_type} &middot; "
                    f"at={artifact.timestamp.isoformat()}<br/>{artifact.raw_payload}",
                    styles["BodyText"],
                )
            )

    doc.build(story)
    return buffer.getvalue()
