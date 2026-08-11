
from tkinter import *
from tkinter import messagebox

try:
    from PIL import Image as PILImage, ImageTk
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

from utils.branding_helpers import add_branding_strip

from services.auth_service import login
from utils.theme import (
    PRIMARY, PRIMARY_DARK, BACKGROUND, WHITE, TEXT,
    FONT_TITLE, FONT_BODY, FONT_BODY_BOLD,
    apply_app_style
)

from utils.window_helpers import size_and_center
# =====================================================================

def open_login_window(on_success):
    """
    on_success: a function to call (with no arguments) once login
    succeeds - main.py will pass in "open the Dashboard" here.
    """

    win = Tk()
    win.withdraw()
    win.title("Inventra ERP | Login")
    try:
        win.iconbitmap("assets/ims.ico")
    except Exception:
        pass

    add_branding_strip(win)
    win.configure(bg=BACKGROUND)

    size_and_center(win, width_ratio=0.28, height_ratio=0.65, resizable=False)

    apply_app_style()

    # ---------------- Header ----------------
    header_frame = Frame(win, bg=PRIMARY, height=140)
    header_frame.pack(fill=X)
    header_frame.pack_propagate(False)

    if PIL_AVAILABLE:
        try:
            logo_img = PILImage.open("assets/logo.png")
            logo_img.thumbnail((200, 150))
            logo_photo = ImageTk.PhotoImage(logo_img)

            logo_label = Label(header_frame, image=logo_photo, bg=PRIMARY)
            logo_label.image = logo_photo
            logo_label.pack(pady=(15, 5))
        except Exception as e:
            print("LOGO LOAD FAILED:", e)
            Label(
                header_frame, text="Inventra ERP",
                bg=PRIMARY, fg=WHITE, font=FONT_BODY_BOLD
            ).pack(pady=(25, 5))
    else:
        print("PIL not available")
        Label(
            header_frame, text="Inventra ERP",
            bg=PRIMARY, fg=WHITE, font=FONT_BODY_BOLD
        ).pack(pady=(25, 5))
# --------------------------------------------------------------------
    Label(
            header_frame, text="Business Management System",
            bg=PRIMARY, fg=WHITE, font=("Segoe UI", 9)
        ).pack(pady=(0, 10))
    # ---------------- Form ----------------
    form_frame = Frame(win, bg=BACKGROUND)
    form_frame.pack(fill=BOTH, expand=True, padx=40, pady=30)

    username = StringVar()
    password = StringVar()

    Label(form_frame, text="Username", bg=BACKGROUND, font=FONT_BODY).pack(anchor="w", pady=(10, 2))
    username_entry = Entry(form_frame, textvariable=username, font=FONT_BODY)
    username_entry.pack(fill=X, ipady=5)

    Label(form_frame, text="Password", bg=BACKGROUND, font=FONT_BODY).pack(anchor="w", pady=(15, 2))
    password_entry = Entry(form_frame, textvariable=password, show="•", font=FONT_BODY)
    password_entry.pack(fill=X, ipady=5)

    error_label = Label(form_frame, text="", bg=BACKGROUND, fg="red", font=FONT_BODY)
    error_label.pack(pady=(8, 0))
# ===================================================================================

    def handle_login():
        if username.get().strip() == "":
            error_label.config(text="Please enter your username.")
            username_entry.focus_set()
            return

        if password.get().strip() == "":
            error_label.config(text="Please enter your password.")
            password_entry.focus_set()
            return

        if login(username.get().strip(), password.get().strip()):
            win.destroy()
            on_success()
        else:
            error_label.config(text="Invalid username or password.")
    # ===========================================================================

    Button(
        form_frame, text="Login", bg=PRIMARY, fg=WHITE,
        font=FONT_BODY_BOLD, relief=FLAT, cursor="hand2",
        command=handle_login
    ).pack(side=BOTTOM, fill=X, ipady=8, pady=(20, 10))

    username_entry.bind("<Return>", lambda event: handle_login())
    password_entry.bind("<Return>", lambda event: handle_login())

    username_entry.focus_set()
    win.deiconify() 
    win.mainloop()