from tkinter import Label, Entry, Button
# from utils.ui_helpers import add_buttons, labeled_entry
from tkcalendar import DateEntry
from utils.theme import PRIMARY, WHITE
# ====================================================================

def add_buttons(parent, buttons, width=16):
    """buttons: list of (text, command) tuples"""
    for i, (text, command) in enumerate(buttons):
        Button(
            parent, text=text, width=width, command=command
        ).grid(row=0, column=i, padx=5, pady=5, sticky="ew")


def labeled_entry(parent, text, row, col, variable, readonly=False, justify="right"):
    Label(parent, text=text).grid(row=row, column=col, padx=10, pady=8, sticky="w")

    entry = Entry(
        parent, textvariable=variable,
        state="readonly" if readonly else "normal",
        justify=justify
    )
    entry.grid(row=row, column=col + 1, padx=10, pady=8, sticky="ew")
    return entry
# =============================================================
# ===== Date Picker ==============
def labeled_date_picker(parent, text, row, col, width=12):
    """
    Places a Label at (row, col) and a DateEntry (calendar picker)
    at (row, col+1). Returns the DateEntry widget - call
    .get_date().isoformat() on it to get a "YYYY-MM-DD" string.
    """
    Label(parent, text=text).grid(row=row, column=col, padx=10, pady=8, sticky="w")

    picker = DateEntry(
        parent, width=width, date_pattern="yyyy-mm-dd",
        background=PRIMARY, foreground=WHITE, borderwidth=2,
        showweeknumbers=False
    )
    picker.grid(row=row, column=col + 1, padx=10, pady=8, sticky="ew")

    return picker