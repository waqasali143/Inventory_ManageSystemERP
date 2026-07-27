from tkinter import StringVar

# =====================================================================
# Before: every function (add_to_cart, remove_cart_item, clear_cart,
# save_purchase...) had to take 6 separate parameters:
#   gross_total, discount, discount_amount, tax, tax_amount, net_total
#
# After: those 6 StringVars live inside one PurchaseSummary object,
# so functions take a single `summary` parameter instead.
# =====================================================================


class PurchaseSummary:

    def __init__(self):
        self.gross_total = StringVar(value="0.00")
        self.discount = StringVar(value="0.00")            # Percentage
        self.discount_amount = StringVar(value="0.00")     # Auto Calculated
        self.tax = StringVar(value="0.00")                 # Percentage
        self.tax_amount = StringVar(value="0.00")           # Auto Calculated
        self.net_total = StringVar(value="0.00")

    # ---------------------------------------------------
    # Reset all fields back to their default values
    # ---------------------------------------------------
    def reset(self):
        self.gross_total.set("0.00")
        self.discount.set("0.00")
        self.discount_amount.set("0.00")
        self.tax.set("0.00")
        self.tax_amount.set("0.00")
        self.net_total.set("0.00")

    # ---------------------------------------------------
    # Convert all fields to floats, ready for saving to DB
    # ---------------------------------------------------
    def as_floats(self):
        return (
            float(self.gross_total.get()),
            float(self.discount.get()),
            float(self.discount_amount.get()),
            float(self.tax.get()),
            float(self.tax_amount.get()),
            float(self.net_total.get())
        )
