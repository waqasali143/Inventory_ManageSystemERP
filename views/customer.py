from tkinter import *
from tkinter import ttk

from services.customer_service import (
    load_customers, save_customer, update_customer, delete_customer
)
from services.sales_service import get_sales_by_customer
from services.settings_service import format_currency
from utils.theme import (
    PRIMARY, BACKGROUND, WHITE,
    FONT_TITLE, FONT_BODY, apply_app_style
)
from utils.branding_helpers import add_branding_strip
from utils.shortcut_helper import bind_shortcuts

from services.invoice_service import generate_customer_statement
from utils.tree_helpers import build_treeview
from utils.window_helpers import size_and_center

CUSTOMER_COLUMNS = ("id", "name", "contact", "email", "address", "status")


# =====================================
# Load customers into the tree
# =====================================
def refresh_customers(tree, search_term=None):

    for row in tree.get_children():
        tree.delete(row)

    rows = load_customers(search_term)

    for row in rows:
        tree.insert("", END, values=row)


def search_customer(search, tree):
    refresh_customers(tree, search.get().strip())


# =====================================
# Pull the selected row into the form fields
# =====================================
def select_customer(event, tree, name, contact, email, address, selected_id, ntn, is_filer):

    selected = tree.focus()
    values = tree.item(selected, "values")

    if not values:
        return

    selected_id.set(values[0])
    name.set(values[1])
    contact.set(values[2])
    email.set(values[3])
    address.set(values[4])
    ntn.set(values[6])
    is_filer.set(bool(values[7]))


def clear_fields(selected_id, name, contact, email, address, ntn, is_filer, name_entry):

    selected_id.set("")
    name.set("")
    contact.set("")
    email.set("")
    address.set("")
    ntn.set("")
    is_filer.set(False)

    name_entry.focus_set()


# =====================================
# Button handlers (wrap service calls + refresh + clear on success)
# =====================================
def handle_save(name, contact, email, address, tree, ntn, is_filer):
    if save_customer(name, contact, email, address, ntn, is_filer):
        refresh_customers(tree)
        name.set("")
        contact.set("")
        email.set("")
        address.set("")
        ntn.set("")
        is_filer.set(False)


def handle_update(selected_id, name, contact, email, address, tree, ntn, is_filer):
    if update_customer(selected_id, name, contact, email, address, ntn, is_filer):
        refresh_customers(tree)
        selected_id.set("")
        name.set("")
        contact.set("")
        email.set("")
        address.set("")
        ntn.set("")
        is_filer.set(False)


def handle_delete(selected_id, tree):
    if delete_customer(selected_id):
        refresh_customers(tree)
        selected_id.set("")


