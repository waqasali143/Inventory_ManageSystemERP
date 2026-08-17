from tkinter import *
from tkinter import ttk
from tkinter import messagebox
from tkinter import CENTER, E
from utils.tree_helpers import clear_treeview 
from utils.export_helpers import export_to_excel
from utils.branding_helpers import add_branding_strip

# ==========================================
# Third Party
# ==========================================
# from ttkbootstrap import Style

# ==========================================
# Local Modules
# ==========================================
# from repositories import purchase_repository as repo
from utils.tree_helpers import build_treeview, reload_treeview
from utils.ui_helpers import add_buttons, labeled_entry, labeled_date_picker
from utils.shortcut_helper import bind_shortcuts
from utils.barcode_helpers import create_scan_entry

from services.invoice_service import generate_purchase_receipt, generate_purchase_report_pdf

from services.settings_service import format_currency
from services.purchase_summary import PurchaseSummary
from utils.window_helpers import size_and_center
from services.purchase_service import (
    calculate_purchase_totals, remove_cart_item, clear_cart, clear_purchase_form, save_purchase, 
    load_suppliers, get_supplier_id_by_name, load_products, get_product_cost_price, 
    get_product_stock, get_purchase_history, get_purchase_header, get_purchase_items,
    get_purchase_items_for_return, process_purchase_return,get_all_purchase_returns
)
from services.supplier_service import get_supplier_filer_status
from services.tax_service import get_applicable_tax_rate
# =====================================
# Product Selected
# =====================================

def on_product_selected(event, purchase_price, 
                        current_stock, 
                        stock_after_purchase, product_map):

    product_name = event.widget.get()

    product_id = product_map.get(product_name)

    if product_id is None:
        return

    purchase_price.set(get_product_cost_price(product_name))
    stock = get_product_stock(product_name)
    current_stock.set(stock)
    stock_after_purchase.set(stock)
# -------------------------------------
#   Validation Function
# -------------------------------------
def validate_cart_input(
        product,
        purchase_price,
        quantity
    ):

        product_name = product.get().strip()

        if product_name == "":
            messagebox.showerror(
                "Error",
                "Please select a product."
            )
            return None

        if purchase_price.get() == "":
            messagebox.showerror(
                "Error",
                "Purchase Price is required."
            )
            return None

        if quantity.get() == "":
            messagebox.showerror(
                "Error",
                "Quantity is required."
            )
            return None

        try:

            price = float(purchase_price.get())

            qty = int(quantity.get())

        except ValueError:

            messagebox.showerror(
                "Error",
                "Invalid Price or Quantity."
            )
            return None

        return (
            product_name,
            price,
            qty
        )
# -----------------------------------
#   Clear Purchase Fields
# -----------------------------------
def clear_purchase_fields(

        product,
        purchase_price,
        quantity,
        line_total,
        product_combo

    ):
        product.set("")
        purchase_price.set("")
        quantity.set("")
        line_total.set("0.00")

        product_combo.focus_set()

# =====================================
# Merge Cart Item
# =====================================

def merge_cart_item(
        cart_tree,
        product_id,
        product_name,
        price,
        qty
    ):

        for item in cart_tree.get_children():

            values = cart_tree.item(item, "values")

            old_product_id = int(values[0])
            old_price = float(values[2])

            if old_product_id == product_id and old_price == price:

                new_qty = int(values[3]) + qty

                new_line_total = new_qty * price

                cart_tree.item(
                    item,
                    values=(
                        product_id,
                        product_name,
                        price,
                        new_qty,
                        new_line_total
                    )
                )
                return True
        return False
# =====================================
# Insert Cart Item
# =====================================
def insert_cart_item(
        cart_tree,
        product_id,
        product_name,
        price,
        qty
    ):
        line_total = price * qty

        cart_tree.insert(
            "",
            END,
            values=(
                product_id,
                product_name,
                price,
                qty,
                line_total
            )
        )
# ==========================================================
# CALCULATE LINE TOTAL
# ==========================================================
def calculate_line_total(
        purchase_price,
        quantity,
        line_total
    ):
    """
    Calculate Line Total
    Formula:
        Purchase Price × Quantity
    """
    try:
        price = float(
            purchase_price.get().strip()
        )
        qty = int(
            quantity.get().strip()
        )
        total = price * qty

        line_total.set(
            f"{total:.2f}"
        )
    except ValueError:
        line_total.set("0.00")
# ===== Upsate Stock Preview  ===========
def update_stock_preview(current_stock, quantity, stock_after_purchase):
    try:
        stock = int(current_stock.get())
        qty = int(quantity.get().strip())
        stock_after_purchase.set(str(stock + qty))
    except ValueError:
        stock_after_purchase.set(current_stock.get())

# =====================================
# Add To Cart
# =====================================
def add_to_cart(
        cart_tree, product_combo, product_map,
        product, purchase_price, quantity, line_total,
        summary, supplier
    ):
        if supplier.get().strip() == "":
            messagebox.showerror("Error", "Please select a supplier before adding items.")
            return
