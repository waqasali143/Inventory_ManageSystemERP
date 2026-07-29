# ===========================================================
# IMPORTS
# ===========================================================

from tkinter import *
from tkinter import ttk

try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

from datetime import datetime
from time import strftime
from services.settings_service import get_currency, set_currency
from views import product
from views import supplier
from views import customer
import sqlite3

from utils import event_bus

from views.sales import sales_window, open_sale_return_history_window
from views.purchase import purchase_window, open_return_history_window

from utils.theme import (
    PRIMARY, PRIMARY_DARK, SIDEBAR, SIDEBAR_ACTIVE, BACKGROUND,
    WHITE, TEXT, MUTED_TEXT, BORDER,
    BLUE, GREEN, PURPLE, ORANGE, RED, TEAL,
    FONT_TITLE, FONT_HEADING, FONT_BODY, FONT_BODY_BOLD, FONT_SMALL,
    apply_app_style, stripe_treeview
)
# ===========================================================
# DASHBOARD CLASS
# ===========================================================
class Dashboard:
    # -------------------------------------------------------
    # Constructor
    # -------------------------------------------------------
    def __init__(self):

        global dashboard_instance
        dashboard_instance = self

        self.root = Toplevel()
        self.active_sidebar_key = "dashboard"
        self.configure_window()
        self.center_window()
        self.create_header()
        self.create_main_layout()
        self.load_dashboard_data()
        event_bus.subscribe(self.load_dashboard_data)
# ===========================================================
# ON CLOSE
# ===========================================================
    def on_close(self):
        event_bus.unsubscribe(self.load_dashboard_data)
        self.root.destroy()
# -------------------------------------------------------
# Configure Window
# -------------------------------------------------------
    def configure_window(self):

        self.root.title("Inventory Management System")
        self.root.geometry("1400x780")
        self.root.configure(bg=BACKGROUND)
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.root.resizable(False, False)
        self.root.iconbitmap("assets/ims.ico")
        apply_app_style()
# -------------------------------------------------------
# Center Window
# -------------------------------------------------------
    def center_window(self):

        width = 1400
        height = 780

        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()

        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2)

        self.root.geometry(

            f"{width}x{height}+{x}+{y}"
        )
# ===========================================================
# HEADER
# ===========================================================
    def create_header(self):

        self.header = Frame(
            self.root,
            bg=PRIMARY,
            height=75
        )
        self.header.pack(
            fill=X,
            side=TOP
        )
        self.header.pack_propagate(False)

        self.create_logo()

        self.create_title()

        self.create_datetime()

        self.create_refresh_button()
        self.create_currency_selector()
# ===========================================================
# REFRESH BUTTON
# ===========================================================
    def create_refresh_button(self):

        self.refresh_btn = Button(
            self.header,
            text="🔄 Refresh",
            command=self.manual_refresh,
            font=FONT_BODY_BOLD,
            bg=PRIMARY,
            fg=WHITE,
            activebackground=PRIMARY_DARK,
            activeforeground=WHITE,
            relief=FLAT,
            bd=0,
            cursor="hand2",
            padx=14,
            pady=4
        )
        self.refresh_btn.pack(side=RIGHT, padx=(0, 15))
# ===========================================================
# CURRENCY SELECTOR
# ===========================================================
    def create_currency_selector(self):

        currency_frame = Frame(self.header, bg=PRIMARY)
        currency_frame.pack(side=RIGHT, padx=(0, 15))

        Label(
            currency_frame, text="Currency:",
            bg=PRIMARY, fg=WHITE, font=FONT_BODY
        ).pack(side=LEFT, padx=(0, 5))

        self.currency_var = StringVar(value=get_currency())

        currency_dropdown = ttk.Combobox(
            currency_frame, textvariable=self.currency_var,
            values=["Rs", "$", "€", "£", "₹"],
            width=5, state="readonly"
        )
        currency_dropdown.pack(side=LEFT)

        currency_dropdown.bind(
            "<<ComboboxSelected>>",
            lambda event: self.on_currency_change()
        )

    def on_currency_change(self):
        set_currency(self.currency_var.get())
# ===========================================================
# MANUAL REFRESH (with brief visual feedback)
# ===========================================================
    def manual_refresh(self):
        self.load_dashboard_data()

        self.refresh_btn.config(text="✅ Updated")
        self.root.after(1000, self.reset_refresh_button)

    def reset_refresh_button(self):
        self.refresh_btn.config(text="🔄 Refresh")
# ===========================================================
# HEADER LOGO
# ===========================================================
    def create_logo(self):

        if not PIL_AVAILABLE:
            return

        try:
            logo = Image.open("assets/logo.png")
            logo = logo.resize((45, 45))
            self.logo_image = ImageTk.PhotoImage(logo)

            Label(
                self.header,
                image=self.logo_image,
                bg=PRIMARY
            ).pack(
                side=LEFT,
                padx=20
            )
        except Exception as e:
            print("Logo could not be loaded:", e)
