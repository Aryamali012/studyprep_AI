from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.styles import getSampleStyleSheet

def generate_pdf(text, filename):
    file_path = f"storage/notes/{filename}.pdf"
    doc = SimpleDocTemplate(file_path)
    styles = getSampleStyleSheet()
    content = [Paragraph(line, styles["Normal"]) for line in text.split("\n")]
    doc.build(content)
    return file_path