# -----------------------------------------
# Validate User Input
# -----------------------------------------
        data = validate_cart_input(product, purchase_price, quantity)
        if data is None:
            return

        product_name, price, qty = data

        product_id = product_map[product_name]
    # -----------------------------------------
    # Merge Existing Cart Item
    # -----------------------------------------
        merged = merge_cart_item(
            cart_tree,
            product_id,
            product_name,
            price,
            qty
        )
        if not merged:
    # -----------------------------------------
    # Insert New Cart Item
    # -----------------------------------------
            insert_cart_item(
                cart_tree, product_id,
                product_name,
                price, qty
            )
    # -----------------------------------------
    # Clear Entry Fields
    # -----------------------------------------
        clear_purchase_fields(
            product, purchase_price,
            quantity, line_total,
            product_combo
        )
    # -----------------------------------------
    # Update purchase totals
    # -----------------------------------------
        calculate_purchase_totals(cart_tree, summary)
# ----------------------------------------------
#  Purchase Window
# ------------------------------------------
def purchase_window():

    win = Toplevel()
    add_branding_strip(win)
    
    win.title("Purchase Management")
    win.state("zoomed")   # window

    # Center Window
    width = 1150
    height = 700

    win.iconbitmap("assets/ims.ico")

    screen_width = win.winfo_screenwidth()
    screen_height = win.winfo_screenheight()

    x = int((screen_width / 2) - (width / 2))
    y = int((screen_height / 2) - (height / 2))

    win.geometry(f"{width}x{height}+{x}+{y}")

    win.focus_force()
    # ==========================
    # Variables
    # ==========================

    supplier = StringVar()
    invoice_no = StringVar()
    product = StringVar()
    purchase_price = StringVar()
    quantity = StringVar()
    current_stock = StringVar(value="0")
    stock_after_purchase = StringVar(value="0")

    line_total = StringVar(value="0.00")
    summary = PurchaseSummary()

    gross_display = StringVar(value=format_currency(0))
    discount_amt_display = StringVar(value=format_currency(0))
    tax_amt_display = StringVar(value=format_currency(0))
    net_display = StringVar(value=format_currency(0))

    def sync_currency_displays(*args):
        gross_display.set(format_currency(float(summary.gross_total.get() or 0)))
        discount_amt_display.set(format_currency(float(summary.discount_amount.get() or 0)))
        tax_amt_display.set(format_currency(float(summary.tax_amount.get() or 0)))
        net_display.set(format_currency(float(summary.net_total.get() or 0)))

    summary.gross_total.trace_add("write", sync_currency_displays)
    summary.discount_amount.trace_add("write", sync_currency_displays)
    summary.tax_amount.trace_add("write", sync_currency_displays)
    summary.net_total.trace_add("write", sync_currency_displays)
# ==========================================================
# Main Layout Frame
# ==========================================================
    main_frame = Frame(win, bg="white")

    main_frame.pack(
        fill=BOTH,
        expand=True,
        padx=10,
        pady=10
    )
    main_frame.columnconfigure(0, weight=3)
    main_frame.columnconfigure(1, weight=1)
    main_frame.rowconfigure(1, weight=1)

    # -------------------------------------
    # Purchase Details
    # ==========================
    purchase_frame = LabelFrame(
        win,
        text="Purchase Details",
        padx=10,
        pady=10
    )
    purchase_frame.grid(
        in_=main_frame,
        row=0,
        column=0,
        padx=(0, 10),
        pady=5,
        sticky="nsew"
    )
    #-------------------------------------------------
    # Purchase Cart
    # ==========================

    cart_frame = LabelFrame(
        win,
        text="Purchase Cart",
        padx=10,
        pady=10
    )

    cart_frame.grid(
        in_=main_frame,
        row=1,
        column=0,
        columnspan=2,
        pady=(10, 0),
        sticky="nsew"
    )
# -------------------------------------
#       ScrollBar
    scrollbar_y = Scrollbar(cart_frame)

    scrollbar_y.pack(
        side=RIGHT,
        fill=Y
    )
    # ==========================================================
    # Purchase Items TreeView, Heading, Columns
    # ==========================================================
    CART_COLUMNS = [
    {"key": "Product ID", "heading": "Product ID", "width": 90, "anchor": CENTER},
    {"key": "Product", "heading": "Product", "width": 250, "anchor": W},
    {"key": "Purchase Price", "heading": "Purchase Price", "width": 130, "anchor": E},
    {"key": "Quantity", "heading": "Quantity", "width": 100, "anchor": CENTER},
    {"key": "Line Total", "heading": "Line Total", "width": 140, "anchor": E},
    ]
    cart_tree = build_treeview(cart_frame, CART_COLUMNS)
    cart_tree.configure(yscrollcommand=scrollbar_y.set)
    scrollbar_y.config(command=cart_tree.yview)

    #   TreeView Hide Product ID, User ID Not Seen
    cart_tree["displaycolumns"] = (
        "Product",
        "Purchase Price",
        "Quantity",
        "Line Total"
    )
    # ----Pack------
    cart_tree.pack(fill=BOTH,expand=True)
    # ------------------------------------
    #====  Handle ==========
    def handle_save_purchase():
        save_purchase(supplier, invoice_no, purchase_date_picker, cart_tree, summary,
                      payment_type, amount_paid)
        product.set("")
        purchase_price.set("")
        quantity.set("")
        line_total.set("0.00")
        current_stock.set("0")
        stock_after_purchase.set("0")
        payment_type.set("Cash")
        on_payment_type_change()
