
import sqlite3
from database.database import get_connection

def fetch_products(search_term=None):

    conn = get_connection()
    cursor = conn.cursor()

    base_query = """
        SELECT id, name, cost_price, sale_price, quantity, status, barcode
        FROM products
    """

    if search_term:
        cursor.execute(
            base_query + " WHERE name LIKE ? OR barcode LIKE ? ORDER BY id DESC",
            ("%" + search_term + "%", "%" + search_term + "%")
        )
    else:
        cursor.execute(base_query + " ORDER BY id DESC")

    rows = cursor.fetchall()
    conn.close()

    return rows
# -----------------------------------------------------------------------------------------
def fetch_product_by_name(name, exclude_id=None):

    conn = get_connection()
    cursor = conn.cursor()

    if exclude_id is None:
        cursor.execute(
            "SELECT id FROM products WHERE LOWER(name) = LOWER(?)",
            (name,)
        )
    else:
        cursor.execute(
            "SELECT id FROM products WHERE LOWER(name) = LOWER(?) AND id != ?",
            (name, exclude_id)
        )

    row = cursor.fetchone()
    conn.close()

    return row

def insert_product(name, cost_price, sale_price, quantity, status, barcode=""):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO products(name, cost_price, sale_price, quantity, status, barcode)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (name, cost_price, sale_price, quantity, status, barcode))

    conn.commit()
    conn.close()

def update_product(product_id, name, cost_price, sale_price, quantity, status, barcode=""):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE products
        SET name=?, cost_price=?, sale_price=?, quantity=?, status=?, barcode=?
        WHERE id=?
    """, (name, cost_price, sale_price, quantity, status, barcode, product_id))

    conn.commit()
    conn.close()

def delete_product(product_id):
    """
    Returns:
        (True, None)       -> deleted successfully
        (False, "in_use")  -> product is referenced by a past
                               purchase/sale, cannot delete
    """
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("DELETE FROM products WHERE id=?", (product_id,))
        conn.commit()
        return True, None

    except sqlite3.IntegrityError:
        conn.rollback()
        return False, "in_use"

    finally:
        conn.close()

def set_product_status(product_id, status):
    """Used for the soft-delete (deactivate) fallback."""

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE products SET status=? WHERE id=?",
        (status, product_id)
    )

    conn.commit()
    conn.close()
# ====================================================================

def bulk_insert_products(products):
    """
    products: list of tuples (name, cost_price, sale_price, quantity, status)
    Skips any product whose name already exists (case-insensitive).
    Returns (inserted_count, skipped_names)
    """
    conn = get_connection()
    cursor = conn.cursor()

    inserted = 0
    skipped = []

    for name, cost_price, sale_price, quantity, status in products:
        cursor.execute(
            "SELECT id FROM products WHERE LOWER(name) = LOWER(?)", (name,)
        )
        if cursor.fetchone():
            skipped.append(name)
            continue

        cursor.execute("""
            INSERT INTO products(name, cost_price, sale_price, quantity, status)
            VALUES (?, ?, ?, ?, ?)
        """, (name, cost_price, sale_price, quantity, status))
        inserted += 1

    conn.commit()
    conn.close()

    return inserted, skipped
# ----------------------------------------------------------------------------------
# = = =  Find Product with Scan = = =

def fetch_product_by_barcode(barcode):
    """Used for scan-to-add: looks up a product by its exact barcode."""

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, name, cost_price, sale_price, quantity, status, barcode
        FROM products
        WHERE barcode = ? AND barcode != ''
    """, (barcode,))

    row = cursor.fetchone()
    conn.close()

    return row


def fetch_product_by_barcode_unique_check(barcode, exclude_id=None):
    """Used to prevent two products from sharing the same barcode."""

    if not barcode:
        return None

    conn = get_connection()
    cursor = conn.cursor()

    if exclude_id is None:
        cursor.execute("SELECT id FROM products WHERE barcode = ?", (barcode,))
    else:
        cursor.execute(
            "SELECT id FROM products WHERE barcode = ? AND id != ?",
            (barcode, exclude_id)
        )

    row = cursor.fetchone()
    conn.close()

    return row