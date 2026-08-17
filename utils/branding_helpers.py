from tkinter import Frame, Label
from services.settings_service import get_business_info
from services.auth_service import get_current_user

try:
    from PIL import Image as PILImage, ImageTk
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

APP_NAME = "Inventra POS & ERP"


def add_branding_strip(win, bg="#E5E7EB", fg="#4B5563"):
    """
    Adds a slim identity strip to the very top of any window:
    "[logo] Inventra POS & ERP | <Business Name>" on the left,
    "<logged-in user>" on the right.
    Call this FIRST, before building the window's own colored header.
    """
    business = get_business_info()
    business_name = business.get("name", "")
    logo_path = business.get("logo_path")
    user = get_current_user()

    strip = Frame(win, bg=bg, height=24)
    strip.pack(fill="x", side="top")
    strip.pack_propagate(False)

    left_frame = Frame(strip, bg=bg)
    left_frame.pack(side="left", padx=12)

    app_text = APP_NAME + ("  |  " if business_name else "")
    Label(
        left_frame, text=app_text, bg=bg, fg=fg, font=("Segoe UI", 8)
    ).pack(side="left")

    if PIL_AVAILABLE and logo_path:
        try:
            logo = PILImage.open(logo_path)
            logo.thumbnail((18, 18))
            # Keep a reference on the strip widget itself - Tkinter
            # doesn't hold its own reference to PhotoImage, so without
            # this the image gets garbage-collected and just vanishes.
            strip.logo_image = ImageTk.PhotoImage(logo)
            Label(left_frame, image=strip.logo_image, bg=bg).pack(side="left", padx=(0, 4))
        except Exception:
            pass  # a corrupt/unreadable logo file should never break the app

    if business_name:
        Label(
            left_frame, text=business_name, bg=bg, fg=fg, font=("Segoe UI", 8)
        ).pack(side="left")

    if user.get("full_name") or user.get("role"):
        right_text = f"{user.get('full_name') or ''} ({user.get('role') or ''})".strip()
        Label(
            strip, text=right_text, bg=bg, fg=fg, font=("Segoe UI", 8)
        ).pack(side="right", padx=12)