# ========================================================
#   New Purchase Handler (F3)
#   Same reset as a successful save, minus the actual saving -
#   mirrors handle_save_purchase's field clearing below.
# ===========================================================
    def handle_new_purchase():
        clear_purchase_form(supplier, cart_tree, summary)
        invoice_no.set("")
        product.set("")
        purchase_price.set("")
        quantity.set("")
        line_total.set("0.00")
        current_stock.set("0")
        stock_after_purchase.set("0")
        payment_type.set("Cash")
        on_payment_type_change()

# ===========================
#   Escape Handler
#   Confirms before closing if the cart still has unsaved items,
#   same safeguard as Sales.
# ===========================
    def handle_escape():
        if cart_tree.get_children():
            confirm = messagebox.askyesno(
                "Unsaved Purchase",
                "This purchase hasn't been saved yet. Close anyway?"
            )
            if not confirm:
                return
        win.destroy()

# ===========================
#   Keyboard Shortcuts
#   F2 = Save Purchase, F3 = New Purchase, Escape = Close (with
#   confirm), Delete (cart selected) = Remove Item, Enter (in
#   Quantity) = Add To Cart
# ===========================
    bind_shortcuts(win, {
        "<F2>": handle_save_purchase,
        "<F3>": handle_new_purchase,
        "<Escape>": handle_escape,
    })
    cart_tree.bind("<Delete>", lambda event: remove_cart_item(cart_tree, summary))
    # =====================================
    # Purchase Summary
    # =====================================

    summary_frame = LabelFrame(
        win,
        text="Purchase Summary",
        padx=10,
        pady=10
        )
    summary_frame.grid(
        in_=main_frame,
        row=0,
        column=1,
        padx=(10, 0),
        pady=5,
        sticky="new"
    )

    def refresh_totals():
        calculate_purchase_totals(cart_tree, summary)
    
    labeled_entry(summary_frame, "Gross Total", 0, 0, gross_display, readonly=True)

    discount_entry = labeled_entry(summary_frame, "Discount %", 1, 0, summary.discount)
    discount_entry.bind("<KeyRelease>", lambda event: refresh_totals())

    labeled_entry(summary_frame, "Discount Amount", 2, 0, discount_amt_display, readonly=True)

    tax_entry = labeled_entry(summary_frame, "Tax %", 3, 0, summary.tax)
    tax_entry.bind("<KeyRelease>", lambda event: refresh_totals())

    labeled_entry(summary_frame, "Tax Amount", 4, 0, tax_amt_display, readonly=True)

    Label(summary_frame, text="Net Total", font=("Arial", 10, "bold")
        ).grid(row=5, column=0, sticky="w", pady=5)
    Entry(summary_frame, textvariable=net_display,
        width=20, state="readonly", justify="right",
        font=("Arial", 10, "bold")
        ).grid(row=5, column=1, padx=10)

# ---------------------------------------------
#   Payment Type (Cash / Credit)
# ---------------------------------------------
    payment_type = StringVar(value="Cash")
    amount_paid = StringVar(value="0")

    Label(summary_frame, text="Payment", font=("Arial", 9, "bold")
        ).grid(row=6, column=0, sticky="w", pady=(12, 2))

    payment_frame = Frame(summary_frame)
    payment_frame.grid(row=6, column=1, sticky="w", pady=(12, 2))

    amount_paid_entry = Entry(summary_frame, textvariable=amount_paid, width=20)

    def on_payment_type_change():
        if payment_type.get() == "Credit":
            amount_paid_entry.config(state="normal")
            amount_paid.set("0")
        else:
            amount_paid.set(str(net_display.get()))
            amount_paid_entry.config(state="disabled")

    Radiobutton(
        payment_frame, text="Cash", variable=payment_type, value="Cash",
        command=on_payment_type_change
    ).pack(side=LEFT)

    Radiobutton(
        payment_frame, text="Credit", variable=payment_type, value="Credit",
        command=on_payment_type_change
    ).pack(side=LEFT, padx=(10, 0))

    Label(summary_frame, text="Amount Paid Now"
        ).grid(row=7, column=0, sticky="w", pady=5)
    amount_paid_entry.grid(row=7, column=1, padx=10)
    amount_paid_entry.config(state="disabled")  # Cash is selected by default

    refresh_totals()  # show correctly formatted currency as soon as the window opens
    