# ===========================================================
# HEADER TITLE
# ===========================================================
    def create_title(self):

        Label(
            self.header,
            text="Inventory Management System",
            bg=PRIMARY,
            fg=WHITE,
            font=("Segoe UI",20,"bold")
        ).pack(side=LEFT, padx=(25, 10))
# ===========================================================
# HEADER DATE & TIME
# ===========================================================
    def create_datetime(self):

        self.datetime_label = Label(
            self.header,
            bg=PRIMARY,
            fg=WHITE,
            font=("Segoe UI",11,"bold")
        )

        self.datetime_label.pack(
            side=RIGHT,
            padx=20
        )

        self.update_datetime()
# ===========================================================
# UPDATE DATE TIME
# ===========================================================
    def update_datetime(self):

        current = datetime.now().strftime(
            "%d %b %Y   %I:%M:%S %p"
        )

        self.datetime_label.config(
            text=current
        )

        self.datetime_label.after(
            1000,
            self.update_datetime
        )
# ===========================================================
# MAIN LAYOUT
# ===========================================================
    def create_main_layout(self):

        self.main_frame = Frame(
            self.root,
            bg=BACKGROUND
        )

        self.main_frame.pack(
            fill=BOTH,
            expand=True
        )
        self.create_sidebar()

        self.create_content()
# ===========================================================
# SIDEBAR
# ===========================================================
    def create_sidebar(self):

        self.sidebar = Frame(
            self.main_frame,
            bg=SIDEBAR,
            width=220
        )
        self.sidebar.pack(
            side=LEFT,
            fill=Y
        )

        self.sidebar.pack_propagate(False)
        Label(
            self.sidebar,
            text="MENU",
            bg=SIDEBAR,
            fg=WHITE,
            font=("Segoe UI",18,"bold")
        ).pack(
            pady=25
        )

        self.create_sidebar_buttons()
# ===========================================================
# CONTENT AREA
# ===========================================================
    def create_content(self):

        self.content = Frame(
            self.main_frame,
            bg=BACKGROUND
        )

        self.content.pack(
            side=LEFT,
            fill=BOTH,
            expand=True
        )
        self.create_summary_section()
# ===========================================================
# SUMMARY SECTION
# ===========================================================
    def create_summary_section(self):

        self.summary_frame = Frame(
            self.content,
            bg=BACKGROUND
        )
        self.summary_frame.pack(
            fill=X,
            padx=20,
            pady=20
        )

        self.create_summary_cards()
        self.create_quick_action_section()
# ===========================================================
# SUMMARY CARD
# ===========================================================
    def summary_card(self, parent, title, value, color):

        card = Frame(
            parent,
            bg=color,
            width=170,
            height=110
        )
        card.pack(
            side=LEFT,
            padx=10
        )
        card.pack_propagate(False)

        Label(
            card,
            text=title,
            bg=color,
            fg=WHITE,
            font=("Segoe UI",11,"bold")
        ).pack(
            pady=(18,6)
        )
        value_label = Label(
            card,
            text=value,
            bg=color,
            fg=WHITE,
            font=("Segoe UI",26,"bold")
        )
        value_label.pack()

        return value_label
# ===========================================================
# CREATE SUMMARY CARDS
# ===========================================================
    def create_summary_cards(self):

        self.products_count = self.summary_card(
            self.summary_frame,
            "Products",
            "0",
            BLUE
        )
        self.customers_count = self.summary_card(
            self.summary_frame,
            "Customers",
            "0",
            GREEN
        )
        self.suppliers_count = self.summary_card(
            self.summary_frame,
            "Suppliers",
            "0",
            PURPLE
        )
        self.sales_count = self.summary_card(
            self.summary_frame,
            "Sales",
            "0",
            ORANGE
        )
        self.purchase_count = self.summary_card(
            self.summary_frame,
            "Purchase",
            "0",
            TEAL
        )
        self.low_stock_count = self.summary_card(
            self.summary_frame,
            "Low Stock",
            "0",
            RED
        )
# ===========================================================
# QUICK ACTION SECTION
# ===========================================================
    def create_quick_action_section(self):

        Label(
            self.content,
            text="Quick Actions",
            bg=BACKGROUND,
            fg=TEXT,
            font=("Segoe UI",18,"bold")
        ).pack(
            anchor="w",
            padx=20,
            pady=(15,10)
        )

        self.action_frame = Frame(
            self.content,
            bg=BACKGROUND
        )

        self.action_frame.pack(
            fill=X,
            padx=20
        )

        self.create_action_cards()
        self.create_dashboard_panels()
