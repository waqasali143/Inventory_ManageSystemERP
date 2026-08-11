from tkinter import Entry, StringVar
from services.product_service import get_product_by_barcode


def create_scan_entry(parent, on_product_found, **entry_kwargs):
    """
    Creates an Entry widget that behaves as a barcode-scan field:
    when a barcode is scanned (scanner types the code + presses
    Enter automatically), on_product_found(product_row) is called
    with the matching product, and the field clears itself for the
    next scan.

    on_product_found: function that receives (id, name, cost_price,
                       sale_price, quantity, status, barcode)
    Returns the Entry widget - caller places it with .grid()/.pack().
    """
    scan_var = StringVar()
    entry = Entry(parent, textvariable=scan_var, **entry_kwargs)

    def handle_scan(event):
        code = scan_var.get().strip()
        scan_var.set("")

        if not code:
            return

        product = get_product_by_barcode(code)

        if product:
            on_product_found(product)
        else:
            from tkinter import messagebox
            messagebox.showerror("Not Found", f"No product found with barcode: {code}")

    entry.bind("<Return>", handle_scan)

    return entry