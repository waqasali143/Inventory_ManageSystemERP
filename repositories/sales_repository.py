from database.database import get_connection

# =====================================================================
# Sales module's data layer - only talks to the database.
# =====================================================================

def fetch_active_customers():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT name FROM customers
        WHERE status='Active'
        ORDER BY name
    """)

    customers = [row[0] for row in cursor.fetchall()]
    conn.close()

    return customers


def fetch_active_products():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, name FROM products
        WHERE status != 'Inactive'
        ORDER BY name
    """)

    products = cursor.fetchall()
    conn.close()

    return products
# =====================================================================
def fetch_product_details(product_id):
    """Returns (sale_price, quantity, cost_price) for a product."""

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT sale_price, quantity, cost_price
        FROM products
        WHERE id = ?
    """, (product_id,))

    row = cursor.fetchone()
    conn.close()

    return row
# =============================================================================
def fetch_customer_id(customer_name):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id FROM customers WHERE name = ?
    """, (customer_name,))

    row = cursor.fetchone()
    conn.close()

    if row:
        return row[0]
    return None
# =======================================================
def generate_sale_no():
    """MAX(id)+1 instead of COUNT(*) - COUNT breaks (produces a
    duplicate Sale No) if any sale row was ever deleted."""

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT MAX(id) FROM sales")
    result = cursor.fetchone()
    conn.close()

    next_id = 1 if result[0] is None else result[0] + 1
    return f"SAL-{next_id:06d}"


# =====================================================================

def insert_sale_header(
        cursor,
        sale_no,
        customer_id,
        gross_total,
        discount,
        discount_amount,
        tax,
        tax_amount,
        net_total,
        payment_status="Paid",
        amount_paid=None
    ):

    if amount_paid is None:
        amount_paid = net_total  # Cash sale - fully paid by default

    cursor.execute("""
        INSERT INTO sales(
            sale_no,
            customer_id,
            sale_date,
            gross_total,
            discount,
            discount_amount,
            tax,
            tax_amount,
            net_total,
            payment_status,
            amount_paid
        )
        VALUES(?, ?, datetime('now'), ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        sale_no,
        customer_id,
        gross_total,
        discount,
        discount_amount,
        tax,
        tax_amount,
        net_total,
        payment_status,
        amount_paid
    ))

    return cursor.lastrowid

# ====================================================================================
def insert_sale_items(cursor, sale_id, items):
    """items: list of tuples -> (product_id, sale_price, cost_price, quantity, subtotal)"""

    for product_id, sale_price, cost_price, quantity, subtotal in items:
        cursor.execute("""
            INSERT INTO sale_items(
                sale_id, product_id, sale_price, cost_price, quantity, subtotal
            )
            VALUES (?, ?, ?, ?, ?, ?)
        """, (sale_id, product_id, sale_price, cost_price, quantity, subtotal))
# ----------------------------------------------------------------------------------------
def decrement_product_stock(cursor, product_id, quantity):

    cursor.execute("""
        UPDATE products
        SET quantity = quantity - ?
        WHERE id = ?
    """, (quantity, product_id))
# =====================================================
# History Details Function
# =====================================================
def fetch_sales_history(search_term=None, date_from=None, date_to=None):

    conn = get_connection()
    cursor = conn.cursor()

    base_query = """
        SELECT
            s.id,
            s.sale_no,
            c.name,
            s.sale_date,
            s.gross_total,
            s.discount,
            s.discount_amount,
            s.tax,
            s.tax_amount,
            s.net_total,
            COALESCE((
                SELECT SUM(si.quantity)
                FROM sale_items si
                WHERE si.sale_id = s.id
            ), 0) AS total_quantity,
            COALESCE((
                SELECT SUM(sr.quantity)
                FROM sale_returns sr
                WHERE sr.sale_id = s.id
            ), 0) AS returned_qty,
            s.payment_status,
            s.amount_paid,
            (s.net_total - s.amount_paid) AS balance_due
        FROM sales s
        INNER JOIN customers c
            ON s.customer_id = c.id
    """
    conditions = []
    params = []

    if search_term:
        conditions.append("s.sale_no LIKE ?")
        params.append("%" + search_term + "%")

    if date_from and date_to:
        conditions.append("date(s.sale_date) BETWEEN ? AND ?")
        params.append(date_from)
        params.append(date_to)

    if conditions:
        base_query += " WHERE " + " AND ".join(conditions)

    base_query += " ORDER BY s.id DESC"

    cursor.execute(base_query, params)
    rows = cursor.fetchall()
    conn.close()

    return rows

# =================================================================

def fetch_sale_header(sale_id):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            s.sale_no,
            c.name,
            s.sale_date,
            s.gross_total,
            s.discount,
            s.discount_amount,
            s.tax,
            s.tax_amount,
            s.net_total,
            s.payment_status,
            s.amount_paid
        FROM sales s
        INNER JOIN customers c
            ON s.customer_id = c.id
        WHERE s.id = ?
    """, (sale_id,))

    row = cursor.fetchone()
    conn.close()

    return row


