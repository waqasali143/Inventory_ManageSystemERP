from database.database import get_connection


# =====================================================================
# TOTALS (Sales, Purchase, Expenses) for a date range
# =====================================================================
def fetch_totals(start_date, end_date):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT COALESCE(SUM(net_total), 0)
        FROM sales
        WHERE date(sale_date) BETWEEN ? AND ?
    """, (start_date, end_date))
    total_sales = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COALESCE(SUM(net_total), 0)
        FROM purchases
        WHERE date(purchase_date) BETWEEN ? AND ?
    """, (start_date, end_date))
    total_purchases = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COALESCE(SUM(amount), 0)
        FROM expenses
        WHERE date(expense_date) BETWEEN ? AND ?
    """, (start_date, end_date))
    total_expenses = cursor.fetchone()[0]

    conn.close()

    return total_sales, total_purchases, total_expenses

# =====================================================================
# TAX TOTALS (Sales tax collected vs Purchase tax paid) for a date range
# =====================================================================
def fetch_tax_totals(start_date, end_date):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT COALESCE(SUM(tax_amount), 0)
        FROM sales
        WHERE date(sale_date) BETWEEN ? AND ?
    """, (start_date, end_date))
    sales_tax = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COALESCE(SUM(tax_amount), 0)
        FROM purchases
        WHERE date(purchase_date) BETWEEN ? AND ?
    """, (start_date, end_date))
    purchase_tax = cursor.fetchone()[0]

    conn.close()

    return sales_tax, purchase_tax

# =====================================================================
# PROFIT / LOSS
# Gross Profit = Sum((sale_price - cost_price) * quantity) for all
#                sale_items in the date range
# Net Profit   = Gross Profit - Total Expenses
# =====================================================================
def fetch_gross_profit(start_date, end_date):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT COALESCE(SUM((si.sale_price - si.cost_price) * si.quantity), 0)
        FROM sale_items si
        INNER JOIN sales s ON si.sale_id = s.id
        WHERE date(s.sale_date) BETWEEN ? AND ?
    """, (start_date, end_date))

    gross_profit = cursor.fetchone()[0]
    conn.close()

    return gross_profit
# =====================================================================
# TOP SELLING PRODUCTS (best or worst, by quantity sold)
# =====================================================================
def fetch_top_products(start_date, end_date, limit=10, worst=False):

    conn = get_connection()
    cursor = conn.cursor()

    order = "ASC" if worst else "DESC"

    cursor.execute(f"""
        SELECT
            p.name,
            SUM(si.quantity) AS total_qty,
            SUM(si.subtotal) AS total_revenue
        FROM sale_items si
        INNER JOIN sales s ON si.sale_id = s.id
        INNER JOIN products p ON si.product_id = p.id
        WHERE date(s.sale_date) BETWEEN ? AND ?
        GROUP BY si.product_id
        ORDER BY total_qty {order}
        LIMIT ?
    """, (start_date, end_date, limit))

    rows = cursor.fetchall()
    conn.close()

    return rows
# =====================================================================
# EXPENSE BREAKDOWN (by category) - used for the pie chart
# =====================================================================
def fetch_expense_breakdown(start_date, end_date):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT category, SUM(amount)
        FROM expenses
        WHERE date(expense_date) BETWEEN ? AND ?
        GROUP BY category
        ORDER BY SUM(amount) DESC
    """, (start_date, end_date))

    rows = cursor.fetchall()
    conn.close()

    return rows
# =====================================================================
# SALES vs PURCHASE TREND (daily totals) - used for the line chart
# =====================================================================
def fetch_daily_sales_trend(start_date, end_date):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT date(sale_date), SUM(net_total)
        FROM sales
        WHERE date(sale_date) BETWEEN ? AND ?
        GROUP BY date(sale_date)
        ORDER BY date(sale_date)
    """, (start_date, end_date))

    rows = cursor.fetchall()
    conn.close()

    return rows
# ==================================================
def fetch_daily_purchase_trend(start_date, end_date):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT date(purchase_date), SUM(net_total)
        FROM purchases
        WHERE date(purchase_date) BETWEEN ? AND ?
        GROUP BY date(purchase_date)
        ORDER BY date(purchase_date)
    """, (start_date, end_date))

    rows = cursor.fetchall()
    conn.close()

    return rows
# ============================================================
# ======= Product wise calculation ================
def fetch_product_wise_raw(start_date, end_date):
    """
    Returns raw rows needed to build a per-product profit breakdown:
    (product_name, quantity, sale_price, cost_price, subtotal,
     sale_gross_total, sale_discount_amount, sale_net_total, sale_amount_paid)
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            p.name,
            si.quantity,
            si.sale_price,
            si.cost_price,
            si.subtotal,
            s.gross_total,
            s.discount_amount,
            s.net_total,
            s.amount_paid
        FROM sale_items si
        INNER JOIN sales s ON si.sale_id = s.id
        INNER JOIN products p ON si.product_id = p.id
        WHERE date(s.sale_date) BETWEEN ? AND ?
    """, (start_date, end_date))

    rows = cursor.fetchall()
    conn.close()

    return rows
# ===================================================================
# ====== Current Stock =====================
def fetch_current_stock_map():
    """Returns {product_name: current_quantity} for every product -
    used to show remaining stock alongside the profit report."""

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT name, quantity FROM products")
    rows = cursor.fetchall()
    conn.close()

    return dict(rows)
# ============================================================
# ======= Unsolved Products =========
def fetch_unsold_products(start_date, end_date):
    """
    Products that had ZERO sales in the given date range - useful
    for spotting slow-moving/stagnant stock.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT p.name, p.quantity
        FROM products p
        WHERE p.status != 'Inactive'
          AND p.id NOT IN (
              SELECT si.product_id
              FROM sale_items si
              INNER JOIN sales s ON si.sale_id = s.id
              WHERE date(s.sale_date) BETWEEN ? AND ?
          )
        ORDER BY p.name
    """, (start_date, end_date))

    rows = cursor.fetchall()
    conn.close()

    return rows