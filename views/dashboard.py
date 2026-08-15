# ===========================================================
# IMPORTS
# ===========================================================

from tkinter import *
from tkinter import ttk

try:
    from PIL import Image as PILImage, ImageTk
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False


from datetime import datetime
from time import strftime
from services.settings_service import get_currency, set_currency, format_currency,get_app_title, get_business_info
from services.auth_service import has_permission, get_current_user, logout
from views import role as role_view
from views import product, supplier, customer, expense, user, business_settings

from views.report import open_report_window
from views.about import open_about_window
from views.credit_ledger import open_window as open_credit_ledger
import sqlite3

from utils import event_bus

from views.sales import sales_window, open_sale_return_history_window, sales_history
from views.purchase import purchase_window, open_return_history_window, purchase_history

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

        self.root = Tk()
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
        if hasattr(self, "datetime_job"):
            self.root.after_cancel(self.datetime_job)
        event_bus.unsubscribe(self.load_dashboard_data)
        self.root.destroy()

# =============================================================
# ========= Handle Logout =====================================

    def handle_logout(self):
        if hasattr(self, "datetime_job"):
            self.root.after_cancel(self.datetime_job)
        event_bus.unsubscribe(self.load_dashboard_data)
        logout()
        self.root.destroy()

        from views.login import open_login_window
        from views.dashboard import open_dashboard
        open_login_window(on_success=open_dashboard)

# -------------------------------------------------------
# Configure Window
# -------------------------------------------------------
    def configure_window(self):

        self.root.title(get_app_title())
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
        self.header.pack(fill=X,side=TOP)
        self.header.pack_propagate(False)

        self.create_logo()

        self.create_title()

        self.create_datetime()

        self.create_refresh_button()
        self.create_currency_selector()
        self.create_user_badge()
