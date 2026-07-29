import sqlite3
from database.database import get_connection


def fetch_suppliers(search_term=None):

    conn = get_connection()
    cursor = conn.cursor()

    base_query = """
        SELECT id, name, contact, email, address, status
        FROM suppliers
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

def fetch_supplier_by_name(name, exclude_id=None):

    conn = get_connection()
    cursor = conn.cursor()

    if exclude_id is None:
        cursor.execute(
            "SELECT id FROM suppliers WHERE LOWER(name) = LOWER(?)",
            (name,)
        )
    else:
        cursor.execute(
            "SELECT id FROM suppliers WHERE LOWER(name) = LOWER(?) AND id != ?",
            (name, exclude_id)
        )

    row = cursor.fetchone()
    conn.close()

    return row

def insert_supplier(name, contact, email, address):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO suppliers(name, contact, email, address)
        VALUES (?, ?, ?, ?)
    """, (name, contact, email, address))

    conn.commit()
    conn.close()

def update_supplier(supplier_id, name, contact, email, address):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE suppliers
        SET name=?, contact=?, email=?, address=?
        WHERE id=?
    """, (name, contact, email, address, supplier_id))

    conn.commit()
    conn.close()

def delete_supplier(supplier_id):
    """
    Returns:
        (True, None)       -> deleted successfully
        (False, "in_use")  -> supplier is referenced by a past purchase,
                               cannot delete
    """
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("DELETE FROM suppliers WHERE id=?", (supplier_id,))
        conn.commit()
        return True, None

    except sqlite3.IntegrityError:
        conn.rollback()
        return False, "in_use"

    finally:
        conn.close()

def set_supplier_status(supplier_id, status):
    """Used for the soft-delete (deactivate) fallback."""

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE suppliers SET status=? WHERE id=?",
        (status, supplier_id)
    )

    conn.commit()
    conn.close()