
from tkinter import messagebox
from repositories import user_repository as repo
from utils import event_bus

from repositories import role_repository

def get_available_roles():
    """Role names for the dropdown - pulled live from the roles table."""
    return [name for _id, name in role_repository.fetch_roles()]
# =====================================
# Validation
# =====================================
def validate_user_data(full_name, username, password, role):

    if username.get().strip() == "":
        return False, "Username is required."

    if len(username.get().strip()) < 3:
        return False, "Username must be at least 3 characters."

    if password.get().strip() == "":
        return False, "Password is required."

    if len(password.get().strip()) < 4:
        return False, "Password must be at least 4 characters."

    if role.get() not in get_available_roles():
        return False, "Please select a valid role."
    
    return True, ""

# =====================================
# Load
# =====================================
def load_users():
    return repo.fetch_users()

# =====================================
# Save User
# =====================================
def save_user(full_name, username, password, role):

    is_valid, message = validate_user_data(full_name, username, password, role)
    if not is_valid:
        messagebox.showerror("Validation Error", message)
        return False

    if repo.fetch_user_by_username(username.get().strip()):
        messagebox.showerror("Error", "Username already exists!")
        return False

    repo.insert_user(
        full_name.get().strip(),
        username.get().strip(),
        password.get().strip(),
        role.get()
    )

    event_bus.publish()

    messagebox.showinfo("Success", "User Added Successfully")
    return True

# =====================================
# Deactivate / Reactivate User
# =====================================
def set_user_status(selected_id, status):

    if not selected_id.get():
        messagebox.showerror("Error", "Please select a user first.")
        return False

    repo.update_user_status(selected_id.get(), status)

    event_bus.publish()

    messagebox.showinfo("Success", f"User marked as {status}.")
    return True