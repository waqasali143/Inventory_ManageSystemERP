from tkinter import *
from tkinter import ttk

from tkinter import messagebox
from utils.ui_helpers import add_buttons, labeled_entry, labeled_date_picker
from utils.export_helpers import export_to_excel
from utils.window_helpers import size_and_center
from utils.branding_helpers import add_branding_strip
from utils.barcode_helpers import create_scan_entry

from services.sales_summary import SalesSummary
from services.sales_service import (
    load_customers, get_customer_id_by_name, load_products, get_product_details,
    validate_sale_line, calculate_sale_totals,
    remove_cart_item, clear_cart, clear_sale_form,
    save_sale, get_sales_history, get_sale_header, get_sale_items,
    get_sale_items_for_return, get_returns_for_sale, process_sale_return,
    get_all_sale_returns
)
from services.settings_service import format_currency
from services.invoice_service import generate_sale_invoice_a4, generate_sales_report_pdf
from utils.shortcut_helper import bind_shortcuts
from services.customer_service import get_customer_filer_status
from services.tax_service import get_applicable_tax_rate

# =====================================
# Sales Window
# =====================================
def sales_window():

    win = Toplevel()
    add_branding_strip(win)

    win.title("Sales Management")
    size_and_center(win, width_ratio=0.9, height_ratio=0.88, resizable=True)

    win.iconbitmap("assets/ims.ico")


    win.focus_force()

# =====================================
# Toolbar
# =====================================
    toolbar = Frame(
        win,
        bd=2,
        relief=RIDGE,
        bg="white"
    )

    toolbar.pack(side=TOP, fill=X)
# =====================================
# Sales Information Frame
# =====================================
    sales_frame = LabelFrame(
        win,
        text="Sales Information",
        padx=10,
        pady=10
    )

    sales_frame.pack(
        fill="x",
        padx=10,
        pady=10
    )
# =====================================
# Sales Totals Frame
# =====================================
    totals_frame = LabelFrame(
        win,
        text="Sales Totals",
        padx=10,
        pady=10
    )
    totals_frame.pack(
        side=BOTTOM,
        fill="x",
        padx=10,
        pady=(0, 10)
    )
    # -----------------------------
    # Summary Object (replaces the 4 separate DoubleVars)
    # -----------------------------
    summary = SalesSummary()

    gross_display = StringVar(value=format_currency(0))
    discount_amt_display = StringVar(value=format_currency(0))
    tax_amt_display = StringVar(value=format_currency(0))
    net_display = StringVar(value=format_currency(0))

    def refresh_totals():
        calculate_sale_totals(cart_tree, summary)
        gross_display.set(format_currency(float(summary.gross_total.get())))
        discount_amt_display.set(format_currency(float(summary.discount_amount.get())))
        tax_amt_display.set(format_currency(float(summary.tax_amount.get())))
        net_display.set(format_currency(float(summary.net_total.get())))

    # -------------------------------------
    # Gross Total
    # -------------------------------------
    Label(totals_frame, text="Gross Total").grid(row=0, column=0, padx=5, pady=5)
    Entry(
        totals_frame, textvariable=gross_display,
        width=16, state="readonly", justify="right"
    ).grid(row=0, column=1, padx=5, pady=5)

    # -------------------------------------
    # Discount %
    # -------------------------------------
    Label(totals_frame, text="Discount %").grid(row=0, column=2, padx=5, pady=5)
    discount_entry = Entry(totals_frame, textvariable=summary.discount, width=16, justify="right")
    discount_entry.grid(row=0, column=3, padx=5, pady=5)
    discount_entry.bind("<KeyRelease>", lambda event: refresh_totals())

    # -------------------------------------
    # Discount Amount (NEW - this is the field that was missing
    # before, so the actual discount amount never got saved)
    # -------------------------------------
    Label(totals_frame, text="Discount Amt").grid(row=0, column=4, padx=5, pady=5)
    Entry(
        totals_frame, textvariable=discount_amt_display,
        width=16, state="readonly", justify="right"
    ).grid(row=0, column=5, padx=5, pady=5)

    # ---------------------------------
    # Tax %
    # ---------------------------------
    Label(totals_frame, text="Tax %").grid(row=1, column=0, padx=5, pady=5)
    tax_entry = Entry(totals_frame, textvariable=summary.tax, width=16, justify="right")
    tax_entry.grid(row=1, column=1, padx=5, pady=5)
    tax_entry.bind("<KeyRelease>", lambda event: refresh_totals())

    # ---------------------------------
    # Tax Amount (NEW - same reason as Discount Amount)
    # ---------------------------------
    Label(totals_frame, text="Tax Amt").grid(row=1, column=2, padx=5, pady=5)
    Entry(
        totals_frame, textvariable=tax_amt_display, width=16, 
        state="readonly", justify="right"
    ).grid(row=1, column=3, padx=5, pady=5)

    # ---------------------------------
    # Net Total
    # ---------------------------------
    Label(
        totals_frame, text="Net Total", font=("Arial", 10, "bold")
    ).grid(row=1, column=4, padx=5, pady=5)
    Entry(
        totals_frame, textvariable=net_display, width=16, 
        state="readonly", justify="right", font=("Arial", 10, "bold")
    ).grid(row=1, column=5, padx=5, pady=5)

