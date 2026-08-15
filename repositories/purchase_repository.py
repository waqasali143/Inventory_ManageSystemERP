from database.database import get_connection

# =====================================================================
# This file only talks to the database (raw SQL). It knows nothing
# about Tkinter, StringVars, or Treeview widgets. Every function here
# takes plain Python values in and returns plain Python values out.
# =====================================================================


# =====================================
# Load Active Suppliers
# =====================================
def fetch_active_suppliers():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT name
        FROM suppliers
        WHERE status='Active'
        ORDER BY name
    """)

    suppliers = [row[0] for row in cursor.fetchall()]

    conn.close()

    return suppliers

# =====================================
# Load Active Products
# =====================================
def fetch_active_products():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, name
        FROM products
        WHERE status != 'Inactive'
        ORDER BY name
    """)

    products = cursor.fetchall()

    conn.close()

    return products

# =====================================
# Get Supplier ID
# =====================================
def fetch_supplier_id(supplier_name):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id
        FROM suppliers
        WHERE name = ?
    """, (
        supplier_name,
    ))

    row = cursor.fetchone()

    conn.close()

    if row is None:
        return None

    return row[0]


# =====================================
# Get Product Cost Price
# =====================================
def fetch_product_cost_price(product_name):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT cost_price
        FROM products
        WHERE name = ?
    """, (
        product_name,
    ))

    row = cursor.fetchone()

    conn.close()

    if row:
        return row[0]

    return ""

# =====================================
# Generate Purchase Number
# =====================================
def generate_purchase_no():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT MAX(id)
        FROM purchases
    """)

    result = cursor.fetchone()

    conn.close()

    if result[0] is None:
        next_id = 1
    else:
        next_id = result[0] + 1

    return f"PUR-{next_id:06d}"

# =====================================
# Insert Purchase Header
# (cursor is passed in so the caller controls the transaction/commit)
# =====================================
def insert_purchase_header(
        cursor,
        purchase_no,
        invoice_no,
        supplier_id,
        purchase_date,
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
        amount_paid = net_total  # Cash purchase - fully paid by default

    cursor.execute("""
        INSERT INTO purchases(
            purchase_no,
            invoice_no,
            supplier_id,
            purchase_date,
            gross_total,
            discount,
            discount_amount,
            tax,
            tax_amount,
            net_total,
            payment_status,
            amount_paid
        )
        VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        purchase_no,
        invoice_no,
        supplier_id,
        purchase_date,
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

# =====================================
# Insert Purchase Items
# items: list of tuples -> (product_id, purchase_price, quantity, subtotal)
# =====================================
def insert_purchase_items(cursor, purchase_id, items):

    for product_id, purchase_price, quantity, subtotal in items:

        cursor.execute("""
            INSERT INTO purchase_items(
                purchase_id,
                product_id,
                purchase_price,
                quantity,
                subtotal
            )
            VALUES(?, ?, ?, ?, ?)
        """, (
            purchase_id,
            product_id,
            purchase_price,
            quantity,
            subtotal
        ))


# =====================================
# Increase Product Stock
# =====================================
def increment_product_stock(cursor, product_id, quantity):

    cursor.execute("""
        UPDATE products
        SET quantity = quantity + ?
        WHERE id = ?
    """, (
        quantity,
        product_id
    ))

# =====================================
# Update Product Cost Price
# (called from save_purchase - freezes the latest purchase price
#  as the product's current cost, same as sale_price is on Sales)
# =====================================
def update_product_cost_price(cursor, product_id, cost_price):

    cursor.execute("""
        UPDATE products
        SET cost_price = ?
        WHERE id = ?
    """, (
        cost_price,
        product_id
    ))

# =====================================
# Fetch Purchase History
# (search_term=None -> all rows, otherwise filters by purchase_no)
# =====================================
def fetch_purchase_history(search_term=None, date_from=None, date_to=None):

    conn = get_connection()
    cursor = conn.cursor()

    base_query = """
        SELECT
            p.id,
            p.purchase_no,
            s.name,
            p.gross_total,
            p.discount,
            p.discount_amount,
            p.tax,
            p.tax_amount,
            p.net_total,
            p.purchase_date,
            COALESCE((
                SELECT SUM(pi.quantity)
                FROM purchase_items pi
                WHERE pi.purchase_id = p.id
            ), 0) AS total_quantity,
            COALESCE((
                    SELECT SUM(pr.quantity)
                    FROM purchase_returns pr
                    WHERE pr.purchase_id = p.id
            ), 0) AS returned_qty,
            p.payment_status,
            p.amount_paid,
            (p.net_total - p.amount_paid) AS balance_due
        FROM purchases p
        INNER JOIN suppliers s
            ON p.supplier_id = s.id
    """
    conditions = []
    params = []

    if search_term:
        conditions.append("p.purchase_no LIKE ?")
        params.append("%" + search_term + "%")

    if date_from and date_to:
        conditions.append("date(p.purchase_date) BETWEEN ? AND ?")
        params.append(date_from)
        params.append(date_to)

    if conditions:
        base_query += " WHERE " + " AND ".join(conditions)

    base_query += " ORDER BY p.id DESC"

    cursor.execute(base_query, params)
    rows = cursor.fetchall()
    conn.close()

    return rows
    
