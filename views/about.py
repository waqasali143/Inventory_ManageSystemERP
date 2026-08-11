from tkinter import *

try:
    from PIL import Image as PILImage, ImageTk
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

from utils.theme import (
    PRIMARY, BACKGROUND, WHITE,
    FONT_TITLE, FONT_BODY, FONT_BODY_BOLD,
    apply_app_style
)
from utils.window_helpers import size_and_center

# =====================================================================
# Single source of truth for app/developer info - login.py's footer
# imports these same constants, so it's never out of sync with here.
# =====================================================================
APP_VERSION = "1.0.0"
DEVELOPER_NAME = "Ai Developer Waqas Ali"
DEVELOPER_EMAIL = "aktech897@gmail.com"
DEVELOPER_CONTACT = "+92-329-8151730"

ABOUT_NOTE = (
    "Inventra ERP is a complete business management solution built for "
    "retail and wholesale businesses of any size - from a single shop "
    "to a multi-branch operation.\n\n"
    "Sales, purchases, inventory, customers, suppliers, and staff are "
    "all managed in one place, with real-time stock tracking, low-stock "
    "alerts, and built-in FBR-compliant filer/non-filer tax handling. "
    "Every sale and purchase generates a clean, print-ready invoice - "
    "NTN included automatically for registered customers and suppliers.\n\n"
    "Detailed sales, purchase, and profit reports are always a click "
    "away, so decisions are made on real numbers, not guesswork. Built "
    "with speed in mind - keyboard shortcuts throughout mean less "
    "reaching for the mouse and faster checkouts at the counter."
)


def open_about_window():

    win = Toplevel()
    win.title("About")
    win.configure(bg=BACKGROUND)

    size_and_center(win, width_ratio=0.34, height_ratio=0.9, resizable=False)
    apply_app_style()

    # ---------------- Header ----------------
    header_frame = Frame(win, bg=PRIMARY, height=110)
    header_frame.pack(fill=X)
    header_frame.pack_propagate(False)

    if PIL_AVAILABLE:
        try:
            logo_img = PILImage.open("assets/logo.png")
            logo_img.thumbnail((160, 80))
            logo_photo = ImageTk.PhotoImage(logo_img)

            logo_label = Label(header_frame, image=logo_photo, bg=PRIMARY)
            logo_label.image = logo_photo  # keep a reference, or it gets garbage collected
            logo_label.pack(pady=(15, 5))
        except Exception:
            Label(
                header_frame, text="Inventra ERP",
                bg=PRIMARY, fg=WHITE, font=FONT_TITLE
            ).pack(pady=(25, 5))
    else:
        Label(
            header_frame, text="Inventra ERP",
            bg=PRIMARY, fg=WHITE, font=FONT_TITLE
        ).pack(pady=(25, 5))

    Label(
        header_frame, text="Business Management System",
        bg=PRIMARY, fg=WHITE, font=("Segoe UI", 9)
    ).pack(pady=(0, 10))

    # ---------------- Body ----------------
    body_frame = Frame(win, bg=BACKGROUND)
    body_frame.pack(fill=BOTH, expand=True, padx=25, pady=20)

    Label(
        body_frame, text=ABOUT_NOTE, bg=BACKGROUND, font=FONT_BODY,
        wraplength=370, justify=LEFT
    ).pack(anchor="w", pady=(0, 15))

    Label(
        body_frame, text="Contact & Version", bg=BACKGROUND, fg=PRIMARY,
        font=FONT_BODY_BOLD
    ).pack(anchor="w", pady=(0, 4))

    Label(
        body_frame, text=f"Version: {APP_VERSION}",
        bg=BACKGROUND, font=FONT_BODY
    ).pack(anchor="w", pady=2)

    Label(
        body_frame, text=f"Developer: {DEVELOPER_NAME}",
        bg=BACKGROUND, font=FONT_BODY
    ).pack(anchor="w", pady=2)

    Label(
        body_frame, text=f"Email: {DEVELOPER_EMAIL}",
        bg=BACKGROUND, font=FONT_BODY
    ).pack(anchor="w", pady=2)

    Label(
        body_frame, text=f"Contact: {DEVELOPER_CONTACT}",
        bg=BACKGROUND, font=FONT_BODY
    ).pack(anchor="w", pady=2)

    # ---------------- Copy Details Button ----------------
    details_text = (
        f"Inventra ERP\n"
        f"Version: {APP_VERSION}\n"
        f"Developer: {DEVELOPER_NAME}\n"
        f"Email: {DEVELOPER_EMAIL}\n"
        f"Contact: {DEVELOPER_CONTACT}"
    )

    def handle_copy_details():
        win.clipboard_clear()
        win.clipboard_append(details_text)
        win.update()  # keeps the clipboard content after this window closes

        copy_btn.config(text="✅ Copied!")
        win.after(1500, lambda: copy_btn.config(text="📋 Copy Details"))

    copy_btn = Button(
        body_frame, text="📋 Copy Details", bg=PRIMARY, fg=WHITE,
        relief=FLAT, cursor="hand2", command=handle_copy_details
    )
    copy_btn.pack(side=BOTTOM, fill=X, pady=(20, 0), ipady=6)