# ---------------------------------
# Payment Type (Cash / Credit)
# ---------------------------------
    payment_type = StringVar(value="Cash")
    amount_paid = StringVar(value="0")

    Label(totals_frame, text="Payment").grid(row=2, column=0, padx=5, pady=5)

    payment_frame = Frame(totals_frame)
    payment_frame.grid(row=2, column=1, padx=5, pady=5, sticky="w")

    amount_paid_entry = Entry(totals_frame, textvariable=amount_paid, width=16, justify="right")

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

    Label(totals_frame, text="Amount Paid Now").grid(row=2, column=2, padx=5, pady=5)
    amount_paid_entry.grid(row=2, column=3, padx=5, pady=5)
    amount_paid_entry.config(state="disabled")  # Cash is selected by default

# =====================================
# Sales Cart Frame
# =====================================
    cart_frame = LabelFrame(
        win,
        text="Sales Cart",
        padx=10,
        pady=10
    )

    cart_frame.pack(
        fill="both",
        expand=True,
        padx=10,
        pady=10
    )
    
# ======  Scrollbars  ======
    scroll_y = Scrollbar(
        cart_frame,
        orient=VERTICAL
    )
    scroll_x = Scrollbar(
        cart_frame,
        orient=HORIZONTAL
    )
# ====  Treeview  ===========
    cart_tree = ttk.Treeview(
        cart_frame,
        columns=(
            "product_id",
            "product",
            "price",
            "qty",
            "total"
        ),
        yscrollcommand=scroll_y.set,
        xscrollcommand=scroll_x.set
    )
# ==========================
#   Scrollbar Connect
# ==========================
    scroll_y.config(
        command=cart_tree.yview
    )
    scroll_x.config(
        command=cart_tree.xview
    )
    scroll_y.pack(
        side=RIGHT,
        fill=Y
    )
    scroll_x.pack(
        side=BOTTOM,
        fill=X
    )
# =========================
#   Headings
# =========================
    cart_tree.heading(
        "product",
        text="Product"
    )
    cart_tree.heading(
        "price",
        text="Sale Price"
    )
    cart_tree.heading(
        "qty",
        text="Quantity"
    )
    cart_tree.heading(
        "total",
        text="Total"
    )
# ==========================
#   Columns
# ==========================
    cart_tree.column(
        "product",
        width=350
    )
    cart_tree.column(
        "price",
        width=120,
        anchor=E
    )
    cart_tree.column(
        "qty",
        width=100,
        anchor=CENTER
    )
    cart_tree.column(
        "total",
        width=120,
        anchor=E
    )
