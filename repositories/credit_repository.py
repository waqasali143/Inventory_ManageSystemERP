import sqlite3
from database.database import get_connection

# =====================================================================
# This file only talks to the database (raw SQL) for the Credit
# Ledger - same convention as the other *_repository.py files. It
# knows nothing about Tkinter or business validation.
#
# Balance formula (customer side, supplier side is the mirror):
#   Amount owed = SUM(net_total - amount_paid) for that customer's
#                 sales where payment_status != 'Paid'
#   Balance     = Amount owed - SUM(customer_payments.amount
#                                    WHERE sale_id IS NULL)
#
# A ledger payment recorded AGAINST a specific invoice (sale_id set)
# directly increases that sale's own amount_paid (and recomputes its
# payment_status) via apply_payment_to_sale() - so it's already
# reflected in "Amount owed" above and must NOT be subtracted again
# here. Only untargeted/generic payments (sale_id IS NULL) still need
# the separate subtraction. This is what keeps a single invoice's
# balance, its status, and the customer's overall balance all in sync
# with each other - previously a payment only touched the aggregate
# total, leaving each invoice's own balance/status stuck at whatever
# it was at the time of sale, which is what caused the mismatch
# between the Credit Ledger's total and the printed Statement.
#
# NOTE: fetch_customers_with_balance() / fetch_suppliers_with_balance()
# filter with WHERE (not HAVING) - HAVING requires GROUP BY to work
# correctly against a per-row correlated subquery in SQLite; without
# it, the filter doesn't reliably apply per customer/supplier.
# =====================================================================


def _ensure_payment_link_columns():
    """
    One-time, safe schema upgrade: adds sale_id / purchase_id to the
    payments tables if they aren't already there. Runs at import time;
    ALTER TABLE ADD COLUMN is idempotent-safe here because SQLite
    raises OperationalError if the column already exists, which we
    just swallow - so this is harmless to run on every app start,
    on both a brand-new database and an existing one.
    """
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("ALTER TABLE customer_payments ADD COLUMN sale_id INTEGER")
    except sqlite3.OperationalError:
        pass  # column already exists

    try:
        cursor.execute("ALTER TABLE supplier_payments ADD COLUMN purchase_id INTEGER")
    except sqlite3.OperationalError:
        pass  # column already exists

    conn.commit()
    conn.close()


_ensure_payment_link_columns()


# =====================================
# Customer Balance
# =====================================
def fetch_customer_balance(customer_id):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT COALESCE(SUM(net_total - amount_paid), 0)
        FROM sales
        WHERE customer_id = ? AND payment_status != 'Paid'
    """, (customer_id,))
    amount_owed = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COALESCE(SUM(amount), 0)
        FROM customer_payments
        WHERE customer_id = ? AND sale_id IS NULL
    """, (customer_id,))
    amount_received = cursor.fetchone()[0]

    conn.close()

    return amount_owed - amount_received


