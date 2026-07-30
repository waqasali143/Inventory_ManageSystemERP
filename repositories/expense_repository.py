from database.database import get_connection


def fetch_expenses(search_term=None):

    conn = get_connection()
    cursor = conn.cursor()

    base_query = """
        SELECT id, category, description, amount, expense_date
        FROM expenses
    """

    if search_term:
        cursor.execute(
            base_query + " WHERE category LIKE ? ORDER BY id DESC",
            ("%" + search_term + "%",)
        )
    else:
        cursor.execute(base_query + " ORDER BY id DESC")

    rows = cursor.fetchall()
    conn.close()

    return rows
# ==========================================================================
def insert_expense(category, description, amount, expense_date):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO expenses(category, description, amount, expense_date)
        VALUES (?, ?, ?, ?)
    """, (category, description, amount, expense_date))

    conn.commit()
    conn.close()
# ============================================================================
def update_expense(expense_id, category, description, amount, expense_date):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE expenses
        SET category=?, description=?, amount=?, expense_date=?
        WHERE id=?
    """, (category, description, amount, expense_date, expense_id))

    conn.commit()
    conn.close()
# =====================================================================
def delete_expense(expense_id):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM expenses WHERE id=?", (expense_id,))

    conn.commit()
    conn.close()