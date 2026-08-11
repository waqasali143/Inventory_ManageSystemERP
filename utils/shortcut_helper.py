# =====================================================================
# Central place to wire keyboard shortcuts (F2=Save, F3=New, Ctrl+P=Print
# etc.) onto any Toplevel window - so every screen wires shortcuts the
# same one-line way instead of each file writing its own bind() calls.
# =====================================================================


def bind_shortcuts(win, shortcuts):
    """
    Registers keyboard shortcuts on a single window.

    win: the Toplevel (or root) the shortcuts should apply to.
    shortcuts: dict of {tkinter key-sequence: callback}, e.g.
        {
            "<F2>": handle_save,
            "<F3>": new_sale,
            "<Control-p>": print_invoice,
        }

    Bound with win.bind() (not bind_all) on purpose - this scopes the
    shortcut to THIS window only, so if two windows are open at once
    (e.g. Sales + Sales History), F2 in one never fires the other's
    handler. Function keys and Ctrl-combinations pass through Entry/
    Combobox widgets untouched, so this works even while a field has
    focus and the user is typing.
    """
    for key_sequence, callback in shortcuts.items():
        win.bind(key_sequence, lambda event, cb=callback: cb())
