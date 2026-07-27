
from tkinter import *
from tkinter import ttk
from tkinter import messagebox
import sqlite3

# ===========================================================
# PRODUCT MODULE CONSTANTS
# ===========================================================
WINDOW_WIDTH = 950
WINDOW_HEIGHT = 600

PRIMARY_COLOR = "#0F4C81"
BACKGROUND_COLOR = "#F4F6F9"

FONT_TITLE = ("Segoe UI", 18, "bold")
FONT_LABEL = ("Segoe UI", 10)
FONT_BUTTON = ("Segoe UI", 10, "bold")

BUTTON_WIDTH = 12

PRODUCT_STATUS = "Active"

selected_id = None

def save_product(name,cost_price,sale_price,quantity,tree):

# ===========================================================
# VALIDATE PRODUCT
# ===========================================================
    is_valid, message = validate_product_data(
        name,
        cost_price,
        sale_price,
        quantity
    )
    if not is_valid:
        messagebox.showerror(
            "Validation Error",
            message
        )
        return
        
    conn = sqlite3.connect("database/inventory.db")
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM products WHERE LOWER(name)=LOWER(?)",
        (name.get().strip().title(),)
    )

    product = cursor.fetchone()

    if product:
        messagebox.showerror(
            "Error",
            "Product already exists!"
        )
        conn.close()
        return
    
    try:
        product_cost_price = float(cost_price.get())
        product_sale_price = float(sale_price.get())
        product_quantity = int(quantity.get())
    except ValueError:
        conn.close()
        messagebox.showerror(
            "Invalid Input",
            "Cost Price and Sale Price must be numbers and Quantity must be an integer."
        )
        return

    cursor.execute("""
    INSERT INTO products(
        name,
        cost_price,
        sale_price,
        quantity,
        status
    )
    VALUES (?, ?, ?, ?, ?)
    """,
    (
        name.get().strip(),
        product_cost_price,
        product_sale_price,
        product_quantity,
        get_product_status(product_quantity)
    ))
    conn.commit()
    conn.close()

    messagebox.showinfo("Success", "Product Added Successfully")

    # Fields Clear
    name.set("")
    cost_price.set("")
    sale_price.set("")
    quantity.set("")
    show_products(tree) 
# ========================
# Show Products
# ===========================
def show_products(tree):

    # Clear old rows
    for row in tree.get_children():
        tree.delete(row)

    conn = sqlite3.connect("database/inventory.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            id,
            name,
            cost_price,
            sale_price,
            quantity,
            status
        FROM products
        ORDER BY id DESC
    """)

    rows = cursor.fetchall()

    conn.close()

    for row in rows:
        tree.insert("", END, values=row)
# ==============================================
# SEARCH PRODUCTS
# ==============================================
def search_products(search, tree):

    # Treeview empty before
    for row in tree.get_children():
        tree.delete(row)

    conn = sqlite3.connect("database/inventory.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            id,
            name,
            cost_price,
            sale_price,
            quantity,
            status
        FROM products
        WHERE name LIKE ?
        ORDER BY id DESC
    """,
    ('%' + search.get().strip() + '%', ))

    rows = cursor.fetchall()

    conn.close()

    if search.get().strip() == "":

        show_products(tree)
        return
    if len(rows) == 0:
        return

    for row in rows:
        tree.insert("", END, values=row)
# ===========================================================
# LIVE SEARCH
# ===========================================================
def live_search(event, search, tree):
    search_products(search, tree)
# ============================================
def get_selected_product(
    event,
    tree,
    name,
    cost_price,
    sale_price,
    quantity
):

    global selected_id

    selected = tree.focus()

    values = tree.item(selected, "values")

    if not values:
        return

    selected_id = values[0]

    name.set(values[1])
    cost_price.set(values[2])
    sale_price.set(values[3])
    quantity.set(values[4])
# ==========================================
# Update Product Function

def update_product(name, cost_price, sale_price, quantity, tree):

    global selected_id

    if selected_id is None:
        messagebox.showerror("Error", "Please select a product first.")
        return
