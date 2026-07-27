
import ctypes
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    pass

from database.database import connect
from tkinter import Tk
from views import dashboard
from views import login

# Database create 
connect()

# Main window
root = Tk()
root.withdraw()      # Main window hide

# Login Window 
# login.open_login()

#  Open Dashboard
dashboard.open_dashboard()

root.mainloop()