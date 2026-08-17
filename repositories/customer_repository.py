import sqlite3
from database.database import get_connection

def fetch_customer_id_by_name_and_contact(name, contact):
    """
    Matches on Name AND Contact together, not name alone - two different
    real customers can share the same name, so name-only matching risks
    silently attributing a sale to the wrong person. Used by POS's
    walk-in flow, where a new customer is captured inline rather than
    picked from an existing registered list.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT id FROM customers WHERE LOWER(name) = LOWER(?) AND contact = ?",
        (name, contact)
    )
    row = cursor.fetchone()
    conn.close()

    return row[0] if row else None


def fetch_customers(search_term=None):

    conn = get_connection()
    cursor = conn.cursor()

    base_query = """
        SELECT id, name, contact, email, address, status, ntn, is_filer
        FROM customers
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

def insert_customer(name, contact, email, address, ntn="", is_filer=0):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO customers(name, contact, email, address, ntn, is_filer)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (name, contact, email, address, ntn, is_filer))

    new_id = cursor.lastrowid

    conn.commit()
    conn.close()

    return new_id

def update_customer(customer_id, name, contact, email, address, ntn="", is_filer=0):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE customers
        SET name=?, contact=?, email=?, address=?, ntn=?, is_filer=?
        WHERE id=?
    """, (name, contact, email, address, ntn, is_filer, customer_id))

    conn.commit()
    conn.close()

def delete_customer(customer_id):
    """
    Returns:
        (True, None)       -> deleted successfully
        (False, "in_use")  -> customer is referenced by a past sale,
                               cannot delete
    """
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("DELETE FROM customers WHERE id=?", (customer_id,))
        conn.commit()
        return True, None

    except sqlite3.IntegrityError:
        conn.rollback()
        return False, "in_use"

    finally:
        conn.close()

def set_customer_status(customer_id, status):
    """Used for the soft-delete (deactivate) fallback."""

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE customers SET status=? WHERE id=?",
        (status, customer_id)
    )

    conn.commit()
    conn.close()
# -----------------------------------------------------------
# = = = = This function use for Sales Window = = = =
# ==========================================================
def fetch_customer_filer_status(customer_id):
    """Returns True if the customer is a Filer, False otherwise."""

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT is_filer FROM customers WHERE id = ?", (customer_id,))
    row = cursor.fetchone()
    conn.close()

    return bool(row[0]) if row else False
# ==========================================================================================
def fetch_customer_ntn(customer_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT ntn
        FROM customers
        WHERE id = ?
    """, (customer_id,))

    row = cursor.fetchone()
    conn.close()

    return row[0] if row else ""