# =====================================
# Main Window
# =====================================
def open_window():

    win = Toplevel()
    add_branding_strip(win)

    win.title("Customer Management")
    win.geometry("950x600")
    win.resizable(False, False)
    win.iconbitmap("assets/ims.ico")

    # ---------------- Variables ----------------
    search = StringVar()
    name = StringVar()
    contact = StringVar()
    email = StringVar()
    address = StringVar()
    selected_id = StringVar()

    # ---------------- Search Frame ----------------
    search_frame = LabelFrame(win, text="Search Customer", padx=10, pady=10)
    search_frame.pack(fill="x", padx=10, pady=10)

    Label(search_frame, text="Customer Name").grid(row=0, column=0, padx=5)

    search_entry = Entry(search_frame, textvariable=search, width=30)
    search_entry.grid(row=0, column=1)

    Button(
        search_frame, text="Search", width=12,
        command=lambda: search_customer(search, tree)
    ).grid(row=0, column=2, padx=10)

    Button(
        search_frame, text="Show All", width=12,
        command=lambda: refresh_customers(tree)
    ).grid(row=0, column=3)

    # ---------------- Customer Details Frame ----------------
    customer_frame = LabelFrame(win, text="Customer Details", padx=10, pady=10)
    customer_frame.pack(fill="x", padx=10)

    Label(customer_frame, text="Customer Name").grid(row=0, column=0)
    name_entry = Entry(customer_frame, textvariable=name, width=35)
    name_entry.grid(row=0, column=1, padx=10)

    Label(customer_frame, text="Contact").grid(row=1, column=0)
    Entry(customer_frame, textvariable=contact, width=35).grid(row=1, column=1, padx=10, pady=5)

    Label(customer_frame, text="Email").grid(row=2, column=0)
    Entry(customer_frame, textvariable=email, width=35).grid(row=2, column=1, padx=10)

    Label(customer_frame, text="Address").grid(row=3, column=0)
    Entry(customer_frame, textvariable=address, width=35).grid(row=3, column=1, padx=10, pady=5)

    Label(customer_frame, text="NTN").grid(row=4, column=0)
    ntn = StringVar()
    Entry(customer_frame, textvariable=ntn, width=35).grid(row=4, column=1, padx=10, pady=5)

    is_filer = BooleanVar(value=False)
    Checkbutton(customer_frame, text="Filer (registered with FBR)", variable=is_filer).grid(
        row=5, column=1, sticky="w", padx=10, pady=5)

    # ---------------- Buttons ----------------
    button_frame = Frame(customer_frame)
    button_frame.grid(row=6, column=0, columnspan=2, pady=15)

    Button(
        button_frame, text="Save", width=10,
        command=lambda: handle_save(name, contact, email, address, tree, ntn, is_filer)
    ).grid(row=0, column=0, padx=5)

    Button(
        button_frame, text="Update", width=10,
        command=lambda: handle_update(selected_id, name, contact, email, address, tree, ntn, is_filer)
    ).grid(row=0, column=1, padx=5)

    Button(
        button_frame, text="Delete", width=10,
        command=lambda: handle_delete(selected_id, tree)
    ).grid(row=0, column=2, padx=5)

    Button(
        button_frame, text="Clear", width=10,
        command=lambda: clear_fields(selected_id, name, contact, email, address, ntn, is_filer, name_entry)
    ).grid(row=0, column=3, padx=5)

    Button(
        button_frame, text="Sales History", width=14,
        command=lambda: open_customer_sales_history(selected_id, name)
    ).grid(row=0, column=4, padx=5)

    # ---------------- Customer Table ----------------
    table_frame = Frame(win)
    table_frame.pack(fill=BOTH, expand=True, padx=10, pady=10)

    scrollbar_y = Scrollbar(table_frame)
    scrollbar_y.pack(side=RIGHT, fill=Y)

    tree = ttk.Treeview(
        table_frame,
        columns=CUSTOMER_COLUMNS,
        show="headings",
        yscrollcommand=scrollbar_y.set
    )
    scrollbar_y.config(command=tree.yview)

    tree.heading("id", text="ID")
    tree.heading("name", text="Customer Name")
    tree.heading("contact", text="Contact")
    tree.heading("email", text="Email")
    tree.heading("address", text="Address")
    tree.heading("status", text="Status")

    tree.column("id", width=60, anchor=CENTER, stretch=False)
    tree.column("name", width=200, stretch=False)
    tree.column("contact", width=140, stretch=False)
    tree.column("email", width=200, stretch=False)
    tree.column("address", width=220, stretch=True)
    tree.column("status", width=90, anchor=CENTER, stretch=False)

    tree.pack(fill=BOTH, expand=True)

    tree.bind(
        "<<TreeviewSelect>>",
        lambda event: select_customer(event, tree, name, contact, email, address, selected_id, ntn, is_filer)
    )
# =============================================================
#   Keyboard Shortcuts
#   F2 = Save (new record) or Update (if a row is selected),
#   Escape = Close window
# ==============================================================
    def handle_f2():
        if selected_id.get():
            handle_update(selected_id, name, contact, email, address, tree, ntn, is_filer)
        else:
            handle_save(name, contact, email, address, tree, ntn, is_filer)

    bind_shortcuts(win, {
        "<F2>": handle_f2,
        "<Escape>": win.destroy,
    })
