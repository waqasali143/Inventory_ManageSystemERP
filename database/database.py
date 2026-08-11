
from database.db_config import DB_PATH
import sqlite3
import bcrypt
# =====================================
# Database Connection
# =====================================
def get_connection():
    """
    Return SQLite database connection.
    """
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA busy_timeout = 10000")
    return conn
# =====================================================
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

        barcode TEXT DEFAULT '',

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

# ============================================================
    cursor.execute("SELECT id, password FROM users")
    all_users = cursor.fetchall()

    for user_id, stored_password in all_users:
        # bcrypt hashes always start with "$2" - if it doesn't, this
        # is old plain-text data that needs to be hashed once.
        if not stored_password.startswith("$2"):
            hashed = bcrypt.hashpw(stored_password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
            cursor.execute("UPDATE users SET password=? WHERE id=?", (hashed, user_id))
# =====================================
# Settings Table
# (key-value store for system-wide settings like currency,
#  business name, etc. - one row per setting)
# =====================================
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS settings(
        key TEXT PRIMARY KEY,
        value TEXT NOT NULL
    )
    """)

    default_settings = {
        "currency": "Rs",
        "filer_tax_rate": "2",
        "non_filer_tax_rate": "4",
        "business_name": "",
        "business_address": "",
        "business_phone": "",
        "business_ntn": "",
    }

    for key, value in default_settings.items():
        cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
        if cursor.fetchone() is None:
            cursor.execute(
                "INSERT INTO settings(key, value) VALUES (?, ?)", (key, value)
            )
# =====================================
# Roles Table
# =====================================
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS roles(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

# =====================================
# Role Permissions Table
# (one row per (role, section) that IS allowed)
# =====================================
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS role_permissions(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        role_id INTEGER NOT NULL,
        section TEXT NOT NULL,
        FOREIGN KEY(role_id) REFERENCES roles(id) ON DELETE CASCADE
    )
    """)

# =====================================
# Seed default roles (only if roles table is empty)
# =====================================
    cursor.execute("SELECT COUNT(*) FROM roles")
    if cursor.fetchone()[0] == 0:

        cursor.execute("INSERT INTO roles(name) VALUES ('Admin')")
        admin_role_id = cursor.lastrowid

        cursor.execute("INSERT INTO roles(name) VALUES ('Cashier')")
        cashier_role_id = cursor.lastrowid

        all_sections = [
            "products", "customers", "suppliers", "sales", "purchase",
            "expenses", "users", "business_settings", "reports"
        ]
        for section in all_sections:
            cursor.execute(
                "INSERT INTO role_permissions(role_id, section) VALUES (?, ?)",
                (admin_role_id, section)
            )

        for section in ["sales", "purchase"]:
            cursor.execute(
                "INSERT INTO role_permissions(role_id, section) VALUES (?, ?)",
                (cashier_role_id, section)
            )
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

        ntn TEXT DEFAULT '',

        is_filer INTEGER NOT NULL DEFAULT 0,

        status TEXT NOT NULL DEFAULT 'Active',

        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
# =======================================================

    suppliers_existing_columns = [
        row[1] for row in cursor.execute(
            "PRAGMA table_info(suppliers)"
        ).fetchall()
    ]

    if "ntn" not in suppliers_existing_columns:
        cursor.execute("ALTER TABLE suppliers ADD COLUMN ntn TEXT DEFAULT ''")

    if "is_filer" not in suppliers_existing_columns:
        cursor.execute("ALTER TABLE suppliers ADD COLUMN is_filer INTEGER NOT NULL DEFAULT 0")
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

        ntn TEXT DEFAULT '',

        is_filer INTEGER NOT NULL DEFAULT 0,

        status TEXT NOT NULL DEFAULT 'Active',

        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
# ==========================================================
# = = = = Customer Table Migration = = = =
# ==========================================================

    customers_existing_columns = [
        row[1] for row in cursor.execute(
            "PRAGMA table_info(customers)"
        ).fetchall()
    ]

    if "ntn" not in customers_existing_columns:
        cursor.execute("ALTER TABLE customers ADD COLUMN ntn TEXT DEFAULT ''")

    if "is_filer" not in customers_existing_columns:
        cursor.execute("ALTER TABLE customers ADD COLUMN is_filer INTEGER NOT NULL DEFAULT 0")
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
    
    products_existing_columns = [
        row[1] for row in cursor.execute(
            "PRAGMA table_info(products)"
        ).fetchall()
    ]

    if "barcode" not in products_existing_columns:
        cursor.execute(
            "ALTER TABLE products ADD COLUMN barcode TEXT DEFAULT ''"
        )
# ==================================================
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
            cost_price REAL NOT NULL DEFAULT 0,
            quantity INTEGER NOT NULL,
            subtotal REAL NOT NULL,
            FOREIGN KEY (sale_id)
            REFERENCES sales(id),
            FOREIGN KEY (product_id)
            REFERENCES products(id)
        )
    """)

# =====================================
# Sale Items Migration
# (adds cost_price to an already-existing table, and backfills old
#  rows using each product's current cost - best-effort for old data)
# =====================================
    sale_items_columns = [
        row[1] for row in cursor.execute(
            "PRAGMA table_info(sale_items)"
        ).fetchall()
    ]

    if "cost_price" not in sale_items_columns:
        cursor.execute(
            "ALTER TABLE sale_items ADD COLUMN cost_price REAL NOT NULL DEFAULT 0"
        )
        cursor.execute("""
            UPDATE sale_items
            SET cost_price = (
                SELECT cost_price FROM products
                WHERE products.id = sale_items.product_id
            )
            WHERE cost_price = 0
        """)
# =============================================================
# ------------  Expenses Table  ---------------------------
# ============================================================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS expenses
        (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT NOT NULL,
            description TEXT DEFAULT '',
            amount REAL NOT NULL,
            expense_date TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
# ---------------------------------------------
# ----------------
    conn.commit()

    conn.close()
print("Database Connected Successfully")
connect()
# =============================================
