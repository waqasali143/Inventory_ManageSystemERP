
from database.database import get_connection

ALL_SECTIONS = [
    ("products", "Products"),
    ("customers", "Customers"),
    ("suppliers", "Suppliers"),
    ("sales", "Sales"),
    ("purchase", "Purchase"),
    ("expenses", "Expenses"),
    ("users", "User Management"),
    ("business_settings", "Business Settings"),
    ("reports", "Reports & History"),
    ("credit", "Credit Ledger"),
]

def fetch_roles():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id, name FROM roles ORDER BY name")
    rows = cursor.fetchall()
    conn.close()

    return rows

def fetch_role_by_name(name):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM roles WHERE name = ?", (name,))
    row = cursor.fetchone()
    conn.close()

    return row[0] if row else None

def fetch_permissions_for_role(role_id):
    """Returns a set of section-keys this role is allowed to access."""

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT section FROM role_permissions WHERE role_id = ?", (role_id,))
    rows = cursor.fetchall()
    conn.close()

    return {row[0] for row in rows}

def fetch_permissions_for_role_name(role_name):
    """Convenience: look up permissions directly by role name (what
    the logged-in user's session actually stores)."""

    role_id = fetch_role_by_name(role_name)
    if role_id is None:
        return set()

    return fetch_permissions_for_role(role_id)

def insert_role(name, sections):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("INSERT INTO roles(name) VALUES (?)", (name,))
    role_id = cursor.lastrowid

    for section in sections:
        cursor.execute(
            "INSERT INTO role_permissions(role_id, section) VALUES (?, ?)",
            (role_id, section)
        )

    conn.commit()
    conn.close()

def update_role_permissions(role_id, sections):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM role_permissions WHERE role_id = ?", (role_id,))

    for section in sections:
        cursor.execute(
            "INSERT INTO role_permissions(role_id, section) VALUES (?, ?)",
            (role_id, section)
        )

    conn.commit()
    conn.close()

def delete_role(role_id):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM roles WHERE id = ?", (role_id,))

    conn.commit()
    conn.close()