# =================================================
#  Label
# -----------------------------------
    Label(
        purchase_frame,
            text="Supplier"
        ).grid(row=0, column=0, padx=10, pady=8, sticky="w")
    # ----------------------------------------------------------
    # Invoice No
    # ----------------------------------------------------------
    Label(
        purchase_frame,
        text="Invoice No"
        ).grid(row=0, column=2, padx=10, pady=8, sticky="w")

    invoice_entry = Entry(
            purchase_frame,
            textvariable=invoice_no
        )

    invoice_entry.grid(row=0, column=3, padx=10, pady=8, sticky="ew")


    Label(
        purchase_frame,
            text="Product"
        ).grid(row=1, column=0, padx=10, pady=8, sticky="w")
# ----------------------------------------------------------
# Purchase Date
# ----------------------------------------------------------
    Label(
        purchase_frame,
        text="Purchase Date"
        ).grid(row=1, column=2, padx=10, pady=8, sticky="w")

    purchase_date_picker = labeled_date_picker(purchase_frame, "Purchase Date", 1, 2)

    Label(
        purchase_frame,
            text="Purchase Price"
        ).grid(row=2, column=0, padx=10, pady=8, sticky="w")
    labeled_entry(
         purchase_frame, "Current Stock", 3, 2, current_stock, readonly=True)
    labeled_entry(
         purchase_frame, "Stock After Purchase", 4, 0, stock_after_purchase, readonly=True)
    
    Label(
        purchase_frame,
            text="Quantity"
        ).grid(row=2, column=2, padx=10, pady=8, sticky="w")
    # ----------------------------------------------
    # Line Total
    # ----------------------------------------------
    Label(
        purchase_frame,
            text="Line Total"
        ).grid(row=3, column=0, padx=10, pady=8, sticky="w")
    line_total_entry = Entry(
            purchase_frame,
            textvariable=line_total,
            state="readonly",
            justify="right"
        )
    line_total_entry.grid(row=3, column=1, padx=10, pady=8, sticky="ew")
# ----------------------------------------------
# Supplier Combobox
# ----------------------------------------------
    supplier_combo = ttk.Combobox(
        purchase_frame,
        textvariable=supplier,
        width=35,
        state="readonly"
    )

    supplier_combo.grid(
        row=0,
        column=1,
        padx=10,
        pady=8
    )
# ----------------------------------------------
# Product Combobox
# ---------------------------------------------
    product_combo = ttk.Combobox(
        purchase_frame,
        textvariable=product,
        width=35,
        state="readonly"
    )

    product_combo.grid(
        row=1,
        column=1,
        padx=10,
        pady=8
    )
# ---------------------------------------------
# Barcode Scan
# (scanning fills product/price/stock and adds the line to the
#  cart immediately, same convenience as the Sales screen)
# ---------------------------------------------
    def on_barcode_scanned(product_row):
        product_id, product_name, cost_price, sale_price_value, stock, status, barcode_value = product_row

        if product_name not in product_map:
            product_map[product_name] = product_id

        product.set(product_name)
        purchase_price.set(cost_price)
        current_stock.set(stock)
        stock_after_purchase.set(stock)
        quantity.set(1)

        add_to_cart(
            cart_tree, product_combo, product_map,
            product, purchase_price, quantity, line_total, summary, supplier
        )

    Label(purchase_frame, text="Scan Barcode").grid(row=4, column=2, padx=10, pady=8, sticky="w")
    scan_entry = create_scan_entry(purchase_frame, on_barcode_scanned, width=20)
    scan_entry.grid(row=4, column=3, padx=10, pady=8, sticky="ew")

# ---------------------------------------------
# Purchase Price Entry
# --------------------------------------------
    purchase_price_entry = Entry(
        purchase_frame,
        textvariable=purchase_price,
    )
    purchase_price_entry.grid(
        row=2,
        column=1,
        padx=10,
        pady=8,
        sticky="ew"
    )
# ----------------------------------------------
# Quantity Entry
# ----------------------------------------------
    quantity_entry = Entry(
        purchase_frame,
        textvariable=quantity,
    )
    quantity_entry.grid(
        row=2,
        column=3,
        padx=10,
        pady=8,
        sticky="ew"
    )  
# -----------------------------------------
#       Bind
# -----------------------------------------
    purchase_price_entry.bind(
        "<KeyRelease>",
        lambda event: calculate_line_total(
            purchase_price,
            quantity,
            line_total
        )
    )

    quantity_entry.bind(
        "<KeyRelease>",
        lambda event:(
            calculate_line_total(purchase_price, quantity, line_total),
            update_stock_preview(current_stock, quantity, stock_after_purchase)
        )
    )
