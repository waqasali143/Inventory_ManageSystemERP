import ctypes
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    pass

from database.database import connect
from views.login import open_login_window
from views import dashboard

connect()


def show_dashboard():
    dashboard.open_dashboard()


open_login_window(on_success=show_dashboard)