# =====================================
# All Customers With an Outstanding Balance
# (for the Credit Ledger list screen - includes extra columns so the
#  list is useful on its own without opening each statement)
# =====================================
def fetch_customers_with_balance():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            c.id,
            c.name,
            c.contact,
            (
                COALESCE((
                    SELECT SUM(s.net_total - s.amount_paid)
                    FROM sales s
                    WHERE s.customer_id = c.id
                      AND s.payment_status != 'Paid'
                ), 0)
                -
                COALESCE((
                    SELECT SUM(cp.amount)
                    FROM customer_payments cp
                    WHERE cp.customer_id = c.id
                      AND cp.sale_id IS NULL
                ), 0)
            ) AS balance,
            COALESCE((
                SELECT COUNT(*)
                FROM sales s
                WHERE s.customer_id = c.id
                  AND s.payment_status != 'Paid'
            ), 0) AS open_invoices,
            (
                SELECT MAX(cp.payment_date)
                FROM customer_payments cp
                WHERE cp.customer_id = c.id
            ) AS last_payment_date
        FROM customers c
        WHERE (
            COALESCE((
                SELECT SUM(s.net_total - s.amount_paid)
                FROM sales s
                WHERE s.customer_id = c.id
                  AND s.payment_status != 'Paid'
            ), 0)
            -
            COALESCE((
                SELECT SUM(cp.amount)
                FROM customer_payments cp
                WHERE cp.customer_id = c.id
                  AND cp.sale_id IS NULL
            ), 0)
        ) > 0
        ORDER BY balance DESC
    """)

    rows = cursor.fetchall()
    conn.close()

    return rows


# =====================================
# Customers With Balance - Report Version
# (same list as fetch_customers_with_balance(), plus Amount Paid and
#  Last Payment Amount - used ONLY by the Reports "Credit" tab, so
#  fetch_customers_with_balance() itself stays untouched for any other
#  screen - e.g. the Credit Ledger - that already relies on its shape)
# =====================================
def fetch_customers_with_balance_report(search_term=None):

    conn = get_connection()
    cursor = conn.cursor()

    search_clause = ""
    params = []
    if search_term:
        search_clause = """
            AND (
                c.name LIKE ?
                OR EXISTS (
                    SELECT 1 FROM sales s2
                    WHERE s2.customer_id = c.id AND s2.sale_no LIKE ?
                )
            )
        """
        params = [f"%{search_term}%", f"%{search_term}%"]

    cursor.execute(f"""
        SELECT
            c.id,
            c.name,
            c.contact,
            (
                COALESCE((
                    SELECT SUM(s.net_total - s.amount_paid)
                    FROM sales s
                    WHERE s.customer_id = c.id
                      AND s.payment_status != 'Paid'
                ), 0)
                -
                COALESCE((
                    SELECT SUM(cp.amount)
                    FROM customer_payments cp
                    WHERE cp.customer_id = c.id
                      AND cp.sale_id IS NULL
                ), 0)
            ) AS balance,
            COALESCE((
                SELECT SUM(cp.amount)
                FROM customer_payments cp
                WHERE cp.customer_id = c.id
                  AND cp.sale_id IS NULL
            ), 0) AS amount_paid,
            COALESCE((
                SELECT COUNT(*)
                FROM sales s
                WHERE s.customer_id = c.id
                  AND s.payment_status != 'Paid'
            ), 0) AS open_invoices,
            (
                SELECT cp.amount
                FROM customer_payments cp
                WHERE cp.customer_id = c.id
                ORDER BY cp.payment_date DESC
                LIMIT 1
            ) AS last_payment_amount,
            (
                SELECT date(cp.payment_date)
                FROM customer_payments cp
                WHERE cp.customer_id = c.id
                ORDER BY cp.payment_date DESC
                LIMIT 1
            ) AS last_payment_date
        FROM customers c
        WHERE (
            COALESCE((
                SELECT SUM(s.net_total - s.amount_paid)
                FROM sales s
                WHERE s.customer_id = c.id
                  AND s.payment_status != 'Paid'
            ), 0)
            -
            COALESCE((
                SELECT SUM(cp.amount)
                FROM customer_payments cp
                WHERE cp.customer_id = c.id
                  AND cp.sale_id IS NULL
            ), 0)
        ) > 0
        {search_clause}
        ORDER BY balance DESC
    """, params)

    rows = cursor.fetchall()
    conn.close()

    return rows


# =====================================
# Customer Payment History (statement of account)
# =====================================
def fetch_customer_payment_history(customer_id):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT cp.payment_date, cp.amount, cp.notes, s.sale_no
        FROM customer_payments cp
        LEFT JOIN sales s ON cp.sale_id = s.id
        WHERE cp.customer_id = ?
        ORDER BY cp.payment_date DESC
    """, (customer_id,))

    rows = cursor.fetchall()
    conn.close()

    return rows


def fetch_customer_credit_sales(customer_id):
    """Every credit (unpaid/partial) sale for this customer - the
    'what they bought on credit' half of the statement."""

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, sale_no, sale_date, net_total, amount_paid,
               (net_total - amount_paid) AS balance, payment_status
        FROM sales
        WHERE customer_id = ? AND payment_status != 'Paid'
        ORDER BY sale_date DESC
    """, (customer_id,))

    rows = cursor.fetchall()
    conn.close()

    return rows


# =====================================
# Record a Customer Payment
# =====================================
def insert_customer_payment(customer_id, amount, notes, sale_id=None):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO customer_payments(customer_id, amount, notes, sale_id)
        VALUES (?, ?, ?, ?)
    """, (customer_id, amount, notes, sale_id))

    conn.commit()
    conn.close()


