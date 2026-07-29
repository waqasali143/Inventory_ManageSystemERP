
from tkinter import *
from tkinter import ttk

from services.product_service import (
    load_products, save_product, update_product, delete_product
)
from utils.theme import (
    PRIMARY, BACKGROUND, WHITE,
    FONT_TITLE, FONT_BODY, FONT_BODY_BOLD,
    apply_app_style
)
from utils.tree_helpers import build_treeview, reload_treeview
from utils.ui_helpers import add_buttons, labeled_entry
from utils.window_helpers import size_and_center

PRODUCT_COLUMNS = [
    {"key": "id", "heading": "ID", "width": 60, "anchor": CENTER, "stretch": False},
    {"key": "name", "heading": "Product Name", "width": 260, "stretch": True},
    {"key": "cost_price", "heading": "Cost Price", "width": 130, "anchor": E, "stretch": False},
    {"key": "sale_price", "heading": "Sale Price", "width": 130, "anchor": E, "stretch": False},
    {"key": "quantity", "heading": "Quantity", "width": 100, "anchor": CENTER, "stretch": False},
    {"key": "status", "heading": "Status", "width": 120, "anchor": CENTER, "stretch": False},
    ]

# =====================================================================
# Load products into the tree + color rows by stock status
# =====================================================================
def refresh_products(tree, search_term=None):

    rows = load_products(search_term)
    reload_treeview(tree, rows)

    tree.tag_configure("out_of_stock", background="#FEE2E2", foreground="#B91C1C")
    tree.tag_configure("low_stock", background="#FEF3C7", foreground="#92400E")
    tree.tag_configure("inactive", background="#F3F4F6", foreground="#9CA3AF")

    for row_id in tree.get_children():
        status = tree.item(row_id, "values")[5]

        if status == "Out of Stock":
            tree.item(row_id, tags=("out_of_stock",))
        elif status == "Low Stock":
            tree.item(row_id, tags=("low_stock",))
        elif status == "Inactive":
            tree.item(row_id, tags=("inactive",))

def live_search(event, search, tree):
    refresh_products(tree, search.get().strip())

# =====================================================================
# Pull the double-clicked row into the form fields
# =====================================================================
def get_selected_product(event, tree, selected_id, name, cost_price, sale_price, quantity,
                          quantity_entry, quantity_hint):

    selected = tree.focus()
    values = tree.item(selected, "values")

    if not values:
        return

    selected_id.set(values[0])
    name.set(values[1])
    cost_price.set(values[2])
    sale_price.set(values[3])
    quantity.set(values[4])

    quantity_entry.config(state="readonly")
    quantity_hint.config(text="🔒 locked — use Purchase/Sale to change stock")
# ==============================================================================
# ===== Clear Field ============
# =============================================================================
def clear_fields(selected_id, name, cost_price, sale_price, quantity,
                  quantity_entry, quantity_hint):
    selected_id.set("")
    name.set("")
    cost_price.set("")
    sale_price.set("")
    quantity.set("")

    quantity_entry.config(state="normal")
    quantity_hint.config(text="(new product — set opening stock)")

# =====================================================================
# Button handlers (wrap service calls + refresh + clear on success)
# =====================================================================
def handle_save(selected_id, name, cost_price, sale_price, quantity, tree,
                 quantity_entry, quantity_hint):
    if save_product(name, cost_price, sale_price, quantity):
        refresh_products(tree)
        clear_fields(selected_id, name, cost_price, sale_price, quantity,
                      quantity_entry, quantity_hint)

def handle_update(selected_id, name, cost_price, sale_price, quantity, tree,
                   quantity_entry, quantity_hint):
    if update_product(selected_id.get(), name, cost_price, sale_price, quantity):
        refresh_products(tree)
        clear_fields(selected_id, name, cost_price, sale_price, quantity,
                      quantity_entry, quantity_hint)
        
def handle_delete(selected_id, name, cost_price, sale_price, quantity, tree,
                   quantity_entry, quantity_hint):
    if delete_product(selected_id.get()):
        refresh_products(tree)
        clear_fields(selected_id, name, cost_price, sale_price, quantity,
                      quantity_entry, quantity_hint)