# =========================================================
#   Show & Pack
#   (product_id column stays hidden - only used internally)
# =========================================================
    cart_tree["show"] = "headings"
    cart_tree["displaycolumns"] = ("product", "price", "qty", "total")

    cart_tree.pack(
        fill=BOTH,
        expand=True
    )
    refresh_totals()  # now cart_tree exists, safe to call

# ===========================
#   Keyboard Shortcut
#   Delete (while cart_tree has focus) = Remove selected cart item.
#   Bound on cart_tree itself, not the window - so it never fires
#   while the user is deleting text inside a normal Entry field.
# ===========================
    def handle_remove_cart_item():
        remove_cart_item(cart_tree, summary)
        refresh_totals()

    cart_tree.bind("<Delete>", lambda event: handle_remove_cart_item())
# ===========================
#   Customer Field
# ==========================
    Label(
        sales_frame,
        text="Customer"
    ).grid(
        row=0,
        column=0,
        padx=5,
        pady=5
    )
    customer = StringVar()

    customer_combo = ttk.Combobox(
        sales_frame,
        textvariable=customer,
        width=30,
        state="readonly"
    )
    customer_combo.grid(
        row=0,
        column=1,
        padx=5,
        pady=5
    )
    customer_combo["values"] = load_customers()

# ---------------------------
#  Customer Selected
#  (auto-fills Tax % based on the customer's filer status —
#  summary/refresh_totals already exist above, so it's safe here)
# ---------------------------
    def on_customer_selected(event):

        customer_name = customer_combo.get()
        customer_id = get_customer_id_by_name(customer_name)

        if customer_id is None:
            return

        is_filer = get_customer_filer_status(customer_id)
        tax_rate = get_applicable_tax_rate(is_filer)

        summary.tax.set(str(tax_rate))
        refresh_totals()

    customer_combo.bind("<<ComboboxSelected>>", on_customer_selected)
# ==========================
#   Product Field
# --------------===========
    Label(
        sales_frame,
        text="Product"
    ).grid(
        row=0,
        column=2,
        padx=5,
        pady=5
    )
    product = StringVar()
    product_combo = ttk.Combobox(
        sales_frame,
        textvariable=product,
        width=30,
        state="readonly"
    )
    product_combo.grid(
        row=0,
        column=3,
        padx=5,
        pady=5
    )
# -------------------------------------------------------------------

    def on_barcode_scanned(product_row):
            product_id, product_name, cost_price, sale_price_value, stock, status, barcode_value = product_row

            if product_name not in product_map:
                product_map[product_name] = product_id

            product.set(product_name)
            sale_price.set(sale_price_value)
            available_stock.set(stock)
            quantity.set(1)

            add_to_cart()  # turant cart mein add ho jaye

    Label(sales_frame, text="Scan Barcode").grid(row=2, column=2, padx=10, pady=8, sticky="w")
    scan_entry = create_scan_entry(sales_frame, on_barcode_scanned, width=20)
    scan_entry.grid(row=2, column=3, padx=10, pady=8, sticky="ew")
    scan_entry.focus_set()

# ----------------------------
    products = load_products()

    product_map = {}

    product_names = []

    for product_id, product_name in products:

        product_map[product_name] = product_id

        product_names.append(product_name)

    product_combo["values"] = product_names
# ==========================
# Quantity Fields
# ==========================
    Label(
        sales_frame,
        text="Quantity"
    ).grid(
        row=1,
        column=0,
        padx=5,
        pady=5
    )
    quantity = IntVar(value=1)

    quantity_entry = Entry(
        sales_frame,
        textvariable=quantity,
        width=15
    )
    quantity_entry.grid(
        row=1,
        column=1,
        padx=5,
        pady=5,
        sticky="w"
    )
# ==========================
#  Sale Price Field
# =========================
    Label(
        sales_frame,
        text="Sale Price"
    ).grid(
        row=1,
        column=2,
        padx=5,
        pady=5
    )
    sale_price = DoubleVar()

    sale_price_entry = Entry(
        sales_frame,
        textvariable=sale_price,
        width=15,
        state="readonly"
    )
    sale_price_entry.grid(
        row=1,
        column=3,
        padx=5,
        pady=5,
        sticky="w"
    )