def apply_payment_to_sale(sale_id, amount):
    """
    Increases the given sale's own amount_paid by `amount` (capped at
    its net_total) and recomputes its payment_status - this is what
    makes a Credit Ledger payment targeted at a specific invoice
    actually show up on that invoice (Statement, Reports), instead of
    only moving the customer's aggregate total.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT net_total, amount_paid FROM sales WHERE id = ?", (sale_id,))
    row = cursor.fetchone()
    if row is None:
        conn.close()
        return

    net_total, current_paid = row
    new_paid = min(current_paid + amount, net_total)
    new_status = "Paid" if new_paid >= net_total else ("Partial" if new_paid > 0 else "Credit")

    cursor.execute(
        "UPDATE sales SET amount_paid = ?, payment_status = ? WHERE id = ?",
        (new_paid, new_status, sale_id)
    )

    conn.commit()
    conn.close()


# =====================================
# Supplier Balance
# =====================================
def fetch_supplier_balance(supplier_id):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT COALESCE(SUM(net_total - amount_paid), 0)
        FROM purchases
        WHERE supplier_id = ? AND payment_status != 'Paid'
    """, (supplier_id,))
    amount_owed = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COALESCE(SUM(amount), 0)
        FROM supplier_payments
        WHERE supplier_id = ? AND purchase_id IS NULL
    """, (supplier_id,))
    amount_paid_out = cursor.fetchone()[0]

    conn.close()

    return amount_owed - amount_paid_out


# =====================================
# All Suppliers We Owe Money To
# =====================================
def fetch_suppliers_with_balance():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            s.id,
            s.name,
            s.contact,
            (
                COALESCE((
                    SELECT SUM(p.net_total - p.amount_paid)
                    FROM purchases p
                    WHERE p.supplier_id = s.id
                      AND p.payment_status != 'Paid'
                ), 0)
                -
                COALESCE((
                    SELECT SUM(sp.amount)
                    FROM supplier_payments sp
                    WHERE sp.supplier_id = s.id
                      AND sp.purchase_id IS NULL
                ), 0)
            ) AS balance,
            COALESCE((
                SELECT COUNT(*)
                FROM purchases p
                WHERE p.supplier_id = s.id
                  AND p.payment_status != 'Paid'
            ), 0) AS open_invoices,
            (
                SELECT MAX(sp.payment_date)
                FROM supplier_payments sp
                WHERE sp.supplier_id = s.id
            ) AS last_payment_date
        FROM suppliers s
        WHERE (
            COALESCE((
                SELECT SUM(p.net_total - p.amount_paid)
                FROM purchases p
                WHERE p.supplier_id = s.id
                  AND p.payment_status != 'Paid'
            ), 0)
            -
            COALESCE((
                SELECT SUM(sp.amount)
                FROM supplier_payments sp
                WHERE sp.supplier_id = s.id
                  AND sp.purchase_id IS NULL
            ), 0)
        ) > 0
        ORDER BY balance DESC
    """)

    rows = cursor.fetchall()
    conn.close()

    return rows


# =====================================
# Suppliers With Balance - Report Version
# (mirror of fetch_customers_with_balance_report(), supplier side)
# =====================================
def fetch_suppliers_with_balance_report(search_term=None):

    conn = get_connection()
    cursor = conn.cursor()

    search_clause = ""
    params = []
    if search_term:
        search_clause = """
            AND (
                s.name LIKE ?
                OR EXISTS (
                    SELECT 1 FROM purchases p2
                    WHERE p2.supplier_id = s.id AND p2.purchase_no LIKE ?
                )
            )
        """
        params = [f"%{search_term}%", f"%{search_term}%"]

    cursor.execute(f"""
        SELECT
            s.id,
            s.name,
            s.contact,
            (
                COALESCE((
                    SELECT SUM(p.net_total - p.amount_paid)
                    FROM purchases p
                    WHERE p.supplier_id = s.id
                      AND p.payment_status != 'Paid'
                ), 0)
                -
                COALESCE((
                    SELECT SUM(sp.amount)
                    FROM supplier_payments sp
                    WHERE sp.supplier_id = s.id
                      AND sp.purchase_id IS NULL
                ), 0)
            ) AS balance,
            COALESCE((
                SELECT SUM(sp.amount)
                FROM supplier_payments sp
                WHERE sp.supplier_id = s.id
                  AND sp.purchase_id IS NULL
            ), 0) AS amount_paid,
            COALESCE((
                SELECT COUNT(*)
                FROM purchases p
                WHERE p.supplier_id = s.id
                  AND p.payment_status != 'Paid'
            ), 0) AS open_invoices,
            (
                SELECT sp.amount
                FROM supplier_payments sp
                WHERE sp.supplier_id = s.id
                ORDER BY sp.payment_date DESC
                LIMIT 1
            ) AS last_payment_amount,
            (
                SELECT date(sp.payment_date)
                FROM supplier_payments sp
                WHERE sp.supplier_id = s.id
                ORDER BY sp.payment_date DESC
                LIMIT 1
            ) AS last_payment_date
        FROM suppliers s
        WHERE (
            COALESCE((
                SELECT SUM(p.net_total - p.amount_paid)
                FROM purchases p
                WHERE p.supplier_id = s.id
                  AND p.payment_status != 'Paid'
            ), 0)
            -
            COALESCE((
                SELECT SUM(sp.amount)
                FROM supplier_payments sp
                WHERE sp.supplier_id = s.id
                  AND sp.purchase_id IS NULL
            ), 0)
        ) > 0
        {search_clause}
        ORDER BY balance DESC
    """, params)

    rows = cursor.fetchall()
    conn.close()

    return rows


