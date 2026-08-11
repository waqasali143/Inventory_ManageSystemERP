
from database.database import get_connection
import bcrypt

def verify_login(username, password):
    """
    Returns the user's (id, full_name, role) if credentials match,
    otherwise None.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, full_name, role, password
        FROM users
        WHERE username = ? AND status = 'Active'
    """, (username,))

    row = cursor.fetchone()
    conn.close()

    if row is None:
        return None

    user_id, full_name, role, stored_hash = row

    if bcrypt.checkpw(password.encode("utf-8"), stored_hash.encode("utf-8")):
        return (user_id, full_name, role)

    return None
# ======================================================

def update_last_login(user_id):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?
    """, (user_id,))

    conn.commit()
    conn.close()
# =====================================================
def fetch_users():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, full_name, username, role, status
        FROM users
        ORDER BY id DESC
    """)

    rows = cursor.fetchall()
    conn.close()

    return rows

# ===========================================================================
def fetch_user_by_username(username, exclude_id=None):

    conn = get_connection()
    cursor = conn.cursor()

    if exclude_id is None:
        cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
    else:
        cursor.execute(
            "SELECT id FROM users WHERE username = ? AND id != ?",
            (username, exclude_id)
        )

    row = cursor.fetchone()
    conn.close()

    return row

# =====================================================================
def insert_user(full_name, username, password, role):

    conn = get_connection()
    cursor = conn.cursor()

    hashed = hash_password(password)

    cursor.execute("""
        INSERT INTO users(full_name, username, password, role)
        VALUES (?, ?, ?, ?)
    """, (full_name, username, hashed, role))

    conn.commit()
    conn.close()

# =====================================================================
def update_user_status(user_id, status):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("UPDATE users SET status=? WHERE id=?", (status, user_id))

    conn.commit()
    conn.close()
# ================================================
def hash_password(plain_password):
    return bcrypt.hashpw(plain_password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")