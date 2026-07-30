from tkinter import *
from tkinter import ttk

from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from services.report_service import (
    get_weekly_range, get_monthly_range, get_custom_range, get_report_data
)
from services.settings_service import format_currency
from utils.theme import (
    PRIMARY, PRIMARY_DARK, BACKGROUND, WHITE, TEXT,
    GREEN, RED, BLUE, ORANGE,
    FONT_TITLE, FONT_BODY, FONT_BODY_BOLD,
    apply_app_style
)
from utils.tree_helpers import build_treeview, reload_treeview
from utils.window_helpers import size_and_center


def open_report_window():

    win = Toplevel()
    win.title("Business Reports")
    win.configure(bg=BACKGROUND)

    size_and_center(win, width_ratio=0.85, height_ratio=0.9, resizable=True)

    apply_app_style()

    # ---------------- Header ----------------
    header_frame = Frame(win, bg=PRIMARY, height=60)
    header_frame.pack(fill=X)
    header_frame.pack_propagate(False)

    Label(
        header_frame, text="BUSINESS REPORTS",
        bg=PRIMARY, fg=WHITE, font=FONT_TITLE
    ).pack(side=LEFT, padx=20)

    # ---------------- Scrollable Body ----------------
    canvas = Canvas(win, bg=BACKGROUND, highlightthickness=0)
    scrollbar = Scrollbar(win, orient=VERTICAL, command=canvas.yview)
    body = Frame(canvas, bg=BACKGROUND)

    body.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
    canvas.create_window((0, 0), window=body, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)

    canvas.pack(side=LEFT, fill=BOTH, expand=True)
    scrollbar.pack(side=RIGHT, fill=Y)

    # ---------------- Filter Bar ----------------
    filter_frame = LabelFrame(
        body, text="Report Period", bg=BACKGROUND,
        font=FONT_BODY_BOLD, padx=10, pady=10
    )
    filter_frame.pack(fill="x", padx=20, pady=15)

    custom_start = StringVar()
    custom_end = StringVar()

    Label(filter_frame, text="Custom Start (YYYY-MM-DD)", bg=BACKGROUND).grid(row=0, column=2, padx=5)
    Entry(filter_frame, textvariable=custom_start, width=14).grid(row=0, column=3, padx=5)

    Label(filter_frame, text="Custom End (YYYY-MM-DD)", bg=BACKGROUND).grid(row=0, column=4, padx=5)
    Entry(filter_frame, textvariable=custom_end, width=14).grid(row=0, column=5, padx=5)

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

# ---------------- Summary Cards ----------------
    summary_frame = Frame(body, bg=BACKGROUND)
    summary_frame.pack(fill="x", padx=20, pady=(0, 15))

    def summary_card(parent, title, color):
        card = Frame(parent, bg=color, width=190, height=90)
        card.pack(side=LEFT, padx=8)
        card.pack_propagate(False)

        Label(card, text=title, bg=color, fg=WHITE, font=FONT_BODY_BOLD).pack(pady=(14, 4))
        value_label = Label(card, text="0", bg=color, fg=WHITE, font=("Segoe UI", 16, "bold"))
        value_label.pack()

        return value_label

    sales_value = summary_card(summary_frame, "Total Sales", BLUE)
    purchase_value = summary_card(summary_frame, "Total Purchases", ORANGE)
    expense_value = summary_card(summary_frame, "Total Expenses", "#8B5CF6")
    profit_value = summary_card(summary_frame, "Net Profit", GREEN)

    # ---------------- Best/Worst Products Tables ----------------
    tables_frame = Frame(body, bg=BACKGROUND)
    tables_frame.pack(fill="x", padx=20, pady=(0, 15))

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
    best_tree = build_treeview(best_frame, PRODUCT_COLUMNS, height=8)
    best_tree.pack(fill="both", expand=True)

    worst_frame = LabelFrame(
        tables_frame, text="Top 10 Worst-Selling Products", bg=BACKGROUND,
        font=FONT_BODY_BOLD, padx=10, pady=10
    )
    worst_frame.pack(side=LEFT, fill="both", expand=True)
    worst_tree = build_treeview(worst_frame, PRODUCT_COLUMNS, height=8)
    worst_tree.pack(fill="both", expand=True)

    # ---------------- Load Report Data ----------------
    def load_report(start_date, end_date):

        data = get_report_data(start_date, end_date)

        sales_value.config(text=format_currency(data["total_sales"]))
        purchase_value.config(text=format_currency(data["total_purchases"]))
        expense_value.config(text=format_currency(data["total_expenses"]))
        profit_value.config(text=format_currency(data["net_profit"]))

        best_rows = [(name, qty, format_currency(revenue)) for name, qty, revenue in data["best_products"]]
        worst_rows = [(name, qty, format_currency(revenue)) for name, qty, revenue in data["worst_products"]]

        reload_treeview(best_tree, best_rows)
        reload_treeview(worst_tree, worst_rows)

        draw_charts(data) 
# ==========================================================================================
    def apply_custom_range():
        start, end, error = get_custom_range(custom_start.get().strip(), custom_end.get().strip())
        if error:
            from tkinter import messagebox
            messagebox.showerror("Error", error)
            return
        load_report(start, end)
# ====================================================================================
# ---------------- Charts ----------------
    charts_frame = Frame(body, bg=BACKGROUND)
    charts_frame.pack(fill="x", padx=20, pady=(0, 20))

    # --- Line Chart: Sales vs Purchase Trend ---
    trend_frame = LabelFrame(
        charts_frame, text="Sales vs Purchase Trend", bg=BACKGROUND,
        font=FONT_BODY_BOLD, padx=10, pady=10
    )
    trend_frame.pack(side=LEFT, fill="both", expand=True, padx=(0, 10))

    trend_figure = Figure(figsize=(5, 3.2), dpi=90)
    trend_ax = trend_figure.add_subplot(111)
    trend_canvas = FigureCanvasTkAgg(trend_figure, master=trend_frame)
    trend_canvas.get_tk_widget().pack(fill="both", expand=True)

    # --- Pie Chart: Expense Breakdown ---
    expense_frame_chart = LabelFrame(
        charts_frame, text="Expense Breakdown", bg=BACKGROUND,
        font=FONT_BODY_BOLD, padx=10, pady=10
    )
    expense_frame_chart.pack(side=LEFT, fill="both", expand=True)

    expense_figure = Figure(figsize=(4, 3.2), dpi=90)
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
    # ---------------- Default: load Weekly on open ----------------
    load_report(*get_weekly_range()) 