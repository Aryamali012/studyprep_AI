from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, ListFlowable, ListItem
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.colors import HexColor
import os


def generate_pdf(text: str, filename: str):
    output_dir = "storage/notes"
    os.makedirs(output_dir, exist_ok=True)

    file_path = os.path.join(output_dir, f"{filename}.pdf")

    doc = SimpleDocTemplate(
        file_path,
        pagesize=A4,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40,
    )

    styles = getSampleStyleSheet()

    styles.add(ParagraphStyle(
        name="SP_Title",
        fontSize=20,
        leading=26,
        alignment=TA_CENTER,
        spaceAfter=20
    ))

    styles.add(ParagraphStyle(
        name="SP_Heading",
        fontSize=14,
        leading=18,
        textColor=HexColor("#1f4ed8"),
        spaceBefore=16,
        spaceAfter=8
    ))

    styles.add(ParagraphStyle(
        name="SP_Text",
        fontSize=11,
        leading=16,
        spaceAfter=6
    ))

    story = []

    for line in text.split("\n"):
        line = line.strip()

        if not line:
            story.append(Spacer(1, 10))
            continue

        if line.startswith("# "):
            story.append(Paragraph(line[2:], styles["SP_Title"]))

        elif line.startswith("## "):
            story.append(Paragraph(line[3:], styles["SP_Heading"]))

        elif line.startswith("- "):
            story.append(
                ListFlowable(
                    [ListItem(Paragraph(line[2:], styles["SP_Text"]))],
                    bulletType="bullet"
                )
            )

        else:
            story.append(Paragraph(line, styles["SP_Text"]))

    doc.build(story)
    return file_path
