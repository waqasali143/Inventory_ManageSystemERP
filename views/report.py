from tkinter import *
from tkinter import ttk

from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from utils.export_helpers import export_multi_sheet_excel
from services.report_service import (
    get_weekly_range, get_monthly_range, get_custom_range, get_report_data, get_product_wise_report
)
from services.credit_service import get_credit_report_data
from services.settings_service import format_currency
from utils.theme import (
    PRIMARY, PRIMARY_DARK, BACKGROUND, WHITE, TEXT,
    GREEN, RED, BLUE, ORANGE,
    FONT_TITLE, FONT_BODY, FONT_BODY_BOLD,
    apply_app_style
)
from utils.branding_helpers import add_branding_strip

from services.invoice_service import generate_business_report_pdf, generate_credit_report_pdf
from utils.tree_helpers import build_treeview, reload_treeview
from utils.window_helpers import size_and_center
from utils.ui_helpers import add_buttons, labeled_entry, labeled_date_picker
# ==========================================================================
def open_report_window():

    win = Toplevel()
    add_branding_strip(win)

    win.withdraw()
    win.title("Business Reports")

    size_and_center(win, width_ratio=0.92, height_ratio=1, resizable=True)

    win.iconbitmap("assets/ims.ico")
    win.configure(bg=BACKGROUND)


    apply_app_style()

    # ---------------- Header ----------------
    header_frame = Frame(win, bg=PRIMARY, height=60)
    header_frame.pack(fill=X)
    header_frame.pack_propagate(False)

    Label(
        header_frame, text="BUSINESS REPORTS",
        bg=PRIMARY, fg=WHITE, font=FONT_TITLE
    ).pack(side=LEFT, padx=20)

    # ---------------- Filter Bar (always visible, above the tabs) ----------------
    filter_frame = LabelFrame(
        win, text="Report Period", bg=BACKGROUND,
        font=FONT_BODY_BOLD, padx=10, pady=10
    )
    filter_frame.pack(fill="x", padx=20, pady=15)
# ============================================================================
# =========  Date Picker  ===================================
    start_date_picker = labeled_date_picker(filter_frame, "Start Date", 0, 2)
    end_date_picker = labeled_date_picker(filter_frame, "End Date", 0, 4)
# ============================================================================

    Button(
        filter_frame, text="Weekly", width=12,
        command=lambda: load_report(*get_weekly_range())
    ).grid(row=0, column=0, padx=5)

    Button(
        filter_frame, text="Monthly", width=12,
        command=lambda: load_report(*get_monthly_range())
    ).grid(row=0, column=1, padx=5)

    Button(
        filter_frame, text="Apply Custom Range", width=18,
        command=lambda: apply_custom_range()
    ).grid(row=0, column=6, padx=10)

    def handle_print_business_report():
        try:
            generate_business_report_pdf(
                latest_data["value"], current_range["from"], current_range["to"],
                latest_data.get("product_details"), latest_data.get("unsold_products"),
                latest_credit_data["value"]
            )
        except Exception as e:
            from tkinter import messagebox
            messagebox.showerror("Print Report Failed", f"{type(e).__name__}: {e}")

    Button(
        filter_frame, text="🖨 Print Report", width=14,
        command=handle_print_business_report
    ).grid(row=0, column=7, padx=10)
