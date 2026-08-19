from tkinter import *
from tkinter import ttk

from utils.branding_helpers import add_branding_strip

from services.expense_service import (
    load_expenses, save_expense, update_expense, delete_expense
)
from services.settings_service import format_currency
from utils.theme import (
    PRIMARY, BACKGROUND, WHITE,
    FONT_TITLE, FONT_BODY, FONT_BODY_BOLD,
    apply_app_style
)
from utils.tree_helpers import build_treeview, reload_treeview
from utils.ui_helpers import add_buttons, labeled_entry
from utils.window_helpers import size_and_center

EXPENSE_COLUMNS = [
    {"key": "id", "heading": "ID", "width": 60, "anchor": CENTER, "stretch": False},
    {"key": "category", "heading": "Category", "width": 160, "stretch": False},
    {"key": "description", "heading": "Description", "width": 260, "stretch": True},
    {"key": "amount", "heading": "Amount", "width": 130, "anchor": E, "stretch": False},
    {"key": "date", "heading": "Date", "width": 130, "anchor": CENTER, "stretch": False},
]

# =====================================================================
# Load expenses into the tree (with formatted currency)
# =====================================================================
def refresh_expenses(tree, search_term=None):

    rows = load_expenses(search_term)

    formatted_rows = [
        (row[0], row[1], row[2], format_currency(row[3]), row[4])
        for row in rows
    ]
    reload_treeview(tree, formatted_rows)

def live_search(event, search, tree):
    refresh_expenses(tree, search.get().strip())

# =====================================================================
# Pull the selected row into the form fields
# =====================================================================
def get_selected_expense(event, tree, selected_id, category, description, amount, expense_date):

    selected = tree.focus()
    values = tree.item(selected, "values")

    if not values:
        return

    selected_id.set(values[0])
    category.set(values[1])
    description.set(values[2])
    # values[3] is currency-formatted text (e.g. "Rs 1,500.00") - strip
    # everything except the number so it's safe to edit/save again
    raw_amount = "".join(ch for ch in values[3] if ch.isdigit() or ch == ".")
    amount.set(raw_amount)
    expense_date.set(values[4])

def clear_fields(selected_id, category, description, amount, expense_date):
    selected_id.set("")
    category.set("")
    description.set("")
    amount.set("")
    expense_date.set("")

# =====================================================================
# Button handlers
# =====================================================================
def handle_save(category, description, amount, expense_date, tree):
    if save_expense(category, description, amount, expense_date):
        refresh_expenses(tree)
        category.set("")
        description.set("")
        amount.set("")
        expense_date.set("")

def handle_update(selected_id, category, description, amount, expense_date, tree):
    if update_expense(selected_id, category, description, amount, expense_date):
        refresh_expenses(tree)
        clear_fields(selected_id, category, description, amount, expense_date)

def handle_delete(selected_id, category, description, amount, expense_date, tree):
    if delete_expense(selected_id):
        refresh_expenses(tree)
        clear_fields(selected_id, category, description, amount, expense_date)

# =====================================================================
# Main Window
# =====================================================================
def open_window():

    win = Toplevel()
    add_branding_strip(win)

    win.title("Expense Management")
    win.configure(bg=BACKGROUND)

    size_and_center(win, width_ratio=0.65, height_ratio=0.7, resizable=True)

    apply_app_style()
    win.iconbitmap("assets/ims.ico")


    # ---------------- Variables ----------------
    selected_id = StringVar()
    search = StringVar()
    category = StringVar()
    description = StringVar()
    amount = StringVar()
    expense_date = StringVar()

    # ---------------- Header ----------------
    header_frame = Frame(win, bg=PRIMARY, height=60)
    header_frame.pack(fill=X)
    header_frame.pack_propagate(False)

    Label(
        header_frame, text="EXPENSE MANAGEMENT",
        bg=PRIMARY, fg=WHITE, font=FONT_TITLE
    ).pack(side=LEFT, padx=20)

    Label(
        header_frame, text="Track Business Expenses",
        bg=PRIMARY, fg=WHITE, font=FONT_BODY
    ).pack(side=RIGHT, padx=20)

    main_frame = Frame(win, bg=BACKGROUND)
    main_frame.pack(fill=BOTH, expand=True)

    # ---------------- Search ----------------
    search_frame = LabelFrame(
        main_frame, text="Search Expense", bg=BACKGROUND,
        font=FONT_BODY_BOLD, padx=10, pady=10
    )
    search_frame.pack(fill="x", padx=20, pady=(15, 10))

    Label(search_frame, text="Category", bg=BACKGROUND).grid(row=0, column=0, padx=5)

    search_entry = Entry(search_frame, textvariable=search, width=30)
    search_entry.grid(row=0, column=1)
    search_entry.bind("<KeyRelease>", lambda event: live_search(event, search, tree))

    Button(
        search_frame, text="Search", width=12,
        command=lambda: refresh_expenses(tree, search.get().strip())
    ).grid(row=0, column=2, padx=10)

    Button(
        search_frame, text="Show All", width=12,
        command=lambda: refresh_expenses(tree)
    ).grid(row=0, column=3)

    # ---------------- Expense Form ----------------
    expense_frame = LabelFrame(
        main_frame, text="Expense Details", bg=BACKGROUND,
        font=FONT_BODY_BOLD, padx=10, pady=10
    )
    expense_frame.pack(fill="x", padx=20, pady=(5, 10))
    expense_frame.columnconfigure(1, weight=1)
    expense_frame.columnconfigure(3, weight=1)

    labeled_entry(expense_frame, "Category", 0, 0, category, justify="left")
    labeled_entry(expense_frame, "Amount", 0, 2, amount)

    labeled_entry(expense_frame, "Description", 1, 0, description, justify="left")
    labeled_entry(expense_frame, "Date", 1, 2, expense_date, justify="left")

    Label(
        expense_frame, text="(Date optional — blank = today, format: YYYY-MM-DD)",
        bg=BACKGROUND, fg="gray", font=("Segoe UI", 8)
    ).grid(row=2, column=0, columnspan=4, sticky="w", padx=10)

    # ---------------- Buttons ----------------
    button_frame = Frame(expense_frame, bg=BACKGROUND)
    button_frame.grid(row=3, column=0, columnspan=4, pady=15)
    button_frame.columnconfigure((0, 1, 2, 3), weight=1)

    add_buttons(button_frame, [
        ("💾 Save", lambda: handle_save(category, description, amount, expense_date, tree)),
        ("✏ Update", lambda: handle_update(selected_id, category, description, amount, expense_date, tree)),
        ("🗑 Delete", lambda: handle_delete(selected_id, category, description, amount, expense_date, tree)),
        ("🧹 Clear", lambda: clear_fields(selected_id, category, description, amount, expense_date)),
    ])

    # ---------------- Expense Table ----------------
    table_frame = Frame(main_frame, bg=BACKGROUND)
    table_frame.pack(fill=BOTH, expand=True, padx=20, pady=(5, 20))

    scrollbar_y = Scrollbar(table_frame)
    scrollbar_y.pack(side=RIGHT, fill=Y)

    tree = build_treeview(table_frame, EXPENSE_COLUMNS)
    tree.configure(yscrollcommand=scrollbar_y.set)
    scrollbar_y.config(command=tree.yview)
    tree.pack(fill=BOTH, expand=True)

    tree.bind(
        "<Double-1>",
        lambda event: get_selected_expense(event, tree, selected_id, category, description, amount, expense_date)
    )

    refresh_expenses(tree)