import sqlite3
from database.database import get_connection

def fetch_customers(search_term=None):

    conn = get_connection()
    cursor = conn.cursor()

    base_query = """
        SELECT id, name, contact, email, address, status
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

def insert_customer(name, contact, email, address):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO customers(name, contact, email, address)
        VALUES (?, ?, ?, ?)
    """, (name, contact, email, address))

    conn.commit()
    conn.close()

def update_customer(customer_id, name, contact, email, address):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE customers
        SET name=?, contact=?, email=?, address=?
        WHERE id=?
    """, (name, contact, email, address, customer_id))

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