# ----------------------------------------------------------------
    Button(
        filter_frame, text="🗂 Export to Excel", width=16,
        command=lambda: export_current_report()
    ).grid(row=0, column=8, padx=10)
    # =============================
    # === Helper Function Export ====

    def export_current_report():
        product_details = latest_data.get("product_details")

        if not product_details:
            from tkinter import messagebox
            messagebox.showerror("Error", "Please load a report first.")
            return

        sold_headers = ["Product", "Qty Sold", "Revenue", "Discount", "Cost", 
                        "Profit", "Current Stock", "Sold on Credit"]
        unsold_headers = ["Product", "Current Stock"]
        credit_headers = ["Type", "Name", "Contact", "Balance", "Amount Paid",
                          "Open Invoices", "Last Payment Amount", "Last Payment Date"]
        summary_headers = ["Metric", "Amount"]

        credit_data = latest_credit_data.get("value") or {"customers": [], "suppliers": []}

        credit_rows = [
            (
                "Customer", name, contact, balance, amount_paid, open_invoices,
                last_payment_amount if last_payment_amount is not None else "",
                last_payment_date or ""
            )
            for _id, name, contact, balance, amount_paid, open_invoices,
                last_payment_amount, last_payment_date in credit_data["customers"]
        ] + [
            (
                "Supplier", name, contact, balance, amount_paid, open_invoices,
                last_payment_amount if last_payment_amount is not None else "",
                last_payment_date or ""
            )
            for _id, name, contact, balance, amount_paid, open_invoices,
                last_payment_amount, last_payment_date in credit_data["suppliers"]
        ]

        report_data = latest_data["value"]
        summary_rows = [
            ("Total Sales", report_data["total_sales"]),
            ("Total Purchases", report_data["total_purchases"]),
            ("Cost of Sold Items", report_data["cost_of_sold_items"]),
            ("Tax Collected (Sales)", report_data["sales_tax"]),
            ("Tax Paid (Purchases)", report_data["purchase_tax"]),
            ("Total Expenses", report_data["total_expenses"]),
            ("Gross Profit", report_data["gross_profit"]),
            ("Total Profit", report_data["total_profit"]),
            ("Total Receivable", credit_data.get("total_receivable", 0)),
            ("Total Payable", credit_data.get("total_payable", 0)),
        ]

        export_multi_sheet_excel([
            ("Summary", summary_headers, summary_rows),
            ("Sold Products", sold_headers, product_details),
            ("Not Sold", unsold_headers, latest_data.get("unsold_products", [])),
            ("Credit", credit_headers, credit_rows),
        ], f"Business_Report_{current_range['from']}_to_{current_range['to']}")
        
    # ---------------- Tabs (Notebook) - NO scrolling needed, so no flicker ----------------
    latest_data = {"value": None}
    current_range = {"from": "", "to": ""}

    notebook = ttk.Notebook(win)
    notebook.pack(fill=BOTH, expand=True, padx=20, pady=(0, 20))

    overview_tab = Frame(notebook, bg=BACKGROUND)
    charts_tab = Frame(notebook, bg=BACKGROUND)

    details_tab = Frame(notebook, bg=BACKGROUND)
    unsold_tab = Frame(notebook, bg=BACKGROUND)
    credit_tab = Frame(notebook, bg=BACKGROUND)


    notebook.add(overview_tab, text="  📋 Overview  ")
    notebook.add(charts_tab, text="  📈 Charts  ")
    notebook.add(details_tab, text="  📦 Product Details  ")
    notebook.add(unsold_tab, text="  🚫 Not Sold  ")
    notebook.add(credit_tab, text="  💳 Credit  ")

    # ================================================================
    # TAB 1: OVERVIEW - Summary Cards + Best/Worst Product Tables
    # ================================================================
    summary_frame = Frame(overview_tab, bg=BACKGROUND)
    summary_frame.pack(fill="x", padx=10, pady=15)

    def summary_card(parent, title, color):
        card = Frame(parent, bg=color, width=190, height=90)
        card.pack(side=LEFT, padx=8)
        card.pack_propagate(False)

        Label(card, text=title, bg=color, fg=WHITE, font=FONT_BODY_BOLD).pack(pady=(14, 4))
        value_label = Label(card, text="0", bg=color, fg=WHITE, font=("Segoe UI", 16, "bold"))
        value_label.pack()

        return value_label

    sales_value = summary_card(summary_frame, "Total Sales (Incl. Tax)", BLUE)
    purchase_value = summary_card(summary_frame, "Total Purchases (Incl. Tax)", ORANGE)
    expense_value = summary_card(summary_frame, "Total Expenses", "#8B5CF6")
    profit_value = summary_card(summary_frame, "Total Profit (Excl. Tax)", GREEN)
    overview_receivable_value = summary_card(summary_frame, "Total Receivable", "#059669")
    overview_payable_value = summary_card(summary_frame, "Total Payable", "#DC2626")

    # Second row: Cost of Sold Items sits right under Total Purchases
    # on purpose - so it's easy to see this is the cost of only the
    # items actually sold, not everything bought from suppliers.
    summary_frame_2 = Frame(overview_tab, bg=BACKGROUND)
    summary_frame_2.pack(fill="x", padx=10, pady=(0, 15))

    cogs_value = summary_card(summary_frame_2, "Cost of Sold Items (Excl. Tax)", "#0D9488")
    sales_tax_value = summary_card(summary_frame_2, "Tax Collected (Sales)", "#2563EB")
    purchase_tax_value = summary_card(summary_frame_2, "Tax Paid (Purchases)", "#D97706")

    tables_frame = Frame(overview_tab, bg=BACKGROUND)
    tables_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

    PRODUCT_COLUMNS = [
        {"key": "name", "heading": "Product", "width": 180, "stretch": True},
        {"key": "qty", "heading": "Qty Sold", "width": 90, "anchor": CENTER, "stretch": False},
        {"key": "revenue", "heading": "Revenue", "width": 110, "anchor": E, "stretch": False},
    ]

    best_frame = LabelFrame(
        tables_frame, text="Top 10 Best-Selling Products", bg=BACKGROUND,
        font=FONT_BODY_BOLD, padx=10, pady=10
    )
    best_frame.pack(side=LEFT, fill="both", expand=True, padx=(0, 10))
    best_tree = build_treeview(best_frame, PRODUCT_COLUMNS, height=10)
    best_tree.pack(fill="both", expand=True)

    worst_frame = LabelFrame(
        tables_frame, text="Top 10 Worst-Selling Products", bg=BACKGROUND,
        font=FONT_BODY_BOLD, padx=10, pady=10
    )
    worst_frame.pack(side=LEFT, fill="both", expand=True)
    worst_tree = build_treeview(worst_frame, PRODUCT_COLUMNS, height=10)
    worst_tree.pack(fill="both", expand=True)

    # ================================================================
    # TAB 2: CHARTS - Line Chart + Pie Chart
    # ================================================================
    charts_frame = Frame(charts_tab, bg=BACKGROUND)
    charts_frame.pack(fill="both", expand=True, padx=10, pady=15)

    trend_frame = LabelFrame(
        charts_frame, text="Sales vs Purchase Trend", bg=BACKGROUND,
        font=FONT_BODY_BOLD, padx=10, pady=10
    )
    trend_frame.pack(side=LEFT, fill="both", expand=True, padx=(0, 10))

    trend_figure = Figure(figsize=(5.5, 4.2), dpi=90)
    trend_ax = trend_figure.add_subplot(111)
    trend_canvas = FigureCanvasTkAgg(trend_figure, master=trend_frame)
    trend_canvas.get_tk_widget().pack(fill="both", expand=True)

    expense_frame_chart = LabelFrame(
        charts_frame, text="Expense Breakdown", bg=BACKGROUND,
        font=FONT_BODY_BOLD, padx=10, pady=10
    )
    expense_frame_chart.pack(side=LEFT, fill="both", expand=True)

    expense_figure = Figure(figsize=(4.5, 4.2), dpi=90)
    expense_ax = expense_figure.add_subplot(111)
    expense_canvas = FigureCanvasTkAgg(expense_figure, master=expense_frame_chart)
    expense_canvas.get_tk_widget().pack(fill="both", expand=True)

    def draw_charts(data):

        # ---- Line Chart ----
        trend_ax.clear()

        sales_dates = [row[0] for row in data["sales_trend"]]
        sales_amounts = [row[1] for row in data["sales_trend"]]

        purchase_dates = [row[0] for row in data["purchase_trend"]]
        purchase_amounts = [row[1] for row in data["purchase_trend"]]

        if sales_dates:
            trend_ax.plot(sales_dates, sales_amounts, marker="o", color="#3B82F6", label="Sales")
        if purchase_dates:
            trend_ax.plot(purchase_dates, purchase_amounts, marker="o", color="#F59E0B", label="Purchase")

        trend_ax.legend(fontsize=8)
        trend_ax.tick_params(axis="x", rotation=45, labelsize=7)
        trend_ax.tick_params(axis="y", labelsize=7)
        trend_figure.tight_layout()
        trend_canvas.draw()