# ===========================
# Available Stock Field
# ===========================
    Label(
        sales_frame,
        text="Available Stock"
    ).grid(
        row=2,
        column=0,
        padx=5,
        pady=5
    )
    available_stock = IntVar()

    stock_entry = Entry(
        sales_frame,
        textvariable=available_stock,
        width=15,
        state="readonly"
    )
    stock_entry.grid(
        row=2,
        column=1,
        padx=5,
        pady=5,
        sticky="w"
    )
# ---------------------------
#  Product Selected
#  (placed here so sale_price/available_stock already exist)
# ---------------------------
    def on_product_selected(event):

        product_name = product_combo.get()
        product_id = product_map.get(product_name)

        if product_id is None:
            return

        details = get_product_details(product_id)
        if details:
            sale_price.set(details[0])
            available_stock.set(details[1])

    product_combo.bind("<<ComboboxSelected>>", on_product_selected)

# =====================================================
#   Add To Cart Handler
#   (duplicate-check + insert, then recalculate totals)
# =====================================================
    def add_to_cart():

        if not validate_sale_line(customer, product, quantity, available_stock):
            return

        product_name = product.get()
        product_id = product_map.get(product_name)

        for item in cart_tree.get_children():
            values = cart_tree.item(item, "values")
            if int(values[0]) == product_id:
                messagebox.showerror(
                    "Duplicate Product",
                    "This product is already added to the cart."
                )
                return

        subtotal = quantity.get() * sale_price.get()

        cart_tree.insert("", "end", values=(
            product_id, product_name, sale_price.get(), quantity.get(), subtotal
        ))

        calculate_sale_totals(cart_tree, summary)

        refresh_totals()

        product.set("")
        quantity.set(1)
        sale_price.set(0)
        available_stock.set(0)

# ===========================
#   Keyboard Shortcut
#   Enter (while typing Quantity) = Add To Cart, same as clicking
#   the button - lets a cashier scan/select, type qty, hit Enter
# ===========================
    quantity_entry.bind("<Return>", lambda event: add_to_cart())

# ===========================
#   Save Handler
# ===========================
    def handle_save():
        if save_sale(customer, cart_tree, summary, payment_type, amount_paid):
            clear_sale_form(customer, product, quantity, sale_price, 
                            available_stock, cart_tree, summary)
            refresh_totals()
            payment_type.set("Cash")
            on_payment_type_change()

# ===========================
#   Keyboard Shortcuts
#   F2 = Save Sale, F3 = New Sale (same actions as the buttons below,
#   just faster for cashiers who don't want to reach for the mouse)
# ===========================
    def handle_escape():
        if cart_tree.get_children():
            confirm = messagebox.askyesno(
                "Unsaved Sale",
                "This sale hasn't been saved yet. Close anyway?"
            )
            if not confirm:
                return
        win.destroy()

    def handle_new_sale():
        clear_sale_form(customer, product, quantity, sale_price, available_stock, cart_tree, summary)
        refresh_totals()
        payment_type.set("Cash")
        on_payment_type_change()

    bind_shortcuts(win, {
        "<F2>": handle_save,
        "<F3>": handle_new_sale,
        "<Escape>": handle_escape,
    })
# ===========================
#   Buttons
# ==========================
    Button(
        toolbar, text="New Sale", width=15,
        command=handle_new_sale
    ).pack(side=LEFT, padx=5, pady=5)

    Button(
        toolbar, text="Add To Cart", width=15,
        command=add_to_cart
    ).pack(side=LEFT, padx=5, pady=5)

    Button(
        toolbar, text="Remove Item", width=15,
        command=handle_remove_cart_item
    ).pack(side=LEFT, padx=5, pady=5)

    Button(
        toolbar, text="Save Sale", width=15,
        command=handle_save
    ).pack(side=LEFT, padx=5, pady=5)

    Button(
        toolbar, text="Sales History", width=15,
        command=sales_history
    ).pack(side=LEFT, padx=5, pady=5)

    Button(
        toolbar, text="Process Return", width=15,
        command=open_return_window
    ).pack(side=LEFT, padx=5, pady=5)

    Button(
        toolbar, text="Return History", width=15,
        command=open_sale_return_history_window
    ).pack(side=LEFT, padx=5, pady=5)