# =====================================
# Fetch Purchase Header (for details window)
# =====================================
def fetch_purchase_header(purchase_id):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            p.purchase_no,
            p.invoice_no,
            s.name,
            p.purchase_date,
            p.gross_total,
            p.discount,
            p.discount_amount,
            p.tax,
            p.tax_amount,
            p.net_total,
            p.payment_status,
            p.amount_paid
        FROM purchases p
        INNER JOIN suppliers s
            ON p.supplier_id = s.id
        WHERE p.id = ?
    """, (purchase_id,))

    row = cursor.fetchone()
    conn.close()

    return row

# =====================================
# Fetch Purchase Items (for details window)
# =====================================
def fetch_purchase_items(purchase_id):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            pr.name,
            pi.purchase_price,
            pi.quantity,
            pi.subtotal
        FROM purchase_items pi
        INNER JOIN products pr
            ON pi.product_id = pr.id
        WHERE pi.purchase_id = ?
        ORDER BY pi.id
    """, (
        purchase_id,
    ))

    rows = cursor.fetchall()

    conn.close()

    return rows
# ==============================================
#          Product Stock
# =============================================
def fetch_product_stock(product_name):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT quantity
        FROM products
        WHERE name = ?
    """, (product_name,))

    row = cursor.fetchone()
    conn.close()

    if row:
        return row[0]
    return 0
# =====================================
# Purchase Returns
# =====================================
def fetch_purchase_items_for_return(purchase_id):
    """
    Returns each purchased line for this purchase along with how much
    of it has already been returned before - so the UI can show/limit
    the maximum quantity that can still be returned.
    """

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            pi.product_id,
            p.name,
            pi.quantity,
            COALESCE((
                SELECT SUM(pr.quantity)
                FROM purchase_returns pr
                WHERE pr.purchase_id = pi.purchase_id
                  AND pr.product_id = pi.product_id
            ), 0) AS already_returned
        FROM purchase_items pi
        INNER JOIN products p ON pi.product_id = p.id
        WHERE pi.purchase_id = ?
        ORDER BY pi.id
    """, (purchase_id,))

    rows = cursor.fetchall()
    conn.close()

    return rows


def insert_purchase_return(cursor, purchase_id, product_id, quantity, reason):

    cursor.execute("""
        INSERT INTO purchase_returns(purchase_id, product_id, quantity, reason)
        VALUES (?, ?, ?, ?)
    """, (purchase_id, product_id, quantity, reason))

    return cursor.lastrowid


def decrement_product_stock(cursor, product_id, quantity):
    """Removes returned quantity from stock (going back to supplier)."""

    cursor.execute("""
        UPDATE products
        SET quantity = quantity - ?
        WHERE id = ?
    """, (quantity, product_id))


def fetch_returns_for_purchase(purchase_id):
    """Used to display return history for a specific purchase."""

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT p.name, pr.quantity, pr.reason, pr.return_date
        FROM purchase_returns pr
        INNER JOIN products p ON pr.product_id = p.id
        WHERE pr.purchase_id = ?
        ORDER BY pr.id
    """, (purchase_id,))

    rows = cursor.fetchall()
    conn.close()

    return rows
# =========================================================
# =========  Return Purchase ==========
# =========================================================
def fetch_all_purchase_returns(today_only=False):

    conn = get_connection()
    cursor = conn.cursor()

    base_query = """
        SELECT
            pr.return_date,
            p.purchase_no,
            pd.name,
            pr.quantity,
            pr.reason
        FROM purchase_returns pr
        INNER JOIN purchases p ON pr.purchase_id = p.id
        INNER JOIN products pd ON pr.product_id = pd.id
    """

    if today_only:
        cursor.execute(
            base_query + " WHERE date(pr.return_date) = date('now') ORDER BY pr.id DESC"
        )
    else:
        cursor.execute(base_query + " ORDER BY pr.id DESC")

    rows = cursor.fetchall()
    conn.close()

    return rows
# ==============================================
# ======  purchases_by_supplier  =======
# =============================================
def fetch_purchases_by_supplier(supplier_id):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            p.id, p.purchase_no, p.purchase_date,
            p.gross_total, p.discount_amount, p.tax_amount, p.net_total,
            p.payment_status, (p.net_total - p.amount_paid) AS balance_due
        FROM purchases p
        WHERE p.supplier_id = ?
        ORDER BY p.id DESC
    """, (supplier_id,))

    rows = cursor.fetchall()
    conn.close()

    return rows