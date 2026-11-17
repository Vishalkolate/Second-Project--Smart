import os
import io
import qrcode
from django.conf import settings
from django.core.files.base import ContentFile
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib import colors
from reportlab.pdfgen import canvas


def generate_qr_for_certificate(cert, host="127.0.0.1:8000"):
    verification_url = f"http://{host}/certificates/verify/{cert.certificate_number}/"
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=6,
        border=2,
    )
    qr.add_data(verification_url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#0f172a", back_color="white")

    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    filename = f"qr_{cert.certificate_number}.png"
    cert.qr_code_image.save(filename, ContentFile(buffer.getvalue()), save=False)


def generate_certificate_pdf(cert, host="127.0.0.1:8000"):
    if not cert.qr_code_image:
        generate_qr_for_certificate(cert, host)
        cert.save()

    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=landscape(letter))
    width, height = landscape(letter)

    # Background / Decorative Border
    p.setFillColor(colors.HexColor('#f8fafc'))
    p.rect(0, 0, width, height, fill=1, stroke=0)

    # Double outer border
    p.setStrokeColor(colors.HexColor('#1e40af'))  # Primary dark blue
    p.setLineWidth(5)
    p.rect(20, 20, width - 40, height - 40)

    p.setStrokeColor(colors.HexColor('#d97706'))  # Gold accent
    p.setLineWidth(1.5)
    p.rect(26, 26, width - 52, height - 52)

    # Institute Name
    p.setFillColor(colors.HexColor('#0f172a'))
    p.setFont("Helvetica-Bold", 26)
    p.drawCentredString(width / 2.0, height - 75, "SMART LMS & INTERNSHIP MANAGEMENT")

    p.setFont("Helvetica-Bold", 12)
    p.setFillColor(colors.HexColor('#475569'))
    p.drawCentredString(width / 2.0, height - 95, "CENTRE FOR PROFESSIONAL DEVELOPMENT & INDUSTRIAL TRAINING")

    # Certificate Title
    p.setFont("Helvetica-Bold", 22)
    p.setFillColor(colors.HexColor('#1e40af'))
    cert_title = "CERTIFICATE OF COMPLETION" if cert.certificate_type == 'Course Completion' else "CERTIFICATE OF INTERNSHIP EXCELLENCE"
    p.drawCentredString(width / 2.0, height - 145, cert_title)

    # Body
    p.setFont("Helvetica", 14)
    p.setFillColor(colors.HexColor('#334155'))
    p.drawCentredString(width / 2.0, height - 180, "This is proudly presented to")

    p.setFont("Helvetica-Bold", 26)
    p.setFillColor(colors.HexColor('#0f172a'))
    student_name = cert.student.get_full_name() or cert.student.username
    p.drawCentredString(width / 2.0, height - 215, student_name.upper())

    # Line under student name
    p.setStrokeColor(colors.HexColor('#94a3b8'))
    p.setLineWidth(1)
    p.line((width / 2.0) - 180, height - 222, (width / 2.0) + 180, height - 222)

    p.setFont("Helvetica", 13)
    p.setFillColor(colors.HexColor('#334155'))
    prog = cert.target_title
    p.drawCentredString(width / 2.0, height - 250, "for successfully fulfilling all requirements and completing")

    p.setFont("Helvetica-Bold", 17)
    p.setFillColor(colors.HexColor('#1e40af'))
    p.drawCentredString(width / 2.0, height - 275, f"'{prog}'")

    p.setFont("Helvetica", 12)
    p.setFillColor(colors.HexColor('#475569'))
    issue_date_str = cert.issue_date.strftime('%B %d, %Y')
    p.drawCentredString(width / 2.0, height - 305, f"Awarded on this day: {issue_date_str}")

    # Certificate ID and Verification note
    p.setFont("Helvetica-Bold", 10)
    p.setFillColor(colors.HexColor('#64748b'))
    p.drawString(50, 65, f"Certificate ID: {cert.certificate_number}")
    p.setFont("Helvetica", 9)
    p.drawString(50, 50, "Scan QR code to verify authenticity online.")

    # Draw QR Code if available
    if cert.qr_code_image and os.path.exists(cert.qr_code_image.path):
        p.drawImage(cert.qr_code_image.path, 50, 85, width=70, height=70)

    # Signatures
    p.line(width - 240, 75, width - 60, 75)
    p.setFont("Helvetica-Bold", 11)
    p.setFillColor(colors.HexColor('#0f172a'))
    p.drawCentredString(width - 150, 60, "Authorized Signatory")
    p.setFont("Helvetica", 9)
    p.setFillColor(colors.HexColor('#64748b'))
    p.drawCentredString(width - 150, 48, "Director of Academic & Technical Affairs")

    p.showPage()
    p.save()

    buffer.seek(0)
    filename = f"cert_{cert.certificate_number}.pdf"
    cert.pdf_file.save(filename, ContentFile(buffer.getvalue()), save=True)
    return cert.pdf_file.url