# ===========================================================
# VALIDATE PRODUCT Update
# ===========================================================
    is_valid, message = validate_product_data(
        name,
        cost_price,
        sale_price,
        quantity
    )
    if not is_valid:
        messagebox.showerror(
            "Validation Error",
            message
        )
        return

    product_cost_price = float(
        cost_price.get()
    )
    product_sale_price = float(
        sale_price.get()
    )
    product_quantity = int(
        quantity.get()
    )

    # if (name.get() == "" or cost_price.get() == "" or
    #     sale_price.get() == "" or quantity.get() == ""):
    #     messagebox.showerror("Error", "All fields are required.")
    #     return
    
    # try:
    #     product_cost_price = float(cost_price.get())
    #     product_sale_price = float(sale_price.get())
    #     product_quantity = int(quantity.get())

    # except ValueError:
    #     messagebox.showerror(
    #         "Invalid Input",
    #         "Cost Price and Sale Price must be numbers and Quantity must be an integer."
    #     )
    #     return
# ----------------------------------------
#   database connection
# --------------------------------------
    conn = sqlite3.connect("database/inventory.db")
    cursor = conn.cursor()
# ===========================================================
# DUPLICATE PRODUCT VALIDATION
# ===========================================================
    cursor.execute(
        """
        SELECT id
        FROM products
        WHERE LOWER(name)=LOWER(?)
        AND id!=?
        """,
        (name.get().strip(), selected_id)
    )
    duplicate_product = cursor.fetchone()

    if duplicate_product:
        conn.close()
        messagebox.showerror(
            "Duplicate Product",
            "Product name already exists."
        )
        return
# ------------------------------------------------
    cursor.execute("""
        UPDATE products
        SET
            name=?,
            cost_price=?,
            sale_price=?,
            quantity=?,
            status=?
        WHERE id=?
    """,
    (
        name.get().strip(),
        product_cost_price,
        product_sale_price,
        product_quantity,
        get_product_status(product_quantity),
        selected_id
    ))

    conn.commit()
    conn.close()

    messagebox.showinfo("Success", "Product Updated Successfully")

    show_products(tree)

    name.set("")
    cost_price.set("")
    sale_price.set("")
    quantity.set("")

    selected_id = None
# ==========================================
#  Delete Product Function

def delete_product(name, cost_price, sale_price, quantity, tree):

    global selected_id

    if selected_id is None:
        messagebox.showerror(
            "Error",
            "Please select a product first."
        )
        return

    answer = messagebox.askyesno(
        "Delete Product",
        "Are you sure you want to delete this product?"
    )

    if answer:

        conn = sqlite3.connect("database/inventory.db")

        cursor = conn.cursor()

        cursor.execute(
            "DELETE FROM products WHERE id=?",
            (selected_id,)
        )

        conn.commit()
        conn.close()

        messagebox.showinfo(
            "Success",
            "Product Deleted Successfully"
        )

        show_products(tree)

        clear_fields(
        name,
        cost_price,
        sale_price,
        quantity
        )

        selected_id = None
# ==========================================
#  Clear Function

def clear_fields(name, cost_price, sale_price, quantity):

    global selected_id

    name.set("")
    cost_price.set("")
    sale_price.set("")
    quantity.set("")

    selected_id = None
# ===========================================================
# GET PRODUCT STATUS
# ===========================================================
def get_product_status(quantity):
    """
    Returns product stock status based on quantity.

    Rules
    -----
    Quantity = 0      -> Out of Stock
    Quantity 1-5      -> Low Stock
    Quantity > 5      -> Active
    """
    if quantity <= 0:
        return "Out of Stock"

    elif quantity <= 5:
        return "Low Stock"

    else:
        return "Active"
# ===========================================================
# VALIDATE PRODUCT DATA
# ===========================================================
def validate_product_data(
        name,
        cost_price,
        sale_price,
        quantity
    ):
        """
        Validate Product Data

        Returns:
            (True, "")                     -> Validation Passed
            (False, "Error Message")       -> Validation Failed
        """
    # ---------------------------------
    # Product Name
    # ---------------------------------
        product_name = name.get().strip()

        if product_name == "":
            return False, "Product Name is required."

        if len(product_name) < 2:
            return False, "Product Name must contain at least 2 characters."

        if len(product_name) > 100:
            return False, "Product Name cannot exceed 100 characters."
    # ---------------------------------
    # Cost Price
    # ---------------------------------
        try:
            product_cost = float(cost_price.get())

        except ValueError:
            return False, "Invalid Cost Price."

        if product_cost <= 0:
            return False, "Cost Price must be greater than zero."
    # ---------------------------------
    # Sale Price
    # ---------------------------------
        try:
            product_sale = float(sale_price.get())

        except ValueError:
            return False, "Invalid Sale Price."

        if product_sale <= 0:
            return False, "Sale Price must be greater than zero."

        if product_sale < product_cost:
            return False, "Sale Price cannot be less than Cost Price."
    # ---------------------------------
    # Quantity
    # ---------------------------------
        try:
            product_qty = int(quantity.get())

        except ValueError:
            return False, "Quantity must be an integer."

        if product_qty < 0:
            return False, "Quantity cannot be negative."

        return True, ""