# =====================================
# Sales History Window
# =====================================
def sales_history():

    history_win = Toplevel()
    history_win.title("Sales History")
    size_and_center(history_win, width_ratio=.95, height_ratio=.97, resizable=True)

    history_win.iconbitmap("assets/ims.ico")
    search_frame = LabelFrame(history_win, text="Search Sale", padx=10, pady=10)
    search_frame.pack(fill="x", padx=10, pady=10)
# ======================================================================================
# ======== Date Picker ==================

    Label(search_frame, text="Sale No").grid(row=0, column=0, padx=5)
    sale_search = StringVar()
    Entry(search_frame, textvariable=sale_search, width=30).grid(row=0, column=1, padx=5)

    Button(
        search_frame, text="Search", width=12,
        command=lambda: load_history(sale_search.get().strip())
    ).grid(row=0, column=2, padx=5)

    Button(
        search_frame, text="Show All", width=12,
        command=lambda: load_history()
    ).grid(row=0, column=3, padx=5)

    date_from_picker = labeled_date_picker(search_frame, "From", 1, 0)
    date_to_picker = labeled_date_picker(search_frame, "To", 1, 2)

    Button(
        search_frame, text="Filter by Date", width=14,
        command=lambda: load_history(
            date_from=date_from_picker.get(), date_to=date_to_picker.get()
        )
    ).grid(row=1, column=4, padx=5)
# =======================================================================================
# =========== Print ==================
    Button(
        search_frame, text="🖨 Print Report", width=14,
        command=lambda: generate_sales_report_pdf(
            get_sales_history(None, date_from_picker.get(), date_to_picker.get()),
            date_from_picker.get(), date_to_picker.get()
        )
    ).grid(row=1, column=5, padx=5)

    Button(
        search_frame, text="🖨 Print Selected", width=14,
        command=lambda: print_selected_invoice()
    ).grid(row=1, column=6, padx=5)

    Button(
        search_frame, text="🗂 Export to Excel", width=16,
        command=lambda: export_current_history()
    ).grid(row=1, column=7, padx=5)
# ===============================================================
    def export_current_history():
        rows = get_sales_history(
            sale_search.get().strip() or None,
            date_from_picker.get(), date_to_picker.get()
        )

        headers = [
            "ID", "Sale No", "Customer", "Date",
            "Gross Total", "Discount %", "Discount Amt",
            "Tax %", "Tax Amt", "Net Total", "Qty Sold", "Returned Qty",
            "Payment Status", "Amount Paid", "Balance Due"
        ]

        export_to_excel(headers, rows, "Sales_History")
# ============================================================================

    def print_selected_invoice():
        selected = history_tree.focus()
        if not selected:
            from tkinter import messagebox
            messagebox.showerror("Error", "Please select a sale from the list first.")
            return
        values = history_tree.item(selected, "values")
        generate_sale_invoice_a4(values[0])

# ===========================
#   Keyboard Shortcut
#   Ctrl+P = Print the currently selected sale's invoice
# ===========================
    bind_shortcuts(history_win, {
        "<Control-p>": print_selected_invoice,
    })