def fetch_sale_items(sale_id):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT p.name, si.sale_price, si.quantity, si.subtotal
        FROM sale_items si
        INNER JOIN products p ON si.product_id = p.id
        WHERE si.sale_id = ?
        ORDER BY si.id
    """, (sale_id,))

    rows = cursor.fetchall()
    conn.close()

    return rows
# =====================================
# Sale Returns
# =====================================
def fetch_sale_items_for_return(sale_id):
    """
    Returns each sold line for this sale along with how much of it
    has already been returned before - so the UI can show/limit the
    maximum quantity that can still be returned.
    """

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            si.product_id,
            p.name,
            si.quantity,
            COALESCE((
                SELECT SUM(sr.quantity)
                FROM sale_returns sr
                WHERE sr.sale_id = si.sale_id
                  AND sr.product_id = si.product_id
            ), 0) AS already_returned
        FROM sale_items si
        INNER JOIN products p ON si.product_id = p.id
        WHERE si.sale_id = ?
        ORDER BY si.id
    """, (sale_id,))

    rows = cursor.fetchall()
    conn.close()

    return rows


def insert_sale_return(cursor, sale_id, product_id, quantity, reason):

    cursor.execute("""
        INSERT INTO sale_returns(sale_id, product_id, quantity, reason)
        VALUES (?, ?, ?, ?)
    """, (sale_id, product_id, quantity, reason))

    return cursor.lastrowid


def increment_product_stock(cursor, product_id, quantity):
    """Adds returned quantity back into stock."""

    cursor.execute("""
        UPDATE products
        SET quantity = quantity + ?
        WHERE id = ?
    """, (quantity, product_id))


def fetch_returns_for_sale(sale_id):
    """Used to display return history for a specific sale."""

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT p.name, sr.quantity, sr.reason, sr.return_date
        FROM sale_returns sr
        INNER JOIN products p ON sr.product_id = p.id
        WHERE sr.sale_id = ?
        ORDER BY sr.id
    """, (sale_id,))

    rows = cursor.fetchall()
    conn.close()

    return rows
# =============================================
# ===== Return Details  ==========
# =============================================
def fetch_all_sale_returns(today_only=False):

    conn = get_connection()
    cursor = conn.cursor()

    base_query = """
        SELECT
            sr.return_date,
            s.sale_no,
            p.name,
            sr.quantity,
            sr.reason
        FROM sale_returns sr
        INNER JOIN sales s ON sr.sale_id = s.id
        INNER JOIN products p ON sr.product_id = p.id
    """

    if today_only:
        cursor.execute(
            base_query + " WHERE date(sr.return_date) = date('now') ORDER BY sr.id DESC"
        )
    else:
        cursor.execute(base_query + " ORDER BY sr.id DESC")

    rows = cursor.fetchall()
    conn.close()

    return rows
# =========================================================
def fetch_sales_by_customer(customer_id):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            s.id, s.sale_no, s.sale_date,
            s.gross_total, s.discount_amount, s.tax_amount, s.net_total,
            s.payment_status, (s.net_total - s.amount_paid) AS balance_due
        FROM sales s
        WHERE s.customer_id = ?
        ORDER BY s.id DESC
    """, (customer_id,))

    rows = cursor.fetchall()
    conn.close()

    return rows