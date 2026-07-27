from tkinter import *
from tkinter import ttk
import sqlite3
from tkinter import messagebox

# ===============================================
# Show Customers
# ==============================================
def show_customers(tree):

    # Purana data remove
    for row in tree.get_children():
        tree.delete(row)

    conn = sqlite3.connect("database/inventory.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT * FROM customers
        ORDER BY id DESC
    """)

    rows = cursor.fetchall()

    conn.close()

    for row in rows:
        tree.insert("", END, values=row)
# ================================================================

def save_customer(name, contact, email, address, tree):

    if (
        name.get().strip() == "" or
        contact.get().strip() == ""
    ):
        messagebox.showerror(
            "Error",
            "Customer Name and Contact are required!"
        )
        return

    conn = sqlite3.connect("database/inventory.db")
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO customers(name, contact, email, address)
        VALUES (?, ?, ?, ?)
    """, (
        name.get().strip(),
        contact.get().strip(),
        email.get().strip(),
        address.get().strip()
    ))

    conn.commit()
    conn.close()

    messagebox.showinfo(
        "Success",
        "Customer Added Successfully"
    )

    name.set("")
    contact.set("")
    email.set("")
    address.set("")
    show_customers(tree)
# =================================================
# Update Customer
# =================================================
def update_customer(
    selected_id,
    name,
    contact,
    email,
    address,
    tree
):

    if selected_id.get() == "":
        messagebox.showerror(
            "Update",
            "Please select a customer first."
        )
        return

    if (
        name.get().strip() == "" or
        contact.get().strip() == ""
    ):
        messagebox.showerror(
            "Error",
            "Customer Name and Contact are required!"
        )
        return

    conn = sqlite3.connect("database/inventory.db")
    cursor = conn.cursor()

    cursor.execute(""" UPDATE customers SET
                                  
            name=?,
            contact=?,
            email=?,
            address=?
        WHERE id=?
    """, (
        name.get().strip(),
        contact.get().strip(),
        email.get().strip(),
        address.get().strip(),
        selected_id.get()
    ))

    conn.commit()
    conn.close()

    messagebox.showinfo(
        "Success",
        "Customer Updated Successfully"
    )

    name.set("")
    contact.set("")
    email.set("")
    address.set("")
    selected_id.set("")

    show_customers(tree)
# ================================================
# Delete Customer
# ------------------------------------------------
def delete_customer(selected_id, tree):

    if selected_id.get() == "":
        messagebox.showerror(
            "Delete",
            "Please select a customer first."
        )
        return

    confirm = messagebox.askyesno(
        "Confirm Delete",
        "Are you sure you want to delete this customer?"
    )

    if not confirm:
        return

    conn = sqlite3.connect("database/inventory.db")
    cursor = conn.cursor()

    cursor.execute("""
        DELETE FROM customers
        WHERE id=?
    """, (
        selected_id.get(),
    ))

    conn.commit()
    conn.close()

    messagebox.showinfo(
        "Success",
        "Customer Deleted Successfully"
    )

    selected_id.set("")

    show_customers(tree)
# ================================================
# Clear Fields
# -----------------------------------------------
def clear_fields(selected_id,name,contact,email,address,name_entry):

    selected_id.set("")

    name.set("")
    contact.set("")
    email.set("")
    address.set("")

    name_entry.focus_set()    
