from tkinter import messagebox
from database.database import get_connection
from repositories import purchase_repository as repo
from datetime import date
from utils import event_bus
# =====================================================================
# This file contains business logic ONLY:
#   - reading form data / validating it
#   - calculating totals
#   - deciding what to save
# It does NOT contain any raw SQL (that's in repositories/purchase_repository.py)
# and it does NOT build any windows (that's in views/purchase.py).
# =====================================================================


# =====================================
# Load Active Suppliers / Products
# (thin wrappers so views/purchase.py only imports from "services",
#  never directly from "repositories")
# =====================================
def load_suppliers():
    return repo.fetch_active_suppliers()

def get_supplier_id_by_name(supplier_name):
    """Resolve a supplier's ID from the name shown in the combobox.

    Same pattern as sales_service.get_customer_id_by_name - reuses the
    repo lookup save_purchase() already relies on, so Purchase can
    fetch the supplier's filer status for tax auto-fill without a
    separate id/name map.
    """
    return repo.fetch_supplier_id(supplier_name)

def load_products():
    return repo.fetch_active_products()

def get_product_cost_price(product_name):
    return repo.fetch_product_cost_price(product_name)

def get_product_stock(product_name):
    return repo.fetch_product_stock(product_name)

def get_purchase_history(search_term=None, date_from=None, date_to=None):
    return repo.fetch_purchase_history(search_term, date_from, date_to)

def get_purchase_header(purchase_id):
    return repo.fetch_purchase_header(purchase_id)

def resolve_purchase_date(purchase_date_str):

    value = purchase_date_str.strip()

    if value == "":
        return date.today().isoformat(), None

    try:
        date.fromisoformat(value)
    except ValueError:
        return None, "Purchase Date must be in YYYY-MM-DD format."

    return value, None

def get_purchase_items(purchase_id):
    return repo.fetch_purchase_items(purchase_id)
# =====================================
# Return History (admin-facing summary of all returns) wrapper
# =====================================
def get_all_purchase_returns(today_only=False):
    return repo.fetch_all_purchase_returns(today_only)
# =====================================
# Supplier-wise Purchase History wrapper
# =====================================
def get_purchases_by_supplier(supplier_id):
    return repo.fetch_purchases_by_supplier(supplier_id)
# =====================================
# Purchase Validation
# =====================================
def validate_purchase(supplier, cart_tree):

    if supplier.get().strip() == "":
        messagebox.showerror(
            "Error",
            "Please select a supplier."
        )
        return False

    if not cart_tree.get_children():
        messagebox.showerror(
            "Error",
            "Purchase cart is empty."
        )
        return False

    return True


# =====================================
# Calculate Purchase Totals
# =====================================
def calculate_purchase_totals(cart_tree, summary):

    gross = 0.0

    for item in cart_tree.get_children():
        values = cart_tree.item(item)["values"]
        gross += float(values[4])

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

    selected = cart_tree.focus()

    if not selected:
        messagebox.showwarning(
            "Warning",
            "Please select an item."
        )
        return

    confirm = messagebox.askyesno(
        "Confirm",
        "Do you want to remove the selected item?"
    )
    if not confirm:
        return

    cart_tree.delete(selected)

    calculate_purchase_totals(cart_tree, summary)

# =====================================
# Clear Cart
# =====================================
def clear_cart(cart_tree, summary):

    if not cart_tree.get_children():
        messagebox.showwarning(
            "Warning",
            "Cart is already empty."
        )
        return

    confirm = messagebox.askyesno(
        "Confirm",
        "Do you want to clear the cart?"
    )
    if not confirm:
        return

    for item in cart_tree.get_children():
        cart_tree.delete(item)

    summary.reset()

# =====================================
# Clear Purchase Form
# =====================================
def clear_purchase_form(supplier, cart_tree, summary):

    supplier.set("")

    for item in cart_tree.get_children():
        cart_tree.delete(item)

    summary.reset()

# =====================================
# Read Cart Items out of the Treeview
# into plain tuples the repository layer can save
# =====================================
def _extract_cart_items(cart_tree):

    items = []

    for item in cart_tree.get_children():

        values = cart_tree.item(item, "values")

        product_id = int(values[0])
        purchase_price = float(values[2])
        quantity = int(values[3])
        subtotal = float(values[4])

        items.append((product_id, purchase_price, quantity, subtotal))

    return items