# =====================================================================
# Main Window
# =====================================================================
def open_window():

    win = Toplevel()
    win.title("Inventory Management System | Product Management")
    win.configure(bg=BACKGROUND)

    size_and_center(win, width_ratio=0.7, height_ratio=0.75, resizable=True)

    apply_app_style()

    # ---------------- Variables ----------------
    selected_id = StringVar()
    search = StringVar()
    name = StringVar()
    cost_price = StringVar()
    sale_price = StringVar()
    quantity = StringVar()

    # ---------------- Header ----------------
    header_frame = Frame(win, bg=PRIMARY, height=60)
    header_frame.pack(fill=X)
    header_frame.pack_propagate(False)

    Label(
        header_frame, text="PRODUCT MANAGEMENT",
        bg=PRIMARY, fg=WHITE, font=FONT_TITLE
    ).pack(side=LEFT, padx=20)

    Label(
        header_frame, text="Manage Products, Stock & Pricing",
        bg=PRIMARY, fg=WHITE, font=FONT_BODY
    ).pack(side=RIGHT, padx=20)

    main_frame = Frame(win, bg=BACKGROUND)
    main_frame.pack(fill=BOTH, expand=True)

    # ---------------- Search ----------------
    search_frame = LabelFrame(
        main_frame, text="Search Product", bg=BACKGROUND,
        font=FONT_BODY_BOLD, padx=10, pady=10
    )
    search_frame.pack(fill="x", padx=20, pady=(15, 10))

    Label(search_frame, text="Product Name", bg=BACKGROUND).grid(row=0, column=0, padx=5)

    search_entry = Entry(search_frame, textvariable=search, width=30)
    search_entry.grid(row=0, column=1)
    search_entry.bind("<KeyRelease>", lambda event: live_search(event, search, tree))

    Button(
        search_frame, text="Search", width=12,
        command=lambda: refresh_products(tree, search.get().strip())
    ).grid(row=0, column=2, padx=10)

    Button(
        search_frame, text="Show All", width=12,
        command=lambda: refresh_products(tree)
    ).grid(row=0, column=3)

    # ---------------- Product Form ----------------
    product_frame = LabelFrame(
        main_frame, text="Product Details", bg=BACKGROUND,
        font=FONT_BODY_BOLD, padx=10, pady=10
    )
    product_frame.pack(fill="x", padx=20, pady=(5, 10))
    product_frame.columnconfigure(1, weight=1)
    product_frame.columnconfigure(3, weight=1)

    labeled_entry(product_frame, "Product Name", 0, 0, name, justify="left")
    labeled_entry(product_frame, "Cost Price", 0, 2, cost_price)

    labeled_entry(product_frame, "Sale Price", 1, 0, sale_price)
    quantity_entry = labeled_entry(product_frame, "Quantity", 1, 2, quantity)

    quantity_hint = Label(
        product_frame, text="(new product — set opening stock)",
        bg=BACKGROUND, fg="gray", font=("Segoe UI", 8)
    )
    quantity_hint.grid(row=1, column=4, padx=5, sticky="w")

    # ---------------- Buttons ----------------
    button_frame = Frame(product_frame, bg=BACKGROUND)
    button_frame.grid(row=2, column=0, columnspan=4, pady=20)
    button_frame.columnconfigure((0, 1, 2, 3), weight=1)

    add_buttons(button_frame, [
        ("💾 Save", lambda: handle_save(selected_id, name, cost_price, sale_price, 
                                        quantity, tree, quantity_entry, quantity_hint)),
        ("✏ Update", lambda: handle_update(selected_id, name, cost_price, sale_price, 
                                           quantity, tree, quantity_entry, quantity_hint)),
        ("🗑 Delete", lambda: handle_delete(selected_id, name, cost_price, sale_price, 
                                            quantity, tree, quantity_entry, quantity_hint)),
        ("🧹 Clear", lambda: clear_fields(selected_id, name, cost_price, sale_price, 
                                          quantity, quantity_entry, quantity_hint)),
    ])

    # ---------------- Product Table ----------------
    table_frame = Frame(main_frame, bg=BACKGROUND)
    table_frame.pack(fill=BOTH, expand=True, padx=20, pady=(5, 20))

    scrollbar_y = Scrollbar(table_frame)
    scrollbar_y.pack(side=RIGHT, fill=Y)

    tree = build_treeview(table_frame, PRODUCT_COLUMNS)
    tree.configure(yscrollcommand=scrollbar_y.set)
    scrollbar_y.config(command=tree.yview)
    tree.pack(fill=BOTH, expand=True)

    tree.bind(
        "<Double-1>",
        lambda event: get_selected_product(event, tree, selected_id, name, 
                                           cost_price, sale_price, quantity,
                                            quantity_entry, quantity_hint)
    )
# ==============================================================================
    refresh_products(tree)
    name_entry_widget = product_frame.grid_slaves(row=0, column=1)
    if name_entry_widget:
        name_entry_widget[0].focus_set()