import tempfile
import os

from datetime import datetime
from services.settings_service import format_currency
from services.sales_service import get_sale_header, get_sale_items, get_customer_id_by_name
from services.customer_service import get_customer_filer_status, get_customer_ntn
from utils.pdf_helpers import create_pdf_with_letterhead, draw_items_table_header, open_pdf


def generate_sale_invoice(sale_id):

    (
        sale_no, customer_name, sale_date,
        gross_total, discount, discount_amount,
        tax, tax_amount, net_total
    ) = get_sale_header(sale_id)

    items = get_sale_items(sale_id)

    pdf = create_pdf_with_letterhead("SALES INVOICE")

    pdf.set_font("Helvetica", "", 10)
    pdf.cell(95, 6, f"Invoice No: {sale_no}")
    pdf.cell(95, 6, f"Date: {sale_date}", ln=True)
    pdf.cell(95, 6, f"Customer: {customer_name}", ln=True)
    
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

    pdf.ln(15)
    pdf.set_font("Helvetica", "I", 8)
    pdf.cell(0, 5, f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M')}", align="C")

    file_path = os.path.join(tempfile.gettempdir(), f"{sale_no}.pdf")
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

    file_path = os.path.join(tempfile.gettempdir(), f"Sales_Report_{date_from}_to_{date_to}.pdf")
    pdf.output(file_path)

    open_pdf(file_path)

    return file_path
# ================================================================
# PURCHASE RECEIPT
# ================================================================
from services.purchase_service import get_purchase_header, get_purchase_items


def generate_purchase_receipt(purchase_id):

    (
        purchase_no, invoice_no, supplier_name, purchase_date,
        gross_total, discount, discount_amount,
        tax, tax_amount, net_total
    ) = get_purchase_header(purchase_id)

    items = get_purchase_items(purchase_id)

    pdf = create_pdf_with_letterhead("PURCHASE RECEIPT")

    pdf.set_font("Helvetica", "", 10)
    pdf.cell(95, 6, f"Purchase No: {purchase_no}")
    pdf.cell(95, 6, f"Date: {purchase_date}", ln=True)
    pdf.cell(95, 6, f"Supplier: {supplier_name}")
    pdf.cell(95, 6, f"Supplier Invoice No: {invoice_no or '-'}", ln=True)
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

    pdf.ln(15)
    pdf.set_font("Helvetica", "I", 8)
    pdf.cell(0, 5, f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M')}", align="C")

    file_path = os.path.join(tempfile.gettempdir(), f"{purchase_no}.pdf")
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

    file_path = os.path.join(tempfile.gettempdir(), f"Purchase_Report_{date_from}_to_{date_to}.pdf")
    pdf.output(file_path)

    open_pdf(file_path)

    return file_path

# ================================================================
# CUSTOMER STATEMENT
# ================================================================
def generate_customer_statement(customer_name, rows):
    """
    rows: same as get_sales_by_customer() returns
          (id, sale_no, date, gross_total, discount_amount, tax_amount, net_total)
    """
    pdf = create_pdf_with_letterhead(f"CUSTOMER STATEMENT - {customer_name}")

    draw_items_table_header(pdf, [
        ("Sale No", 45, "L"),
        ("Date", 55, "L"),
        ("Gross Total", 45, "R"),
        ("Net Total", 45, "R"),
    ])

    total_purchased = 0.0

    for row in rows:
        sale_id, sale_no, date_str, gross_total, discount_amount, tax_amount, net_total = row
        pdf.cell(45, 8, str(sale_no), border=1)
        pdf.cell(55, 8, str(date_str), border=1)
        pdf.cell(45, 8, format_currency(gross_total), border=1, align="R")
        pdf.cell(45, 8, format_currency(net_total), border=1, align="R", ln=True)
        total_purchased += net_total

    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(145, 8, "Total Purchased", border=1)
    pdf.cell(45, 8, format_currency(total_purchased), border=1, align="R", ln=True)

    file_path = os.path.join(tempfile.gettempdir(), f"Statement_{customer_name}.pdf")
    pdf.output(file_path)

    open_pdf(file_path)

    return file_path

# ================================================================
# SUPPLIER STATEMENT
# ================================================================
def generate_supplier_statement(supplier_name, rows):
    """
    rows: same as get_purchases_by_supplier() returns
          (id, purchase_no, date, gross_total, discount_amount, tax_amount, net_total)
    """
    pdf = create_pdf_with_letterhead(f"SUPPLIER STATEMENT - {supplier_name}")

    draw_items_table_header(pdf, [
        ("Purchase No", 45, "L"),
        ("Date", 55, "L"),
        ("Gross Total", 45, "R"),
        ("Net Total", 45, "R"),
    ])

    total_spent = 0.0

    for row in rows:
        purchase_id, purchase_no, date_str, gross_total, discount_amount, tax_amount, net_total = row
        pdf.cell(45, 8, str(purchase_no), border=1)
        pdf.cell(55, 8, str(date_str), border=1)
        pdf.cell(45, 8, format_currency(gross_total), border=1, align="R")
        pdf.cell(45, 8, format_currency(net_total), border=1, align="R", ln=True)
        total_spent += net_total

    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(145, 8, "Total Spent", border=1)
    pdf.cell(45, 8, format_currency(total_spent), border=1, align="R", ln=True)

    file_path = os.path.join(tempfile.gettempdir(), f"Statement_{supplier_name}.pdf")
    pdf.output(file_path)

    open_pdf(file_path)

    return file_path

# ================================================================
# BUSINESS REPORT (Reports window se)
# ================================================================
def generate_business_report_pdf(data, date_from, date_to, product_details=None, unsold_products=None):
    """
    data: dictionary from get_report_data()
    product_details: list from get_product_wise_report()
    unsold_products: list from get_unsold_products()
    """
    pdf = create_pdf_with_letterhead(f"BUSINESS REPORT ({date_from} to {date_to})")

    # ---------------- Summary ----------------
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 8, "Summary", ln=True)
    pdf.set_font("Helvetica", "", 10)

    summary_rows = [
        ("Total Sales", data["total_sales"]),
        ("Total Purchases", data["total_purchases"]),
        ("Gross Profit (from items sold)", data["gross_profit"]),
        ("Total Expenses", data["total_expenses"]),
        ("Total Profit", data["total_profit"]),
    ]

    for label, value in summary_rows:
        pdf.cell(90, 7, label)
        pdf.cell(60, 7, format_currency(value), align="R", ln=True)

    pdf.ln(6)

    # ---------------- Best Selling Products ----------------
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 8, "Top 10 Best-Selling Products", ln=True)

    draw_items_table_header(pdf, [
        ("Product", 90, "L"),
        ("Qty Sold", 40, "C"),
        ("Revenue", 45, "R"),
    ])

    for name, qty, revenue in data["best_products"]:
        pdf.cell(90, 8, str(name), border=1)
        pdf.cell(40, 8, str(qty), border=1, align="C")
        pdf.cell(45, 8, format_currency(revenue), border=1, align="R", ln=True)

    pdf.ln(6)

    # ---------------- Worst Selling Products ----------------
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 8, "Top 10 Worst-Selling Products", ln=True)

    draw_items_table_header(pdf, [
        ("Product", 90, "L"),
        ("Qty Sold", 40, "C"),
        ("Revenue", 45, "R"),
    ])

    for name, qty, revenue in data["worst_products"]:
        pdf.cell(90, 8, str(name), border=1)
        pdf.cell(40, 8, str(qty), border=1, align="C")
        pdf.cell(45, 8, format_currency(revenue), border=1, align="R", ln=True)

    pdf.ln(6)

    # ---------------- Full Product-wise Profit Breakdown ----------------
    if product_details:
        pdf.add_page()
        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(0, 8, "Product-wise Profit Breakdown", ln=True)

        draw_items_table_header(pdf, [
            ("Product", 38, "L"),
            ("Qty", 12, "C"),
            ("Revenue", 28, "R"),
            ("Discount", 26, "R"),
            ("Cost", 28, "R"),
            ("Profit", 28, "R"),
            ("Current Stock", 30, "C"),
        ])

        pdf.set_font("Helvetica", "", 8)

        for name, qty, revenue, discount, cost, profit, stock in product_details:
            pdf.cell(38, 8, str(name), border=1)
            pdf.cell(12, 8, str(qty), border=1, align="C")
            pdf.cell(28, 8, format_currency(revenue), border=1, align="R")
            pdf.cell(26, 8, format_currency(discount), border=1, align="R")
            pdf.cell(28, 8, format_currency(cost), border=1, align="R")
            pdf.cell(28, 8, format_currency(profit), border=1, align="R")
            pdf.cell(30, 8, str(stock), border=1, align="C", ln=True)

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

    pdf.ln(15)
    pdf.set_font("Helvetica", "I", 8)
    pdf.cell(0, 5, f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M')}", align="C")

    file_path = os.path.join(tempfile.gettempdir(), f"Business_Report_{date_from}_to_{date_to}.pdf")
    pdf.output(file_path)

    open_pdf(file_path)

    return file_path