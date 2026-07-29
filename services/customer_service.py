from tkinter import messagebox
from repositories import customer_repository as repo
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
# Save Customer
# =====================================
def save_customer(name, contact, email, address):

    is_valid, message = validate_customer_data(name, contact)
    if not is_valid:
        messagebox.showerror("Validation Error", message)
        return False

    repo.insert_customer(
        name.get().strip(),
        contact.get().strip(),
        email.get().strip(),
        address.get().strip()
    )

    event_bus.publish()

    messagebox.showinfo("Success", "Customer Added Successfully")
    return True

# =====================================
# Update Customer
# =====================================
def update_customer(selected_id, name, contact, email, address):

    if not selected_id.get():
        messagebox.showerror("Error", "Please select a customer first.")
        return False

    is_valid, message = validate_customer_data(name, contact)
    if not is_valid:
        messagebox.showerror("Validation Error", message)
        return False

    repo.update_customer(
        selected_id.get(),
        name.get().strip(),
        contact.get().strip(),
        email.get().strip(),
        address.get().strip()
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