# ==================================================================================
#   Keyboard Shortcut
#   Enter (while typing Quantity) = Add To Cart, same as clicking
#   the button
# ==================================================================================
    quantity_entry.bind(
        "<Return>",
        lambda event: add_to_cart(
            cart_tree, product_combo, product_map,
            product, purchase_price, quantity, line_total, summary, supplier
        )
    )
# =====================================
# Buttons Frame
# =====================================
    button_frame = Frame(purchase_frame)

    button_frame.grid(
        row=5,
        column=0,
        columnspan=4,
        pady=(15, 5),
        sticky="ew"
    )
    button_frame.columnconfigure((0, 1, 2, 3, 4), weight=1)

# =====================================
# Buttons
# =====================================
    add_buttons(button_frame, [
            ("Add To Cart", lambda: add_to_cart(cart_tree, product_combo, product_map,
                product, purchase_price, quantity, line_total, summary, supplier)),
            ("Remove Item", lambda: remove_cart_item(cart_tree, summary)),
            ("Clear Cart", lambda: clear_cart(cart_tree, summary)),
            ("Save Purchase", handle_save_purchase),
            ("Purchase History", purchase_history),
            ("Process Return", open_purchase_return_window),
            ("Return History", open_return_history_window),

        ])
# ----------------------------------------------
#  Supplier , Products load in combobox
# -------------------------------------------
    supplier_combo["values"] = load_suppliers()

# ---------------------------
#  Supplier Selected
#  (auto-fills Tax % based on the supplier's filer status —
#  summary/refresh_totals already exist above, so it's safe here)
# ---------------------------
    def on_supplier_selected(event):

        supplier_name = supplier_combo.get()
        supplier_id = get_supplier_id_by_name(supplier_name)

        if supplier_id is None:
            return

        is_filer = get_supplier_filer_status(supplier_id)
        tax_rate = get_applicable_tax_rate(is_filer)

        summary.tax.set(str(tax_rate))
        refresh_totals()

    supplier_combo.bind("<<ComboboxSelected>>", on_supplier_selected)

    products = load_products()

    product_map = {}

    product_names = []

    for product_id, product_name in products:

        product_map[product_name] = product_id

        product_names.append(product_name)

    product_combo["values"] = product_names
# -----------------------------------------------
#  event bind
# -----------------------------------------
    product_combo.bind(
    "<<ComboboxSelected>>",
    lambda event: on_product_selected(
        event, purchase_price,
        current_stock, stock_after_purchase, 
        product_map
        )
    )
# --------------------------------------------
# =====================================
# Load Purchase History (into Treeview)
# =====================================
def load_purchase_history(history_tree, search_term=None, date_from=None, date_to=None):
    reload_treeview(history_tree, get_purchase_history(search_term, date_from, date_to))

# =====================================
# Purchase History Window
# =====================================
def purchase_history():

    history_win = Toplevel()
    history_win.title("Purchase History")
    screen_width = history_win.winfo_screenwidth()
    screen_height = history_win.winfo_screenheight()

    width = int(screen_width * 0.90)
    height = int(screen_height * 0.80)

    x = (screen_width - width) // 2
    y = (screen_height - height) // 2

    history_win.geometry(
        f"{width}x{height}+{x}+{y}"
    )

    history_win.minsize(950, 500)

    history_win.iconbitmap("assets/ims.ico")

# ========================================================================
    # Search Frame
# =========================================================================
    search_frame = LabelFrame(history_win, text="Search Purchase", padx=10, pady=10)
    search_frame.pack(fill="x", padx=10, pady=10)

    Label(search_frame, text="Purchase No").grid(row=0, column=0, padx=5)
    purchase_search = StringVar()

    Entry(search_frame, textvariable=purchase_search, width=30).grid(row=0, column=1, padx=5)

    date_from_picker = labeled_date_picker(search_frame, "From", 1, 0)
    date_to_picker = labeled_date_picker(search_frame, "To", 1, 2)

    Button(
        search_frame, text="Filter by Date", width=14,
        command=lambda: load_purchase_history(
            history_tree, date_from=date_from_picker.get(), date_to=date_to_picker.get()
        )
    ).grid(row=1, column=4, padx=5)
    #========================================================
    Button(
        search_frame, text="🖨 Print Report", width=14,
        command=lambda: generate_purchase_report_pdf(
            get_purchase_history(None, date_from_picker.get(), date_to_picker.get()),
            date_from_picker.get(), date_to_picker.get()
        )
    ).grid(row=1, column=5, padx=5)

    Button(
        search_frame, text="🖨 Print Selected", width=14,
        command=lambda: print_selected_receipt()
    ).grid(row=1, column=6, padx=5)

    Button(
        search_frame, text="🗂 Export to Excel", width=16,
        command=lambda: export_current_history()
    ).grid(row=1, column=7, padx=5)
    # ===========================================
    # ======= Helper function Excel export ======
    def export_current_history():
        rows = get_purchase_history(
            purchase_search.get().strip() or None,
            date_from_picker.get(), date_to_picker.get()
        )

        headers = [
            "ID", "Purchase No", "Supplier", "Gross Total",
            "Discount %", "Discount Amt", "Tax %", "Tax Amt",
            "Net Total", "Date", "Qty", "Returned Qty",
            "Payment Status", "Amount Paid", "Balance Due"
        ]

        export_to_excel(headers, rows, "Purchase_History")
