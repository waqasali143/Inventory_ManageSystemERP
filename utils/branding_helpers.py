from tkinter import Frame, Label
from services.settings_service import get_business_info
from services.auth_service import get_current_user

APP_NAME = "Inventra ERP"


def add_branding_strip(win, bg="#E5E7EB", fg="#4B5563"):
    """
    Adds a slim identity strip to the very top of any window:
    "Inventra ERP | <Business Name>" on the left,
    "<logged-in user>" on the right.
    Call this FIRST, before building the window's own colored header.
    """
    business_name = get_business_info().get("name", "")
    user = get_current_user()

    strip = Frame(win, bg=bg, height=24)
    strip.pack(fill="x", side="top")
    strip.pack_propagate(False)

    left_text = APP_NAME
    if business_name:
        left_text += f"  |  {business_name}"

    Label(
        strip, text=left_text, bg=bg, fg=fg, font=("Segoe UI", 8)
    ).pack(side="left", padx=12)

    if user.get("full_name") or user.get("role"):
        right_text = f"{user.get('full_name') or ''} ({user.get('role') or ''})".strip()
        Label(
            strip, text=right_text, bg=bg, fg=fg, font=("Segoe UI", 8)
        ).pack(side="right", padx=12)