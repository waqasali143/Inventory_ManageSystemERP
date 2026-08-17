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


def create_thermal_pdf_with_letterhead(title, paper_width_mm=80):
    """
    Same purpose as create_pdf_with_letterhead(), but sized for a
    thermal receipt roll (80mm or 58mm) instead of A4: narrow width,
    small fonts, tight spacing. Page height is set generously (297mm,
    same as A4's height) since FPDF needs a fixed page size up front -
    on a real continuous-roll thermal printer, the driver cuts the
    paper at the end of the printed content, so the unused length
    below the receipt is not actually a concern in practice.
    """
    business = get_business_info()

    pdf = FPDF(format=(paper_width_mm, 297), unit="mm")
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=6)
    pdf.set_margins(left=3, top=4, right=3)

    logo_max_h = 12 if paper_width_mm >= 80 else 9
    logo_path = business.get("logo_path")
    if logo_path:
        try:
            # Centered small logo above the name, rather than the A4
            # version's top-left placement - there's no room to the
            # side of centered text on a narrow receipt.
            pdf.image(logo_path, x=(paper_width_mm - logo_max_h) / 2, y=pdf.get_y(), h=logo_max_h)
            pdf.ln(logo_max_h + 1)
        except Exception:
            pass

    content_w = paper_width_mm - 6  # inside the 3mm left/right margins

    if business["name"]:
        pdf.set_font("Helvetica", "B", 11)
        pdf.multi_cell(content_w, 4.5, business["name"], align="C")

    pdf.set_font("Helvetica", "", 7.5)
    if business["address"]:
        pdf.multi_cell(content_w, 3.5, business["address"], align="C")
    if business["phone"]:
        pdf.cell(content_w, 3.5, f"Ph: {business['phone']}", ln=True, align="C")
    if business["ntn"]:
        pdf.cell(content_w, 3.5, f"NTN: {business['ntn']}", ln=True, align="C")

    pdf.ln(1)
    pdf.set_draw_color(120, 120, 120)
    pdf.line(pdf.l_margin, pdf.get_y(), paper_width_mm - pdf.r_margin, pdf.get_y())
    pdf.ln(2)

    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(content_w, 5, title, ln=True, align="C")
    pdf.ln(1)

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