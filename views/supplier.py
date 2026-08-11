from tkinter import *
from tkinter import ttk

from services.supplier_service import (
    load_suppliers, save_supplier, update_supplier, delete_supplier
)
from services.purchase_service import get_purchases_by_supplier
from services.settings_service import format_currency

from utils.theme import (
    PRIMARY, BACKGROUND, WHITE, TEXT,
    FONT_TITLE, FONT_BODY, FONT_BODY_BOLD,
    apply_app_style
)
from utils.branding_helpers import add_branding_strip

from services.invoice_service import generate_supplier_statement
from utils.tree_helpers import build_treeview
from utils.window_helpers import size_and_center
from utils.shortcut_helper import bind_shortcuts

SUPPLIER_COLUMNS = ("id", "name", "contact", "email", "address", "status")


# =====================================
# Load suppliers into the tree
# =====================================
def refresh_suppliers(tree, search_term=None):

    for row in tree.get_children():
        tree.delete(row)

    rows = load_suppliers(search_term)

    for row in rows:
        tree.insert("", END, values=row)


def search_supplier(search, tree):
    refresh_suppliers(tree, search.get().strip())


# =====================================
# Pull the selected row into the form fields
# =====================================
def select_supplier(event, tree, name, contact, email, address, selected_id, ntn, is_filer):

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
    if save_supplier(name, contact, email, address, ntn, is_filer):
        refresh_suppliers(tree)
        name.set("")
        contact.set("")
        email.set("")
        address.set("")
        ntn.set("")
        is_filer.set(False)


def handle_update(selected_id, name, contact, email, address, tree, ntn, is_filer):
    if update_supplier(selected_id, name, contact, email, address, ntn, is_filer):
        refresh_suppliers(tree)
        selected_id.set("")
        name.set("")
        contact.set("")
        email.set("")
        address.set("")
        ntn.set("")
        is_filer.set(False)


def handle_delete(selected_id, tree):
    if delete_supplier(selected_id):
        refresh_suppliers(tree)
        selected_id.set("")


# =====================================
# Main Window
# =====================================
def open_window():

    win = Toplevel()
    add_branding_strip(win)

    win.title("Supplier Management")
    win.geometry("950x650")
    win.resizable(False, False)
    win.iconbitmap("assets/ims.ico")

    # ---------------- Variables ----------------
    search = StringVar()
    name = StringVar()
    contact = StringVar()
    email = StringVar()
    address = StringVar()
    selected_id = StringVar()
    ntn = StringVar()
    is_filer = BooleanVar(value=False)

    # ---------------- Search Frame ----------------
    search_frame = LabelFrame(win, text="Search Supplier", padx=10, pady=10)
    search_frame.pack(fill="x", padx=10, pady=10)

    Label(search_frame, text="Supplier Name").grid(row=0, column=0, padx=5)

    search_entry = Entry(search_frame, textvariable=search, width=30)
    search_entry.grid(row=0, column=1)

    Button(
        search_frame, text="Search", width=12,
        command=lambda: search_supplier(search, tree)
    ).grid(row=0, column=2, padx=10)

    Button(
        search_frame, text="Show All", width=12,
        command=lambda: refresh_suppliers(tree)
    ).grid(row=0, column=3)

    # ---------------- Supplier Details Frame ----------------
    supplier_frame = LabelFrame(win, text="Supplier Details", padx=10, pady=10)
    supplier_frame.pack(fill="x", padx=10)

    Label(supplier_frame, text="Supplier Name").grid(row=0, column=0)
    name_entry = Entry(supplier_frame, textvariable=name, width=35)
    name_entry.grid(row=0, column=1, padx=10)

    Label(supplier_frame, text="Contact").grid(row=1, column=0)
    Entry(supplier_frame, textvariable=contact, width=35).grid(row=1, column=1, padx=10, pady=5)

    Label(supplier_frame, text="Email").grid(row=2, column=0)
    Entry(supplier_frame, textvariable=email, width=35).grid(row=2, column=1, padx=10)

    Label(supplier_frame, text="Address").grid(row=3, column=0)
    Entry(supplier_frame, textvariable=address, width=35).grid(row=3, column=1, padx=10, pady=5)

    Label(supplier_frame, text="NTN").grid(row=4, column=0)
    Entry(supplier_frame, textvariable=ntn, width=35).grid(row=4, column=1, padx=10, pady=5)

    Checkbutton(
        supplier_frame, text="Filer (registered with FBR)", variable=is_filer
    ).grid(row=5, column=1, sticky="w", padx=10, pady=5)

    # ---------------- Buttons ----------------
    button_frame = Frame(supplier_frame)
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
        button_frame, text="Purchase History", width=16,
        command=lambda: open_supplier_purchase_history(selected_id, name, ntn, is_filer)
    ).grid(row=0, column=4, padx=5)

    # ---------------- Supplier Table ----------------
    table_frame = Frame(win)
    table_frame.pack(fill=BOTH, expand=True, padx=10, pady=10)

    scrollbar_y = Scrollbar(table_frame)
    scrollbar_y.pack(side=RIGHT, fill=Y)

    tree = ttk.Treeview(
        table_frame,
        columns=SUPPLIER_COLUMNS,
        show="headings",
        yscrollcommand=scrollbar_y.set
    )
    scrollbar_y.config(command=tree.yview)

    tree.heading("id", text="ID")
    tree.heading("name", text="Supplier Name")
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
        lambda event: select_supplier(event, tree, name, contact, email, address, selected_id, ntn, is_filer)
    )

    refresh_suppliers(tree)
    name_entry.focus_set()

