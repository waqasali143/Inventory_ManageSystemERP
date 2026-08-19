import tempfile
import os

from datetime import datetime
from services.settings_service import format_currency, get_receipt_printer_type
from services.sales_service import get_sale_header, get_sale_items, get_customer_id_by_name
from services.customer_service import get_customer_filer_status, get_customer_ntn
from utils.pdf_helpers import (
    create_pdf_with_letterhead, create_thermal_pdf_with_letterhead,
    draw_items_table_header, open_pdf
)


def _unique_pdf_path(base_name):
    """
    Builds a temp-folder PDF path that's unique per generation (timestamp
    suffix). Report/statement filenames are otherwise fixed per date-range
    or per customer/supplier, so if a previously generated PDF is still
    open in a viewer, Windows locks it and the next save fails with
    PermissionError. A unique name every time sidesteps that entirely -
    no need to ask the user to close the old file first.
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return os.path.join(tempfile.gettempdir(), f"{base_name}_{timestamp}.pdf")


def _fit_text(value, max_chars=14):
    """
    FPDF's cell() doesn't wrap or clip text - a string longer than its
    column bleeds into the neighboring cell. Used for fields with
    unpredictable length (e.g. contact numbers can be any length),
    where a fixed column width alone can't guarantee it'll fit.

    Uses three ASCII dots ("...") rather than the single Unicode
    ellipsis character ("…") - the standard PDF core font ("helvetica")
    only supports WinAnsi/Latin-1 characters, and "…" isn't one of
    them, which raises FPDFUnicodeEncodingException.
    """
    text = str(value) if value else ""
    if len(text) > max_chars:
        return text[:max_chars - 3] + "..."
    return text


def generate_sale_invoice(sale_id):
    """
    Prints the sale invoice using whichever Receipt Printer type is
    set in Business Settings (A4 / Thermal 80mm / Thermal 58mm) -
    callers never need to know or care which layout was used.
    """
    printer_type = get_receipt_printer_type()

    if printer_type == "thermal_80mm":
        return _generate_sale_invoice_thermal(sale_id, paper_width_mm=80)
    elif printer_type == "thermal_58mm":
        return _generate_sale_invoice_thermal(sale_id, paper_width_mm=58)
    else:
        return generate_sale_invoice_a4(sale_id)


def generate_sale_invoice_a4(sale_id):

    (
        sale_no, customer_name, sale_date,
        gross_total, discount, discount_amount,
        tax, tax_amount, net_total,
        payment_status, amount_paid
    ) = get_sale_header(sale_id)

    items = get_sale_items(sale_id)

    pdf = create_pdf_with_letterhead("SALES INVOICE")

    # ---------------- Header row: Invoice No (left) / Date (right) ----------------
    # Right-aligned to x=175 so it lines up with the items table's
    # right edge below (Product 85 + Price 35 + Qty 25 + Subtotal 45 = 190,
    # same total width the header row spans).
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(95, 6, f"Invoice No: {sale_no}")
    pdf.cell(95, 6, f"Date: {sale_date}", align="R", ln=True)

    pdf.cell(95, 6, f"Customer: {customer_name}", ln=True)

    # Filer customers get their NTN printed automatically (FBR
    # requirement for invoices to registered/filer buyers).
    customer_id = get_customer_id_by_name(customer_name)
    if customer_id and get_customer_filer_status(customer_id):
        ntn = get_customer_ntn(customer_id)
        pdf.cell(95, 6, f"NTN: {ntn}", ln=True)

    pdf.ln(4)

    draw_items_table_header(pdf, [
        ("Product", 85, "L"),
        ("Price", 35, "R"),
        ("Qty", 25, "C"),
        ("Subtotal", 45, "R"),
    ])

    for product, price, qty, subtotal in items:
        pdf.cell(85, 8, str(product), border=1)
        pdf.cell(35, 8, format_currency(price), border=1, align="R")
        pdf.cell(25, 8, str(qty), border=1, align="C")
        pdf.cell(45, 8, format_currency(subtotal), border=1, align="R", ln=True)

    pdf.ln(6)

    def totals_row(label, value, bold=False):
        pdf.set_font("Helvetica", "B" if bold else "", 10)
        pdf.set_x(130)
        pdf.cell(45, 7, label, align="L")
        pdf.cell(25, 7, value, align="R", ln=True)

    totals_row("Gross Total:", format_currency(gross_total))
    totals_row(f"Discount ({discount}%):", format_currency(discount_amount))
    totals_row(f"Tax ({tax}%):", format_currency(tax_amount))
    totals_row("Net Total:", format_currency(net_total), bold=True)

    # ---------------- Payment / Credit Info ----------------
    # Only shown when it's not a plain fully-paid Cash sale, so a
    # normal cash invoice stays exactly as clean as before.
    balance_due = net_total - amount_paid

    if payment_status != "Paid":
        pdf.ln(2)
        totals_row("Amount Paid:", format_currency(amount_paid))
        totals_row(f"Balance Due ({payment_status}):", format_currency(balance_due), bold=True)

    pdf.ln(15)
    pdf.set_font("Helvetica", "I", 8)
    pdf.cell(0, 5, f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M')}", align="C")

    file_path = _unique_pdf_path(sale_no)
    pdf.output(file_path)

    open_pdf(file_path)

    return file_path
# ================================================================


def _generate_sale_invoice_thermal(sale_id, paper_width_mm=80):

    (
        sale_no, customer_name, sale_date,
        gross_total, discount, discount_amount,
        tax, tax_amount, net_total,
        payment_status, amount_paid
    ) = get_sale_header(sale_id)

    items = get_sale_items(sale_id)

    pdf = create_thermal_pdf_with_letterhead("SALES RECEIPT", paper_width_mm)
    content_w = paper_width_mm - 6

    pdf.set_font("Helvetica", "", 7.5)
    pdf.cell(content_w, 4, f"Invoice: {sale_no}", ln=True)
    pdf.cell(content_w, 4, f"Date: {sale_date}", ln=True)
    pdf.multi_cell(content_w, 4, f"Customer: {customer_name}")

    customer_id = get_customer_id_by_name(customer_name)
    if customer_id and get_customer_filer_status(customer_id):
        ntn = get_customer_ntn(customer_id)
        pdf.cell(content_w, 4, f"NTN: {ntn}", ln=True)

    pdf.ln(1)
    pdf.set_draw_color(150, 150, 150)
    pdf.line(pdf.l_margin, pdf.get_y(), paper_width_mm - pdf.r_margin, pdf.get_y())
    pdf.ln(2)

    # ---- Items: name on its own line, "qty x price" / subtotal below -
    # a single row per item doesn't fit legibly at 58-80mm width.
    for product, price, qty, subtotal in items:
        pdf.set_font("Helvetica", "B", 7.5)
        pdf.multi_cell(content_w, 3.6, str(product))
        pdf.set_font("Helvetica", "", 7.5)
        pdf.cell(content_w * 0.6, 3.6, f"{qty} x {format_currency(price)}")
        pdf.cell(content_w * 0.4, 3.6, format_currency(subtotal), align="R", ln=True)

    pdf.ln(1)
    pdf.line(pdf.l_margin, pdf.get_y(), paper_width_mm - pdf.r_margin, pdf.get_y())
    pdf.ln(2)

    def totals_row(label, value, bold=False):
        pdf.set_font("Helvetica", "B" if bold else "", 7.5)
        pdf.cell(content_w * 0.6, 4, label)
        pdf.cell(content_w * 0.4, 4, value, align="R", ln=True)

    totals_row("Gross Total:", format_currency(gross_total))
    totals_row(f"Discount ({discount}%):", format_currency(discount_amount))
    totals_row(f"Tax ({tax}%):", format_currency(tax_amount))
    totals_row("Net Total:", format_currency(net_total), bold=True)

    balance_due = net_total - amount_paid
    if payment_status != "Paid":
        pdf.ln(1)
        totals_row("Amount Paid:", format_currency(amount_paid))
        totals_row(f"Balance ({payment_status}):", format_currency(balance_due), bold=True)

    pdf.ln(3)
    pdf.set_font("Helvetica", "I", 6.5)
    pdf.multi_cell(content_w, 3, f"Printed {datetime.now().strftime('%Y-%m-%d %H:%M')}", align="C")
    pdf.ln(1)
    pdf.set_font("Helvetica", "B", 8)
    pdf.multi_cell(content_w, 4, "Thank you for your business!", align="C")

    file_path = _unique_pdf_path(sale_no)
    pdf.output(file_path)

    open_pdf(file_path)

    return file_path
# ================================================================

def generate_sales_report_pdf(rows, date_from, date_to):
    """
    rows: the same rows shown in the Sales History table
          (id, sale_no, customer, date, ..., net_total, ...)
    Prints a summary listing (not individual invoices).
    """
    pdf = create_pdf_with_letterhead(f"SALES REPORT ({date_from} to {date_to})")

    draw_items_table_header(pdf, [
        ("Sale No", 45, "L"),
        ("Customer", 55, "L"),
        ("Date", 45, "L"),
        ("Net Total", 45, "R"),
    ])

    grand_total = 0.0

    for row in rows:
        sale_no, customer, date_str, net_total = row[1], row[2], row[3], row[9]
        pdf.cell(45, 8, str(sale_no), border=1)
        pdf.cell(55, 8, str(customer), border=1)
        pdf.cell(45, 8, str(date_str), border=1)
        pdf.cell(45, 8, format_currency(net_total), border=1, align="R", ln=True)
        grand_total += net_total

    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(145, 8, "Grand Total", border=1)
    pdf.cell(45, 8, format_currency(grand_total), border=1, align="R", ln=True)

    file_path = _unique_pdf_path(f"Sales_Report_{date_from}_to_{date_to}")
    pdf.output(file_path)

    open_pdf(file_path)

    return file_path


# ================================================================
# PRODUCT LIST (Products screen - "Print Product List" button)
# ================================================================
def generate_product_list_pdf(rows, search_term=None):
    """
    rows: the same rows shown in the Product Management table
          (id, name, cost_price, sale_price, quantity, status, barcode)
    Prints the currently visible list (respects an active search filter,
    if any) with Cost Price and Stock Value (Cost Price x Quantity), so
    it can double as a stock-value sheet for stock-taking or an auditor.
    """
    title = "PRODUCT LIST"
    if search_term:
        title += f' (filtered: "{search_term}")'

    pdf = create_pdf_with_letterhead(title)

    draw_items_table_header(pdf, [
        ("Product Name", 54, "L"),
        ("Barcode", 24, "L"),
        ("Cost Price", 24, "R"),
        ("Sale Price", 24, "R"),
        ("Qty", 14, "C"),
        ("Status", 22, "C"),
        ("Stock Value", 28, "R"),
    ])

    total_qty = 0
    total_stock_value = 0.0

    for _id, name, cost_price, sale_price, quantity, status, barcode in rows:
        stock_value = cost_price * quantity

        pdf.cell(54, 8, str(name), border=1)
        pdf.cell(24, 8, str(barcode or "-"), border=1)
        pdf.cell(24, 8, format_currency(cost_price), border=1, align="R")
        pdf.cell(24, 8, format_currency(sale_price), border=1, align="R")
        pdf.cell(14, 8, str(quantity), border=1, align="C")
        pdf.cell(22, 8, str(status), border=1, align="C")
        pdf.cell(28, 8, format_currency(stock_value), border=1, align="R", ln=True)

        total_qty += quantity
        total_stock_value += stock_value

    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(138, 8, f"Total ({len(rows)} products, {total_qty} units in stock)", border=1)
    pdf.cell(52, 8, format_currency(total_stock_value), border=1, align="R", ln=True)

    file_path = _unique_pdf_path("Product_List")
    pdf.output(file_path)

    open_pdf(file_path)

    return file_path
# ================================================================
# PURCHASE RECEIPT
# ================================================================
from services.purchase_service import get_purchase_header, get_purchase_items
from services.supplier_service import get_supplier_filer_status


def generate_purchase_receipt(purchase_id):

    (
        purchase_no, invoice_no, supplier_name, purchase_date,
        gross_total, discount, discount_amount,
        tax, tax_amount, net_total,
        payment_status, amount_paid
    ) = get_purchase_header(purchase_id)

    items = get_purchase_items(purchase_id)

    pdf = create_pdf_with_letterhead("PURCHASE RECEIPT")

    # ---------------- Header row: Purchase No (left) / Date (right) ----------------
    # Same right-alignment fix as the sales invoice above.
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(95, 6, f"Purchase No: {purchase_no}")
    pdf.cell(95, 6, f"Date: {purchase_date}", align="R", ln=True)

    pdf.cell(95, 6, f"Supplier: {supplier_name}")
    pdf.cell(95, 6, f"Supplier Invoice No: {invoice_no or '-'}", align="R", ln=True)
    pdf.ln(4)

    draw_items_table_header(pdf, [
        ("Product", 85, "L"),
        ("Price", 35, "R"),
        ("Qty", 25, "C"),
        ("Subtotal", 45, "R"),
    ])

    for product, price, qty, subtotal in items:
        pdf.cell(85, 8, str(product), border=1)
        pdf.cell(35, 8, format_currency(price), border=1, align="R")
        pdf.cell(25, 8, str(qty), border=1, align="C")
        pdf.cell(45, 8, format_currency(subtotal), border=1, align="R", ln=True)

    pdf.ln(6)

    def totals_row(label, value, bold=False):
        pdf.set_font("Helvetica", "B" if bold else "", 10)
        pdf.set_x(130)
        pdf.cell(45, 7, label, align="L")
        pdf.cell(25, 7, value, align="R", ln=True)

    totals_row("Gross Total:", format_currency(gross_total))
    totals_row(f"Discount ({discount}%):", format_currency(discount_amount))
    totals_row(f"Tax ({tax}%):", format_currency(tax_amount))
    totals_row("Net Total:", format_currency(net_total), bold=True)

    # ---------------- Payment / Credit Info ----------------
    balance_due = net_total - amount_paid

    if payment_status != "Paid":
        pdf.ln(2)
        totals_row("Amount Paid:", format_currency(amount_paid))
        totals_row(f"Balance Due ({payment_status}):", format_currency(balance_due), bold=True)

    pdf.ln(15)
    pdf.set_font("Helvetica", "I", 8)
    pdf.cell(0, 5, f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M')}", align="C")

    file_path = _unique_pdf_path(purchase_no)
    pdf.output(file_path)

    open_pdf(file_path)

    return file_path


def generate_purchase_report_pdf(rows, date_from, date_to):
    """
    rows: the same rows shown in the Purchase History table
          (id, purchase_no, supplier, gross_total, ..., net_total, date, ...)
    """
    pdf = create_pdf_with_letterhead(f"PURCHASE REPORT ({date_from} to {date_to})")

    draw_items_table_header(pdf, [
        ("Purchase No", 45, "L"),
        ("Supplier", 55, "L"),
        ("Date", 45, "L"),
        ("Net Total", 45, "R"),
    ])

    grand_total = 0.0

    for row in rows:
        purchase_no, supplier, date_str, net_total = row[1], row[2], row[9], row[8]
        pdf.cell(45, 8, str(purchase_no), border=1)
        pdf.cell(55, 8, str(supplier), border=1)
        pdf.cell(45, 8, str(date_str), border=1)
        pdf.cell(45, 8, format_currency(net_total), border=1, align="R", ln=True)
        grand_total += net_total

    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(145, 8, "Grand Total", border=1)
    pdf.cell(45, 8, format_currency(grand_total), border=1, align="R", ln=True)

    file_path = _unique_pdf_path(f"Purchase_Report_{date_from}_to_{date_to}")
    pdf.output(file_path)

    open_pdf(file_path)

    return file_path

# ================================================================
# CUSTOMER STATEMENT
# ================================================================
def generate_customer_statement(customer_name, rows):
    """
    rows: same as get_sales_by_customer() returns
          (id, sale_no, date, gross_total, discount_amount, tax_amount,
           net_total, payment_status, balance_due)
    """
    pdf = create_pdf_with_letterhead(f"CUSTOMER STATEMENT - {customer_name}")

    draw_items_table_header(pdf, [
        ("Sale No", 32, "L"),
        ("Date", 38, "L"),
        ("Net Total", 30, "R"),
        ("Payment", 25, "C"),
        ("Amount Paid", 30, "R"),
        ("Balance Due", 30, "R"),
    ])

    total_purchased = 0.0
    total_balance = 0.0

    for row in rows:
        sale_id, sale_no, date_str, gross_total, discount_amount, tax_amount, \
            net_total, payment_status, balance_due = row
        amount_paid = net_total - balance_due

        pdf.cell(32, 8, str(sale_no), border=1)
        pdf.cell(38, 8, str(date_str), border=1)
        pdf.cell(30, 8, format_currency(net_total), border=1, align="R")
        pdf.cell(25, 8, str(payment_status), border=1, align="C")
        pdf.cell(30, 8, format_currency(amount_paid), border=1, align="R")
        pdf.cell(30, 8, format_currency(balance_due), border=1, align="R", ln=True)

        total_purchased += net_total
        total_balance += balance_due

    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(125, 8, "Total Purchased", border=1)
    pdf.cell(30, 8, format_currency(total_purchased), border=1, align="R", ln=True)

    pdf.cell(125, 8, "Total Outstanding Balance", border=1)
    pdf.cell(30, 8, format_currency(total_balance), border=1, align="R", ln=True)

    file_path = _unique_pdf_path(f"Statement_{customer_name}")
    pdf.output(file_path)

    open_pdf(file_path)

    return file_path

# ================================================================
# SUPPLIER STATEMENT
# ================================================================
def generate_supplier_statement(supplier_name, rows):
    """
    rows: same as get_purchases_by_supplier() returns
          (id, purchase_no, date, gross_total, discount_amount, tax_amount,
           net_total, payment_status, balance_due)
    """
    pdf = create_pdf_with_letterhead(f"SUPPLIER STATEMENT - {supplier_name}")

    draw_items_table_header(pdf, [
        ("Purchase No", 32, "L"),
        ("Date", 38, "L"),
        ("Net Total", 30, "R"),
        ("Payment", 25, "C"),
        ("Amount Paid", 30, "R"),
        ("Balance Due", 30, "R"),
    ])

    total_spent = 0.0
    total_balance = 0.0

    for row in rows:
        purchase_id, purchase_no, date_str, gross_total, discount_amount, tax_amount, \
            net_total, payment_status, balance_due = row[:9]
        amount_paid = net_total - balance_due

        pdf.cell(32, 8, str(purchase_no), border=1)
        pdf.cell(38, 8, str(date_str), border=1)
        pdf.cell(30, 8, format_currency(net_total), border=1, align="R")
        pdf.cell(25, 8, str(payment_status), border=1, align="C")
        pdf.cell(30, 8, format_currency(amount_paid), border=1, align="R")
        pdf.cell(30, 8, format_currency(balance_due), border=1, align="R", ln=True)

        total_spent += net_total
        total_balance += balance_due

    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(125, 8, "Total Spent", border=1)
    pdf.cell(30, 8, format_currency(total_spent), border=1, align="R", ln=True)

    pdf.cell(125, 8, "Total Outstanding Balance", border=1)
    pdf.cell(30, 8, format_currency(total_balance), border=1, align="R", ln=True)

    file_path = _unique_pdf_path(f"Statement_{supplier_name}")
    pdf.output(file_path)

    open_pdf(file_path)

    return file_path

# ================================================================
# BUSINESS REPORT (Reports window se)
# ================================================================
def generate_business_report_pdf(data, date_from, date_to, product_details=None,
                                  unsold_products=None, credit_data=None):
    """
    data: dictionary from get_report_data()
    product_details: list from get_product_wise_report()
    unsold_products: list from get_unsold_products()
    credit_data: dict from credit_service.get_credit_report_data()
                 {"customers": [...], "suppliers": [...],
                  "total_receivable": x, "total_payable": y}
    """
    pdf = create_pdf_with_letterhead(f"BUSINESS REPORT ({date_from} to {date_to})")

    # ---------------- Summary ----------------
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 8, "Summary", ln=True)
    pdf.set_font("Helvetica", "", 10)

    summary_rows = [
        ("Total Sales (Incl. Tax)", data["total_sales"]),
        ("Total Purchases (Incl. Tax)", data["total_purchases"]),
        ("Cost of Sold Items (COGS, Excl. Tax)", data["cost_of_sold_items"]),
        ("Tax Collected (Sales)", data["sales_tax"]),
        ("Tax Paid (Purchases)", data["purchase_tax"]),
        ("Gross Profit (from items sold, Excl. Tax)", data["gross_profit"]),
        ("Total Expenses", data["total_expenses"]),
        ("Total Profit (Excl. Tax)", data["total_profit"]),
    ]

    if credit_data:
        summary_rows.append(("Total Receivable (owed by customers)", credit_data["total_receivable"]))
        summary_rows.append(("Total Payable (owed to suppliers)", credit_data["total_payable"]))

    for label, value in summary_rows:
        pdf.cell(130, 7, label)
        pdf.cell(60, 7, format_currency(value), align="R", ln=True)

    pdf.ln(6)

    # ---------------- Best Selling Products ----------------
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 8, "Top 10 Best-Selling Products", ln=True)

    draw_items_table_header(pdf, [
        ("Product", 95, "L"),
        ("Qty Sold", 40, "C"),
        ("Revenue", 55, "R"),
    ])

    for name, qty, revenue in data["best_products"]:
        pdf.cell(95, 8, str(name), border=1)
        pdf.cell(40, 8, str(qty), border=1, align="C")
        pdf.cell(55, 8, format_currency(revenue), border=1, align="R", ln=True)

    pdf.ln(6)

    # ---------------- Worst Selling Products ----------------
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 8, "Top 10 Worst-Selling Products", ln=True)

    draw_items_table_header(pdf, [
        ("Product", 95, "L"),
        ("Qty Sold", 40, "C"),
        ("Revenue", 55, "R"),
    ])

    for name, qty, revenue in data["worst_products"]:
        pdf.cell(95, 8, str(name), border=1)
        pdf.cell(40, 8, str(qty), border=1, align="C")
        pdf.cell(55, 8, format_currency(revenue), border=1, align="R", ln=True)

    pdf.ln(6)

    # ---------------- Full Product-wise Profit Breakdown ----------------
    if product_details:
        pdf.add_page()
        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(0, 8, "Product-wise Profit Breakdown", ln=True)

        draw_items_table_header(pdf, [
            ("Product", 34, "L"),
            ("Qty", 10, "C"),
            ("Revenue", 24, "R"),
            ("Discount", 20, "R"),
            ("Cost", 24, "R"),
            ("Profit", 24, "R"),
            ("Stock", 22, "C"),
            ("On Credit", 32, "R"),
        ])

        pdf.set_font("Helvetica", "", 8)

        for name, qty, revenue, discount, cost, profit, stock, credit in product_details:
            pdf.cell(34, 8, str(name), border=1)
            pdf.cell(10, 8, str(qty), border=1, align="C")
            pdf.cell(24, 8, format_currency(revenue), border=1, align="R")
            pdf.cell(20, 8, format_currency(discount), border=1, align="R")
            pdf.cell(24, 8, format_currency(cost), border=1, align="R")
            pdf.cell(24, 8, format_currency(profit), border=1, align="R")
            pdf.cell(22, 8, str(stock), border=1, align="C")
            pdf.cell(32, 8, format_currency(credit), border=1, align="R", ln=True)

    # ---------------- Products Not Sold (4-column layout) ----------------
    if unsold_products:
        pdf.add_page()
        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(0, 8, "Products Not Sold in This Period", ln=True)
        pdf.ln(2)

        pdf.set_font("Helvetica", "B", 9)
        pdf.set_fill_color(30, 41, 59)
        pdf.set_text_color(255, 255, 255)
        pdf.cell(65, 7, "Product", border=1, fill=True)
        pdf.cell(30, 7, "Stock", border=1, fill=True, align="C")
        pdf.cell(65, 7, "Product", border=1, fill=True)
        pdf.cell(30, 7, "Stock", border=1, fill=True, align="C", ln=True)

        pdf.set_font("Helvetica", "", 8)
        pdf.set_text_color(0, 0, 0)

        for i in range(0, len(unsold_products), 2):
            left_name, left_stock = unsold_products[i]

            pdf.cell(65, 7, str(left_name)[:30], border=1)
            pdf.cell(30, 7, str(left_stock), border=1, align="C")

            if i + 1 < len(unsold_products):
                right_name, right_stock = unsold_products[i + 1]
                pdf.cell(65, 7, str(right_name)[:30], border=1)
                pdf.cell(30, 7, str(right_stock), border=1, align="C", ln=True)
            else:
                pdf.cell(65, 7, "", border=1)
                pdf.cell(30, 7, "", border=1, ln=True)

    # ---------------- Credit Summary (own page, own heading) ----------------
    if credit_data:
        pdf.add_page()
        pdf.set_font("Helvetica", "B", 13)
        pdf.cell(0, 10, "CREDIT SUMMARY", ln=True, align="C")
        pdf.ln(2)

        pdf.set_font("Helvetica", "", 10)
        pdf.cell(130, 7, "Total Receivable (owed by customers)")
        pdf.cell(60, 7, format_currency(credit_data["total_receivable"]), align="R", ln=True)

        pdf.cell(130, 7, "Total Payable (owed to suppliers)")
        pdf.cell(60, 7, format_currency(credit_data["total_payable"]), align="R", ln=True)

        pdf.ln(6)

        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(0, 8, "Customers - Balance Owed", ln=True)

        draw_items_table_header(pdf, [
            ("Customer", 38, "L"),
            ("Contact", 32, "L"),
            ("Balance", 32, "R"),
            ("Paid", 28, "R"),
            ("Inv", 10, "C"),
            ("Last Amt", 28, "R"),
            ("Last Date", 22, "C"),
        ])

        for _id, name, contact, balance, amount_paid, open_invoices, \
                last_payment_amount, last_payment_date in credit_data["customers"]:
            pdf.cell(38, 8, _fit_text(name, 18), border=1)
            pdf.cell(32, 8, _fit_text(contact, 15), border=1)
            pdf.cell(32, 8, format_currency(balance), border=1, align="R")
            pdf.cell(28, 8, format_currency(amount_paid), border=1, align="R")
            pdf.cell(10, 8, str(open_invoices), border=1, align="C")
            pdf.cell(28, 8, format_currency(last_payment_amount) if last_payment_amount is not None else "-",
                      border=1, align="R")
            pdf.cell(22, 8, last_payment_date or "-", border=1, align="C", ln=True)

        if not credit_data["customers"]:
            pdf.set_font("Helvetica", "I", 9)
            pdf.cell(0, 7, "No outstanding customer balances.", ln=True)

        pdf.ln(6)

        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(0, 8, "Suppliers - Balance We Owe", ln=True)

        draw_items_table_header(pdf, [
            ("Supplier", 38, "L"),
            ("Contact", 32, "L"),
            ("Balance", 32, "R"),
            ("Paid", 28, "R"),
            ("Inv", 10, "C"),
            ("Last Amt", 28, "R"),
            ("Last Date", 22, "C"),
        ])

        for _id, name, contact, balance, amount_paid, open_invoices, \
                last_payment_amount, last_payment_date in credit_data["suppliers"]:
            pdf.cell(38, 8, _fit_text(name, 18), border=1)
            pdf.cell(32, 8, _fit_text(contact, 15), border=1)
            pdf.cell(32, 8, format_currency(balance), border=1, align="R")
            pdf.cell(28, 8, format_currency(amount_paid), border=1, align="R")
            pdf.cell(10, 8, str(open_invoices), border=1, align="C")
            pdf.cell(28, 8, format_currency(last_payment_amount) if last_payment_amount is not None else "-",
                      border=1, align="R")
            pdf.cell(22, 8, last_payment_date or "-", border=1, align="C", ln=True)

        if not credit_data["suppliers"]:
            pdf.set_font("Helvetica", "I", 9)
            pdf.cell(0, 7, "No outstanding supplier balances.", ln=True)

    pdf.ln(15)
    pdf.set_font("Helvetica", "I", 8)
    pdf.cell(0, 5, f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M')}", align="C")

    file_path = _unique_pdf_path(f"Business_Report_{date_from}_to_{date_to}")
    pdf.output(file_path)

    open_pdf(file_path)

    return file_path


# ================================================================
# CREDIT REPORT (Reports window - new "Credit" tab)
# ================================================================
def generate_credit_report_pdf(report_data):
    """
    report_data: dict from credit_service.get_credit_report_data()
                 {"customers": [...], "suppliers": [...],
                  "total_receivable": x, "total_payable": y}
    """
    pdf = create_pdf_with_letterhead("CREDIT REPORT")

    # ---------------- Summary ----------------
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 8, "Summary", ln=True)
    pdf.set_font("Helvetica", "", 10)

    pdf.cell(130, 7, "Total Receivable (owed by customers)")
    pdf.cell(60, 7, format_currency(report_data["total_receivable"]), align="R", ln=True)

    pdf.cell(130, 7, "Total Payable (owed to suppliers)")
    pdf.cell(60, 7, format_currency(report_data["total_payable"]), align="R", ln=True)

    pdf.ln(6)

    # ---------------- Customers ----------------
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 8, "Customers - Balance Owed", ln=True)

    draw_items_table_header(pdf, [
        ("Customer", 38, "L"),
        ("Contact", 32, "L"),
        ("Balance", 32, "R"),
        ("Paid", 28, "R"),
        ("Inv", 10, "C"),
        ("Last Amt", 28, "R"),
        ("Last Date", 22, "C"),
    ])

    for customer_id, name, contact, balance, amount_paid, open_invoices, \
            last_payment_amount, last_payment_date in report_data["customers"]:
        pdf.cell(38, 8, _fit_text(name, 18), border=1)
        pdf.cell(32, 8, _fit_text(contact, 15), border=1)
        pdf.cell(32, 8, format_currency(balance), border=1, align="R")
        pdf.cell(28, 8, format_currency(amount_paid), border=1, align="R")
        pdf.cell(10, 8, str(open_invoices), border=1, align="C")
        pdf.cell(28, 8, format_currency(last_payment_amount) if last_payment_amount is not None else "-",
                  border=1, align="R")
        pdf.cell(22, 8, last_payment_date or "-", border=1, align="C", ln=True)

    pdf.ln(6)

    # ---------------- Suppliers ----------------
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 8, "Suppliers - Balance We Owe", ln=True)

    draw_items_table_header(pdf, [
        ("Supplier", 38, "L"),
        ("Contact", 32, "L"),
        ("Balance", 32, "R"),
        ("Paid", 28, "R"),
        ("Inv", 10, "C"),
        ("Last Amt", 28, "R"),
        ("Last Date", 22, "C"),
    ])

    for supplier_id, name, contact, balance, amount_paid, open_invoices, \
            last_payment_amount, last_payment_date in report_data["suppliers"]:
        pdf.cell(38, 8, _fit_text(name, 18), border=1)
        pdf.cell(32, 8, _fit_text(contact, 15), border=1)
        pdf.cell(32, 8, format_currency(balance), border=1, align="R")
        pdf.cell(28, 8, format_currency(amount_paid), border=1, align="R")
        pdf.cell(10, 8, str(open_invoices), border=1, align="C")
        pdf.cell(28, 8, format_currency(last_payment_amount) if last_payment_amount is not None else "-",
                  border=1, align="R")
        pdf.cell(22, 8, last_payment_date or "-", border=1, align="C", ln=True)

    pdf.ln(15)
    pdf.set_font("Helvetica", "I", 8)
    pdf.cell(0, 5, f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M')}", align="C")

    file_path = _unique_pdf_path("Credit_Report")
    pdf.output(file_path)

    open_pdf(file_path)

    return file_path


# =====================================================================
# CREDIT STATEMENT (per Customer/Supplier - "View Statement" window in
# Credit Ledger). Two sections: open credit transactions, and the full
# payment history received/made for that party.
# =====================================================================
def generate_credit_statement_pdf(party_type, party_name, credit_rows, payment_rows):
    """
    party_type: "Customer" or "Supplier"
    credit_rows: (id, no, date, net_total, amount_paid_at_sale, balance, payment_status)
                 - same as get_customer_credit_sales()/get_supplier_credit_purchases()
    payment_rows: (date, amount, notes, invoice_no)
                 - same as get_customer_payment_history()/get_supplier_payment_history()
                 - invoice_no is None for a general/untargeted payment
    """
    pdf = create_pdf_with_letterhead(f"{party_type.upper()} CREDIT STATEMENT - {party_name}")

    # ---------------- Unpaid / Partial Transactions ----------------
    doc_label = "Sales" if party_type == "Customer" else "Purchases"
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 8, f"Unpaid / Partial {doc_label}", ln=True)

    draw_items_table_header(pdf, [
        ("No", 34, "L"),
        ("Date", 38, "L"),
        ("Net Total", 32, "R"),
        ("Paid at Sale", 32, "R"),
        ("Balance", 32, "R"),
        ("Status", 22, "C"),
    ])

    total_balance = 0.0
    for _id, no, date_str, net_total, amount_paid, balance, payment_status in credit_rows:
        pdf.cell(34, 8, str(no), border=1)
        pdf.cell(38, 8, str(date_str), border=1)
        pdf.cell(32, 8, format_currency(net_total), border=1, align="R")
        pdf.cell(32, 8, format_currency(amount_paid), border=1, align="R")
        pdf.cell(32, 8, format_currency(balance), border=1, align="R")
        pdf.cell(22, 8, str(payment_status), border=1, align="C", ln=True)
        total_balance += balance

    if not credit_rows:
        pdf.set_font("Helvetica", "I", 9)
        pdf.cell(0, 7, "No unpaid or partial records.", ln=True)
        pdf.set_font("Helvetica", "", 10)
    else:
        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(136, 8, "Total Outstanding Balance", border=1)
        pdf.cell(32, 8, format_currency(total_balance), border=1, align="R")
        pdf.cell(22, 8, "", border=1, ln=True)
        pdf.set_font("Helvetica", "", 10)

    pdf.ln(6)

    # ---------------- Payment History ----------------
    payment_label = "Payments Received" if party_type == "Customer" else "Payments Made"
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 8, payment_label, ln=True)

    draw_items_table_header(pdf, [
        ("Date", 34, "L"),
        ("Amount", 32, "R"),
        ("Applied To Invoice", 44, "C"),
        ("Notes", 80, "L"),
    ])

    total_paid = 0.0
    for date_str, amount, notes, invoice_no in payment_rows:
        pdf.cell(34, 8, str(date_str), border=1)
        pdf.cell(32, 8, format_currency(amount), border=1, align="R")
        pdf.cell(44, 8, str(invoice_no) if invoice_no else "General payment", border=1, align="C")
        pdf.cell(80, 8, str(notes or ""), border=1, ln=True)
        total_paid += amount

    if not payment_rows:
        pdf.set_font("Helvetica", "I", 9)
        pdf.cell(0, 7, "No payments recorded yet.", ln=True)
    else:
        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(34, 8, "Total Paid", border=1)
        pdf.cell(32, 8, format_currency(total_paid), border=1, align="R")
        pdf.cell(124, 8, "", border=1, ln=True)

    file_path = _unique_pdf_path(f"Statement_{party_name}")
    pdf.output(file_path)

    open_pdf(file_path)

    return file_path