# ===========================================================
# ACTION CARD
# ===========================================================
    def action_card(
        self,
        parent,
        icon,
        title,
        subtitle,
        command
    ):
        card = Frame(
            parent,
            bg=WHITE,
            width=180,
            height=130,
            bd=1,
            relief="solid",
            cursor="hand2"
        )
        card.pack(
            side=LEFT,
            padx=10,
            pady=10
        )
        card.pack_propagate(False)

        Label(
            card,
            text=icon,
            bg=WHITE,
            font=("Segoe UI Emoji",24)
        ).pack(
            pady=(15,5)
        )

        Label(
            card,
            text=title,
            bg=WHITE,
            fg=TEXT,
            font=("Segoe UI",11,"bold")
        ).pack()

        Label(
            card,
            text=subtitle,
            bg=WHITE,
            fg="gray40",
            font=("Segoe UI",9)
        ).pack(
            pady=(3,0)
        )

# ===========================================================
# CLICK EVENTS
# ===========================================================
        def on_click(event=None):
            command()

        card.bind("<Button-1>", on_click)

        for widget in card.winfo_children():
            widget.bind("<Button-1>", on_click)

        return card
# ===========================================================
# CREATE ACTION CARDS
# ===========================================================
    def create_action_cards(self):

        self.action_card(
            self.action_frame,
            "📦",
            "Products",
            "Manage Products",
            product.open_window
        )

        self.action_card(
            self.action_frame,
            "👥",
            "Customers",
            "Manage Customers",
            customer.open_window
        )

        self.action_card(
            self.action_frame,
            "🚚",
            "Suppliers",
            "Manage Suppliers",
            supplier.open_window
        )

        self.action_card(
            self.action_frame,
            "💰",
            "Sales",
            "Create Invoice",
            sales_window
        )

        self.action_card(
            self.action_frame,
            "🛒",
            "Purchase",
            "Stock Entry",
            purchase_window
        )

        self.action_card(
            self.action_frame,
            "📊",
            "Reports",
            "View Reports",
            lambda: None
        )
# ===========================================================
# DASHBOARD PANELS
# ===========================================================
    def create_dashboard_panels(self):

        self.panel_frame = Frame(
            self.content,
            bg=BACKGROUND
        )
        self.panel_frame.pack(
            fill=BOTH,
            expand=True,
            padx=20,
            pady=20
        )
        self.create_recent_sales_panel()

        self.create_low_stock_panel()
    # ===========================================================
    # RECENT SALES PANEL
    # ===========================================================
    def create_recent_sales_panel(self):

        sales_frame = LabelFrame(
            self.panel_frame,
            text="Recent Sales",
            font=("Segoe UI",11,"bold"),
            bg=WHITE,
            fg=TEXT,
            padx=10,
            pady=10
        )
        sales_frame.pack(
            side=LEFT,
            fill=BOTH,
            expand=True,
            padx=(0,10)
        )
        columns = (
            "Invoice No",
            "Customer",
            "Net Total"
        )
        self.sales_tree = ttk.Treeview(

            sales_frame,
            columns=columns,

            show="headings",

            height=10
        )
        for col in columns:

            self.sales_tree.heading(col,text=col)

            self.sales_tree.column(
                col,
                anchor=CENTER,
                width=120
            )
        self.sales_tree.pack(
            fill=BOTH,
            expand=True
        )
# ===========================================================
# LOW STOCK PANEL
# ===========================================================
    def create_low_stock_panel(self):

        stock_frame = LabelFrame(
            self.panel_frame,
            text="Low Stock Products",
            font=("Segoe UI",11,"bold"),
            bg=WHITE,
            fg=TEXT,
            padx=10,
            pady=10
        )
        stock_frame.pack(
            side=LEFT,
            fill=BOTH,
            expand=True
        )
        columns = (
            "Product",
            "Stock"
        )
        self.stock_tree = ttk.Treeview(

            stock_frame,
            columns=columns,

            show="headings",

            height=10
        )
        self.stock_tree.heading(
            "Product",
            text="Product"
        )
        self.stock_tree.heading(
            "Stock",
            text="Stock"
        )
        self.stock_tree.column(
            "Product",
            width=220,
            anchor=W
        )
        self.stock_tree.column(
            "Stock",
            width=80,
            anchor=CENTER
        )
        self.stock_tree.pack(
            fill=BOTH,
            expand=True
        )
