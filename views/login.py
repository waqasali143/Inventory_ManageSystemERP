
from tkinter import *
import sqlite3
from tkinter import messagebox
from views import dashboard

# ======================================
# Login User
# =====================================
def login_user(username, password, password_entry, win):

    if username.get().strip() == "" or password.get().strip() == "":
        messagebox.showerror(
            "Error",
            "Username and Password are required."
        )
        return

    conn = sqlite3.connect("database/inventory.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT * FROM users
        WHERE username=? AND password=?
    """, (
        username.get().strip(),
        password.get().strip()
    ))

    user = cursor.fetchone()

    conn.close()

    if user:
        messagebox.showinfo(
            "Success",
            "Login Successful"
        )

        win.destroy()

        dashboard.open_dashboard()

    else:

        messagebox.showerror(
            "Login Failed",
            "Invalid Username or Password"
        )

        password.set("")
        password_entry.focus_set()
# ======================================================
def toggle_password(password_entry, show_password):

    if show_password.get():
        password_entry.config(show="")
    else:
        password_entry.config(show="*")
# ======================================================
def open_login():

    win = Toplevel()

    win.title("Login")

    win.geometry("450x350")
# ==========================
# Center Window Login
# ==========================

    window_width = 450
    window_height = 350

    screen_width = win.winfo_screenwidth()
    screen_height = win.winfo_screenheight()

    x = (screen_width // 2) - (window_width // 2)
    y = (screen_height // 2) - (window_height // 2)

    win.geometry(f"{window_width}x{window_height}+{x}+{y}")

    win.resizable(False, False)
    win.iconbitmap("assets/ims.ico")
    win.protocol("WM_DELETE_WINDOW", win.quit)

# ==========================
# Title
# ==========================

    title = Label(
        win,
        text="Inventory Management System",
        font=("Arial", 18, "bold"),
        bg="#0f4c81",
        fg="white",
        pady=12
    )

    title.pack(fill=X)

# ==========================
# Variables
# ==========================

    username = StringVar()
    password = StringVar()
    show_password = BooleanVar()

# ==========================
# Login Frame
# ==========================

    login_frame = Frame(win)

    login_frame.pack(pady=40)

    Label(
        login_frame,
        text="Username",
        font=("Arial", 11)
    ).grid(row=0, column=0, sticky="w", pady=10)

    username_entry = Entry(
        login_frame,
        textvariable=username,
        width=30
    )

    username_entry.grid(row=0, column=1, padx=10)
# =============================================
# Password
# =============================================
    Label(
        login_frame,
        text="Password",
        font=("Arial", 11)
    ).grid(row=1, column=0, sticky="w", pady=10)

    password_entry = Entry(
        login_frame,
        textvariable=password,
        show="*",
        width=30
    )

    password_entry.grid(row=1, column=1, padx=10)
# ===============================================
#  Check Button
# ===============================================
    Checkbutton(
        login_frame,
        text="Show Password",
        variable=show_password,
        command=lambda: toggle_password(
            password_entry,
            show_password
        )
    ).grid(
        row=2,
        column=1,
        sticky="w",
        pady=5
    )
# ===============================================
# Login Button
# ===============================================
    password_entry.bind(
        "<Return>",
        lambda event: login_user(
            username,
            password,
            password_entry,
            win
        )
    )
# ===============================================
    Button(
        login_frame,
        text="Login",
        width=15,
        font=("Arial", 11, "bold"),
        command=lambda: login_user(
        username,
        password,
        password_entry,
        win)
    ).grid(
        row=3,
        column=0,
        columnspan=2,
        pady=20
    )

    username_entry.focus_set()