# ==========================================================
#   Keyboard Shortcuts
#   F2 = Save (new record) or Update (if a row is selected),
#   Escape = Close window
# ==========================================================
    def handle_f2():
        if selected_id.get():
            handle_update(selected_id, name, contact, email, address, tree, ntn, is_filer)
        else:
            handle_save(name, contact, email, address, tree, ntn, is_filer)

    bind_shortcuts(win, {
        "<F2>": handle_f2,
        "<Escape>": win.destroy,
    })

    refresh_suppliers(tree)
    name_entry.focus_set()

# =====================================
# Supplier Purchase History Window
# =====================================
PURCHASE_HISTORY_COLUMNS = [
    {"key": "id", "heading": "ID", "width": 0},
    {"key": "purchase_no", "heading": "Purchase No", "width": 130, "stretch": False},
    {"key": "date", "heading": "Date", "width": 170, "stretch": False},
    {"key": "gross_total", "heading": "Gross Total", "width": 110, "anchor": E, "stretch": False},
    {"key": "discount_amount", "heading": "Discount Amt", "width": 120, "anchor": E, "stretch": False},
    {"key": "tax_amount", "heading": "Tax Amt", "width": 110, "anchor": E, "stretch": True},
    {"key": "net_total", "heading": "Net Total", "width": 130, "anchor": E, "stretch": False},
]


def open_supplier_purchase_history(selected_id, name, ntn, is_filer):

    if not selected_id.get():
        from tkinter import messagebox
        messagebox.showerror("Error", "Please select a supplier first.")
        return

    win = Toplevel()
    win.title(f"Purchase History - {name.get()}")
    size_and_center(win, width_ratio=0.8, height_ratio=1, resizable=True)

    apply_app_style()

    header_frame = Frame(win, bg=PRIMARY, height=60)
    header_frame.pack(fill=X)
    header_frame.pack_propagate(False)

    Label(
        header_frame, text=f"Purchase History — {name.get()}",
        bg=PRIMARY, fg=WHITE, font=FONT_TITLE
    ).pack(side=LEFT, padx=20)

    if is_filer.get():
        Label(
            header_frame, text=f"NTN: {ntn.get()}",
            bg=PRIMARY, fg=WHITE, font=FONT_BODY
        ).pack(side=RIGHT, padx=20)

    table_frame = Frame(win, bg=BACKGROUND)
    table_frame.pack(fill=BOTH, expand=True, padx=15, pady=15)

    scroll_y = Scrollbar(table_frame, orient=VERTICAL)
    scroll_y.pack(side=RIGHT, fill=Y)

    tree = build_treeview(table_frame, PURCHASE_HISTORY_COLUMNS)
    tree.configure(yscrollcommand=scroll_y.set)
    scroll_y.config(command=tree.yview)
    tree["displaycolumns"] = (
        "purchase_no", "date", "gross_total", "discount_amount", "tax_amount", "net_total"
    )
    tree.pack(fill=BOTH, expand=True)

    rows = get_purchases_by_supplier(selected_id.get())

    total_spent = 0.0
    for row in rows:
        formatted_row = (
            row[0], row[1], row[2],
            format_currency(row[3]), format_currency(row[4]),
            format_currency(row[5]), format_currency(row[6])
        )
        tree.insert("", "end", values=formatted_row)
        total_spent += row[6]

    if not rows:
        Label(
            table_frame, text="No purchases found for this supplier.",
            bg=BACKGROUND, fg="gray", font=FONT_BODY
        ).pack(pady=10)

    total_frame = Frame(win, bg="#0B3B63", height=55)
    total_frame.pack(side=BOTTOM, fill=X, padx=10, pady=(0, 15))
    total_frame.pack_propagate(False)

    Label(
        total_frame, text="TOTAL SPENT WITH THIS SUPPLIER",
        bg="#0B3B63", fg=WHITE, font=FONT_BODY
    ).pack(side=LEFT, padx=20)

    Label(
        total_frame, text=format_currency(total_spent),
        bg="#0B3B63", fg=WHITE, font=("Segoe UI", 16, "bold")
    ).pack(side=RIGHT, padx=20)

    Button(
        win, text="🖨 Print Statement", width=20,
        command=lambda: generate_supplier_statement(name.get(), rows)
    ).pack(side=BOTTOM, pady=15)