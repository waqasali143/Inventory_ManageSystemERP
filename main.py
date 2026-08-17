
import ctypes
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    pass

from tkinter import messagebox

from database.database import connect
from views.login import open_login_window
from views import dashboard
from services.license_service import check_license_status, GRACE_DAYS
from views.license_window import open_locked_window

connect()


def show_dashboard():
    result = check_license_status()

    if result["is_locked"]:
        # No dashboard behind this - it's the only window until the
        # renewal is approved, then it hands off into the app itself.
        open_locked_window(on_unlocked=dashboard.open_dashboard)
        return

    days = result["days_remaining"]
    if days is not None and days < 0:
        days_left_in_grace = GRACE_DAYS - abs(days)
        messagebox.showwarning(
            "License Payment Due",
            f"Aapki monthly fee ka payment {abs(days)} din se pending hai.\n"
            f"Agle {days_left_in_grace} din mein pay na kiya to software band ho jayega."
        )

    dashboard.open_dashboard()


open_login_window(on_success=show_dashboard)