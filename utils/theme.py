from tkinter import ttk

# =====================================================================
# Central Design System
# Every color/font used anywhere in the app should come from here.
# Change a color once -> the whole app updates, not just one screen.
# =====================================================================

PRIMARY = "#0F4C81"
PRIMARY_DARK = "#0B3B63"
SIDEBAR = "#1E293B"
SIDEBAR_ACTIVE = "#334155"
BACKGROUND = "#F4F6F9"

WHITE = "#FFFFFF"
TEXT = "#1F2937"
MUTED_TEXT = "#6B7280"
BORDER = "#E2E8F0"

BLUE = "#3B82F6"
GREEN = "#10B981"
PURPLE = "#8B5CF6"
ORANGE = "#F59E0B"
RED = "#EF4444"
TEAL = "#14B8A6"

FONT_FAMILY = "Segoe UI"

FONT_TITLE = (FONT_FAMILY, 18, "bold")
FONT_HEADING = (FONT_FAMILY, 13, "bold")
FONT_BODY = (FONT_FAMILY, 10)
FONT_BODY_BOLD = (FONT_FAMILY, 10, "bold")
FONT_SMALL = (FONT_FAMILY, 9)


# =====================================================================
# Apply a modern look to every ttk.Treeview / ttk.Combobox in the app.
# Call this ONCE, right after the root/Toplevel window is created,
# before building any tables. (Every view - purchase, sales, product,
# dashboard - calls this the same way, so all tables look identical.)
# =====================================================================
def apply_app_style():

    style = ttk.Style()
    style.theme_use("clam")

    # ---------------- Treeview rows ----------------
    style.configure(
        "Treeview",
        background=WHITE,
        fieldbackground=WHITE,
        foreground=TEXT,
        rowheight=32,
        font=FONT_BODY,
        borderwidth=0
    )
    style.map(
        "Treeview",
        background=[("selected", PRIMARY)],
        foreground=[("selected", WHITE)]
    )
# ------------------------------------------------------------
    # Alternating row colors (striped table = easier to read)
    style.configure("Treeview", bordercolor=BORDER)

    # ---------------- Treeview header ----------------
    style.configure(
        "Treeview.Heading",
        background=SIDEBAR,
        foreground=WHITE,
        font=FONT_BODY_BOLD,
        relief="flat",
        padding=(8, 8)
    )

    style.map(
        "Treeview.Heading",
        background=[("active", PRIMARY_DARK)]
    )

    # ---------------- Combobox ----------------
    style.configure(
        "TCombobox",
        fieldbackground=WHITE,
        background=WHITE,
        foreground=TEXT,
        padding=6
    )
# ---------------- Currency Selector (style: blends into header) ----------------
    style.configure(
        "HeaderCurrency.TCombobox",
        fieldbackground=PRIMARY,
        background=PRIMARY,
        foreground=WHITE,
        arrowcolor=WHITE,
        bordercolor=PRIMARY,
        padding=6,
        relief="flat",
        borderwidth=0,
        font=(FONT_FAMILY, 12, "bold")
    )
    style.map(
        "HeaderCurrency.TCombobox",
        fieldbackground=[("readonly", PRIMARY)],
        background=[("readonly", PRIMARY)],
        bordercolor=[("readonly", PRIMARY)]
    )

    # ---------------- Currency Selector (hover state) ----------------
    style.configure(
        "HeaderCurrencyHover.TCombobox",
        fieldbackground=PRIMARY_DARK,
        background=PRIMARY_DARK,
        foreground=WHITE,
        arrowcolor=WHITE,
        bordercolor=PRIMARY_DARK,
        padding=6,
        relief="flat",
        borderwidth=0,
        font=(FONT_FAMILY, 12, "bold")
    )
    style.map(
        "HeaderCurrencyHover.TCombobox",
        fieldbackground=[("readonly", PRIMARY_DARK)],
        background=[("readonly", PRIMARY_DARK)],
        bordercolor=[("readonly", PRIMARY_DARK)]
    )
# =====================================================================
# Call this after inserting rows into any Treeview to get
# alternating (striped) row colors - big readability upgrade.
# =====================================================================
def stripe_treeview(tree, even_color="#FFFFFF", odd_color="#F1F5F9"):

    tree.tag_configure("evenrow", background=even_color)
    tree.tag_configure("oddrow", background=odd_color)

    for index, row_id in enumerate(tree.get_children()):
        tag = "evenrow" if index % 2 == 0 else "oddrow"
        tree.item(row_id, tags=(tag,))
