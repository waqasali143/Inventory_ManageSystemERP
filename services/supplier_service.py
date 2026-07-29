
from tkinter import messagebox
from repositories import supplier_repository as repo
from utils import event_bus

# =====================================
# Validation
# =====================================
def validate_supplier_data(name, contact):

    supplier_name = name.get().strip()

    if supplier_name == "":
        return False, "Supplier Name is required."

    if len(supplier_name) < 2:
        return False, "Supplier Name must contain at least 2 characters."

    if contact.get().strip() == "":
        return False, "Contact is required."

    return True, ""

# =====================================
# Load / Search
# =====================================
def load_suppliers(search_term=None):
    return repo.fetch_suppliers(search_term)

# =====================================
# Save Supplier
# =====================================
def save_supplier(name, contact, email, address):

    is_valid, message = validate_supplier_data(name, contact)
    if not is_valid:
        messagebox.showerror("Validation Error", message)
        return False

    supplier_name = name.get().strip()

    if repo.fetch_supplier_by_name(supplier_name):
        messagebox.showerror("Error", "Supplier already exists!")
        return False

    repo.insert_supplier(
        supplier_name,
        contact.get().strip(),
        email.get().strip(),
        address.get().strip()
    )

    event_bus.publish()

    messagebox.showinfo("Success", "Supplier Added Successfully")
    return True

# =====================================
# Update Supplier
# =====================================
def update_supplier(selected_id, name, contact, email, address):

    if not selected_id.get():
        messagebox.showerror("Error", "Please select a supplier first.")
        return False

    is_valid, message = validate_supplier_data(name, contact)
    if not is_valid:
        messagebox.showerror("Validation Error", message)
        return False

    supplier_name = name.get().strip()

    if repo.fetch_supplier_by_name(supplier_name, exclude_id=selected_id.get()):
        messagebox.showerror("Duplicate Supplier", "Supplier name already exists.")
        return False

    repo.update_supplier(
        selected_id.get(),
        supplier_name,
        contact.get().strip(),
        email.get().strip(),
        address.get().strip()
    )

    event_bus.publish()

    messagebox.showinfo("Success", "Supplier Updated Successfully")
    return True

# =====================================
# Delete Supplier
# (falls back to deactivating if the supplier is referenced by a
#  past purchase - hard deleting it would break that history)
# =====================================
def delete_supplier(selected_id):

    if not selected_id.get():
        messagebox.showerror("Error", "Please select a supplier first.")
        return False

    confirm = messagebox.askyesno(
        "Confirm Delete",
        "Are you sure you want to delete this supplier?"
    )
    if not confirm:
        return False

    success, reason = repo.delete_supplier(selected_id.get())

    if success:
        event_bus.publish()
        messagebox.showinfo("Success", "Supplier Deleted Successfully")
        return True

    if reason == "in_use":
        deactivate = messagebox.askyesno(
            "Cannot Delete",
            "This supplier is used in existing purchase records, "
            "so it can't be deleted.\n\n"
            "Do you want to mark it as Inactive instead? "
            "(It will be hidden from new purchases, but its "
            "history stays intact.)"
        )
        if deactivate:
            repo.set_supplier_status(selected_id.get(), "Inactive")
            event_bus.publish()
            messagebox.showinfo("Success", "Supplier marked as Inactive.")
            return True

    return False