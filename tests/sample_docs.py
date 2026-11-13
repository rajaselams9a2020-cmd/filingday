from io import BytesIO
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas
from reportlab.platypus import Table, TableStyle


def make_sample_pdf(path: Path) -> Path:
    pdf = canvas.Canvas(str(path), pagesize=letter)

    # Page 1: headings, broken word, repeated header and page numbers.
    pdf.setFont("Helvetica-Bold", 8)
    pdf.drawString(50, 765, "Customer Policy 2026")
    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(50, 730, "1. Account opening")
    pdf.setFont("Helvetica", 11)
    pdf.drawString(50, 700, "Every customer must complete the form.")
    pdf.drawString(50, 680, "regu-")
    pdf.drawString(50, 665, "lation issued today.")
    pdf.setFont("Helvetica-Bold", 13)
    pdf.drawString(50, 630, "1.1 Documents needed")
    pdf.setFont("Helvetica", 11)
    pdf.drawString(50, 600, "Aadhaar or passport is accepted.")
    pdf.drawString(50, 40, "42")
    pdf.drawString(50, 25, "Page 1 of 3")
    pdf.showPage()

    # Page 2: a ruled table.
    pdf.setFont("Helvetica-Bold", 8)
    pdf.drawString(50, 765, "Customer Policy 2026")
    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(50, 730, "2. Fees and charges")
    table = Table(
        [
            ["Service", "Fee (Rs)"],
            ["Cheque book", "150"],
            ["Duplicate statement", "100"],
        ],
        colWidths=[180, 100],
    )
    table.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 1, colors.black),
                ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), 11),
            ]
        )
    )
    table.wrapOn(pdf, 300, 150)
    table.drawOn(pdf, 50, 650)
    pdf.setFont("Helvetica", 11)
    pdf.drawString(50, 600, "Fees include GST and are reviewed every year.")
    pdf.drawString(50, 25, "Page 2 of 3")
    pdf.showPage()

    # Page 3: an image of text, with no searchable PDF text layer.
    image = Image.new("RGB", (1600, 2200), "white")
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default(size=90)
    draw.text((100, 150), "3. Refunds", fill="black", font=font)
    draw.text(
        (100, 350),
        "Refunds are paid within seven working days.",
        fill="black",
        font=font,
    )
    image_bytes = BytesIO()
    image.save(image_bytes, format="PNG")
    image_bytes.seek(0)
    pdf.drawImage(ImageReader(image_bytes), 0, 0, width=letter[0], height=letter[1])
    pdf.save()

    return path


def make_sample_html(path: Path) -> Path:
    path.write_text(
        """<html><body>
        <nav>Menu noise</nav>
        <main>
          <h1>GST Guide</h1>
          <p>Registration information.</p>
          <table><tr><th>Item</th><th>Fee</th></tr>
          <tr><td>Service</td><td>150</td></tr></table>
          <h2>Registration documents</h2>
        </main>
        <footer>Footer noise</footer>
        <script>Ignore this script</script>
        </body></html>""",
        encoding="utf-8",
    )
    return path