# =====================================
# Save Purchase
# (orchestrates: validate -> generate no -> save header -> save items
#  -> update stock -> commit)
# =====================================
def save_purchase(supplier, invoice_no, purchase_date, cart_tree, summary,
                   payment_type=None, amount_paid_str=None):

    if not validate_purchase(supplier, cart_tree):
        return

    resolved_date, error = resolve_purchase_date(purchase_date.get())
    if error:
        messagebox.showerror("Error", error)
        return

    supplier_name = supplier.get().strip()

    gross, discount, discount_amount, tax, tax_amount, net_total = summary.as_floats()

    # payment_type/amount_paid_str are optional so save_purchase still
    # works from any caller that hasn't been updated for Credit yet -
    # defaults to a fully-paid Cash purchase, same as before this
    # feature existed.
    is_credit = payment_type is not None and payment_type.get() == "Credit"

    if is_credit:
        try:
            amount_paid = float(amount_paid_str.get()) if amount_paid_str else 0.0
        except ValueError:
            messagebox.showerror("Error", "Amount Paid must be a number.")
            return

        if amount_paid < 0 or amount_paid > net_total:
            messagebox.showerror(
                "Error", "Amount Paid must be between 0 and the Net Total."
            )
            return

        payment_status = "Paid" if amount_paid >= net_total else \
                          ("Partial" if amount_paid > 0 else "Credit")
    else:
        amount_paid = net_total
        payment_status = "Paid"

    conn = get_connection()
    cursor = conn.cursor()

    try:
        purchase_no = repo.generate_purchase_no()
        supplier_id = repo.fetch_supplier_id(supplier_name)

        purchase_id = repo.insert_purchase_header(
            cursor,
            purchase_no,
            invoice_no.get().strip(),
            supplier_id,
            resolved_date,
            gross,
            discount,
            discount_amount,
            tax,
            tax_amount,
            net_total,
            payment_status,
            amount_paid
        )

        cart_items = _extract_cart_items(cart_tree)
        repo.insert_purchase_items(cursor, purchase_id, cart_items)

        # cost_price is meant to reflect the true "landed cost" per unit
        # - what this item actually cost the business, including its
        # proportional share of the invoice's tax (a real added cost)
        # and net of its share of any discount received (a real
        # reduction) - not just the raw negotiated purchase price.
        # purchase_items.purchase_price above keeps recording the raw
        # price actually invoiced, unchanged - this only affects the
        # product's cost basis used for COGS/profit going forward.
        for product_id, purchase_price, quantity, subtotal in cart_items:
            repo.increment_product_stock(cursor, product_id, quantity)

            if gross > 0:
                allocated_discount = (subtotal / gross) * discount_amount
                allocated_tax = (subtotal / gross) * tax_amount
            else:
                allocated_discount = 0.0
                allocated_tax = 0.0

            landed_cost_total = subtotal - allocated_discount + allocated_tax
            landed_cost_per_unit = landed_cost_total / quantity if quantity else purchase_price

            repo.update_product_cost_price(cursor, product_id, landed_cost_per_unit)

        clear_purchase_form(supplier, cart_tree, summary)
        invoice_no.set("")
        if amount_paid_str is not None:
            amount_paid_str.set("0")

        conn.commit()
        event_bus.publish()
        
        messagebox.showinfo("Success", f"Purchase {purchase_no} saved successfully.")

    except Exception as e:
        conn.rollback()
        messagebox.showerror("Database Error", str(e))

    finally:
        conn.close()
        
# =====================================
# Purchase Returns
# =====================================
def get_purchase_items_for_return(purchase_id):
    return repo.fetch_purchase_items_for_return(purchase_id)


def get_returns_for_purchase(purchase_id):
    return repo.fetch_returns_for_purchase(purchase_id)


def validate_purchase_return(product_id, return_qty, original_qty, already_returned):

    if return_qty <= 0:
        messagebox.showerror("Validation Error", "Return quantity must be greater than zero.")
        return False

    remaining = original_qty - already_returned

    if return_qty > remaining:
        messagebox.showerror(
            "Validation Error",
            f"Cannot return more than {remaining} unit(s) - "
            f"{already_returned} already returned out of {original_qty} purchased."
        )
        return False

    return True

# =====================================
# Process Purchase Return
# (saves the return record, and removes the stock)
# =====================================
def process_purchase_return(purchase_id, product_id, return_qty, reason,
                             original_qty, already_returned):

    if not validate_purchase_return(product_id, return_qty, original_qty, already_returned):
        return False

    conn = get_connection()
    cursor = conn.cursor()

    try:
        repo.insert_purchase_return(cursor, purchase_id, product_id, return_qty, reason)
        repo.decrement_product_stock(cursor, product_id, return_qty)

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