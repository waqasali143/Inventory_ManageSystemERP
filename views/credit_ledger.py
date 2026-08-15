from tkinter import *
from tkinter import ttk, messagebox

from services.credit_service import (
    get_customers_with_balance_detailed, get_suppliers_with_balance_detailed,
    record_customer_payment, record_supplier_payment,
    get_customer_payment_history, get_customer_credit_sales,
    get_supplier_payment_history, get_supplier_credit_purchases,
    get_credit_report_data,
)
from services.invoice_service import generate_credit_report_pdf, generate_credit_statement_pdf
from services.settings_service import format_currency
from utils.theme import (
    PRIMARY, BACKGROUND, WHITE,
    FONT_TITLE, FONT_BODY, FONT_BODY_BOLD,
    apply_app_style
)
from utils.branding_helpers import add_branding_strip
from utils.tree_helpers import build_treeview
from utils.window_helpers import size_and_center


CUSTOMER_BALANCE_COLUMNS = [
    {"key": "id", "heading": "ID", "width": 0},
    {"key": "name", "heading": "Customer", "width": 170, "stretch": True},
    {"key": "contact", "heading": "Contact", "width": 110},
    {"key": "balance", "heading": "Balance Owed", "width": 110, "anchor": E},
    {"key": "amount_paid", "heading": "Amount Paid", "width": 110, "anchor": E},
    {"key": "open_invoices", "heading": "Open Invoices", "width": 100, "anchor": CENTER},
    {"key": "last_payment_amount", "heading": "Last Payment Amt", "width": 120, "anchor": E},
    {"key": "last_payment_date", "heading": "Last Payment Date", "width": 120, "anchor": CENTER},
]

SUPPLIER_BALANCE_COLUMNS = [
    {"key": "id", "heading": "ID", "width": 0},
    {"key": "name", "heading": "Supplier", "width": 170, "stretch": True},
    {"key": "contact", "heading": "Contact", "width": 110},
    {"key": "balance", "heading": "Balance Owed", "width": 110, "anchor": E},
    {"key": "amount_paid", "heading": "Amount Paid", "width": 110, "anchor": E},
    {"key": "open_invoices", "heading": "Open Invoices", "width": 100, "anchor": CENTER},
    {"key": "last_payment_amount", "heading": "Last Payment Amt", "width": 120, "anchor": E},
    {"key": "last_payment_date", "heading": "Last Payment Date", "width": 120, "anchor": CENTER},
]


# =====================================================================
# Main Window
# =====================================================================
def open_window():

    win = Toplevel()
    add_branding_strip(win)

    win.title("Credit Ledger")
    win.configure(bg=BACKGROUND)

    size_and_center(win, width_ratio=0.75, height_ratio=1, resizable=True)
    apply_app_style()

    # ---------------- Header ----------------
    header_frame = Frame(win, bg=PRIMARY, height=60)
    header_frame.pack(fill=X)
    header_frame.pack_propagate(False)

    Label(
        header_frame, text="CREDIT LEDGER",
        bg=PRIMARY, fg=WHITE, font=FONT_TITLE
    ).pack(side=LEFT, padx=20)

    Label(
        header_frame, text="Customer Receivables & Supplier Payables",
        bg=PRIMARY, fg=WHITE, font=FONT_BODY
    ).pack(side=RIGHT, padx=20)

    # ---------------- Tabs ----------------
    notebook = ttk.Notebook(win)
    notebook.pack(fill=BOTH, expand=True, padx=15, pady=15)

    customers_tab = Frame(notebook, bg=BACKGROUND)
    suppliers_tab = Frame(notebook, bg=BACKGROUND)

    notebook.add(customers_tab, text="Customers (Receivables)")
    notebook.add(suppliers_tab, text="Suppliers (Payables)")

    build_customer_tab(customers_tab)
    build_supplier_tab(suppliers_tab)