# =========================================
#  Search Customer
# --------------------------------------
def search_customer(search, tree):

    if search.get().strip() == "":
        messagebox.showerror(
            "Search",
            "Please enter customer name."
        )
        return

    # Purana data remove
    for row in tree.get_children():
        tree.delete(row)

    conn = sqlite3.connect("database/inventory.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT * FROM customers
        WHERE name LIKE ?
    """, (
        "%" + search.get().strip() + "%",
    ))

    rows = cursor.fetchall()

    conn.close()

    if len(rows) == 0:
        messagebox.showinfo(
            "Search",
            "No Customer Found"
        )
        return

    for row in rows:
        tree.insert("", END, values=row)
# =================================================
# Select Customer
# -------------------------------------------------
def select_customer(event,tree,name,contact,email,address,selected_id):

    selected = tree.focus()

    values = tree.item(selected, "values")

    if values:

        selected_id.set(values[0])
        name.set(values[1])
        contact.set(values[2])
        email.set(values[3])
        address.set(values[4])
# =================================================
# ========================================================
def open_window():

    win = Toplevel()

    win.title("Customer Management")

    win.geometry("950x600")

    win.resizable(False, False)

    win.iconbitmap("assets/ims.ico")

    # ==========================
    # Variables
    # ==========================

    search = StringVar()
    name = StringVar()
    contact = StringVar()
    email = StringVar()
    address = StringVar()
    selected_id = StringVar()
    # ==========================================
    # Search Frame
    # ==========================================
    search_frame = LabelFrame(
    win,
    text="Search Customer",
    padx=10,
    pady=10
)
    search_frame.pack(fill="x", padx=10, pady=10)

    Label(
        search_frame,
        text="Customer Name"
    ).grid(row=0, column=0, padx=5)

    Entry(
        search_frame,
        textvariable=search,
        width=30
    ).grid(row=0, column=1)

    Button(
        search_frame,
        text="Search",
        width=12,
        command=lambda: search_customer(
            search,
            tree
        )
    ).grid(row=0, column=2, padx=10)

    Button(
        search_frame,
        text="Show All",
        width=12,
        command=lambda: show_customers(tree)
    ).grid(row=0, column=3)
    # ================================================
    # Customer Details Frame
    # ================================================
    customer_frame = LabelFrame(
    win,
    text="Customer Details",
    padx=10,
    pady=10
)
    customer_frame.pack(fill="x", padx=10)
    # ======================================================
    # Fields inside Customer Details Frame
    # =======================================================
    Label(customer_frame, text="Customer Name").grid(row=0, column=0)

    name_entry = Entry(
    customer_frame,
    textvariable=name,
    width=35
    )

    name_entry.grid(
        row=0,
        column=1,
        padx=10
    )

    Label(customer_frame, text="Contact").grid(row=1, column=0)

    Entry(
        customer_frame,
        textvariable=contact,
        width=35
    ).grid(row=1, column=1, padx=10, pady=5)

    Label(customer_frame, text="Email").grid(row=2, column=0)

    Entry(
        customer_frame,
        textvariable=email,
        width=35
    ).grid(row=2, column=1, padx=10)

    Label(customer_frame, text="Address").grid(row=3, column=0)

    Entry(
        customer_frame,
        textvariable=address,
        width=35
    ).grid(row=3, column=1, padx=10, pady=5)
# ==========================
# Buttons
# ==========================

    button_frame = Frame(customer_frame)

    button_frame.grid(
        row=4,
        column=0,
        columnspan=2,
        pady=15
    )

    Button(
        button_frame,
        text="Save",
        width=10,
        command=lambda:save_customer(
            name,
            contact,
            email,
            address,
            tree
        )
    ).grid(row=0, column=0, padx=5)

    Button(
        button_frame,
        text="Update",
        width=10,
        command=lambda: update_customer(
            selected_id,
            name,
            contact,
            email,
            address,
            tree
        )
    ).grid(row=0, column=1, padx=5)

    Button(
        button_frame,
        text="Delete",
        width=10,
        command=lambda: delete_customer(
            selected_id,
            tree
        )
    ).grid(row=0, column=2, padx=5)

    Button(
        button_frame,
        text="Clear",
        width=10,
        command=lambda: clear_fields(
            selected_id,
            name,
            contact,
            email,
            address,
            name_entry
        )
    ).grid(row=0, column=3, padx=5)
# ==========================
# Customer Table
# ==========================

    table_frame = Frame(win)

    table_frame.pack(
        fill=BOTH,
        expand=True,
        padx=10,
        pady=10
    )

    scrollbar_y = Scrollbar(table_frame)

    scrollbar_y.pack(
        side=RIGHT,
        fill=Y
    )

    tree = ttk.Treeview(
        table_frame,
        columns=(
            "ID",
            "Name",
            "Contact",
            "Email",
            "Address"
        ),
        show="headings",
        yscrollcommand=scrollbar_y.set
    )

    scrollbar_y.config(command=tree.yview)

    tree.heading("ID", text="ID")
    tree.heading("Name", text="Customer Name")
    tree.heading("Contact", text="Contact")
    tree.heading("Email", text="Email")
    tree.heading("Address", text="Address")

    tree.column("ID", width=70)
    tree.column("Name", width=220)
    tree.column("Contact", width=150)
    tree.column("Email", width=220)
    tree.column("Address", width=250)

    tree.pack(fill=BOTH, expand=True)
    # ---This code part of Select Customer----
    tree.bind(
    "<<TreeviewSelect>>",
    lambda event: select_customer(
        event,
        tree,
        name,
        contact,
        email,
        address,
        selected_id
    )
)
# ---------------------------------------
    show_customers(tree)
    name_entry.focus_set()