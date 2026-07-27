from tkinter import *
from tkinter import ttk, messagebox

from database.database import get_connection
from repositories import sales_repository as repo
from utils import event_bus

# =====================================================================
# This file matches the EXACT function names/parameters that
# views/sales.py (as uploaded) already calls - no view changes needed.
# Business logic lives here; raw SQL lives in sales_repository.py.
# =====================================================================


def load_customers():
    return repo.fetch_active_customers()


def load_products():
    return repo.fetch_active_products()


# =====================================
# Called when a product is picked from the combobox
# =====================================
def load_product_information(product_combo, product_map, sale_price, available_stock):

    product_name = product_combo.get()
    product_id = product_map.get(product_name)

    if product_id is None:
        return

    details = repo.fetch_product_details(product_id)
    if details:
        sale_price.set(details[0])
        available_stock.set(details[1])


# =====================================
# Totals (kept simple/flat, matching the original design -
# no percentage math introduced here)
# =====================================
def calculate_totals(cart_tree, gross_total, discount, tax, net_total):

    gross = 0.0
    for item in cart_tree.get_children():
        values = cart_tree.item(item)["values"]
        gross += float(values[3])   # "total" column

    gross_total.set(round(gross, 2))

    net = gross - discount.get() + tax.get()
    net_total.set(round(net, 2))


# =====================================
# Add To Cart
# (cart_tree columns stay exactly as in the original: product, price, qty, total)
# =====================================
def add_to_cart(customer, product, quantity, sale_price, available_stock,
                 cart_tree, gross_total, discount, tax, net_total):

    if customer.get() == "":
        messagebox.showerror("Validation Error", "Please select customer.")
        return

    if product.get() == "":
        messagebox.showerror("Validation Error", "Please select product.")
        return

    if quantity.get() <= 0:
        messagebox.showerror("Validation Error", "Quantity must be greater than zero.")
        return

    if quantity.get() > available_stock.get():
        messagebox.showerror("Stock Error", "Insufficient stock available.")
        return

    product_name = product.get()

    for item in cart_tree.get_children():
        values = cart_tree.item(item, "values")
        if values[0] == product_name:
            messagebox.showerror(
                "Duplicate Product",
                "This product is already added to the cart."
            )
            return

    total = quantity.get() * sale_price.get()

    cart_tree.insert("", "end", values=(
        product_name, sale_price.get(), quantity.get(), total
    ))

    calculate_totals(cart_tree, gross_total, discount, tax, net_total)

    product.set("")
    quantity.set(1)
    sale_price.set(0)
    available_stock.set(0)


# =====================================
# Remove Cart Item
# =====================================
def remove_cart_item(cart_tree, gross_total, discount, tax, net_total):

    selected = cart_tree.selection()

    if not selected:
        messagebox.showerror("Selection Error", "Please select an item.")
        return

    cart_tree.delete(selected[0])
    calculate_totals(cart_tree, gross_total, discount, tax, net_total)


# =====================================
# New Sale / Clear Form
# =====================================
def clear_sale_form(customer, product, quantity, sale_price, available_stock,
                     cart_tree, gross_total, discount, tax, net_total):

    for item in cart_tree.get_children():
        cart_tree.delete(item)

    customer.set("")
    product.set("")
    quantity.set(1)
    sale_price.set(0)
    available_stock.set(0)
    gross_total.set(0)
    discount.set(0)
    tax.set(0)
    net_total.set(0)


# =====================================
# Save Sale
# product_map is used here (not in add_to_cart) to translate the
# product NAME stored in the cart back into a product ID for saving.
# =====================================
def save_sale(customer, product, quantity, sale_price, available_stock,
              cart_tree, gross_total, discount, tax, net_total, product_map):

    if customer.get().strip() == "":
        messagebox.showerror("Error", "Please select a customer.")
        return

    if not cart_tree.get_children():
        messagebox.showerror("Error", "Sales cart is empty.")
        return

    cart_items = []
    for item in cart_tree.get_children():
        values = cart_tree.item(item, "values")
        product_name = values[0]
        product_id = product_map.get(product_name)
        price = float(values[1])
        qty = int(values[2])
        subtotal = float(values[3])
        cart_items.append((product_id, price, qty, subtotal))

    # Re-check live stock right before committing
    for product_id, _price, qty, _subtotal in cart_items:
        details = repo.fetch_product_details(product_id)
        current_stock = details[1] if details else 0
        if qty > current_stock:
            messagebox.showerror(
                "Stock Error",
                "Stock has changed since this item was added to the cart. "
                "Please review the cart and try again."
            )
            return

    conn = get_connection()
    cursor = conn.cursor()

    try:
        sale_no = repo.generate_sale_no()
        customer_id = repo.fetch_customer_id(customer.get().strip())

        gross = gross_total.get()
        discount_value = discount.get()
        tax_value = tax.get()
        net = net_total.get()

        sale_id = repo.insert_sale_header(
            cursor, sale_no, customer_id,
            gross, 0, discount_value, 0, tax_value, net
        )

        repo.insert_sale_items(cursor, sale_id, cart_items)

        for product_id, _price, qty, _subtotal in cart_items:
            repo.decrement_product_stock(cursor, product_id, qty)

        conn.commit()
        event_bus.publish()

        messagebox.showinfo("Success", f"Sale {sale_no} saved successfully.")

        clear_sale_form(
            customer, product, quantity, sale_price, available_stock,
            cart_tree, gross_total, discount, tax, net_total
        )

    except Exception as e:
        conn.rollback()
        messagebox.showerror("Database Error", str(e))

    finally:
        conn.close()


# =====================================
# Sales History (simple/plain window - no styling, matching the
# "don't touch the window design yet" plan)
# =====================================
def sales_history():

    win = Toplevel()
    win.title("Sales History")
    win.geometry("900x500")

    tree = ttk.Treeview(
        win,
        columns=("id", "sale_no", "customer", "date", "gross", "discount", "tax", "net"),
        show="headings"
    )

    columns = [
        ("id", "ID", 50), ("sale_no", "Sale No", 120), ("customer", "Customer", 150),
        ("date", "Date", 150), ("gross", "Gross", 90), ("discount", "Discount", 90),
        ("tax", "Tax", 90), ("net", "Net Total", 100)
    ]
    for key, text, width in columns:
        tree.heading(key, text=text)
        tree.column(key, width=width)

    tree.pack(fill=BOTH, expand=True, padx=10, pady=10)

    # repo row = (id, sale_no, customer, date, gross, discount, discount_amount, tax, tax_amount, net)
    rows = repo.fetch_sales_history()
    for row in rows:
        tree.insert("", "end", values=(
            row[0], row[1], row[2], row[3], row[4], row[6], row[8], row[9]
        ))