# ============================================================================
    def load_history(search_term=None, date_from=None, date_to=None):
        for row in history_tree.get_children():
            history_tree.delete(row)
        rows = get_sales_history(search_term, date_from, date_to)
        for row in rows:
            formatted = (
                row[0], row[1], row[2], row[3],
                format_currency(row[4]), row[5], format_currency(row[6]),
                row[7], format_currency(row[8]), format_currency(row[9]),
                row[10], row[11],
                row[12], format_currency(row[13]), format_currency(row[14])
            )
            history_tree.insert("", END, values=formatted)

    Button(
        search_frame, text="Search", width=12,
        command=lambda: load_history(sale_search.get().strip())
    ).grid(row=0, column=2, padx=5)

    Button(
        search_frame, text="Show All", width=12,
        command=lambda: load_history()
    ).grid(row=0, column=3, padx=5)

    table_frame = Frame(history_win)
    table_frame.pack(fill="both", expand=True, padx=10, pady=10)

    scroll_y = Scrollbar(table_frame, orient=VERTICAL)
    scroll_y.pack(side=RIGHT, fill=Y)

    scroll_x = Scrollbar(table_frame, orient=HORIZONTAL)
    scroll_x.pack(side=BOTTOM, fill=X)

    history_tree = ttk.Treeview(
        table_frame,
        columns=(
            "id", "sale_no", "customer", "date",
            "gross_total", "discount", "discount_amount",
            "tax", "tax_amount", "net_total", "quantity", "returned_qty",
            "payment_status", "amount_paid", "balance_due"
        ),
        yscrollcommand=scroll_y.set,
        xscrollcommand=scroll_x.set
    )
    scroll_y.config(command=history_tree.yview)
    scroll_x.config(command=history_tree.xview)

    history_tree.heading("id", text="ID")
    history_tree.heading("sale_no", text="Sale No")
    history_tree.heading("customer", text="Customer")
    history_tree.heading("date", text="Date")
    history_tree.heading("gross_total", text="Gross Total")
    history_tree.heading("discount", text="Discount %")
    history_tree.heading("discount_amount", text="Discount Amt")
    history_tree.heading("tax", text="Tax %")
    history_tree.heading("tax_amount", text="Tax Amt")
    history_tree.heading("net_total", text="Net Total")
    history_tree.heading("quantity", text="Qty")
    history_tree.heading("returned_qty", text="Returned")
    history_tree.heading("payment_status", text="Payment")
    history_tree.heading("amount_paid", text="Amount Paid")
    history_tree.heading("balance_due", text="Balance Due")


    history_tree.column("id", width=50, anchor=CENTER)
    history_tree.column("sale_no", width=110)
    history_tree.column("customer", width=150)
    history_tree.column("date", width=150)
    history_tree.column("gross_total", width=90, anchor=E)
    history_tree.column("discount", width=80, anchor=E)
    history_tree.column("discount_amount", width=100, anchor=E)
    history_tree.column("tax", width=80, anchor=E)
    history_tree.column("tax_amount", width=90, anchor=E)
    history_tree.column("net_total", width=100, anchor=E)
    history_tree.column("quantity", width=60, anchor=CENTER)
    history_tree.column("returned_qty", width=90, anchor=CENTER)
    history_tree.column("payment_status", width=85, anchor=CENTER)
    history_tree.column("amount_paid", width=100, anchor=E)
    history_tree.column("balance_due", width=100, anchor=E)


    history_tree["show"] = "headings"
    history_tree.pack(fill=BOTH, expand=True)

    load_history()

    def on_double_click(event):
        selected = history_tree.focus()
        if not selected:
            return
        values = history_tree.item(selected, "values")
        show_sale_details(values[0])

    history_tree.bind("<Double-1>", on_double_click)


# =====================================
# Sale Details Window
# =====================================
def show_sale_details(sale_id):

    (
        sale_no, customer_name, sale_date,
        gross_total, discount, discount_amount,
        tax, tax_amount, net_total,
        payment_status, amount_paid
    ) = get_sale_header(sale_id)

    balance_due = net_total - amount_paid

