
from database.database import get_connection

def fetch_setting(key, default=None):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT value FROM settings WHERE key = ?
    """, (key,))

    row = cursor.fetchone()
    conn.close()

    if row:
        return row[0]
    return default

def save_setting(key, value):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO settings(key, value) VALUES (?, ?)
        ON CONFLICT(key) DO UPDATE SET value = excluded.value
    """, (key, value))

    conn.commit()
    conn.close()