# =====================================================================
# Customers Tab - money owed TO the business
# =====================================================================
def build_customer_tab(parent):

    table_frame = Frame(parent, bg=BACKGROUND)
    table_frame.pack(fill=BOTH, expand=True, padx=10, pady=10)

    scrollbar_y = Scrollbar(table_frame)
    scrollbar_y.pack(side=RIGHT, fill=Y)

    tree = build_treeview(table_frame, CUSTOMER_BALANCE_COLUMNS)
    tree.configure(yscrollcommand=scrollbar_y.set)
    scrollbar_y.config(command=tree.yview)
    tree["displaycolumns"] = (
        "name", "contact", "balance", "amount_paid",
        "open_invoices", "last_payment_amount", "last_payment_date"
    )
    tree.pack(fill=BOTH, expand=True)

    total_label = Label(parent, text="", bg=BACKGROUND, font=FONT_BODY_BOLD)
    total_label.pack(anchor="e", padx=10, pady=(0, 5))

    def refresh():
        for row in tree.get_children():
            tree.delete(row)

        rows = get_customers_with_balance_detailed()
        total = 0.0

        for customer_id, name, contact, balance, amount_paid, open_invoices, \
                last_payment_amount, last_payment_date in rows:
            tree.insert("", END, values=(
                customer_id, name, contact, format_currency(balance),
                format_currency(amount_paid), open_invoices,
                format_currency(last_payment_amount) if last_payment_amount is not None else "—",
                last_payment_date or "—"
            ))
            total += balance

        total_label.config(text=f"Total Receivable: {format_currency(total)}")

    refresh()

    def get_selected():
        selected = tree.focus()
        if not selected:
            messagebox.showerror("Error", "Please select a customer first.")
            return None
        values = tree.item(selected, "values")
        return values[0], values[1]  # id, name

    def handle_record_payment():
        selected = get_selected()
        if not selected:
            return
        customer_id, customer_name = selected
        open_payment_dialog(
            parent, "Customer", customer_name,
            lambda amount, notes: record_customer_payment(customer_id, amount, notes),
            refresh
        )

    def handle_view_statement():
        selected = get_selected()
        if not selected:
            return
        customer_id, customer_name = selected
        open_statement_window(
            "Customer", customer_name,
            get_customer_credit_sales(customer_id),
            get_customer_payment_history(customer_id)
        )

    button_frame = Frame(parent, bg=BACKGROUND)
    button_frame.pack(fill=X, padx=10, pady=(0, 10))

    Button(
        button_frame, text="💵 Record Payment", bg=PRIMARY, fg=WHITE,
        relief=FLAT, cursor="hand2", command=handle_record_payment
    ).pack(side=LEFT, padx=5, ipadx=10, ipady=4)

    Button(
        button_frame, text="📄 View Statement", relief=FLAT, cursor="hand2",
        command=handle_view_statement
    ).pack(side=LEFT, padx=5, ipadx=10, ipady=4)

    Button(
        button_frame, text="🔄 Refresh", relief=FLAT, cursor="hand2",
        command=refresh
    ).pack(side=LEFT, padx=5, ipadx=10, ipady=4)

    Button(
        button_frame, text="🖨 Print Credit Report", relief=FLAT, cursor="hand2",
        command=lambda: generate_credit_report_pdf(get_credit_report_data())
    ).pack(side=LEFT, padx=5, ipadx=10, ipady=4)


# =====================================================================
# Suppliers Tab - money the business owes
# =====================================================================
def build_supplier_tab(parent):

    table_frame = Frame(parent, bg=BACKGROUND)
    table_frame.pack(fill=BOTH, expand=True, padx=10, pady=10)

    scrollbar_y = Scrollbar(table_frame)
    scrollbar_y.pack(side=RIGHT, fill=Y)

    tree = build_treeview(table_frame, SUPPLIER_BALANCE_COLUMNS)
    tree.configure(yscrollcommand=scrollbar_y.set)
    scrollbar_y.config(command=tree.yview)
    tree["displaycolumns"] = (
        "name", "contact", "balance", "amount_paid",
        "open_invoices", "last_payment_amount", "last_payment_date"
    )
    tree.pack(fill=BOTH, expand=True)

    total_label = Label(parent, text="", bg=BACKGROUND, font=FONT_BODY_BOLD)
    total_label.pack(anchor="e", padx=10, pady=(0, 5))

    def refresh():
        for row in tree.get_children():
            tree.delete(row)

        rows = get_suppliers_with_balance_detailed()
        total = 0.0

        for supplier_id, name, contact, balance, amount_paid, open_invoices, \
                last_payment_amount, last_payment_date in rows:
            tree.insert("", END, values=(
                supplier_id, name, contact, format_currency(balance),
                format_currency(amount_paid), open_invoices,
                format_currency(last_payment_amount) if last_payment_amount is not None else "—",
                last_payment_date or "—"
            ))
            total += balance

        total_label.config(text=f"Total Payable: {format_currency(total)}")

    refresh()

    def get_selected():
        selected = tree.focus()
        if not selected:
            messagebox.showerror("Error", "Please select a supplier first.")
            return None
        values = tree.item(selected, "values")
        return values[0], values[1]

    def handle_record_payment():
        selected = get_selected()
        if not selected:
            return
        supplier_id, supplier_name = selected
        open_payment_dialog(
            parent, "Supplier", supplier_name,
            lambda amount, notes: record_supplier_payment(supplier_id, amount, notes),
            refresh
        )

    def handle_view_statement():
        selected = get_selected()
        if not selected:
            return
        supplier_id, supplier_name = selected
        open_statement_window(
            "Supplier", supplier_name,
            get_supplier_credit_purchases(supplier_id),
            get_supplier_payment_history(supplier_id)
        )

    button_frame = Frame(parent, bg=BACKGROUND)
    button_frame.pack(fill=X, padx=10, pady=(0, 10))

    Button(
        button_frame, text="💵 Record Payment", bg=PRIMARY, fg=WHITE,
        relief=FLAT, cursor="hand2", command=handle_record_payment
    ).pack(side=LEFT, padx=5, ipadx=10, ipady=4)

    Button(
        button_frame, text="📄 View Statement", relief=FLAT, cursor="hand2",
        command=handle_view_statement
    ).pack(side=LEFT, padx=5, ipadx=10, ipady=4)

    Button(
        button_frame, text="🔄 Refresh", relief=FLAT, cursor="hand2",
        command=refresh
    ).pack(side=LEFT, padx=5, ipadx=10, ipady=4)

    Button(
        button_frame, text="🖨 Print Credit Report", relief=FLAT, cursor="hand2",
        command=lambda: generate_credit_report_pdf(get_credit_report_data())
    ).pack(side=LEFT, padx=5, ipadx=10, ipady=4)


