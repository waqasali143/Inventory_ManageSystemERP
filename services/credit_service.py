from tkinter import messagebox
from repositories import credit_repository as repo
from utils import event_bus

# =====================================================================
# Business logic for the Credit Ledger (customer receivables and
# supplier payables). No raw SQL here - that's in credit_repository.py.
# =====================================================================


# =====================================
# Customer Side
# =====================================
def get_customer_balance(customer_id):
    return repo.fetch_customer_balance(customer_id)


def get_customers_with_balance():
    return repo.fetch_customers_with_balance()


def get_customers_with_balance_detailed(search_term=None):
    """Same list, plus Amount Paid and Last Payment Amount - used by
    the Credit Ledger list view for parity with the Reports Credit tab.
    search_term optionally matches customer name OR an invoice (sale)
    number, so staff can look a customer up by either."""
    return repo.fetch_customers_with_balance_report(search_term)


def get_customer_payment_history(customer_id):
    return repo.fetch_customer_payment_history(customer_id)


def get_customer_credit_sales(customer_id):
    return repo.fetch_customer_credit_sales(customer_id)


def record_customer_payment(customer_id, amount_str, notes="", sale_id=None):
    """
    sale_id: when provided, the payment is applied directly to that
    invoice (reducing its own balance and updating its status), in
    addition to being logged in the payment history. When omitted,
    the payment only reduces the customer's overall balance, the same
    as before this existed.
    """

    try:
        amount = float(amount_str)
    except ValueError:
        messagebox.showerror("Validation Error", "Payment amount must be a number.")
        return False

    if amount <= 0:
        messagebox.showerror("Validation Error", "Payment amount must be greater than zero.")
        return False

    current_balance = repo.fetch_customer_balance(customer_id)

    if amount > current_balance:
        confirm = messagebox.askyesno(
            "Amount Exceeds Balance",
            f"This customer only owes {current_balance:.2f}, but you entered "
            f"{amount:.2f}. Record it anyway (customer will show a credit balance)?"
        )
        if not confirm:
            return False

    repo.insert_customer_payment(customer_id, amount, notes.strip(), sale_id)

    if sale_id is not None:
        repo.apply_payment_to_sale(sale_id, amount)

    event_bus.publish()

    messagebox.showinfo("Success", "Payment recorded successfully.")
    return True


# =====================================
# Supplier Side
# =====================================
def get_supplier_balance(supplier_id):
    return repo.fetch_supplier_balance(supplier_id)


def get_suppliers_with_balance():
    return repo.fetch_suppliers_with_balance()


def get_suppliers_with_balance_detailed(search_term=None):
    """Same list, plus Amount Paid and Last Payment Amount - supplier
    mirror of get_customers_with_balance_detailed()."""
    return repo.fetch_suppliers_with_balance_report(search_term)


def get_supplier_payment_history(supplier_id):
    return repo.fetch_supplier_payment_history(supplier_id)


def get_supplier_credit_purchases(supplier_id):
    return repo.fetch_supplier_credit_purchases(supplier_id)


def record_supplier_payment(supplier_id, amount_str, notes="", purchase_id=None):
    """Supplier-side mirror of record_customer_payment()."""

    try:
        amount = float(amount_str)
    except ValueError:
        messagebox.showerror("Validation Error", "Payment amount must be a number.")
        return False

    if amount <= 0:
        messagebox.showerror("Validation Error", "Payment amount must be greater than zero.")
        return False

    current_balance = repo.fetch_supplier_balance(supplier_id)

    if amount > current_balance:
        confirm = messagebox.askyesno(
            "Amount Exceeds Balance",
            f"You only owe this supplier {current_balance:.2f}, but you entered "
            f"{amount:.2f}. Record it anyway?"
        )
        if not confirm:
            return False

    repo.insert_supplier_payment(supplier_id, amount, notes.strip(), purchase_id)

    if purchase_id is not None:
        repo.apply_payment_to_purchase(purchase_id, amount)

    event_bus.publish()

    messagebox.showinfo("Success", "Payment recorded successfully.")
    return True


# =====================================
# Dashboard / Reports Summary
# =====================================
def get_total_receivable():
    return repo.fetch_total_receivable()


def get_total_payable():
    return repo.fetch_total_payable()


def get_credit_report_data(search_term=None):
    """One call for the Reports 'Credit' tab - customers, suppliers,
    and both grand totals together."""
    return repo.fetch_credit_report_data(search_term)