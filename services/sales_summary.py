from tkinter import StringVar

# =====================================================================
# Same pattern as services/purchase_summary.py — kept consistent so
# both modules calculate discount/tax the same way (percentage with
# an auto-calculated amount), instead of Sales using a different
# "flat number" approach than Purchase.
# =====================================================================

class SalesSummary:

    def __init__(self):
        self.gross_total = StringVar(value="0.00")
        self.discount = StringVar(value="0.00")           # Percentage
        self.discount_amount = StringVar(value="0.00")    # Auto Calculated
        self.tax = StringVar(value="0.00")                # Percentage
        self.tax_amount = StringVar(value="0.00")          # Auto Calculated
        self.net_total = StringVar(value="0.00")

    def reset(self):
        self.gross_total.set("0.00")
        self.discount.set("0.00")
        self.discount_amount.set("0.00")
        self.tax.set("0.00")
        self.tax_amount.set("0.00")
        self.net_total.set("0.00")

    def as_floats(self):
        return (
            float(self.gross_total.get()),
            float(self.discount.get()),
            float(self.discount_amount.get()),
            float(self.tax.get()),
            float(self.tax_amount.get()),
            float(self.net_total.get())
        )