# ==========================================
def open_window():

    win = Toplevel()

    win.title(
        "Inventory Management System | Product Management"
    )
    win.geometry(
        f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}"
    )
    win.configure(
        bg=BACKGROUND_COLOR
    )
    win.resizable(False, False)

    # =========================
    # Variables
    # =========================

    search = StringVar()
    name = StringVar()
    cost_price = StringVar()
    sale_price = StringVar()
    quantity = StringVar()
# ===========================================================
# PROFESSIONAL HEADER
# ===========================================================
    header_frame = Frame(
        win,
        bg=PRIMARY_COLOR,
        height=60
    )
    header_frame.pack(
        fill=X
    )
    header_frame.pack_propagate(False)

    title_label = Label(
        header_frame,
        text="PRODUCT MANAGEMENT",
        bg=PRIMARY_COLOR,
        fg="white",
        font=FONT_TITLE
    )
    title_label.pack(
        side=LEFT,
        padx=20
    )
    subtitle_label = Label(
        header_frame,
        text="Manage Products, Stock & Pricing",
        bg=PRIMARY_COLOR,
        fg="white",
        font=("Segoe UI", 10)
    )
    subtitle_label.pack(
        side=RIGHT,
        padx=20
    )
    # =========================
    # Search Frame
    # =========================
# =======================
# MAIN CONTAINER
# =======================
    main_frame = Frame(
        win,
        bg=BACKGROUND_COLOR
    )
    main_frame.pack(
        fill=BOTH,
        expand=True
    )
    # ------------------------
    search_frame = LabelFrame(
        main_frame,
        text="Search Product",
        font=("Segoe UI", 10, "bold"),
        padx=10,
        pady=10
    )

    search_frame.pack(fill="x", padx=20, pady=(15,10))

    Label(
        search_frame,
        text="Product Name"
    ).grid(row=0, column=0, padx=5)

    search_entry = Entry(
        search_frame,
        textvariable=search,
        width=30
    )
    search_entry.grid(row=0, column=1)

    search_entry.bind(
        "<KeyRelease>",
        lambda event: live_search(
            event,
            search,
            tree
        )
    )
