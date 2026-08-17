from tkinter import messagebox
from repositories import customer_repository as repo
from services import credit_service
from utils import event_bus

# =====================================
# Validation
# =====================================
def validate_customer_data(name, contact):

    customer_name = name.get().strip()

    if customer_name == "":
        return False, "Customer Name is required."

    if len(customer_name) < 2:
        return False, "Customer Name must contain at least 2 characters."

    if contact.get().strip() == "":
        return False, "Contact is required."

    return True, ""

# =====================================
# Load / Search
# =====================================
def load_customers(search_term=None):
    return repo.fetch_customers(search_term)

# =====================================
# Quick Add (POS - walk-in customer)
# Lightweight path used by the POS window when a typed customer name
# doesn't match an existing record: no tkinter Variable wrapping, no
# validation dialog/popup - just the essentials (name + contact) so
# checkout isn't interrupted. Anything more (email/address/NTN/Filer
# status) can be filled in later from the Customers screen.
# =====================================
def quick_add_customer(name, contact):
    new_id = repo.insert_customer(name.strip(), contact.strip(), "", "", "", 0)
    event_bus.publish()
    return new_id


WALKIN_CUSTOMER_NAME = "Walk-in Customer"


def get_or_create_walkin_customer_id():
    """
    Used by POS when the Customer field is left blank - every nameless
    sale is attributed to one shared "Walk-in Customer" record instead
    of leaving the sale without a customer at all (which the rest of
    the app - Credit Ledger, per-customer history - doesn't expect).
    """
    existing_id = repo.fetch_customer_id_by_name_and_contact(WALKIN_CUSTOMER_NAME, "")
    if existing_id is not None:
        return existing_id

    new_id = repo.insert_customer(WALKIN_CUSTOMER_NAME, "", "", "", "", 0)
    event_bus.publish()
    return new_id


def get_customer_id_by_name_and_contact(name, contact):
    return repo.fetch_customer_id_by_name_and_contact(name, contact)

# =====================================
# Save Customer
# =====================================
def save_customer(name, contact, email, address, ntn=None, is_filer=None):

    is_valid, message = validate_customer_data(name, contact)
    if not is_valid:
        messagebox.showerror("Validation Error", message)
        return False

    ntn_value = ntn.get().strip() if ntn else ""
    filer_value = int(is_filer.get()) if is_filer else 0

    repo.insert_customer(
        name.get().strip(),
        contact.get().strip(),
        email.get().strip(),
        address.get().strip(),
        ntn_value,
        filer_value
    )

    event_bus.publish()

    messagebox.showinfo("Success", "Customer Added Successfully")
    return True

# =====================================
# Update Customer
# =====================================
def update_customer(selected_id, name, contact, email, address, ntn=None, is_filer=None):

    if not selected_id.get():
        messagebox.showerror("Error", "Please select a customer first.")
        return False

    is_valid, message = validate_customer_data(name, contact)
    if not is_valid:
        messagebox.showerror("Validation Error", message)
        return False

    ntn_value = ntn.get().strip() if ntn else ""
    filer_value = int(is_filer.get()) if is_filer else 0

    repo.update_customer(
        selected_id.get(),
        name.get().strip(),
        contact.get().strip(),
        email.get().strip(),
        address.get().strip(),
        ntn_value,
        filer_value
    )

    event_bus.publish()

    messagebox.showinfo("Success", "Customer Updated Successfully")
    return True

# =====================================
# Delete Customer
# (falls back to deactivating if the customer is referenced by a
#  past sale - hard deleting it would break that history)
# =====================================
def delete_customer(selected_id):

    if not selected_id.get():
        messagebox.showerror("Error", "Please select a customer first.")
        return False

    confirm = messagebox.askyesno(
        "Confirm Delete",
        "Are you sure you want to delete this customer?"
    )
    if not confirm:
        return False

    success, reason = repo.delete_customer(selected_id.get())

    if success:
        event_bus.publish()
        messagebox.showinfo("Success", "Customer Deleted Successfully")
        return True

    if reason == "in_use":
        deactivate = messagebox.askyesno(
            "Cannot Delete",
            "This customer is used in existing sale records, "
            "so it can't be deleted.\n\n"
            "Do you want to mark it as Inactive instead? "
            "(It will be hidden from new sales, but its "
            "history stays intact.)"
        )
        if deactivate:
            repo.set_customer_status(selected_id.get(), "Inactive")
            event_bus.publish()
            messagebox.showinfo("Success", "Customer marked as Inactive.")
            return True

    return False
# ===================================================
# = = = = = wrapper = = = = =

def get_customer_filer_status(customer_id):
    return repo.fetch_customer_filer_status(customer_id)
# ===========================================================
def get_customer_ntn(customer_id):
    return repo.fetch_customer_ntn(customer_id)

# =====================================
# Credit Balance (thin wrapper so customer.py only ever imports
# from "services", never directly from "credit_service"/repositories)
# =====================================
def get_customer_balance(customer_id):
    return credit_service.get_customer_balance(customer_id)