# ===========================================
        # Button
# ============================================
    Button(
        search_frame, text="Search", width=12,
        command=lambda: load_purchase_history(history_tree, purchase_search.get().strip())
    ).grid(row=0, column=2, padx=5)

    Button(
        search_frame, text="Show All", width=12,
        command=lambda: load_purchase_history(history_tree)
    ).grid(row=0, column=3, padx=5)
# ============================================================================
    # Table Frame
# ============================================================================
    table_frame = Frame(history_win)
    table_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

    scroll_y = Scrollbar(table_frame, orient=VERTICAL)
    scroll_x = Scrollbar(table_frame, orient=HORIZONTAL)

    HISTORY_COLUMNS = [
    {"key": "id","heading": "ID","width": 45,"min_width": 40,"anchor": CENTER},
    {"key": "purchase_no","heading": "Purchase No","width": 105,"min_width": 90,
     "anchor": CENTER},
    {"key": "supplier","heading": "Supplier","width": 110, "min_width": 105, 
     "anchor": CENTER},
    {"key": "gross_total","heading": "Gross Total", "width": 105,"min_width": 90,
        "anchor": CENTER},
    {"key": "discount","heading": "Discount %","width": 75,"min_width": 65,
        "anchor": CENTER},
    {"key": "discount_amount","heading": "Discount Amount","width": 115,
     "min_width": 100, "anchor": E},
    {"key": "tax", "heading": "Tax %", "width": 65,"min_width": 55,
        "anchor": CENTER},
    {"key": "tax_amount","heading": "Tax Amount","width": 105,"min_width": 90,
        "anchor": E},
    {"key": "net_total", "heading": "Net Total","width": 110,"min_width": 95,
        "anchor": E},
    {"key": "date", "heading": "Date", "width": 145, "min_width": 120,
     "anchor": CENTER},
    { "key": "quantity", "heading": "Qty", "width": 60, "min_width": 50,
        "anchor": CENTER},
    { "key": "returned_qty", "heading": "Returned", "width": 70,"min_width": 60,
        "anchor": CENTER},
    {"key": "payment_status", "heading": "Payment", "width": 85, "min_width": 75,
        "anchor": CENTER},
    {"key": "amount_paid", "heading": "Amount Paid", "width": 100, "min_width": 90,
        "anchor": E},
    {"key": "balance_due", "heading": "Balance Due", "width": 100, "min_width": 90,
        "anchor": E},
    ]
    
    history_tree = build_treeview(table_frame, HISTORY_COLUMNS)
    history_tree.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)
    scroll_y.config(command=history_tree.yview)
    scroll_x.config(command=history_tree.xview)

    # history_tree["show"] = "headings"
    scroll_y.pack(side=RIGHT,fill=Y)
    scroll_x.pack(side=BOTTOM,fill=X)
    history_tree.pack(side=TOP,fill=BOTH,expand=True)


    load_purchase_history(history_tree)

    history_tree.bind("<Double-1>", show_purchase_details)
# ==============================================================================

    def print_selected_receipt():
        selected = history_tree.focus()
        if not selected:
            messagebox.showerror("Error", "Please select a purchase from the list first.")
            return
        values = history_tree.item(selected, "values")
        generate_purchase_receipt(values[0])

# ==============================================================
#   Keyboard Shortcut
#   Ctrl+P = Print the currently selected purchase's receipt
# ==============================================================
    bind_shortcuts(history_win, {
        "<Control-p>": print_selected_receipt,
    })
# =====================================
# Load Purchase Details Items (into Treeview)
# =====================================
def load_purchase_details_items(purchase_id, details_tree):
    clear_treeview(details_tree)
    rows = get_purchase_items(purchase_id)
    for index, (product, price, qty, total) in enumerate(rows, start=1):
        details_tree.insert("", "end", values=(index, product,
                                               format_currency(price), qty, format_currency(total)))