# ========= Details Window =================================
    details_win = Toplevel()
    details_win.title("Sale Details")
    details_win.iconbitmap("assets/ims.ico")
    size_and_center(details_win, width_ratio=0.7, height_ratio=1, resizable=True)

    header_frame = LabelFrame(details_win, text="Sale Information", padx=10, pady=10)
    header_frame.pack(fill="x", padx=10, pady=10)

    Label(header_frame, text=f"Sale No : {sale_no}", font=("Arial", 11, "bold")).grid(
        row=0, column=0, padx=10, pady=5, sticky="w")
    Label(header_frame, text=f"Customer : {customer_name}").grid(
        row=1, column=0, padx=10, pady=5, sticky="w")
    Label(header_frame, text=f"Sale Date : {sale_date}").grid(
        row=2, column=0, padx=10, pady=5, sticky="w")
    Label(header_frame, text=f"Payment Status : {payment_status}").grid(
        row=0, column=1, padx=10, pady=5, sticky="w")
    Label(header_frame, text=f"Amount Paid : {format_currency(amount_paid)}").grid(
        row=1, column=1, padx=10, pady=5, sticky="w")
    Label(header_frame, text=f"Balance Due : {format_currency(balance_due)}").grid(
        row=2, column=1, padx=10, pady=5, sticky="w")

    items_frame = Frame(details_win)
    items_frame.pack(fill="both", expand=True, padx=10, pady=10)

    scroll_y = Scrollbar(items_frame, orient=VERTICAL)
    scroll_y.pack(side=RIGHT, fill=Y)

    details_tree = ttk.Treeview(
        items_frame,
        columns=("product", "price", "qty", "subtotal"),
        yscrollcommand=scroll_y.set
    )
    scroll_y.config(command=details_tree.yview)

    details_tree.heading("product", text="Product")
    details_tree.heading("price", text="Sale Price")
    details_tree.heading("qty", text="Quantity")
    details_tree.heading("subtotal", text="Subtotal")

    details_tree.column("product", width=280)
    details_tree.column("price", width=100, anchor=E)
    details_tree.column("qty", width=90, anchor=CENTER)
    details_tree.column("subtotal", width=110, anchor=E)

    details_tree["show"] = "headings"
    details_tree.pack(fill=BOTH, expand=True)

    for product, price, qty, subtotal in get_sale_items(sale_id):
        details_tree.insert("", "end", 
                            values=(product,
                                    format_currency(price), 
                                    qty, format_currency(subtotal)))

    totals_frame = LabelFrame(details_win, text="Totals", padx=10, pady=10)
    totals_frame.pack(fill="x", padx=10, pady=(0, 10))

    Label(totals_frame, text=f"Gross Total : {format_currency(gross_total)}").grid(
        row=0, column=0, padx=15, pady=5, sticky="w")
    Label(totals_frame, text=f"Discount : {discount}%  ({format_currency(discount_amount)})").grid(
        row=0, column=1, padx=15, pady=5, sticky="w")
    Label(totals_frame, text=f"Tax : {tax}%  ({format_currency(tax_amount)})").grid(
        row=0, column=2, padx=15, pady=5, sticky="w")
    Label(totals_frame, text=f"Net Total : {format_currency(net_total)}", font=("Arial", 11, "bold")).grid(
        row=0, column=3, padx=15, pady=5, sticky="w")

    Button(
            details_win, text="🖨 Print Invoice", width=20,
            command=lambda: generate_sale_invoice_a4(sale_id)
        ).pack(side=BOTTOM, pady=(0, 15))

# =====================================
# Sale Return Window
# =====================================
def open_return_window():

    return_win = Toplevel()
    return_win.title("Process Sale Return")

    size_and_center(return_win, width_ratio=0.6, height_ratio=0.6)

    current_sale_id = StringVar()
    return_win.iconbitmap("assets/ims.ico")

    # ---------------- Search ----------------
    search_frame = LabelFrame(return_win, text="Find Sale", padx=10, pady=10)
    search_frame.pack(fill="x", padx=10, pady=10)

    Button(
        search_frame, text="Load Items", width=14,
        command=lambda: load_items_for_return()
    ).grid(row=0, column=2, padx=10)