# ============================
# SEARCH BUTTON, SHOW ALL 
    Button(
    search_frame,
    text="Search",
    width=12,
    command=lambda: search_products(search, tree)
    ).grid(row=0, column=2, padx=10)

    Button(
    search_frame,
    text="Show All",
    width=12,
    command=lambda: show_products(tree)
    ).grid(row=0, column=3)

    # =========================
    # Product Frame Labels Code
    # =========================

    product_frame = LabelFrame(
        main_frame,
        text="Product Details",
        font=("Segoe UI", 10, "bold"),
        padx=10,
        pady=10
    )
    product_frame.pack(fill="x", padx=20, pady=(5,10))

    Label(
        product_frame,
        text="Product Name",
        bg=BACKGROUND_COLOR,
        font=FONT_LABEL
    ).grid(row=0,column=0,padx=10,pady=8,sticky=W)

    name_entry = Entry(
        product_frame,
        textvariable=name,
        width=35
    )
    name_entry.grid(
        row=0,
        column=1,
        padx=10,
        pady=8,
        sticky=EW
    )
    Label(
        product_frame,
        text="Cost Price",
        bg=BACKGROUND_COLOR,
        font=FONT_LABEL
    ).grid(row=0,column=2,padx=10,pady=8,sticky=W)

    Entry(
        product_frame,
        textvariable=cost_price,
        width=20
    ).grid(row=0, column=3, padx=10, pady=8, sticky=EW)

    Label(
        product_frame,
        text="Sale Price",
        bg=BACKGROUND_COLOR,
        font=FONT_LABEL
    ).grid(row=1,column=0,padx=10,pady=8,sticky=W)

    Entry(
        product_frame,
        textvariable=sale_price,
        width=35
    ).grid(row=1, column=1, padx=10, pady=8, sticky=EW)

    Label(
        product_frame,
        text="Quantity",
        bg=BACKGROUND_COLOR,
        font=FONT_LABEL
    ).grid(row=1,column=2,padx=10,pady=8,sticky=W)

    Entry(
        product_frame,
        textvariable=quantity,
        width=20
    ).grid(row=1, column=3, padx=10, pady=8, sticky=EW)
    
    # =================================
    # PRODUCT FORM GRID CONFIGURATION
    # ==================================
    product_frame.columnconfigure(1, weight=1)
    product_frame.columnconfigure(3, weight=1)
    # =========================
    # Buttons
    # =========================

    button_frame = Frame(product_frame, bg=BACKGROUND_COLOR)

    button_frame.grid(row=2, column=0, columnspan=4, pady=20)
    
    save_btn = Button(
        button_frame,
        text="💾 Save",
        width=BUTTON_WIDTH,
        bg="#2E8B57",
        fg="white",
        activebackground="#256F46",
        activeforeground="white",
        font=FONT_BUTTON,
        bd=0,
        cursor="hand2",
        command=lambda: save_product(
            name,
            cost_price,
            sale_price,
            quantity,
            tree
        )
    )
    save_btn.grid(row=0, column=0, padx=5)
    
    update_btn = Button(
        button_frame,
        text="✏ Update",
        width=BUTTON_WIDTH,
        bg="#1976D2",
        fg="white",
        activebackground="#125CA1",
        activeforeground="white",
        font=FONT_BUTTON,
        bd=0,
        cursor="hand2",
        command=lambda: update_product(name, cost_price, sale_price, quantity, tree)
    )
    update_btn.grid(row=0, column=1, padx=5)

    delete_btn = Button(
        button_frame,
        text="🗑 Delete",
        width=BUTTON_WIDTH,
        bg="#D32F2F",
        fg="white",
        activebackground="#B71C1C",
        activeforeground="white",
        font=FONT_BUTTON,
        bd=0,
        cursor="hand2",
        command=lambda: delete_product(name, cost_price, sale_price, quantity, tree)
    )
    delete_btn.grid(row=0, column=2, padx=5)
    
    clear_btn = Button(
        button_frame,
        text="🧹 Clear",
        width=BUTTON_WIDTH,
        bg="#616161",
        fg="white",
        activebackground="#424242",
        activeforeground="white",
        font=FONT_BUTTON,
        bd=0,
        cursor="hand2",
        command=lambda: clear_fields(name, cost_price, sale_price, quantity)
    )
    clear_btn.grid(row=0, column=3, padx=5)
    # =========================
    # Product Table
    # =========================
    table_frame = Frame(
        main_frame,
        bg=BACKGROUND_COLOR
    )
    table_frame.pack(fill=BOTH, expand=True, padx=20, pady=(5,20))

    scrollbar_y = Scrollbar(table_frame)

    scrollbar_y.pack(side=RIGHT, fill=Y)
# ======================================
#   Tree View Code
# ---------------------------------------
    tree = ttk.Treeview(
        table_frame,
        columns=("ID",
        "Name",
        "Cost Price",
        "Sale Price",
        "Quantity",
        "Status"),
        show="headings",
        yscrollcommand=scrollbar_y.set
    )

    scrollbar_y.config(command=tree.yview)

    tree.heading("ID", text="ID")
    tree.heading("Name", text="Product Name")
    tree.heading("Cost Price", text="Cost Price")
    tree.heading("Sale Price", text="Sale Price")
    tree.heading("Quantity", text="Quantity")
    tree.heading("Status", text="Status")

    tree.column("ID", width=60)
    tree.column("Name", width=220)
    tree.column("Cost Price", width=120)
    tree.column("Sale Price", width=120)
    tree.column("Quantity", width=100)
    tree.column("Status", width=100)

    tree.pack(fill=BOTH, expand=True)
    name_entry.focus_set()
    # ================================
    # This Line For Get Select Product Function

    tree.bind(
    "<Double-1>",
    lambda event: get_selected_product(
        event,
        tree,
        name,
        cost_price,
        sale_price,
        quantity
    )
)

