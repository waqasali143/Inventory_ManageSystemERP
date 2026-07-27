from tkinter import Label, Entry, Button
# from utils.ui_helpers import add_buttons, labeled_entry


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