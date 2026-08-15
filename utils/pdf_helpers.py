from fpdf import FPDF
from services.settings_service import get_business_info


def create_pdf_with_letterhead(title):
    """
    Creates a new FPDF document with the business letterhead
    (Logo/Name/Address/Phone/NTN - only the fields that are set) and a
    centered document title already drawn. Any invoice/receipt
    generator (Sales, Purchase, ...) starts from this.
    """
    business = get_business_info()

    pdf = FPDF(format="A4")
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    logo_path = business.get("logo_path")
    if logo_path:
        try:
            pdf.image(logo_path, x=10, y=8, h=16)
        except Exception:
            pass  # a corrupt/unreadable logo file should never break PDF generation

    if business["name"]:
        pdf.set_font("Helvetica", "B", 16)
        pdf.cell(0, 8, business["name"], ln=True, align="C")

    pdf.set_font("Helvetica", "", 9)
    if business["address"]:
        pdf.cell(0, 5, business["address"], ln=True, align="C")
    if business["phone"]:
        pdf.cell(0, 5, f"Phone: {business['phone']}", ln=True, align="C")
    if business["ntn"]:
        pdf.cell(0, 5, f"NTN: {business['ntn']}", ln=True, align="C")

    pdf.ln(4)
    pdf.set_draw_color(180, 180, 180)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(6)

    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 8, title, ln=True, align="C")
    pdf.ln(4)

    return pdf


def draw_items_table_header(pdf, columns):
    """columns: list of (heading_text, width, align)"""
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_fill_color(30, 41, 59)
    pdf.set_text_color(255, 255, 255)

    for heading, width, align in columns:
        pdf.cell(width, 8, heading, border=1, fill=True, align=align)
    pdf.ln()

    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(0, 0, 0)


def open_pdf(file_path):
    import os
    os.startfile(file_path)