# =======================================================================
        # ---- Pie Chart ----
        expense_ax.clear()

        categories = [row[0] for row in data["expense_breakdown"]]
        amounts = [row[1] for row in data["expense_breakdown"]]

        if categories:
            expense_ax.pie(amounts, labels=categories, autopct="%1.0f%%", textprops={"fontsize": 7})
        else:
            expense_ax.text(0.5, 0.5, "No expenses in this period", ha="center", va="center", fontsize=8)

        expense_figure.tight_layout()
        expense_canvas.draw()
# ================================================================
    # TAB 3: PRODUCT DETAILS - full profit breakdown per product
# ================================================================
    details_frame = Frame(details_tab, bg=BACKGROUND)
    details_frame.pack(fill="both", expand=True, padx=10, pady=15)

    Label(
        details_frame,
        text="Revenue, Discount, Cost and Profit here are combined across Cash and "
             "Credit sales for the period (a sale counts once it's made, not once "
             "it's paid for), and are shown excluding tax - sales tax collected is "
             "owed to the tax authority, not business income (see \"Tax Collected\" "
             "on the Overview tab). \"Sold on Credit\" is a historical total for the "
             "selected date range and does not decrease when a customer pays later "
             "through the Credit Ledger, since ledger payments aren't tied to "
             "specific products. See the Credit tab or Credit Ledger for live "
             "outstanding balances.",
        bg=BACKGROUND, fg="gray30", font=("Segoe UI", 8), wraplength=900, justify=LEFT
    ).pack(anchor="w", pady=(0, 8))

    DETAIL_COLUMNS = [
        {"key": "name", "heading": "Product", "width": 150, "stretch": True},
        {"key": "qty", "heading": "Qty Sold", "width": 75, "anchor": CENTER, "stretch": False},
        {"key": "revenue", "heading": "Revenue (Excl. Tax)", "width": 130, "anchor": E, "stretch": False},
        {"key": "discount", "heading": "Discount", "width": 90, "anchor": E, "stretch": False},
        {"key": "cost", "heading": "Cost", "width": 100, "anchor": E, "stretch": False},
        {"key": "profit", "heading": "Profit (Excl. Tax)", "width": 120, "anchor": E, "stretch": False},
        {"key": "stock", "heading": "Current Stock (On Hand)", "width": 130, "anchor": CENTER, "stretch": False},
        {"key": "credit", "heading": "Sold on Credit", "width": 110, "anchor": E, "stretch": False},
    ]

    details_scroll = Scrollbar(details_frame, orient=VERTICAL, command=lambda *args: details_tree.yview(*args))
    details_tree = build_treeview(details_frame, DETAIL_COLUMNS, height=8)
    details_tree.configure(yscrollcommand=details_scroll.set)
    details_scroll.pack(side=RIGHT, fill=Y)
    details_tree.pack(side=TOP, fill="both", expand=True)    

    # ========================================================================
    # ===== Not Sold Product ==========
    
    unsold_frame = Frame(unsold_tab, bg=BACKGROUND)
    unsold_frame.pack(fill="both", expand=True, padx=10, pady=15)

    Label(
        unsold_frame, text="Products Not Sold in This Period",
        bg=BACKGROUND, font=FONT_BODY_BOLD
    ).pack(side=TOP, anchor="w", pady=(0, 10))

    UNSOLD_COLUMNS = [
        {"key": "name", "heading": "Product", "width": 250, "stretch": True},
        {"key": "stock", "heading": "Current Stock (On Hand)", "width": 150, "anchor": CENTER, "stretch": False},
    ]

    unsold_scroll = Scrollbar(unsold_frame, orient=VERTICAL, command=lambda *args: unsold_tree.yview(*args))
    unsold_tree = build_treeview(unsold_frame, UNSOLD_COLUMNS)
    unsold_tree.configure(yscrollcommand=unsold_scroll.set)
    unsold_scroll.pack(side=RIGHT, fill=Y)
    unsold_tree.pack(side=TOP, fill="both", expand=True)

    # ================================================================
    # TAB 5: CREDIT - Receivables (customers) & Payables (suppliers)
    # A point-in-time snapshot, not tied to the Weekly/Monthly/Custom
    # date filter above - it always reflects the current outstanding
    # balances, same as the Credit Ledger screen.
    # ================================================================
    credit_summary_frame = Frame(credit_tab, bg=BACKGROUND)
    credit_summary_frame.pack(fill="x", padx=10, pady=15)

    receivable_value = summary_card(credit_summary_frame, "Total Receivable", GREEN)
    payable_value = summary_card(credit_summary_frame, "Total Payable", RED)

    Button(
        credit_summary_frame, text="🔄 Refresh", width=12,
        command=lambda: load_credit_report()
    ).pack(side=LEFT, padx=20)

    def handle_print_credit_report():
        if not latest_credit_data["value"]:
            return
        try:
            generate_credit_report_pdf(latest_credit_data["value"])
        except Exception as e:
            from tkinter import messagebox
            messagebox.showerror("Print Credit Report Failed", f"{type(e).__name__}: {e}")

    Button(
        credit_summary_frame, text="🖨 Print Credit Report", width=20,
        command=handle_print_credit_report
    ).pack(side=LEFT, padx=5)

    credit_tables_frame = Frame(credit_tab, bg=BACKGROUND)
    credit_tables_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

    CREDIT_COLUMNS = [
        {"key": "name", "heading": "Name", "width": 140, "stretch": True},
        {"key": "contact", "heading": "Contact", "width": 110, "stretch": False},
        {"key": "balance", "heading": "Balance", "width": 110, "anchor": E, "stretch": False},
        {"key": "amount_paid", "heading": "Amount Paid", "width": 110, "anchor": E, "stretch": False},
        {"key": "open_invoices", "heading": "Open Inv.", "width": 80, "anchor": CENTER, "stretch": False},
        {"key": "last_payment_amount", "heading": "Last Pay. Amt", "width": 110, "anchor": E, "stretch": False},
        {"key": "last_payment_date", "heading": "Last Pay. Date", "width": 110, "anchor": CENTER, "stretch": False},
    ]

    def _lock_column_widths(tree, columns):
        """Sets minwidth = width for every column so Tkinter can never
        auto-shrink a column smaller than what its heading/content needs
        - without this, ttk.Treeview silently compresses columns to fit
        the available frame width, which is what was clipping headings."""
        for col in columns:
            tree.column(col["key"], minwidth=col["width"], width=col["width"], stretch=col.get("stretch", False))

    receivable_frame = LabelFrame(
        credit_tables_frame, text="Customers - Amount Owed To Us", bg=BACKGROUND,
        font=FONT_BODY_BOLD, padx=10, pady=10
    )
    receivable_frame.pack(side=LEFT, fill="both", expand=True, padx=(0, 10))
    receivable_tree = build_treeview(receivable_frame, CREDIT_COLUMNS, height=10)
    _lock_column_widths(receivable_tree, CREDIT_COLUMNS)
    receivable_scroll_x = Scrollbar(receivable_frame, orient=HORIZONTAL, command=receivable_tree.xview)
    receivable_tree.configure(xscrollcommand=receivable_scroll_x.set)
    receivable_scroll_x.pack(side=BOTTOM, fill=X)
    receivable_tree.pack(fill="both", expand=True)

    payable_frame = LabelFrame(
        credit_tables_frame, text="Suppliers - Amount We Owe", bg=BACKGROUND,
        font=FONT_BODY_BOLD, padx=10, pady=10
    )
    payable_frame.pack(side=LEFT, fill="both", expand=True)
    payable_tree = build_treeview(payable_frame, CREDIT_COLUMNS, height=10)
    _lock_column_widths(payable_tree, CREDIT_COLUMNS)
    payable_scroll_x = Scrollbar(payable_frame, orient=HORIZONTAL, command=payable_tree.xview)
    payable_tree.configure(xscrollcommand=payable_scroll_x.set)
    payable_scroll_x.pack(side=BOTTOM, fill=X)
    payable_tree.pack(fill="both", expand=True)

    latest_credit_data = {"value": None}

    def load_credit_report():
        data = get_credit_report_data()
        latest_credit_data["value"] = data

        receivable_value.config(text=format_currency(data["total_receivable"]))
        payable_value.config(text=format_currency(data["total_payable"]))
        overview_receivable_value.config(text=format_currency(data["total_receivable"]))
        overview_payable_value.config(text=format_currency(data["total_payable"]))

        customer_rows = [
            (
                name, contact, format_currency(balance), format_currency(amount_paid),
                open_invoices,
                format_currency(last_payment_amount) if last_payment_amount is not None else "—",
                last_payment_date or "—"
            )
            for _id, name, contact, balance, amount_paid, open_invoices,
                last_payment_amount, last_payment_date in data["customers"]
        ]
        supplier_rows = [
            (
                name, contact, format_currency(balance), format_currency(amount_paid),
                open_invoices,
                format_currency(last_payment_amount) if last_payment_amount is not None else "—",
                last_payment_date or "—"
            )
            for _id, name, contact, balance, amount_paid, open_invoices,
                last_payment_amount, last_payment_date in data["suppliers"]
        ]

        reload_treeview(receivable_tree, customer_rows)
        reload_treeview(payable_tree, supplier_rows)

    # ---------------- Load Report Data ----------------
    def load_report(start_date, end_date):

        current_range["from"] = start_date
        current_range["to"] = end_date

        data = get_report_data(start_date, end_date)

        sales_value.config(text=format_currency(data["total_sales"]))
        purchase_value.config(text=format_currency(data["total_purchases"]))
        expense_value.config(text=format_currency(data["total_expenses"]))
        profit_value.config(text=format_currency(data["total_profit"]))
        cogs_value.config(text=format_currency(data["cost_of_sold_items"]))
        sales_tax_value.config(text=format_currency(data["sales_tax"]))
        purchase_tax_value.config(text=format_currency(data["purchase_tax"]))
        best_rows = [(name, qty, format_currency(revenue)) for name, qty, revenue in data["best_products"]]
        worst_rows = [(name, qty, format_currency(revenue)) for name, qty, revenue in data["worst_products"]]

        reload_treeview(best_tree, best_rows)
        reload_treeview(worst_tree, worst_rows)

        product_details = get_product_wise_report(start_date, end_date)
        detail_rows = [
            (name, qty, format_currency(revenue), format_currency(discount),
             format_currency(cost), format_currency(profit), stock, format_currency(credit))
            for name, qty, revenue, discount, cost, profit, stock, credit in product_details
        ]
        reload_treeview(details_tree, detail_rows)

        reload_treeview(unsold_tree, data["unsold_products"])

        latest_data["value"] = data
        latest_data["product_details"] = product_details
        latest_data["unsold_products"] = data["unsold_products"]

        # Only redraw the (slow) charts immediately if the user is
        # currently looking at the Charts tab - otherwise skip it,
        # so switching Weekly/Monthly on the Overview tab stays instant.
        if notebook.index(notebook.select()) == 1:
            draw_charts(data)
# ================================================================================
    def apply_custom_range():
        start = start_date_picker.get_date().isoformat()
        end = end_date_picker.get_date().isoformat()

        if start > end:
            from tkinter import messagebox
            messagebox.showerror("Error", "Start date cannot be after End date.")
            return

        load_report(start, end)
# ========================================================================

    def on_tab_changed(event):
            if notebook.index(notebook.select()) == 1 and latest_data["value"] is not None:
                draw_charts(latest_data["value"])

    notebook.bind("<<NotebookTabChanged>>", on_tab_changed)

    # ---------------- Default: load Weekly on open ----------------
    load_report(*get_weekly_range())
    load_credit_report()

    win.deiconify()