# =====================================================================
# Record Payment Dialog (shared by both tabs)
# =====================================================================
def open_payment_dialog(parent, party_type, party_name, save_callback, on_success):

    win = Toplevel(parent)
    win.title(f"Record Payment - {party_name}")
    win.configure(bg=BACKGROUND)
    win.resizable(False, False)
    win.geometry("360x220")

    Label(
        win, text=f"{party_type}: {party_name}",
        bg=BACKGROUND, font=FONT_BODY_BOLD
    ).pack(pady=(15, 10))

    form_frame = Frame(win, bg=BACKGROUND)
    form_frame.pack(padx=20, fill=X)

    Label(form_frame, text="Amount", bg=BACKGROUND).grid(row=0, column=0, sticky="w", pady=5)
    amount_var = StringVar()
    amount_entry = Entry(form_frame, textvariable=amount_var, width=20)
    amount_entry.grid(row=0, column=1, pady=5)
    amount_entry.focus_set()

    Label(form_frame, text="Notes (optional)", bg=BACKGROUND).grid(row=1, column=0, sticky="w", pady=5)
    notes_var = StringVar()
    Entry(form_frame, textvariable=notes_var, width=20).grid(row=1, column=1, pady=5)

    def handle_confirm():
        if save_callback(amount_var.get(), notes_var.get()):
            on_success()
            win.destroy()

    Button(
        win, text="💾 Save Payment", bg=PRIMARY, fg=WHITE,
        relief=FLAT, cursor="hand2", command=handle_confirm
    ).pack(pady=20, ipadx=10, ipady=6)

    amount_entry.bind("<Return>", lambda event: handle_confirm())
    win.bind("<Escape>", lambda event: win.destroy())


# =====================================================================
# Statement of Account Window (shared by both tabs)
# =====================================================================
def open_statement_window(party_type, party_name, credit_rows, payment_rows):

    win = Toplevel()
    win.title(f"Statement - {party_name}")
    size_and_center(win, width_ratio=0.5, height_ratio=1, resizable=True)
    apply_app_style()

    header_frame = Frame(win, bg=PRIMARY, height=55)
    header_frame.pack(fill=X)
    header_frame.pack_propagate(False)

    Label(
        header_frame, text=f"Statement of Account — {party_name}",
        bg=PRIMARY, fg=WHITE, font=FONT_TITLE
    ).pack(side=LEFT, padx=20)

    # ---------------- Credit Transactions ----------------
    Label(
        win,
        text=f"Unpaid / Partial {'Sales' if party_type == 'Customer' else 'Purchases'}",
        font=FONT_BODY_BOLD
    ).pack(anchor="w", padx=15, pady=(15, 5))

    credit_columns = [
        {"key": "no", "heading": "No", "width": 110},
        {"key": "date", "heading": "Date", "width": 130},
        {"key": "net_total", "heading": "Net Total", "width": 100, "anchor": E},
        {"key": "amount_paid", "heading": "Paid at Sale", "width": 100, "anchor": E},
        {"key": "balance", "heading": "Balance", "width": 100, "anchor": E},
        {"key": "status", "heading": "Status", "width": 90, "anchor": CENTER},
    ]
    credit_tree = build_treeview(win, credit_columns, height=6)
    credit_tree.pack(fill=X, padx=15)

    for no, date_str, net_total, amount_paid, balance, payment_status in credit_rows:
        credit_tree.insert("", END, values=(
            no, date_str, format_currency(net_total),
            format_currency(amount_paid), format_currency(balance), payment_status
        ))

    # ---------------- Payment History ----------------
    Label(
        win,
        text="Payments Received" if party_type == "Customer" else "Payments Made",
        font=FONT_BODY_BOLD
    ).pack(anchor="w", padx=15, pady=(15, 5))

    payment_columns = [
        {"key": "date", "heading": "Date", "width": 160},
        {"key": "amount", "heading": "Amount", "width": 120, "anchor": E},
        {"key": "notes", "heading": "Notes", "width": 200, "stretch": True},
    ]
    payment_tree = build_treeview(win, payment_columns, height=6)
    payment_tree.pack(fill=BOTH, expand=True, padx=15, pady=(0, 15))

    for date_str, amount, notes in payment_rows:
        payment_tree.insert("", END, values=(date_str, format_currency(amount), notes))

    Button(
        win, text="🖨 Print Statement", bg=PRIMARY, fg=WHITE, relief=FLAT, cursor="hand2",
        command=lambda: generate_credit_statement_pdf(party_type, party_name, credit_rows, payment_rows)
    ).pack(pady=(0, 15), ipadx=10, ipady=5)