# ===========================================================
# LOAD DASHBOARD DATA
# ===========================================================
    def load_dashboard_data(self):

        try:
            con = sqlite3.connect("database/inventory.db")

            cur = con.cursor()

            # Products
            cur.execute("SELECT COUNT(*) FROM products")
            self.products_count.config(text=cur.fetchone()[0])

            # Customers
            cur.execute("SELECT COUNT(*) FROM customers")
            self.customers_count.config(text=cur.fetchone()[0])

            # Suppliers
            cur.execute("SELECT COUNT(*) FROM suppliers")
            self.suppliers_count.config(text=cur.fetchone()[0])

            # Sales
            cur.execute("SELECT COUNT(*) FROM sales")
            self.sales_count.config(text=cur.fetchone()[0])

            # Purchase
            cur.execute("SELECT COUNT(*) FROM purchases")
            self.purchase_count.config(text=cur.fetchone()[0])

# ===========================================================
# LOW STOCK COUNT
# (Temporary Threshold = 5)
# Future: minimum_stock column will be used
# ===========================================================

            LOW_STOCK_LIMIT = 5

            cur.execute("""
                SELECT COUNT(*)
                FROM products
                WHERE quantity <= ?
                """,
                (LOW_STOCK_LIMIT,)
            )

            self.low_stock_count.config(
                text=cur.fetchone()[0]
            )
# -----------------------------------------
# Recent Sales
# -----------------------------------------
            self.sales_tree.delete(
                *self.sales_tree.get_children()
            )
            cur.execute("""
            SELECT sale_no,
                customer_id,
                net_total
            FROM sales
            ORDER BY id DESC
            LIMIT 10
            """)
            rows = cur.fetchall()

            for row in rows:
                self.sales_tree.insert(
                    "",
                    END,
                    values=row
                )
            stripe_treeview(self.sales_tree)
# -----------------------------------------
# Low Stock Products
# -----------------------------------------
            self.stock_tree.delete(
                *self.stock_tree.get_children()
            )
            cur.execute(
                """
                SELECT
                    name,
                    quantity
                FROM products
                WHERE quantity <= ?
                ORDER BY quantity ASC
                """,
                (LOW_STOCK_LIMIT,)
            )

            rows = cur.fetchall()

            for row in rows:
                self.stock_tree.insert(
                    "",
                    END,
                    values=row
                )

            con.close()

        except Exception as e:

            print("Dashboard Error :", e)
# ===========================================================
# SIDEBAR BUTTON
# ===========================================================
    def sidebar_button(self, text, command=None, key=None):

        def on_click():
            self.set_active_sidebar(key)
            if command:
                command()

        btn = Button(
            self.sidebar,
            text=text,
            command=on_click,
            font=FONT_BODY_BOLD,
            bg=SIDEBAR,
            fg=WHITE,
            activebackground=PRIMARY,
            activeforeground=WHITE,
            relief=FLAT,
            bd=0,
            cursor="hand2",
            anchor="w",
            padx=20
        )
        btn.pack(fill=X, ipady=12)

        if not hasattr(self, "sidebar_buttons"):
            self.sidebar_buttons = {}
        if key:
            self.sidebar_buttons[key] = btn
# ============ Button Efect ======================
        def on_enter(event):
            btn.config(bg=SIDEBAR_ACTIVE)

        def on_leave(event):
            if key == self.active_sidebar_key:
                btn.config(bg=SIDEBAR_ACTIVE)
            else:
                btn.config(bg=SIDEBAR)

        btn.bind("<Enter>", on_enter)
        btn.bind("<Leave>", on_leave)

        return btn
# ===========================================================
# SET ACTIVE SIDEBAR
# ===========================================================
    def set_active_sidebar(self, key):

        if not hasattr(self, "sidebar_buttons"):
            return

        self.active_sidebar_key = key

        for btn_key, btn in self.sidebar_buttons.items():
            btn.config(bg=SIDEBAR_ACTIVE if btn_key == key else SIDEBAR)
# ===========================================================
# SIDEBAR BUTTONS
# ===========================================================
    def create_sidebar_buttons(self):

        self.sidebar_button("🏠 Dashboard", key="dashboard")

        self.sidebar_button(
            "📦 Products",
            product.open_window,
            key="products"
        )

        self.sidebar_button(
            "👥 Customers",
            customer.open_window,
            key="customers"
        )

        self.sidebar_button(
            "🚚 Suppliers",
            supplier.open_window,
            key="suppliers"
        )

        self.sidebar_button(
            "💰 Sales",
            sales_window,
            key="sales"
        )

        self.sidebar_button(
            "🛒 Purchase",
            purchase_window,
            key="purchase"
        )

        self.sidebar_button(
            "📊 Reports",
            key="reports"
        )

        self.sidebar_button(
            "↩ Sales Returns",
            open_sale_return_history_window,
            key="sales_returns"
        )

        self.sidebar_button(
            "↩ Purchase Returns",
            open_return_history_window,
            key="purchase_returns"
        )
        
        self.sidebar_button(
            "🚪 Logout",
            self.root.destroy
        )
# ===========================================================
# DASHBOARD LAUNCHER
# ===========================================================
def open_dashboard():

    Dashboard()