#===================================================================
# ---------------- Return Form ----------------
# =====================================================================
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
        sold_qty = int(values[2])
        already_returned = int(values[3])

        success = process_sale_return(
            current_sale_id.get(), product_id, return_qty.get(),
            reason.get().strip(), sold_qty, already_returned
        )

        if success:
            load_items_for_return()
            return_qty.set(1)
            reason.set("")

    # ---------------- Items Table ----------------
    items_frame = LabelFrame(return_win, text="Sold Items", padx=10, pady=10)
    items_frame.pack(fill="both", expand=True, padx=10, pady=10)

    items_tree = ttk.Treeview(
        items_frame,
        columns=("product_id", "product", "sold_qty", "already_returned", "remaining"),
        show="headings"
    )
    items_tree.heading("product", text="Product")
    items_tree.heading("sold_qty", text="Sold Qty")
    items_tree.heading("already_returned", text="Already Returned")
    items_tree.heading("remaining", text="Remaining")
    items_tree.column("product", width=250)
    items_tree.column("sold_qty", width=90, anchor=CENTER)
    items_tree.column("already_returned", width=130, anchor=CENTER)
    items_tree.column("remaining", width=100, anchor=CENTER)
    items_tree["displaycolumns"] = ("product", "sold_qty", "already_returned", "remaining")
    items_tree.pack(fill=BOTH, expand=True)

    def load_items_for_return():

        for row in items_tree.get_children():
            items_tree.delete(row)

        sale_no = sale_no_search.get().strip()
        if sale_no == "":
            messagebox.showerror("Error", "Please enter a Sale No.")
            return

        # find sale_id from sale_no via history search (reuses existing function)
        matches = get_sales_history(sale_no)
        if not matches:
            messagebox.showerror("Error", "No sale found with that Sale No.")
            return

        sale_id = matches[0][0]
        current_sale_id.set(sale_id)

        for product_id, product_name, sold_qty, already_returned in get_sale_items_for_return(sale_id):
            remaining = sold_qty - already_returned
            items_tree.insert("", "end", values=(
                product_id, product_name, sold_qty, already_returned, remaining
            ))

    # ---------------- Return FReturn ----------------
    
    Button(
        form_frame, text="Process Return", width=16,
        command=handle_process_return
    ).grid(row=0, column=4, padx=10, pady=5)

# =====================================
# Return History Window
# (shows ALL sale returns, with a "Today Only" filter)
# =====================================
def open_sale_return_history_window():

    win = Toplevel()
    win.title("Sales Return History")
    size_and_center(win, width_ratio=0.75, height_ratio=0.65)

    filter_frame = Frame(win)
    filter_frame.pack(fill="x", padx=10, pady=10)

    show_today_only = BooleanVar(value=False)
    win.iconbitmap("assets/ims.ico")

    def refresh_list():
        for row in returns_tree.get_children():
            returns_tree.delete(row)
        rows = get_all_sale_returns(today_only=show_today_only.get())
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

    returns_tree = ttk.Treeview(
        table_frame,
        columns=("date", "sale_no", "product", "quantity", "reason"),
        show="headings",
        yscrollcommand=scroll_y.set,
        xscrollcommand=scroll_x.set
    )

    returns_tree.heading("date", text="Return Date")
    returns_tree.heading("sale_no", text="Sale No")
    returns_tree.heading("product", text="Product")
    returns_tree.heading("quantity", text="Quantity")
    returns_tree.heading("reason", text="Reason")

    returns_tree.column("date", width=160, stretch=False)
    returns_tree.column("sale_no", width=120, stretch=False)
    returns_tree.column("product", width=220, stretch=False)
    returns_tree.column("quantity", width=90, anchor=CENTER, stretch=False)
    returns_tree.column("reason", width=250, stretch=True)

    scroll_y.config(command=returns_tree.yview)
    scroll_x.config(command=returns_tree.xview)

    scroll_y.pack(side=RIGHT, fill=Y)
    scroll_x.pack(side=BOTTOM, fill=X)

    returns_tree.pack(fill=BOTH, expand=True)

    refresh_list()