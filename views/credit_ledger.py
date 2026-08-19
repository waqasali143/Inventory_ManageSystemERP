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
    win.iconbitmap("assets/ims.ico")

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

    search_frame = Frame(parent, bg=BACKGROUND)
    search_frame.pack(fill=X, padx=10, pady=(10, 0))

    Label(search_frame, text="Search (Name or Invoice No)", bg=BACKGROUND).pack(side=LEFT, padx=(0, 8))
    search_var = StringVar()
    search_entry = Entry(search_frame, textvariable=search_var, width=30)
    search_entry.pack(side=LEFT)

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

        rows = get_customers_with_balance_detailed(search_var.get().strip() or None)
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

    search_entry.bind("<KeyRelease>", lambda event: refresh())
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
        open_invoices = get_customer_credit_sales(customer_id)
        open_payment_dialog(
            parent, "Customer", customer_name, open_invoices,
            lambda amount, notes, sale_id: record_customer_payment(customer_id, amount, notes, sale_id),
            refresh
        )

    def handle_view_statement():
        selected = get_selected()
        if not selected:
            return
        customer_id, customer_name = selected
        open_statement_window("Customer", customer_id, customer_name, on_ledger_refresh=refresh)

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

    search_frame = Frame(parent, bg=BACKGROUND)
    search_frame.pack(fill=X, padx=10, pady=(10, 0))

    Label(search_frame, text="Search (Name or Invoice No)", bg=BACKGROUND).pack(side=LEFT, padx=(0, 8))
    search_var = StringVar()
    search_entry = Entry(search_frame, textvariable=search_var, width=30)
    search_entry.pack(side=LEFT)

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

        rows = get_suppliers_with_balance_detailed(search_var.get().strip() or None)
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

    search_entry.bind("<KeyRelease>", lambda event: refresh())
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
        open_invoices = get_supplier_credit_purchases(supplier_id)
        open_payment_dialog(
            parent, "Supplier", supplier_name, open_invoices,
            lambda amount, notes, purchase_id: record_supplier_payment(supplier_id, amount, notes, purchase_id),
            refresh
        )

    def handle_view_statement():
        selected = get_selected()
        if not selected:
            return
        supplier_id, supplier_name = selected
        open_statement_window("Supplier", supplier_id, supplier_name, on_ledger_refresh=refresh)

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
def open_payment_dialog(parent, party_type, party_name, open_invoices, save_callback, on_success,
                         preselected_invoice_id=None):
    """
    open_invoices: rows from get_customer_credit_sales()/get_supplier_credit_purchases()
                   - (id, no, date, net_total, amount_paid, balance, status)
    save_callback(amount, notes, invoice_id) - invoice_id is None for an
    untargeted/general payment (only offered when there are no open
    invoices to pick from).
    preselected_invoice_id: when set (e.g. called from the Statement
    window with a specific row already selected), the invoice is
    locked to that one instead of offering a picker.
    """

    win = Toplevel(parent)
    win.title(f"Record Payment - {party_name}")
    win.configure(bg=BACKGROUND)
    win.resizable(False, False)
    win.geometry("430x300")
    win.iconbitmap("assets/ims.ico")

    Label(
        win, text=f"{party_type}: {party_name}",
        bg=BACKGROUND, font=FONT_BODY_BOLD
    ).pack(pady=(15, 10))

    form_frame = Frame(win, bg=BACKGROUND)
    form_frame.pack(padx=20, fill=X)

    # label -> (invoice_id, balance)
    invoice_lookup = {}
    invoice_labels = []
    for invoice_id, no, date_str, net_total, amount_paid, balance, status in open_invoices:
        label = f"{no}  (Balance: {format_currency(balance)})"
        invoice_lookup[label] = (invoice_id, balance)
        invoice_labels.append(label)

    invoice_var = StringVar()
    amount_var = StringVar()
    notes_var = StringVar()
    selected_invoice_id = {"value": None}

    row = 0

    if preselected_invoice_id is not None:
        matching = [lbl for lbl, (iid, bal) in invoice_lookup.items() if iid == preselected_invoice_id]
        if matching:
            invoice_var.set(matching[0])
            selected_invoice_id["value"] = preselected_invoice_id
            amount_var.set(f"{invoice_lookup[matching[0]][1]:.2f}")

        Label(form_frame, text="Invoice", bg=BACKGROUND).grid(row=row, column=0, sticky="w", pady=5)
        Label(form_frame, textvariable=invoice_var, bg=BACKGROUND, font=FONT_BODY_BOLD).grid(
            row=row, column=1, sticky="w", pady=5)
        row += 1
    else:
        Label(form_frame, text="Apply to Invoice", bg=BACKGROUND).grid(row=row, column=0, sticky="w", pady=5)
        invoice_entry = Entry(form_frame, textvariable=invoice_var, width=28)
        invoice_entry.grid(row=row, column=1, pady=5, sticky="w")
        listbox_row = row
        row += 1

        invoice_listbox = Listbox(form_frame, height=5, font=("Segoe UI", 9))

        def hide_invoice_list():
            invoice_listbox.grid_remove()

        def pick_invoice(label):
            invoice_var.set(label)
            hide_invoice_list()
            iid, balance = invoice_lookup.get(label, (None, 0))
            selected_invoice_id["value"] = iid
            amount_var.set(f"{balance:.2f}")

        def show_invoice_list(matches):
            if not matches:
                hide_invoice_list()
                return
            invoice_listbox.delete(0, END)
            for lbl in matches[:10]:   # cap so the popup stays manageable
                invoice_listbox.insert(END, lbl)
            invoice_listbox.grid(row=listbox_row + 1, column=1, sticky="w", pady=(0, 5))
            invoice_listbox.lift()

        def filter_invoices(event):
            if event.keysym in ("Up", "Down", "Return", "Escape"):
                return
            typed = invoice_var.get().strip().lower()
            if not typed:
                hide_invoice_list()
                return
            matches = [lbl for lbl in invoice_labels if typed in lbl.lower()]
            show_invoice_list(matches)

        def on_listbox_click(event):
            selection = invoice_listbox.curselection()
            if selection:
                pick_invoice(invoice_listbox.get(selection[0]))

        invoice_entry.bind("<KeyRelease>", filter_invoices)
        invoice_entry.bind("<Escape>", lambda e: hide_invoice_list())
        # Small delay on FocusOut so a click on the listbox (which also
        # blurs the entry) has time to register before the list closes.
        invoice_entry.bind("<FocusOut>", lambda e: form_frame.after(150, hide_invoice_list))
        invoice_listbox.bind("<<ListboxSelect>>", on_listbox_click)

        if invoice_labels:
            pick_invoice(invoice_labels[0])   # default to the first open invoice
        else:
            invoice_var.set("(no open invoices - general payment)")
            invoice_entry.config(state="disabled")

    Label(form_frame, text="Amount", bg=BACKGROUND).grid(row=row, column=0, sticky="w", pady=5)
    amount_entry = Entry(form_frame, textvariable=amount_var, width=20)
    amount_entry.grid(row=row, column=1, pady=5, sticky="w")
    row += 1

    Label(form_frame, text="Notes (optional)", bg=BACKGROUND).grid(row=row, column=0, sticky="w", pady=5)
    Entry(form_frame, textvariable=notes_var, width=20).grid(row=row, column=1, pady=5, sticky="w")

    if preselected_invoice_id is not None:
        amount_entry.focus_set()
    elif not invoice_labels:
        amount_entry.focus_set()
    else:
        invoice_entry.focus_set()

    def handle_confirm():
        if save_callback(amount_var.get(), notes_var.get(), selected_invoice_id["value"]):
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
def open_statement_window(party_type, party_id, party_name, on_ledger_refresh=None):

    def fetch_data():
        if party_type == "Customer":
            return get_customer_credit_sales(party_id), get_customer_payment_history(party_id)
        return get_supplier_credit_purchases(party_id), get_supplier_payment_history(party_id)

    credit_rows, payment_rows = fetch_data()

    win = Toplevel()
    win.title(f"Statement - {party_name}")
    size_and_center(win, width_ratio=0.55, height_ratio=1, resizable=True)
    apply_app_style()
    win.iconbitmap("assets/ims.ico")

    header_frame = Frame(win, bg=PRIMARY, height=55)
    header_frame.pack(fill=X)
    header_frame.pack_propagate(False)

    Label(
        header_frame, text=f"Statement of Account — {party_name}",
        bg=PRIMARY, fg=WHITE, font=FONT_TITLE
    ).pack(side=LEFT, padx=20)

    # ---------------- Credit Transactions ----------------
    credit_header_frame = Frame(win)
    credit_header_frame.pack(fill=X, padx=15, pady=(15, 5))

    Label(
        credit_header_frame,
        text=f"Unpaid / Partial {'Sales' if party_type == 'Customer' else 'Purchases'}",
        font=FONT_BODY_BOLD
    ).pack(side=LEFT)

    Label(credit_header_frame, text="Search Invoice No").pack(side=LEFT, padx=(30, 6))
    search_var = StringVar()
    search_entry = Entry(credit_header_frame, textvariable=search_var, width=20)
    search_entry.pack(side=LEFT)

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

    def populate_credit_tree():
        for row in credit_tree.get_children():
            credit_tree.delete(row)

        typed = search_var.get().strip().lower()
        for sale_id, no, date_str, net_total, amount_paid, balance, payment_status in credit_rows:
            if typed and typed not in no.lower():
                continue
            credit_tree.insert("", END, iid=str(sale_id), values=(
                no, date_str, format_currency(net_total),
                format_currency(amount_paid), format_currency(balance), payment_status
            ))

    search_entry.bind("<KeyRelease>", lambda event: populate_credit_tree())

    payment_button_frame = Frame(win)
    payment_button_frame.pack(fill=X, padx=15, pady=(8, 0))

    def handle_record_payment_for_selected():
        selected = credit_tree.focus()
        if not selected:
            messagebox.showerror("Error", "Please select an invoice from the list above first.")
            return

        sale_id = int(selected)

        def save_and_refresh(amount, notes, invoice_id):
            if party_type == "Customer":
                success = record_customer_payment(party_id, amount, notes, invoice_id)
            else:
                success = record_supplier_payment(party_id, amount, notes, invoice_id)
            return success

        open_payment_dialog(
            win, party_type, party_name, credit_rows, save_and_refresh,
            refresh_statement, preselected_invoice_id=sale_id
        )

    Button(
        payment_button_frame, text="💵 Record Payment for Selected Invoice",
        bg=PRIMARY, fg=WHITE, relief=FLAT, cursor="hand2",
        command=handle_record_payment_for_selected
    ).pack(side=LEFT)

    # ---------------- Payment History ----------------
    Label(
        win,
        text="Payments Received" if party_type == "Customer" else "Payments Made",
        font=FONT_BODY_BOLD
    ).pack(anchor="w", padx=15, pady=(15, 5))

    payment_columns = [
        {"key": "date", "heading": "Date", "width": 140},
        {"key": "amount", "heading": "Amount", "width": 110, "anchor": E},
        {"key": "invoice", "heading": "Applied To Invoice", "width": 140, "anchor": CENTER},
        {"key": "notes", "heading": "Notes", "width": 170, "stretch": True},
    ]
    payment_tree = build_treeview(win, payment_columns, height=6)
    payment_tree.pack(fill=BOTH, expand=True, padx=15, pady=(0, 15))

    def populate_payment_tree():
        for row in payment_tree.get_children():
            payment_tree.delete(row)
        for date_str, amount, notes, invoice_no in payment_rows:
            payment_tree.insert("", END, values=(
                date_str, format_currency(amount), invoice_no or "General payment", notes
            ))

    def refresh_statement():
        nonlocal credit_rows, payment_rows
        credit_rows, payment_rows = fetch_data()
        populate_credit_tree()
        populate_payment_tree()
        if on_ledger_refresh:
            on_ledger_refresh()

    populate_credit_tree()
    populate_payment_tree()

    Button(
        win, text="🖨 Print Statement", bg=PRIMARY, fg=WHITE, relief=FLAT, cursor="hand2",
        command=lambda: generate_credit_statement_pdf(party_type, party_name, credit_rows, payment_rows)
    ).pack(pady=(0, 15), ipadx=10, ipady=5)