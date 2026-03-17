from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
import xml.sax.saxutils as saxutils

def generate_pdf(text, filename):
    file_path = f"storage/notes/{filename}.pdf"
    doc = SimpleDocTemplate(file_path)
    styles = getSampleStyleSheet()
    
    # Escape special characters that would break ReportLab Paragraph elements
    escaped_text = saxutils.escape(text)
    
    content = []
    for line in escaped_text.split("\n"):
        if line.strip():
            content.append(Paragraph(line, styles["Normal"]))
    
    doc.build(content)
    return file_path
