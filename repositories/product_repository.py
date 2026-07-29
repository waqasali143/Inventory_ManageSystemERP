
import sqlite3
from database.database import get_connection

def fetch_products(search_term=None):

    conn = get_connection()
    cursor = conn.cursor()

    base_query = """
        SELECT id, name, cost_price, sale_price, quantity, status
        FROM products
    """

    if search_term:
        cursor.execute(
            base_query + " WHERE name LIKE ? ORDER BY id DESC",
            ("%" + search_term + "%",)
        )
    else:
        cursor.execute(base_query + " ORDER BY id DESC")

    rows = cursor.fetchall()
    conn.close()

    return rows

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

def insert_product(name, cost_price, sale_price, quantity, status):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO products(name, cost_price, sale_price, quantity, status)
        VALUES (?, ?, ?, ?, ?)
    """, (name, cost_price, sale_price, quantity, status))

    conn.commit()
    conn.close()

def update_product(product_id, name, cost_price, sale_price, quantity, status):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE products
        SET name=?, cost_price=?, sale_price=?, quantity=?, status=?
        WHERE id=?
    """, (name, cost_price, sale_price, quantity, status, product_id))

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