# =====================================
# Supplier Payment History (statement of account)
# =====================================
def fetch_supplier_payment_history(supplier_id):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT sp.payment_date, sp.amount, sp.notes, p.purchase_no
        FROM supplier_payments sp
        LEFT JOIN purchases p ON sp.purchase_id = p.id
        WHERE sp.supplier_id = ?
        ORDER BY sp.payment_date DESC
    """, (supplier_id,))

    rows = cursor.fetchall()
    conn.close()

    return rows


def fetch_supplier_credit_purchases(supplier_id):
    """Every credit (unpaid/partial) purchase from this supplier."""

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, purchase_no, purchase_date, net_total, amount_paid,
               (net_total - amount_paid) AS balance, payment_status
        FROM purchases
        WHERE supplier_id = ? AND payment_status != 'Paid'
        ORDER BY purchase_date DESC
    """, (supplier_id,))

    rows = cursor.fetchall()
    conn.close()

    return rows


# =====================================
# Record a Payment We Made to a Supplier
# =====================================
def insert_supplier_payment(supplier_id, amount, notes, purchase_id=None):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO supplier_payments(supplier_id, amount, notes, purchase_id)
        VALUES (?, ?, ?, ?)
    """, (supplier_id, amount, notes, purchase_id))

    conn.commit()
    conn.close()


def apply_payment_to_purchase(purchase_id, amount):
    """Supplier-side mirror of apply_payment_to_sale()."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT net_total, amount_paid FROM purchases WHERE id = ?", (purchase_id,))
    row = cursor.fetchone()
    if row is None:
        conn.close()
        return

    net_total, current_paid = row
    new_paid = min(current_paid + amount, net_total)
    new_status = "Paid" if new_paid >= net_total else ("Partial" if new_paid > 0 else "Credit")

    cursor.execute(
        "UPDATE purchases SET amount_paid = ?, payment_status = ? WHERE id = ?",
        (new_paid, new_status, purchase_id)
    )

    conn.commit()
    conn.close()


# =====================================
# Totals for Dashboard / Reports Summary
# =====================================
def fetch_total_receivable():
    """Total the business is owed by all customers combined."""

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT COALESCE(SUM(net_total - amount_paid), 0)
        FROM sales
        WHERE payment_status != 'Paid'
    """)
    amount_owed = cursor.fetchone()[0]

    cursor.execute("SELECT COALESCE(SUM(amount), 0) FROM customer_payments WHERE sale_id IS NULL")
    amount_received = cursor.fetchone()[0]

    conn.close()

    return amount_owed - amount_received


def fetch_total_payable():
    """Total the business owes all suppliers combined."""

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT COALESCE(SUM(net_total - amount_paid), 0)
        FROM purchases
        WHERE payment_status != 'Paid'
    """)
    amount_owed = cursor.fetchone()[0]

    cursor.execute("SELECT COALESCE(SUM(amount), 0) FROM supplier_payments WHERE purchase_id IS NULL")
    amount_paid_out = cursor.fetchone()[0]

    conn.close()

    return amount_owed - amount_paid_out


# =====================================
# Report Section: Credit Overview
# (one call for a full Credit tab in Reports - customer side,
#  supplier side, and the two grand totals together)
# =====================================
def fetch_credit_report_data(search_term=None):

    return {
        "customers": fetch_customers_with_balance_report(search_term),
        "suppliers": fetch_suppliers_with_balance_report(search_term),
        "total_receivable": fetch_total_receivable(),
        "total_payable": fetch_total_payable(),
    }