# =====================================
# Purchase Details Window
# =====================================
def show_purchase_details(event):

    history_tree = event.widget
    selected = history_tree.focus()

    if not selected:
        return

    values = history_tree.item(selected, "values")
    purchase_id = values[0]

    (
    purchase_no, invoice_no_value, supplier_name, purchase_date_picker,
    gross_total, discount, discount_amount,
    tax, tax_amount, net_total,
    payment_status, amount_paid
    ) = get_purchase_header(purchase_id)

    details_win = Toplevel()
    details_win.title("Purchase Details")
    details_win.iconbitmap("assets/ims.ico")
    size_and_center(details_win, width_ratio=0.7, height_ratio=1, resizable=True)


    header_frame = LabelFrame(details_win, text="Purchase Information", padx=10, pady=10)
    header_frame.pack(fill="x", padx=10, pady=10)

    Label(
        header_frame, text=f"Purchase No : {purchase_no}", font=("Arial", 11, "bold")
    ).grid(row=0, column=0, padx=10, pady=5, sticky="w")

    Label(
        header_frame, text=f"Supplier : {supplier_name}", font=("Arial", 11)
    ).grid(row=1, column=0, padx=10, pady=5, sticky="w")
    Label(
        header_frame, text=f"Invoice No : {invoice_no_value or '-'}", font=("Arial", 11)
    ).grid(row=1, column=1, padx=30, pady=5, sticky="w")

    Label(
        header_frame, text=f"Purchase Date : {purchase_date_picker}", font=("Arial", 11)
    ).grid(row=2, column=0, padx=10, pady=5, sticky="w")
# =========================================================================================
    # Items Frame
# =========================================================================================
    items_frame = Frame(details_win)
    items_frame.pack(fill="both", expand=True, padx=10, pady=10)

    DETAILS_COLUMNS = [
    {"key": "sno", "heading": "S.No", "width": 60, "anchor": CENTER},
    {"key": "product", "heading": "Product", "width": 280, "anchor": CENTER},
    {"key": "price", "heading": "Purchase Price", "width": 120, "anchor": E},
    {"key": "qty", "heading": "Quantity", "width": 100, "anchor": CENTER},
    {"key": "total", "heading": "Total", "width": 120, "anchor": E},
    ]
    details_tree = build_treeview(items_frame, DETAILS_COLUMNS)

    details_tree["show"] = "headings"
    details_tree.pack(fill=BOTH, expand=True)

    load_purchase_details_items(purchase_id, details_tree)
# ===========================================================================
    # Totals Frame
# ===========================================================================
    totals_frame = LabelFrame(details_win, text="Totals", padx=10, pady=10)

    Label(
        totals_frame, text=f"Gross Total : {format_currency(gross_total)}"
    ).grid(row=0, column=0, padx=20, pady=5, sticky="w")

    Label(
        totals_frame, text=f"Discount : {discount}%  ({format_currency(discount_amount)})"
    ).grid(row=0, column=1, padx=20, pady=5, sticky="w")

    Label(
        totals_frame, text=f"Tax : {tax}%  ({format_currency(tax_amount)})"
    ).grid(row=0, column=2, padx=20, pady=5, sticky="w")

    Label(
        totals_frame, text=f"Net Total : {format_currency(net_total)}", font=("Arial", 11, "bold")
    ).grid(row=0, column=3, padx=20, pady=5, sticky="w")

    balance_due = net_total - amount_paid

    Label(
        totals_frame, text=f"Payment : {payment_status}",
        font=("Arial", 10, "bold"),
        fg=("#B91C1C" if payment_status != "Paid" else "#166534")
    ).grid(row=1, column=0, padx=20, pady=5, sticky="w")

    Label(
        totals_frame, text=f"Amount Paid : {format_currency(amount_paid)}"
    ).grid(row=1, column=1, padx=20, pady=5, sticky="w")

    Label(
        totals_frame, text=f"Balance Due : {format_currency(balance_due)}",
        font=("Arial", 10, "bold")
    ).grid(row=1, column=2, padx=20, pady=5, sticky="w")

    totals_frame.pack(fill="x", padx=10, pady=(0, 10))
# ===============================================================
# ======== Print Button ==================
    Button(
        details_win, text="🖨 Print Receipt", width=20,
        command=lambda: generate_purchase_receipt(purchase_id)
    ).pack(side=BOTTOM, pady=(0, 15))
    
