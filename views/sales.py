
from tkinter import *
from tkinter import ttk

from tkinter import messagebox
from services.sales_summary import SalesSummary
from services.sales_service import (
    load_customers, load_products, get_product_details,
    validate_sale_line, calculate_sale_totals,
    remove_cart_item, clear_cart, clear_sale_form,
    save_sale, get_sales_history, get_sale_header, get_sale_items,
    get_sale_items_for_return, get_returns_for_sale, process_sale_return,
    get_all_sale_returns
)
from utils.window_helpers import size_and_center
# =====================================
# Sales Window
# =====================================
def sales_window():

    win = Toplevel()

    win.title("Sales Management")

    size_and_center(win, width_ratio=0.9, height_ratio=0.88)

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

    toolbar.pack(
        side=TOP,
        fill=X
    )
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

    def refresh_totals():
        calculate_sale_totals(cart_tree, summary)

    # -------------------------------------
    # Gross Total
    # -------------------------------------
    Label(totals_frame, text="Gross Total").grid(row=0, column=0, padx=5, pady=5)
    Entry(
        totals_frame, textvariable=summary.gross_total,
        width=12, state="readonly", justify="right"
    ).grid(row=0, column=1, padx=5, pady=5)

    # -------------------------------------
    # Discount %
    # -------------------------------------
    Label(totals_frame, text="Discount %").grid(row=0, column=2, padx=5, pady=5)
    discount_entry = Entry(totals_frame, textvariable=summary.discount, width=12, justify="right")
    discount_entry.grid(row=0, column=3, padx=5, pady=5)
    discount_entry.bind("<KeyRelease>", lambda event: refresh_totals())

    # -------------------------------------
    # Discount Amount (NEW - this is the field that was missing
    # before, so the actual discount amount never got saved)
    # -------------------------------------
    Label(totals_frame, text="Discount Amt").grid(row=0, column=4, padx=5, pady=5)
    Entry(
        totals_frame, textvariable=summary.discount_amount,
        width=12, state="readonly", justify="right"
    ).grid(row=0, column=5, padx=5, pady=5)

    # ---------------------------------
    # Tax %
    # ---------------------------------
    Label(totals_frame, text="Tax %").grid(row=1, column=0, padx=5, pady=5)
    tax_entry = Entry(totals_frame, textvariable=summary.tax, width=12, justify="right")
    tax_entry.grid(row=1, column=1, padx=5, pady=5)
    tax_entry.bind("<KeyRelease>", lambda event: refresh_totals())

    # ---------------------------------
    # Tax Amount (NEW - same reason as Discount Amount)
    # ---------------------------------
    Label(totals_frame, text="Tax Amt").grid(row=1, column=2, padx=5, pady=5)
    Entry(
        totals_frame, textvariable=summary.tax_amount,
        width=12, state="readonly", justify="right"
    ).grid(row=1, column=3, padx=5, pady=5)

    # ---------------------------------
    # Net Total
    # ---------------------------------
    Label(
        totals_frame, text="Net Total", font=("Arial", 10, "bold")
    ).grid(row=1, column=4, padx=5, pady=5)
    Entry(
        totals_frame, textvariable=summary.net_total,
        width=12, state="readonly", justify="right", font=("Arial", 10, "bold")
    ).grid(row=1, column=5, padx=5, pady=5)

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

    Entry(
        sales_frame,
        textvariable=quantity,
        width=15
    ).grid(
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

        product.set("")
        quantity.set(1)
        sale_price.set(0)
        available_stock.set(0)

# ===========================
#   Save Handler
# ===========================
    def handle_save():
        if save_sale(customer, cart_tree, summary):
            clear_sale_form(customer, product, quantity, 
                            sale_price, available_stock, cart_tree, summary)
# ===========================
#   Buttons
# ==========================
    Button(
        toolbar, text="New Sale", width=15,
        command=lambda: clear_sale_form(
            customer, product, quantity, sale_price, available_stock, cart_tree, summary
        )
    ).pack(side=LEFT, padx=5, pady=5)

    Button(
        toolbar, text="Add To Cart", width=15,
        command=add_to_cart
    ).pack(side=LEFT, padx=5, pady=5)

    Button(
        toolbar, text="Remove Item", width=15,
        command=lambda: remove_cart_item(cart_tree, summary)
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
    size_and_center(history_win, width_ratio=0.9, height_ratio=0.75)
    search_frame = LabelFrame(history_win, text="Search Sale", padx=10, pady=10)
    search_frame.pack(fill="x", padx=10, pady=10)

    Label(search_frame, text="Sale No").grid(row=0, column=0, padx=5)
    sale_search = StringVar()
    Entry(search_frame, textvariable=sale_search, width=30).grid(row=0, column=1, padx=5)

    history_tree = None

    def load_history(search_term=None):
        for row in history_tree.get_children():
            history_tree.delete(row)
        rows = get_sales_history(search_term)
        for row in rows:
            history_tree.insert("", END, values=row)

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

    history_tree = ttk.Treeview(
        table_frame,
        columns=(
            "id", "sale_no", "customer", "date",
            "gross_total", "discount", "discount_amount",
            "tax", "tax_amount", "net_total", "returned_qty"
        ),
        yscrollcommand=scroll_y.set
    )
    scroll_y.config(command=history_tree.yview)

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
    history_tree.heading("returned_qty", text="Returned")


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
    history_tree.column("returned_qty", width=90, anchor=CENTER)


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
        tax, tax_amount, net_total
    ) = get_sale_header(sale_id)

    details_win = Toplevel()
    details_win.title("Sale Details")
    details_win.geometry("750x500")
    details_win.resizable(False, False)

    header_frame = LabelFrame(details_win, text="Sale Information", padx=10, pady=10)
    header_frame.pack(fill="x", padx=10, pady=10)

    Label(header_frame, text=f"Sale No : {sale_no}", font=("Arial", 11, "bold")).grid(
        row=0, column=0, padx=10, pady=5, sticky="w")
    Label(header_frame, text=f"Customer : {customer_name}").grid(
        row=1, column=0, padx=10, pady=5, sticky="w")
    Label(header_frame, text=f"Sale Date : {sale_date}").grid(
        row=2, column=0, padx=10, pady=5, sticky="w")

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
        details_tree.insert("", "end", values=(product, f"{price:,.2f}", qty, f"{subtotal:,.2f}"))

    totals_frame = LabelFrame(details_win, text="Totals", padx=10, pady=10)
    totals_frame.pack(fill="x", padx=10, pady=(0, 10))

    Label(totals_frame, text=f"Gross Total : {gross_total:,.2f}").grid(
        row=0, column=0, padx=15, pady=5, sticky="w")
    Label(totals_frame, text=f"Discount : {discount}%  ({discount_amount:,.2f})").grid(
        row=0, column=1, padx=15, pady=5, sticky="w")
    Label(totals_frame, text=f"Tax : {tax}%  ({tax_amount:,.2f})").grid(
        row=0, column=2, padx=15, pady=5, sticky="w")
    Label(totals_frame, text=f"Net Total : {net_total:,.2f}", font=("Arial", 11, "bold")).grid(
        row=0, column=3, padx=15, pady=5, sticky="w")

# =====================================
# Sale Return Window
# =====================================
def open_return_window():

    return_win = Toplevel()
    return_win.title("Process Sale Return")
    size_and_center(return_win, width_ratio=0.6, height_ratio=0.6)

    current_sale_id = StringVar()

    # ---------------- Search ----------------
    search_frame = LabelFrame(return_win, text="Find Sale", padx=10, pady=10)
    search_frame.pack(fill="x", padx=10, pady=10)

    Label(search_frame, text="Sale No").grid(row=0, column=0, padx=5)
    sale_no_search = StringVar()
    Entry(search_frame, textvariable=sale_no_search, width=25).grid(row=0, column=1, padx=5)

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
