from tkinter import *
from tkinter import ttk, messagebox

from utils.branding_helpers import add_branding_strip
from utils.barcode_helpers import create_scan_entry
from utils.shortcut_helper import bind_shortcuts
from utils.window_helpers import size_and_center

from services.sales_summary import SalesSummary
from services.sales_service import (
    load_products, get_product_details,
    validate_sale_line, calculate_sale_totals,
    remove_cart_item, clear_sale_form, save_sale
)
from services.customer_service import (
    quick_add_customer, get_customer_id_by_name_and_contact, get_or_create_walkin_customer_id
)
from services.settings_service import format_currency
from services.invoice_service import generate_sale_invoice
from services.tax_service import get_applicable_tax_rate

CART_COLUMNS = ("product_id", "product", "price", "qty", "subtotal")


# =====================================================================
# POS - Quick Sale Window
#
# A fast, counter-facing alternative to the full Sales Management
# screen: captures a walk-in customer's name/contact right here (no
# need to go create them in the Customers module first), keeps the
# form to the essentials, and prints the receipt automatically the
# moment the sale is saved. Reuses the exact same sales_service /
# invoice_service logic as Sales Management, so a sale made from
# either screen behaves identically in reports, stock, and credit.
# =====================================================================
def pos_window():

    win = Toplevel()
    add_branding_strip(win)

    win.title("Inventra ERP - POS (Quick Sale)")
    size_and_center(win, width_ratio=0.93, height_ratio=1, resizable=True)

    win.iconbitmap("assets/ims.ico")

    win.focus_force()

    root_win = win   # the real Toplevel - needed later for bind_shortcuts/destroy,
                      # since `win` gets reassigned below to the scrollable frame

    # ---------------- Layout scaffolding ----------------
    # 1) checkout_bar is packed FIRST with side=BOTTOM, so its space is
    #    reserved before anything else - the Checkout & Print button
    #    living inside it is therefore ALWAYS visible, on any screen
    #    size, even if the rest of the form needs to scroll.
    # 2) Everything else goes inside a scrollable canvas, so on a short
    #    screen the form scrolls instead of getting cut off.
    checkout_bar = Frame(win)
    checkout_bar.pack(side=BOTTOM, fill=X)

    scroll_container = Frame(win)
    scroll_container.pack(side=TOP, fill=BOTH, expand=True)

    canvas = Canvas(scroll_container, highlightthickness=0)
    scrollbar = Scrollbar(scroll_container, orient=VERTICAL, command=canvas.yview)
    scrollable_frame = Frame(canvas)

    scrollable_frame.bind(
        "<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )
    canvas_window = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)

    # Keep the inner frame exactly as wide as the visible canvas, so
    # fields don't end up narrower than the window (or need horizontal
    # scrolling of their own).
    canvas.bind("<Configure>", lambda e: canvas.itemconfig(canvas_window, width=e.width))

    canvas.pack(side=LEFT, fill=BOTH, expand=True)
    scrollbar.pack(side=RIGHT, fill=Y)

    # Mouse wheel support - scoped to only while the pointer is over
    # this canvas (bind_all + Enter/Leave), and explicitly cleaned up
    # when the window closes. A plain canvas.bind_all() here would
    # register the handler application-wide for the rest of the app's
    # life, still firing after this window closes and referencing an
    # already-destroyed canvas - which is exactly what was corrupting
    # other windows (Sales/Purchase/Products) afterward.
    def _on_mousewheel(event):
        canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _bind_mousewheel(event):
        canvas.bind_all("<MouseWheel>", _on_mousewheel)

    def _unbind_mousewheel(event):
        canvas.unbind_all("<MouseWheel>")

    canvas.bind("<Enter>", _bind_mousewheel)
    canvas.bind("<Leave>", _unbind_mousewheel)
    canvas.bind("<Destroy>", _unbind_mousewheel)  # safety net if the window
                                                   # closes while the pointer
                                                   # is still over the canvas

    win = scrollable_frame  # everything below is built the same way as before,
                            # just now landing inside the scrollable area instead
                            # of directly on the Toplevel

    summary = SalesSummary()

    # ---------------- Customer (walk-in) ----------------
    customer_frame = LabelFrame(win, text="Customer", padx=10, pady=8)
    customer_frame.pack(fill="x", padx=10, pady=(10, 5))

    Label(customer_frame, text="Name", font=("Segoe UI", 10)).grid(
        row=0, column=0, padx=5, pady=5, sticky="w")
    customer = StringVar()
    customer_entry = Entry(
        customer_frame, textvariable=customer, width=28, font=("Segoe UI", 11)
    )
    customer_entry.grid(row=0, column=1, padx=5, pady=5)

    Label(customer_frame, text="Contact", font=("Segoe UI", 10)).grid(
        row=0, column=2, padx=5, pady=5, sticky="w")
    contact = StringVar()
    Entry(
        customer_frame, textvariable=contact, width=20, font=("Segoe UI", 11)
    ).grid(row=0, column=3, padx=5, pady=5)

    Label(
        customer_frame, text="(optional - leave blank for a walk-in sale, or type a name; new name = new customer)",
        fg="gray", font=("Segoe UI", 8)
    ).grid(row=1, column=0, columnspan=4, padx=5, sticky="w")

    # ---------------- Add Item ----------------
    entry_frame = LabelFrame(win, text="Add Item", padx=10, pady=8)
    entry_frame.pack(fill="x", padx=10, pady=5)

    products = load_products()
    product_map = {}
    product_names = []
    for product_id, product_name in products:
        product_map[product_name] = product_id
        product_names.append(product_name)

    product = StringVar()
    quantity = IntVar(value=1)
    sale_price = DoubleVar()
    available_stock = IntVar()

    Label(entry_frame, text="Product").grid(row=0, column=0, padx=5, pady=5, sticky="w")
    product_entry = Entry(entry_frame, textvariable=product, width=28, font=("Segoe UI", 11))
    product_entry.grid(row=0, column=1, padx=5, pady=5)

    product_listbox = Listbox(entry_frame, height=6, font=("Segoe UI", 10))

    def hide_product_list():
        product_listbox.grid_remove()

    def select_product(product_name):
        product.set(product_name)
        hide_product_list()
        product_id = product_map.get(product_name)
        if product_id is not None:
            details = get_product_details(product_id)
            if details:
                sale_price.set(details[0])
                available_stock.set(details[1])
        quantity_entry.focus_set()
        quantity_entry.select_range(0, END)

    def show_product_list(matches):
        if not matches:
            hide_product_list()
            return
        product_listbox.delete(0, END)
        for name in matches[:10]:   # cap so the popup never gets unwieldy
            product_listbox.insert(END, name)
        product_listbox.grid(row=1, column=1, sticky="w", padx=5, pady=(0, 5))
        product_listbox.lift()

    def filter_products(event):
        # Ignore navigation/selection keys - only re-filter on actual typing
        if event.keysym in ("Up", "Down", "Return", "Escape"):
            return
        typed = product.get().strip().lower()
        if not typed:
            hide_product_list()
            return
        matches = [n for n in product_names if typed in n.lower()]
        show_product_list(matches)

    def on_listbox_click(event):
        selection = product_listbox.curselection()
        if selection:
            select_product(product_listbox.get(selection[0]))

    product_entry.bind("<KeyRelease>", filter_products)
    product_entry.bind("<Escape>", lambda e: hide_product_list())
    # Small delay on FocusOut so a click on the listbox (which also
    # blurs the entry) has time to register before the list closes.
    product_entry.bind("<FocusOut>", lambda e: entry_frame.after(150, hide_product_list))
    product_listbox.bind("<<ListboxSelect>>", on_listbox_click)

    Label(entry_frame, text="Qty").grid(row=0, column=2, padx=5, pady=5, sticky="w")
    quantity_entry = Entry(entry_frame, textvariable=quantity, width=6, font=("Segoe UI", 11))
    quantity_entry.grid(row=0, column=3, padx=5, pady=5)

    Label(entry_frame, text="Price").grid(row=0, column=4, padx=5, pady=5, sticky="w")
    Entry(
        entry_frame, textvariable=sale_price, width=12,
        state="readonly", font=("Segoe UI", 11)
    ).grid(row=0, column=5, padx=5, pady=5)

    Label(entry_frame, text="Available Stock").grid(row=0, column=6, padx=(20, 5), pady=5, sticky="w")
    Entry(
        entry_frame, textvariable=available_stock, width=8,
        state="readonly", font=("Segoe UI", 11)
    ).grid(row=0, column=7, padx=5, pady=5)

    def add_to_cart():

        if not validate_sale_line(customer, product, quantity, available_stock, require_customer=False):
            return

        product_name = product.get()
        product_id = product_map.get(product_name)

        for item in cart_tree.get_children():
            values = cart_tree.item(item, "values")
            if int(values[0]) == product_id:
                messagebox.showerror(
                    "Duplicate Product", "This product is already added to the cart."
                )
                return

        subtotal = quantity.get() * sale_price.get()

        cart_tree.insert("", "end", values=(
            product_id, product_name, sale_price.get(), quantity.get(), subtotal
        ))

        refresh_totals()

        product.set("")
        quantity.set(1)
        sale_price.set(0)
        available_stock.set(0)
        product_entry.focus_set()

    def on_barcode_scanned(product_row):
        product_id, product_name, cost_price, sale_price_value, stock, status, barcode_value = product_row

        if product_name not in product_map:
            product_map[product_name] = product_id

        product.set(product_name)
        sale_price.set(sale_price_value)
        available_stock.set(stock)
        quantity.set(1)

        add_to_cart()  # add immediately - that's the point of a barcode scan

    Label(entry_frame, text="Scan Barcode").grid(row=0, column=8, padx=(20, 5), pady=5, sticky="w")
    scan_entry = create_scan_entry(entry_frame, on_barcode_scanned, width=16)
    scan_entry.grid(row=0, column=9, padx=5, pady=5)

    Button(
        entry_frame, text="➕ Add to Cart", font=("Segoe UI", 10, "bold"), command=add_to_cart
    ).grid(row=0, column=10, padx=(20, 5), pady=5)

    # ---------------- Cart ----------------
    cart_frame = Frame(win)
    cart_frame.pack(fill=BOTH, expand=True, padx=10, pady=5)

    scrollbar_y = Scrollbar(cart_frame)
    scrollbar_y.pack(side=RIGHT, fill=Y)

    cart_tree = ttk.Treeview(
        cart_frame, columns=CART_COLUMNS, show="headings",
        height=5, yscrollcommand=scrollbar_y.set
    )
    scrollbar_y.config(command=cart_tree.yview)

    cart_tree.heading("product_id", text="ID")
    cart_tree.heading("product", text="Product")
    cart_tree.heading("price", text="Price")
    cart_tree.heading("qty", text="Qty")
    cart_tree.heading("subtotal", text="Subtotal")

    cart_tree.column("product_id", width=0, stretch=False)
    cart_tree.column("product", width=260, stretch=True)
    cart_tree.column("price", width=100, anchor=E, stretch=False)
    cart_tree.column("qty", width=70, anchor=CENTER, stretch=False)
    cart_tree.column("subtotal", width=120, anchor=E, stretch=False)
    cart_tree["displaycolumns"] = ("product", "price", "qty", "subtotal")

    cart_tree.pack(fill=BOTH, expand=True)
    cart_tree.bind("<Delete>", lambda event: handle_remove())

    def handle_remove():
        remove_cart_item(cart_tree, summary)
        refresh_totals()

    Button(win, text="🗑 Remove Selected Item", command=handle_remove).pack(
        anchor="e", padx=10)

    # ---------------- Totals & Payment ----------------
    totals_frame = LabelFrame(win, text="Payment", padx=10, pady=8)
    totals_frame.pack(fill="x", padx=10, pady=5)

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
        if payment_type.get() == "Cash":
            amount_paid.set(str(summary.net_total.get()))

    ENTRY_WIDTH = 12   # one consistent width for every field in this section

    Label(totals_frame, text="Discount %").grid(row=0, column=0, padx=8, pady=6, sticky="w")
    discount_entry = Entry(totals_frame, textvariable=summary.discount, width=ENTRY_WIDTH, justify="right")
    discount_entry.grid(row=0, column=1, padx=8, pady=6, sticky="w")
    discount_entry.bind("<KeyRelease>", lambda event: refresh_totals())

    Label(totals_frame, text="Tax %").grid(row=0, column=2, padx=8, pady=6, sticky="w")
    tax_entry = Entry(totals_frame, textvariable=summary.tax, width=ENTRY_WIDTH, justify="right")
    tax_entry.grid(row=0, column=3, padx=8, pady=6, sticky="w")
    tax_entry.bind("<KeyRelease>", lambda event: refresh_totals())
    summary.tax.set(str(get_applicable_tax_rate(False)))  # default: non-filer walk-in rate

    Label(totals_frame, text="Gross").grid(row=1, column=0, padx=8, pady=6, sticky="w")
    Entry(totals_frame, textvariable=gross_display, width=ENTRY_WIDTH, state="readonly",
          justify="right").grid(row=1, column=1, padx=8, pady=6, sticky="w")

    Label(totals_frame, text="Disc. Amt").grid(row=1, column=2, padx=8, pady=6, sticky="w")
    Entry(totals_frame, textvariable=discount_amt_display, width=ENTRY_WIDTH, state="readonly",
          justify="right").grid(row=1, column=3, padx=8, pady=6, sticky="w")

    Label(totals_frame, text="Tax Amt").grid(row=1, column=4, padx=8, pady=6, sticky="w")
    Entry(totals_frame, textvariable=tax_amt_display, width=ENTRY_WIDTH, state="readonly",
          justify="right").grid(row=1, column=5, padx=8, pady=6, sticky="w")

    # ---- NET TOTAL gets its own row, full width - it's the one number
    # that matters most here, so it isn't squeezed next to anything else ----
    Label(totals_frame, text="NET TOTAL", font=("Segoe UI", 12, "bold")).grid(
        row=3, column=0, padx=8, pady=(14, 6), sticky="w")
    Label(totals_frame, textvariable=net_display, font=("Segoe UI", 18, "bold"),
          fg="#1E293B").grid(row=3, column=1, columnspan=5, padx=8, pady=(14, 6), sticky="w")

    # ---- Payment Type + Amount Paid: its own row, its own columns -
    # previously these shared columns with the Discount/Tax fields above,
    # which is what made the boxes look mismatched in size ----
    payment_type = StringVar(value="Cash")
    amount_paid = StringVar(value="0")

    payment_row = Frame(totals_frame)
    payment_row.grid(row=2, column=0, columnspan=6, sticky="w", padx=8, pady=(4, 8))

    Label(payment_row, text="Payment Type").pack(side=LEFT, padx=(0, 10))
    Radiobutton(
        payment_row, text="Cash", variable=payment_type, value="Cash",
        command=lambda: on_payment_type_change()
    ).pack(side=LEFT, padx=5)
    Radiobutton(
        payment_row, text="Credit", variable=payment_type, value="Credit",
        command=lambda: on_payment_type_change()
    ).pack(side=LEFT, padx=5)

    Label(payment_row, text="Amount Paid").pack(side=LEFT, padx=(25, 10))
    amount_paid_entry = Entry(payment_row, textvariable=amount_paid, width=ENTRY_WIDTH, justify="right")
    amount_paid_entry.pack(side=LEFT)

    def on_payment_type_change():
        if payment_type.get() == "Credit":
            amount_paid_entry.config(state="normal")
            amount_paid.set("0")
        else:
            amount_paid.set(str(summary.net_total.get()))
            amount_paid_entry.config(state="disabled")
    amount_paid_entry.config(state="disabled")  # Cash selected by default

    # ---------------- Checkout ----------------
    def ensure_customer_exists():
        name = customer.get().strip()
        if not name:
            return get_or_create_walkin_customer_id()

        contact_value = contact.get().strip()

        # Match on Name AND Contact together - name alone isn't reliable,
        # two different real customers can share the same name.
        existing_id = get_customer_id_by_name_and_contact(name, contact_value)
        if existing_id is not None:
            return existing_id

        return quick_add_customer(name, contact_value)

    def handle_checkout():

        if not cart_tree.get_children():
            messagebox.showerror("Error", "Cart is empty - add at least one item.")
            return

        resolved_customer_id = ensure_customer_exists()

        sale_id = save_sale(
            customer, cart_tree, summary, payment_type, amount_paid,
            customer_id=resolved_customer_id
        )
        if not sale_id:
            return  # save_sale already showed the relevant error

        try:
            generate_sale_invoice(sale_id)
        except Exception as e:
            messagebox.showwarning(
                "Saved, but printing failed",
                f"The sale was saved successfully, but the receipt could not be "
                f"printed automatically:\n{e}"
            )

        clear_sale_form(customer, product, quantity, sale_price, available_stock, cart_tree, summary)
        contact.set("")
        refresh_totals()
        payment_type.set("Cash")
        on_payment_type_change()

        customer_entry.focus_set()

    Button(
        checkout_bar, text="💾 Checkout & Print Receipt", bg="#184A9B", fg="white",
        font=("Segoe UI", 12, "bold"), cursor="hand2", command=handle_checkout
    ).pack(fill=X, padx=10, pady=(8, 12), ipady=6)

    bind_shortcuts(root_win, {
        "<Escape>": root_win.destroy,
    })

    refresh_totals()
    customer_entry.focus_set()