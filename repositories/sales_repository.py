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
        WHERE status='Active'
        ORDER BY name
    """)

    products = cursor.fetchall()
    conn.close()

    return products


def fetch_product_details(product_id):
    """Returns (sale_price, quantity) for a product."""

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT sale_price, quantity
        FROM products
        WHERE id = ?
    """, (product_id,))

    row = cursor.fetchone()
    conn.close()

    return row


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


def insert_sale_header(
        cursor,
        sale_no,
        customer_id,
        gross_total,
        discount,
        discount_amount,
        tax,
        tax_amount,
        net_total
    ):

    cursor.execute("""
        INSERT INTO sales(
            sale_no, customer_id, sale_date,
            gross_total, discount, discount_amount,
            tax, tax_amount, net_total
        )
        VALUES (?, ?, datetime('now'), ?, ?, ?, ?, ?, ?)
    """, (
        sale_no, customer_id,
        gross_total, discount, discount_amount,
        tax, tax_amount, net_total
    ))

    return cursor.lastrowid


def insert_sale_items(cursor, sale_id, items):
    """items: list of tuples -> (product_id, sale_price, quantity, subtotal)"""

    for product_id, sale_price, quantity, subtotal in items:
        cursor.execute("""
            INSERT INTO sale_items(
                sale_id, product_id, sale_price, quantity, subtotal
            )
            VALUES (?, ?, ?, ?, ?)
        """, (sale_id, product_id, sale_price, quantity, subtotal))


def decrement_product_stock(cursor, product_id, quantity):

    cursor.execute("""
        UPDATE products
        SET quantity = quantity - ?
        WHERE id = ?
    """, (quantity, product_id))
# =====================================================
# History Details Function
# =====================================================
def fetch_sales_history(search_term=None):

    conn = get_connection()
    cursor = conn.cursor()

    base_query = """
        SELECT
            s.id, s.sale_no, c.name, s.sale_date,
            s.gross_total, s.discount, s.discount_amount,
            s.tax, s.tax_amount, s.net_total
        FROM sales s
        INNER JOIN customers c ON s.customer_id = c.id
    """

    if search_term:
        cursor.execute(
            base_query + " WHERE s.sale_no LIKE ? ORDER BY s.id DESC",
            ("%" + search_term + "%",)
        )
    else:
        cursor.execute(base_query + " ORDER BY s.id DESC")

    rows = cursor.fetchall()
    conn.close()

    return rows


def fetch_sale_header(sale_id):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            s.sale_no, c.name, s.sale_date,
            s.gross_total, s.discount, s.discount_amount,
            s.tax, s.tax_amount, s.net_total
        FROM sales s
        INNER JOIN customers c ON s.customer_id = c.id
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