# =====================================
# Purchase Return Window
# =====================================
def open_purchase_return_window():

    return_win = Toplevel()
    return_win.title("Process Purchase Return")
    return_win.iconbitmap("assets/ims.ico")
    size_and_center(return_win, width_ratio=0.6, height_ratio=0.6)

    current_purchase_id = StringVar()

    # ---------------- Search ----------------
    search_frame = LabelFrame(return_win, text="Find Purchase", padx=10, pady=10)
    search_frame.pack(fill="x", padx=10, pady=10)

    Label(search_frame, text="Purchase No").grid(row=0, column=0, padx=5)
    purchase_no_search = StringVar()
    Entry(search_frame, textvariable=purchase_no_search, width=25).grid(row=0, column=1, padx=5)

    Button(
        search_frame, text="Load Items", width=14,
        command=lambda: load_items_for_return()
    ).grid(row=0, column=2, padx=10)

    # ---------------- Return Form (kept BEFORE the expanding---------
    # items table, so it never gets squeezed off-screen) ----------------
    form_frame = LabelFrame(return_win, text="Return Details", padx=10, pady=10)
    form_frame.pack(fill="x", padx=10, pady=(0, 10))

    Label(form_frame, text="Return Qty").grid(row=0, column=0, padx=5, pady=5)
    return_qty = IntVar(value=1)
    Entry(form_frame, textvariable=return_qty, width=10).grid(row=0, column=1, padx=5, pady=5)

    Label(form_frame, text="Reason").grid(row=0, column=2, padx=5, pady=5)
    reason = StringVar()
    Entry(form_frame, textvariable=reason, width=30).grid(row=0, column=3, padx=5, pady=5)

    def handle_process_return():

        selected = items_tree.focus()
        if not selected:
            messagebox.showerror("Error", "Please select a product from the list.")
            return

        values = items_tree.item(selected, "values")
        product_id = int(values[0])
        purchased_qty = int(values[2])
        already_returned = int(values[3])

        success = process_purchase_return(
            current_purchase_id.get(), product_id, return_qty.get(),
            reason.get().strip(), purchased_qty, already_returned
        )

        if success:
            load_items_for_return()
            return_qty.set(1)
            reason.set("")

    Button(
        form_frame, text="Process Return", width=16,
        command=handle_process_return
    ).grid(row=0, column=4, padx=10, pady=5)

    # ---------------- Items Table ----------------
    items_frame = LabelFrame(return_win, text="Purchased Items", padx=10, pady=10)
    items_frame.pack(fill="both", expand=True, padx=10, pady=10)

    items_tree = ttk.Treeview(
        items_frame,
        columns=("product_id", "product", "purchased_qty", "already_returned", "remaining"),
        show="headings"
    )
    items_tree.heading("product", text="Product")
    items_tree.heading("purchased_qty", text="Purchased Qty")
    items_tree.heading("already_returned", text="Already Returned")
    items_tree.heading("remaining", text="Remaining")
    items_tree.column("product", width=250)
    items_tree.column("purchased_qty", width=110, anchor=CENTER)
    items_tree.column("already_returned", width=130, anchor=CENTER)
    items_tree.column("remaining", width=100, anchor=CENTER)
    items_tree["displaycolumns"] = ("product", "purchased_qty", "already_returned", "remaining")
    items_tree.pack(fill=BOTH, expand=True)

    def load_items_for_return():

        for row in items_tree.get_children():
            items_tree.delete(row)

        purchase_no = purchase_no_search.get().strip()
        if purchase_no == "":
            messagebox.showerror("Error", "Please enter a Purchase No.")
            return

        matches = get_purchase_history(purchase_no)
        if not matches:
            messagebox.showerror("Error", "No purchase found with that Purchase No.")
            return

        purchase_id = matches[0][0]
        current_purchase_id.set(purchase_id)

        for product_id, product_name, purchased_qty, already_returned in get_purchase_items_for_return(purchase_id):
            remaining = purchased_qty - already_returned
            items_tree.insert("", "end", values=(
                product_id, product_name, purchased_qty, already_returned, remaining
            ))
# =====================================
# Return History Window
# (shows ALL returns across all purchases - lets admin see
#  everything returned, with a "Today Only" filter)
# =====================================
RETURN_HISTORY_COLUMNS = [
    {"key": "date", "heading": "Return Date", "width": 160, "stretch": False},
    {"key": "purchase_no", "heading": "Purchase No", "width": 120, "stretch": False},
    {"key": "product", "heading": "Product", "width": 220, "stretch": False},
    {"key": "quantity", "heading": "Quantity", "width": 90, "anchor": CENTER, "stretch": False},
    {"key": "reason", "heading": "Reason", "width": 250, "stretch": False},
    ]

def open_return_history_window():

    win = Toplevel()
    win.title("Purchase Return History")
    win.iconbitmap("assets/ims.ico")
    size_and_center(win, width_ratio=0.75, height_ratio=0.65)

    filter_frame = Frame(win)
    filter_frame.pack(fill="x", padx=10, pady=10)

    show_today_only = BooleanVar(value=False)

    def refresh_list():
        clear_treeview(returns_tree)
        rows = get_all_purchase_returns(today_only=show_today_only.get())
        for row in rows:
            returns_tree.insert("", "end", values=row)

    Checkbutton(
        filter_frame, text="Today's Returns Only",
        variable=show_today_only, command=refresh_list
    ).pack(side=LEFT)

    Button(
        filter_frame, text="Refresh", width=12,
        command=refresh_list
    ).pack(side=RIGHT)

    table_frame = Frame(win)
    table_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

    scroll_y = Scrollbar(table_frame, orient=VERTICAL)
    scroll_x = Scrollbar(table_frame, orient=HORIZONTAL)

    returns_tree = build_treeview(table_frame, RETURN_HISTORY_COLUMNS)
    returns_tree.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)

    scroll_y.config(command=returns_tree.yview)
    scroll_x.config(command=returns_tree.xview)

    scroll_y.pack(side=RIGHT, fill=Y)
    scroll_x.pack(side=BOTTOM, fill=X)

    returns_tree.pack(fill=BOTH, expand=True)

    refresh_list()