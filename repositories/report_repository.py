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