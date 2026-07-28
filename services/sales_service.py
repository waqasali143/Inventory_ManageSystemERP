
import sqlite3

from tkinter import messagebox
from repositories import sales_repository as repo
from database.database import get_connection
from utils import event_bus
# =====================================
# Load Customers
# =====================================

def load_customers():
    return repo.fetch_active_customers()


def load_products():
    return repo.fetch_active_products()


def get_product_details(product_id):
    """Returns (sale_price, stock) for the selected product."""
    return repo.fetch_product_details(product_id)


# =====================================
# Validate Sale Line (before adding to cart)
# =====================================
def validate_sale_line(customer, product, quantity, available_stock):

    if customer.get() == "":
        messagebox.showerror("Validation Error", "Please select customer.")
        return False

    if product.get() == "":
        messagebox.showerror("Validation Error", "Please select product.")
        return False

    if quantity.get() <= 0:
        messagebox.showerror("Validation Error", "Quantity must be greater than zero.")
        return False

    if quantity.get() > available_stock.get():
        messagebox.showerror("Stock Error", "Insufficient stock available.")
        return False

    return True
# =====================================
# Calculate Sale Totals
# =====================================
def calculate_sale_totals(cart_tree, summary):

    gross = 0.0

    for item in cart_tree.get_children():
        values = cart_tree.item(item)["values"]
        gross += float(values[4])   # subtotal column (product_id, product, price, qty, subtotal)

    summary.gross_total.set(f"{gross:.2f}")

    try:
        discount_percent = float(summary.discount.get())
    except ValueError:
        discount_percent = 0.0

    discount_value = gross * discount_percent / 100
    summary.discount_amount.set(f"{discount_value:.2f}")

    subtotal = gross - discount_value

    try:
        tax_percent = float(summary.tax.get())
    except ValueError:
        tax_percent = 0.0

    tax_value = subtotal * tax_percent / 100
    summary.tax_amount.set(f"{tax_value:.2f}")

    final_total = subtotal + tax_value
    summary.net_total.set(f"{final_total:.2f}")
# =====================================
# Remove Cart Item
# =====================================
def remove_cart_item(cart_tree, summary):

    selected = cart_tree.selection()
    if not selected:
        messagebox.showerror("Selection Error", "Please select an item.")
        return

    cart_tree.delete(selected[0])
    calculate_sale_totals(cart_tree, summary)

# =====================================
# Clear Cart
# =====================================
def clear_cart(cart_tree, summary):
    for item in cart_tree.get_children():
        cart_tree.delete(item)
    summary.reset()

# =====================================
# Clear Sale Form
# =====================================
def clear_sale_form(customer, product, quantity, sale_price, available_stock, cart_tree, summary):
    clear_cart(cart_tree, summary)
    customer.set("")
    product.set("")
    quantity.set(1)
    sale_price.set(0)
    available_stock.set(0)

# =====================================
# Extract cart rows into plain tuples for saving
# (cart columns: product_id, product, price, qty, subtotal)
# =====================================
def _extract_cart_items(cart_tree):

    items = []

    for item in cart_tree.get_children():
        values = cart_tree.item(item, "values")

        product_id = int(values[0])
        sale_price = float(values[2])
        quantity = int(values[3])
        subtotal = float(values[4])

        items.append((product_id, sale_price, quantity, subtotal))

    return items

# =====================================
# Save Sale
# Re-checks live stock right before committing, since time may have
# passed since the item was added to the cart.
# =====================================
def save_sale(customer, cart_tree, summary):

    if customer.get().strip() == "":
        messagebox.showerror("Error", "Please select a customer.")
        return False

    if not cart_tree.get_children():
        messagebox.showerror("Error", "Sales cart is empty.")
        return False

    cart_items = _extract_cart_items(cart_tree)

    for product_id, _price, quantity, _subtotal in cart_items:
        details = repo.fetch_product_details(product_id)
        current_stock = details[1] if details else 0

        if quantity > current_stock:
            messagebox.showerror(
                "Stock Error",
                "Stock has changed since this item was added to the cart. "
                "Please review the cart and try again."
            )
            return False

    conn = get_connection()
    cursor = conn.cursor()

    try:
        sale_no = repo.generate_sale_no()
        customer_id = repo.fetch_customer_id(customer.get().strip())

        gross, discount, discount_amount, tax, tax_amount, net_total = summary.as_floats()

        sale_id = repo.insert_sale_header(
            cursor, sale_no, customer_id,
            gross, discount, discount_amount, tax, tax_amount, net_total
        )

        repo.insert_sale_items(cursor, sale_id, cart_items)

        for product_id, _price, quantity, _subtotal in cart_items:
            repo.decrement_product_stock(cursor, product_id, quantity)

        conn.commit()

        event_bus.publish()

        messagebox.showinfo("Success", f"Sale {sale_no} saved successfully.")
        return True

    except Exception as e:
        conn.rollback()
        messagebox.showerror("Database Error", str(e))
        return False

    finally:
        conn.close()
# =====================================
# Sale Returns
# =====================================
def get_sale_items_for_return(sale_id):
    return repo.fetch_sale_items_for_return(sale_id)


def get_returns_for_sale(sale_id):
    return repo.fetch_returns_for_sale(sale_id)


def validate_return(sale_id, product_id, return_qty, original_qty, already_returned):

    if return_qty <= 0:
        messagebox.showerror("Validation Error", "Return quantity must be greater than zero.")
        return False

    remaining = original_qty - already_returned

    if return_qty > remaining:
        messagebox.showerror(
            "Validation Error",
            f"Cannot return more than {remaining} unit(s) - "
            f"{already_returned} already returned out of {original_qty} sold."
        )
        return False

    return True

# =====================================
# Process Sale Return
# (saves the return record, and adds the stock back)
# =====================================
def process_sale_return(sale_id, product_id, return_qty, reason,
                         original_qty, already_returned):

    if not validate_return(sale_id, product_id, return_qty, 
                           original_qty, already_returned):
        return False

    conn = get_connection()
    cursor = conn.cursor()

    try:
        repo.insert_sale_return(cursor, sale_id, product_id, return_qty, reason)
        repo.increment_product_stock(cursor, product_id, return_qty)

        conn.commit()

        event_bus.publish()

        messagebox.showinfo("Success", "Return processed and stock updated.")
        return True

    except Exception as e:
        conn.rollback()
        messagebox.showerror("Database Error", str(e))
        return False

    finally:
        conn.close()
# =====================================
# Thin wrappers for history/details (so views never import
# repositories directly)
# =====================================
def get_sales_history(search_term=None):
    return repo.fetch_sales_history(search_term)

def get_sale_header(sale_id):
    return repo.fetch_sale_header(sale_id)

def get_sale_items(sale_id):
    return repo.fetch_sale_items(sale_id)
# =====================================
# Return History (admin-facing summary of all returns)
# =====================================
def get_all_sale_returns(today_only=False):
    return repo.fetch_all_sale_returns(today_only)