# ==========================================================
# =====  Function Customer Sales history  =========
# ===========================================================
    def open_customer_sales_history(selected_id, name):

        if not selected_id.get():
            from tkinter import messagebox
            messagebox.showerror("Error", "Please select a customer first.")
            return

        win = Toplevel()
        win.title(f"Sales History - {name.get()}")
        size_and_center(win, width_ratio=0.7, height_ratio=1, resizable=True)

        apply_app_style()

        # ---------------- Header ----------------
        header_frame = Frame(win, bg=PRIMARY, height=60)
        header_frame.pack(fill=X)
        header_frame.pack_propagate(False)

        Label(
            header_frame, text=f"Sales History — {name.get()}",
            bg=PRIMARY, fg=WHITE, font=FONT_TITLE
        ).pack(side=LEFT, padx=20)

        if is_filer.get():
            Label(
                header_frame, text=f"NTN: {ntn.get()}",
                bg=PRIMARY, fg=WHITE, font=FONT_BODY
            ).pack(side=RIGHT, padx=20)

        # ---------------- Table ----------------
        table_frame = Frame(win, bg=BACKGROUND)
        table_frame.pack(fill=BOTH, expand=True, padx=15, pady=15)

        scroll_y = Scrollbar(table_frame, orient=VERTICAL)
        scroll_y.pack(side=RIGHT, fill=Y)

        tree = build_treeview(table_frame, SALES_HISTORY_COLUMNS)
        tree.configure(yscrollcommand=scroll_y.set)
        scroll_y.config(command=tree.yview)
        tree["displaycolumns"] = (
            "sale_no", "date", "gross_total", "discount_amount", "tax_amount", "net_total",
            "payment_status", "amount_paid", "balance_due"
        )
        tree.pack(fill=BOTH, expand=True)

        rows = get_sales_by_customer(selected_id.get())

        # get_sales_by_customer() returns 9 fields per row:
        # id, sale_no, date, gross_total, discount_amount, tax_amount,
        # net_total, payment_status, balance_due
        # Amount Paid isn't returned directly, but it's derivable
        # (same approach as the Supplier Purchase History fix).
        total_purchased = 0.0
        for row in rows:
            net_total = row[6]
            payment_status = row[7]
            balance_due = row[8]
            amount_paid = net_total - balance_due

            formatted_row = (
                row[0], row[1], row[2],
                format_currency(row[3]), format_currency(row[4]),
                format_currency(row[5]), format_currency(net_total),
                payment_status, format_currency(amount_paid), format_currency(balance_due)
            )
            tree.insert("", "end", values=formatted_row)
            total_purchased += net_total

        if not rows:
            Label(
                table_frame, text="No sales found for this customer.",
                bg=BACKGROUND, fg="gray", font=FONT_BODY
            ).pack(pady=10)

        # ---------------- Total (highlighted bar) ----------------
        total_frame = Frame(win, bg="#0B3B63", height=55)
        total_frame.pack(side=BOTTOM, fill=X, padx=30, pady=(0, 15))
        total_frame.pack_propagate(False)

        Label(
            total_frame, text="TOTAL PURCHASED BY THIS CUSTOMER",
            bg="#0B3B63", fg=WHITE, font=FONT_BODY
        ).pack(side=LEFT, padx=20)

        Label(
            total_frame, text=format_currency(total_purchased),
            bg="#0B3B63", fg=WHITE, font=("Segoe UI", 16, "bold")
        ).pack(side=RIGHT, padx=20)

        Button(
        win, text="🖨 Print Statement", width=20,
        command=lambda: generate_customer_statement(name.get(), rows)
        ).pack(side=BOTTOM, pady=15)

    refresh_customers(tree)
    name_entry.focus_set()
# =====================================
# Customer Sales History Window
# =====================================
SALES_HISTORY_COLUMNS = [
    {"key": "id", "heading": "ID", "width": 0},
    {"key": "sale_no", "heading": "Sale No", "width": 120, "stretch": False},
    {"key": "date", "heading": "Date", "width": 170, "stretch": False},
    {"key": "gross_total", "heading": "Gross Total", "width": 110, "anchor": E, "stretch": False},
    {"key": "discount_amount", "heading": "Discount Amt", "width": 120, "anchor": E, "stretch": False},
    {"key": "tax_amount", "heading": "Tax Amt", "width": 110, "anchor": E, "stretch": False},
    {"key": "net_total", "heading": "Net Total", "width": 130, "anchor": E, "stretch": False},
    {"key": "payment_status", "heading": "Payment", "width": 90, "anchor": CENTER, "stretch": False},
    {"key": "amount_paid", "heading": "Amount Paid", "width": 110, "anchor": E, "stretch": False},
    {"key": "balance_due", "heading": "Balance Due", "width": 110, "anchor": E, "stretch": True},
]
