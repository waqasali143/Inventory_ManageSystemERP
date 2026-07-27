
import sqlite3
# =====================================
# Database Connection
# =====================================
def get_connection():
    """
    Return SQLite database connection.
    """
    conn = sqlite3.connect("database/inventory.db")
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def connect():

    conn = get_connection()
    cursor = conn.cursor()
# ------------------------------------------------
#                   Product Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS products(
        id INTEGER PRIMARY KEY AUTOINCREMENT,

        name TEXT NOT NULL UNIQUE,

        description TEXT DEFAULT '',

        cost_price REAL NOT NULL,

        sale_price REAL NOT NULL,

        quantity INTEGER NOT NULL DEFAULT 0,

        status TEXT NOT NULL DEFAULT 'Active',

        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )""")
# =====================================================
# User Table Code

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        full_name TEXT,

        username TEXT UNIQUE NOT NULL,

        password TEXT NOT NULL,

        role TEXT NOT NULL,

        status TEXT NOT NULL DEFAULT 'Active',

        last_login TIMESTAMP,

        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
# ===================================================================

    cursor.execute("""
    SELECT * FROM users
    WHERE username=?
    """, ("admin",))

    user = cursor.fetchone()

    if user is None:

        cursor.execute("""
        INSERT INTO users(username, password, role)
        VALUES (?, ?, ?)
        """, (
            "admin",
            "admin123",
            "Admin"
        ))
    # ============================================================
    #  Supplier Table
    # ============================================================
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS suppliers(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        name TEXT NOT NULL UNIQUE,

        contact TEXT NOT NULL,

        email TEXT,

        address TEXT,

        status TEXT NOT NULL DEFAULT 'Active',

        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
# ========================================================
#  Customer Table
# ----------------------------------------------
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS customers(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        name TEXT NOT NULL,

        contact TEXT NOT NULL,

        email TEXT,

        address TEXT,

        status TEXT NOT NULL DEFAULT 'Active',

        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
# =====================================
# Purchase Table
# =====================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS purchases(

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            purchase_no TEXT UNIQUE NOT NULL,

            supplier_id INTEGER NOT NULL,

            purchase_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            gross_total REAL NOT NULL,

            invoice_no TEXT DEFAULT '',

            discount REAL NOT NULL DEFAULT 0,

            discount_amount REAL NOT NULL DEFAULT 0,

            tax REAL NOT NULL DEFAULT 0,

            tax_amount REAL NOT NULL DEFAULT 0,

            net_total REAL NOT NULL,

            status TEXT NOT NULL DEFAULT 'Completed',

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY(supplier_id)
                REFERENCES suppliers(id)
    )
    """)
# =====================================
# Purchase Table Migration
# (adds new columns to an already-existing table
#  created before discount_amount/tax_amount existed)
# =====================================
    existing_columns = [
        row[1] for row in cursor.execute(
            "PRAGMA table_info(purchases)"
        ).fetchall()
    ]

    if "discount_amount" not in existing_columns:
        cursor.execute(
            "ALTER TABLE purchases ADD COLUMN discount_amount REAL NOT NULL DEFAULT 0"
        )

    if "tax_amount" not in existing_columns:
        cursor.execute(
            "ALTER TABLE purchases ADD COLUMN tax_amount REAL NOT NULL DEFAULT 0"
        )

    if "invoice_no" not in existing_columns:
        cursor.execute(
            "ALTER TABLE purchases ADD COLUMN invoice_no TEXT DEFAULT ''"
        )
# =====================================
# Purchase Items Table
# =====================================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS purchase_items(

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            purchase_id INTEGER NOT NULL,

            product_id INTEGER NOT NULL,

            purchase_price REAL NOT NULL,

            quantity INTEGER NOT NULL,

            subtotal REAL NOT NULL,

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (purchase_id)
                REFERENCES purchases(id)
                ON DELETE CASCADE,

            FOREIGN KEY (product_id)
                REFERENCES products(id)
        )
        """)
# =============================================================
# ------------  Purchase Returns Table  ---------------------------
# ============================================================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS purchase_returns
        (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            purchase_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            reason TEXT DEFAULT '',
            return_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (purchase_id)
            REFERENCES purchases(id),
            FOREIGN KEY (product_id)
            REFERENCES products(id)
        )
    """)
# =============================================================
# ------------  Sales Table  ---------------------------
# ============================================================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sales
        (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            sale_no TEXT UNIQUE NOT NULL,

            customer_id INTEGER NOT NULL,

            sale_date TEXT NOT NULL,

            gross_total REAL NOT NULL,

            discount REAL DEFAULT 0,

            discount_amount REAL NOT NULL DEFAULT 0,

            tax REAL DEFAULT 0,

            tax_amount REAL NOT NULL DEFAULT 0,

            net_total REAL NOT NULL,

            FOREIGN KEY (customer_id)
            REFERENCES customers(id)
        )
    """)
# =============================================================
# ------------  Sale Returns Table  ---------------------------
# ============================================================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sale_returns
        (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sale_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            reason TEXT DEFAULT '',
            return_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (sale_id)
            REFERENCES sales(id),
            FOREIGN KEY (product_id)
            REFERENCES products(id)
        )
    """)
# =====================================
# Sales Table Migration
# (adds new columns to an already-existing table
#  created before discount_amount/tax_amount existed)
# =====================================
    sales_existing_columns = [
        row[1] for row in cursor.execute(
            "PRAGMA table_info(sales)"
        ).fetchall()
    ]

    if "discount_amount" not in sales_existing_columns:
        cursor.execute(
            "ALTER TABLE sales ADD COLUMN discount_amount REAL NOT NULL DEFAULT 0"
        )

    if "tax_amount" not in sales_existing_columns:
        cursor.execute(
            "ALTER TABLE sales ADD COLUMN tax_amount REAL NOT NULL DEFAULT 0"
        )
# =============================================================
# ------------  Sales Item Table  ---------------------------
# ============================================================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sale_items
        (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sale_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            sale_price REAL NOT NULL,
            quantity INTEGER NOT NULL,
            subtotal REAL NOT NULL,
            FOREIGN KEY (sale_id)
            REFERENCES sales(id),
            FOREIGN KEY (product_id)
            REFERENCES products(id)
        )
    """)
# -------------------------------------------------------------
    conn.commit()

    conn.close()
print("Database Connected Successfully")
connect()