# =======================================================
    def create_user_badge(self):
            user = get_current_user()
            Label(
                self.header, text=f"👤 {user['full_name'] or user['id']} ({user['role']})",
                bg=PRIMARY, fg=WHITE, font=FONT_BODY
            ).pack(side=RIGHT, padx=15)
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
# CURRENCY SELECTOR (-style: invisible until hover)
# ===========================================================
    def create_currency_selector(self):

        self.currency_var = StringVar(value=get_currency())

        self.currency_dropdown = ttk.Combobox(
            self.header, textvariable=self.currency_var,
            values=["Rs", "$", "€", "£", "₹"],
            width=5, state="readonly",
            style="HeaderCurrency.TCombobox"
        )
        self.currency_dropdown.pack(side=RIGHT, padx=(0, 20), pady=20)

        self.currency_dropdown.bind(
            "<<ComboboxSelected>>",
            lambda event: self.on_currency_change()
        )

        # ---- Hover: highlight background appears ----
        self.currency_dropdown.bind(
            "<Enter>",
            lambda e: self.currency_dropdown.configure(style="HeaderCurrencyHover.TCombobox")
        )
        self.currency_dropdown.bind(
            "<Leave>",
            lambda e: self.currency_dropdown.configure(style="HeaderCurrency.TCombobox")
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
            logo = PILImage.open("assets/logo.png")
            logo = logo.resize((78, 47))  # keeps the logo's ~1.67:1 ratio
            self.logo_image = ImageTk.PhotoImage(logo)

            logo_stack = Frame(self.header, bg=PRIMARY)
            logo_stack.pack(side=LEFT, padx=20)

            Label(
                logo_stack,
                image=self.logo_image,
                bg=PRIMARY
            ).pack(anchor="w")

            Label(
                logo_stack,
                text="Business Management System",
                bg=PRIMARY, fg=WHITE,
                font=("Segoe UI", 9)
            ).pack(anchor="w")

        except Exception as e:
            print("Logo could not be loaded:", e)
    
# ===========================================================
# HEADER TITLE
# ===========================================================
    def create_title(self):

        business_name = get_business_info().get("name", "").strip()
        header_title = business_name if business_name else "Dashboard"

        Label(
            self.header, text=header_title,
            bg=PRIMARY, fg=WHITE, font=FONT_TITLE
        ).pack(side=LEFT, padx=20)
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

        self.datetime_job = self.root.after(1000, self.update_datetime)

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
        self.sidebar.pack(side=LEFT, fill=Y)
        self.sidebar.pack_propagate(False)

        Label(
            self.sidebar, text="MENU", bg=SIDEBAR, fg=WHITE,
            font=("Segoe UI", 14, "bold")
        ).pack(pady=10)

        # ---------------- Fixed Footer: About + Logout (never scrolls away) ----------------
        footer = Frame(self.sidebar, bg=SIDEBAR)
        footer.pack(side=BOTTOM, fill=X)

        about_btn = Button(
            footer, text="ℹ️ About",
            command=open_about_window,
            font=FONT_BODY_BOLD, bg=SIDEBAR, fg=WHITE,
            activebackground=PRIMARY, activeforeground=WHITE,
            relief=FLAT, bd=0, cursor="hand2", anchor="w", padx=20
        )
        about_btn.pack(fill=X, ipady=8)

        logout_btn = Button(
            footer, text="🚪 Logout",
            command=self.handle_logout,
            font=FONT_BODY_BOLD, bg=SIDEBAR, fg=WHITE,
            activebackground=PRIMARY, activeforeground=WHITE,
            relief=FLAT, bd=0, cursor="hand2", anchor="w", padx=20
        )
        logout_btn.pack(fill=X, ipady=8)

        # ---------------- Nav (plain frame, no scrolling) ----------------
        nav_frame = Frame(self.sidebar, bg=SIDEBAR)
        nav_frame.pack(side=TOP, fill=BOTH, expand=True)

        # sidebar_button() will pack into this frame instead of self.sidebar directly
        self.sidebar_nav = nav_frame

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
            command,
            locked=False
        ):
        card_bg = "#F3F4F6" if locked else WHITE

        card = Frame(
            parent,
            bg=card_bg,
            width=180,
            height=130,
            bd=1,
            relief="solid",
            cursor="arrow" if locked else "hand2"
        )
        card.pack(
            side=LEFT,
            padx=10,
            pady=10
        )
        card.pack_propagate(False)

        icon_text = "🔒" if locked else icon
        icon_color = "#9CA3AF" if locked else "black"

        Label(
            card,
            text=icon_text,
            bg=card_bg,
            fg=icon_color,
            font=("Segoe UI Emoji", 24)
        ).pack(
            pady=(15, 5)
        )

        Label(
            card,
            text=title,
            bg=card_bg,
            fg="#9CA3AF" if locked else TEXT,
            font=("Segoe UI", 11, "bold")
        ).pack()

        Label(
            card,
            text="No Access" if locked else subtitle,
            bg=card_bg,
            fg="gray40",
            font=("Segoe UI", 9)
        ).pack(
            pady=(3, 0)
        )

        if not locked:
            def on_click(event):
                command()

            card.bind("<Button-1>", on_click)
            for child in card.winfo_children():
                child.bind("<Button-1>", on_click)
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
            self.action_frame, "📦", "Products", "Manage Products",
            product.open_window, locked=not has_permission("products")
        )

        self.action_card(
            self.action_frame, "👥", "Customers", "Manage Customers",
            customer.open_window, locked=not has_permission("customers")
        )

        self.action_card(
            self.action_frame, "🚚", "Suppliers", "Manage Suppliers",
            supplier.open_window, locked=not has_permission("suppliers")
        )

        self.action_card(
            self.action_frame, "💰", "Sales", "Create Invoice",
            sales_window, locked=not has_permission("sales")
        )

        self.action_card(
            self.action_frame, "🛒", "Purchase", "Stock Entry",
            purchase_window, locked=not has_permission("purchase")
        )

        self.action_card(
            self.action_frame, "📊", "Reports", "View Reports",
            open_report_window, locked=not has_permission("reports")
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
            SELECT s.sale_no,
                c.name,
                s.net_total
            FROM sales s
            INNER JOIN customers c ON s.customer_id = c.id
            ORDER BY s.id DESC
            LIMIT 10
            """)
            rows = cur.fetchall()

            for sale_no, customer_name, net_total in rows:
                self.sales_tree.insert(
                    "",
                    END,
                    values=(sale_no, customer_name, format_currency(net_total))
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
            self.sidebar_nav,
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
        btn.pack(fill=X, ipady=6)

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
# REPORTS & HISTORY DROPDOWN
# ===========================================================
    def create_reports_menu(self):

        menu_btn = Menubutton(
            self.sidebar, text="📊  History Reports  ▾",
            bg=SIDEBAR, fg=WHITE, font=FONT_BODY_BOLD,
            activebackground=PRIMARY, activeforeground=WHITE,
            relief=FLAT, bd=0, anchor="w", padx=20,
            cursor="hand2"
        )
        menu_btn.pack(fill=X, ipady=8)

        reports_menu = Menu(menu_btn, tearoff=0)
        reports_menu.add_command(label="💰 Sales History", command=sales_history)
        reports_menu.add_command(label="🛒 Purchase History", command=purchase_history)
        reports_menu.add_separator()
        reports_menu.add_command(label="↩ Sales Returns", command=open_sale_return_history_window)
        reports_menu.add_command(label="↩ Purchase Returns", command=open_return_history_window)
        
        menu_btn.config(menu=reports_menu)
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

        if has_permission("sales"):
            self.sidebar_button("💰 Sales", sales_window, key="sales")

        if has_permission("purchase"):
            self.sidebar_button("🛒 Purchase", purchase_window, key="purchase")

        if has_permission("products"):
            self.sidebar_button("📦 Products", product.open_window, key="products")

        if has_permission("customers"):
            self.sidebar_button("👥 Customers", customer.open_window, key="customers")

        if has_permission("suppliers"):
            self.sidebar_button("🚚 Suppliers", supplier.open_window, key="suppliers")

        if has_permission("expenses"):
            self.sidebar_button("💸 Expenses", expense.open_window, key="expenses")

        if has_permission("users"):
            self.sidebar_button("👤 Users", user.open_window, key="users")
            self.sidebar_button("🔑 Roles", role_view.open_window, key="roles")

        if has_permission("business_settings"):
            self.sidebar_button("⚙ Business Settings", business_settings.open_window, key="business_settings")

        if has_permission("reports"):
            self.sidebar_button("📊 Reports", command=open_report_window, key="reports")
            self.create_reports_menu()

        if has_permission("credit"):
            self.sidebar_button("💳 Credit Ledger", open_credit_ledger, key="credit")
                    
# ===========================================================
# DASHBOARD LAUNCHER
# ===========================================================
def open_dashboard():
    Dashboard()
    mainloop()